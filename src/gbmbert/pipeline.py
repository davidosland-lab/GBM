"""End-to-end local literature pipeline for GBM-AI research artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tqdm import tqdm

from gbmbert.annotation.schema import EntityType
from gbmbert.extraction.evidence import classify_pubmed_jsonl
from gbmbert.extraction.io import load_pubmed_jsonl, save_entity_jsonl
from gbmbert.extraction.pipeline import (
    DEFAULT_MODEL_NAME,
    BiomedicalNERPipeline,
    run_extraction,
)
from gbmbert.ingest.manifest import (
    build_corpus_manifest,
    save_corpus_manifest,
    save_corpus_manifest_markdown,
)
from gbmbert.knowledge_graph.build_records import build_graph_records_from_jsonl
from gbmbert.knowledge_graph.quality import (
    GraphQualityReport,
    analyze_graph_records_jsonl,
    save_quality_report_json,
    save_quality_report_markdown,
)
from gbmbert.paths import standard_paths

LOGGER = logging.getLogger(__name__)


class PipelineValidationError(RuntimeError):
    """Raised when dry-run graph-record validation finds invalid records."""


@dataclass(frozen=True)
class LiteraturePipelineOutputs:
    entities_jsonl: Path
    evidence_jsonl: Path
    graph_jsonl: Path
    quality_json: Path
    quality_markdown: Path
    manifest_json: Path
    manifest_markdown: Path
    quality_report: GraphQualityReport


def run_literature_pipeline(
    pubmed_jsonl: str | Path,
    *,
    output_dir: str | Path = standard_paths().processed_dir / "literature_pipeline",
    entities_output: str | Path | None = None,
    evidence_output: str | Path | None = None,
    graph_output: str | Path | None = None,
    quality_json_output: str | Path | None = None,
    quality_markdown_output: str | Path | None = None,
    manifest_json_output: str | Path | None = None,
    manifest_markdown_output: str | Path | None = None,
    entity_mode: str = "model",
    lexicon_path: str | Path | None = None,
    model_name: str = DEFAULT_MODEL_NAME,
    device: int = -1,
    reuse_existing: bool = False,
    fail_on_invalid: bool = True,
    entity_extractor: BiomedicalNERPipeline | None = None,
) -> LiteraturePipelineOutputs:
    """Run PubMed JSONL through extraction, evidence classification, graph build, and validation."""

    pubmed_path = Path(pubmed_jsonl)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    entities_path = Path(entities_output) if entities_output else output_path / "entities.jsonl"
    evidence_path = Path(evidence_output) if evidence_output else output_path / "evidence_claims.jsonl"
    graph_path = Path(graph_output) if graph_output else output_path / "graph_records.jsonl"
    quality_json_path = (
        Path(quality_json_output) if quality_json_output else output_path / "graph_quality_report.json"
    )
    quality_markdown_path = (
        Path(quality_markdown_output)
        if quality_markdown_output
        else output_path / "graph_quality_report.md"
    )
    manifest_json_path = (
        Path(manifest_json_output) if manifest_json_output else output_path / "pipeline_manifest.json"
    )
    manifest_markdown_path = (
        Path(manifest_markdown_output)
        if manifest_markdown_output
        else output_path / "pipeline_manifest.md"
    )

    _run_entity_stage(
        pubmed_path,
        entities_path,
        model_name=model_name,
        device=device,
        entity_mode=entity_mode,
        lexicon_path=lexicon_path,
        reuse_existing=reuse_existing,
        entity_extractor=entity_extractor,
    )
    _run_evidence_stage(pubmed_path, evidence_path, reuse_existing=reuse_existing)
    _run_graph_stage(pubmed_path, entities_path, evidence_path, graph_path, reuse_existing=reuse_existing)

    quality_report = analyze_graph_records_jsonl(graph_path)
    save_quality_report_json(quality_report, quality_json_path)
    save_quality_report_markdown(quality_report, quality_markdown_path)
    manifest = build_corpus_manifest(
        [pubmed_path, entities_path, evidence_path, graph_path, quality_json_path, quality_markdown_path],
        name=output_path.name,
        source="GBM-AI literature pipeline",
        command=f"gbmbert-run-pipeline {pubmed_path} --output-dir {output_path} --entity-mode {entity_mode}",
        notes=[
            "Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.",
            f"Entity mode: {entity_mode}",
            f"Lexicon: {lexicon_path or 'built-in default'}",
        ],
    )
    save_corpus_manifest(manifest, manifest_json_path)
    save_corpus_manifest_markdown(manifest, manifest_markdown_path)
    if fail_on_invalid and quality_report.invalid_record_count:
        raise PipelineValidationError(
            f"Graph-record validation found {quality_report.invalid_record_count} invalid record(s)"
        )

    return LiteraturePipelineOutputs(
        entities_jsonl=entities_path,
        evidence_jsonl=evidence_path,
        graph_jsonl=graph_path,
        quality_json=quality_json_path,
        quality_markdown=quality_markdown_path,
        manifest_json=manifest_json_path,
        manifest_markdown=manifest_markdown_path,
        quality_report=quality_report,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local GBM-AI PubMed-to-graph pipeline and produce a pre-load quality report."
        )
    )
    parser.add_argument("pubmed_jsonl", type=Path, help="Input PubMed paper JSONL path.")
    parser.add_argument("--output-dir", type=Path, default=standard_paths().processed_dir / "literature_pipeline")
    parser.add_argument("--entities-output", type=Path)
    parser.add_argument("--evidence-output", type=Path)
    parser.add_argument("--graph-output", type=Path)
    parser.add_argument("--quality-json-output", type=Path)
    parser.add_argument("--quality-markdown-output", type=Path)
    parser.add_argument("--manifest-json-output", type=Path)
    parser.add_argument("--manifest-markdown-output", type=Path)
    parser.add_argument(
        "--entity-mode",
        choices=["model", "lexicon"],
        default="model",
        help="Use the Hugging Face model or a local deterministic lexicon extractor.",
    )
    parser.add_argument(
        "--lexicon",
        type=Path,
        default=Path("configs/extraction/lexicon_gbm_v1.json"),
        help="Lexicon JSON path used when --entity-mode lexicon.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Hugging Face NER model name.")
    parser.add_argument("--device", type=int, default=-1, help="Transformers device id; use -1 for CPU.")
    parser.add_argument("--reuse-existing", action="store_true", help="Skip stages whose output exists.")
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help="Complete even if dry-run graph validation finds invalid records.",
    )
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        outputs = run_literature_pipeline(
            args.pubmed_jsonl,
            output_dir=args.output_dir,
            entities_output=args.entities_output,
            evidence_output=args.evidence_output,
            graph_output=args.graph_output,
            quality_json_output=args.quality_json_output,
            quality_markdown_output=args.quality_markdown_output,
            manifest_json_output=args.manifest_json_output,
            manifest_markdown_output=args.manifest_markdown_output,
            entity_mode=args.entity_mode,
            lexicon_path=args.lexicon,
            model_name=args.model,
            device=args.device,
            reuse_existing=args.reuse_existing,
            fail_on_invalid=not args.allow_invalid,
        )
    except PipelineValidationError as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info("Saved entities to %s", outputs.entities_jsonl)
    LOGGER.info("Saved evidence claims to %s", outputs.evidence_jsonl)
    LOGGER.info("Saved graph records to %s", outputs.graph_jsonl)
    LOGGER.info("Saved quality reports to %s and %s", outputs.quality_json, outputs.quality_markdown)
    LOGGER.info("Saved pipeline manifests to %s and %s", outputs.manifest_json, outputs.manifest_markdown)
    LOGGER.info(
        "Validated %d graph records with %d invalid records",
        outputs.quality_report.record_count,
        outputs.quality_report.invalid_record_count,
    )
    return 0


def _run_entity_stage(
    pubmed_path: Path,
    entities_path: Path,
    *,
    model_name: str,
    device: int,
    entity_mode: str,
    lexicon_path: str | Path | None,
    reuse_existing: bool,
    entity_extractor: BiomedicalNERPipeline | None,
) -> None:
    if reuse_existing and entities_path.exists():
        LOGGER.info("Reusing existing entity JSONL at %s", entities_path)
        return
    if entity_extractor is None:
        if entity_mode == "lexicon":
            entity_extractor = BiomedicalNERPipeline(
                ner_pipeline=create_lexicon_ner_pipeline(lexicon_path)
            )
        else:
            run_extraction(pubmed_path, entities_path, model_name=model_name, device=device)
            return

    papers = list(load_pubmed_jsonl(pubmed_path))
    LOGGER.info("Loaded %d PubMed records from %s", len(papers), pubmed_path)
    results = (
        entity_extractor.extract_from_paper(paper)
        for paper in tqdm(papers, desc="Extracting entities", unit="paper")
    )
    save_entity_jsonl(results, entities_path)


def create_lexicon_ner_pipeline(lexicon_path: str | Path | None = None) -> callable:
    """Create a small deterministic NER function for offline smoke baselines."""

    entries = load_lexicon_entries(lexicon_path)
    compiled = [
        (re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE), term, label)
        for term, label in entries
    ]

    def ner(text: str) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for pattern, term, label in compiled:
            for match in pattern.finditer(text):
                candidates.append(
                    {
                        "word": match.group(0),
                        "entity_group": label.value,
                        "start": match.start(),
                        "end": match.end(),
                        "score": 0.75,
                    }
                )
        selected: list[dict[str, Any]] = []
        occupied: list[tuple[int, int]] = []
        for candidate in sorted(
            candidates,
            key=lambda item: (int(item["start"]), -(int(item["end"]) - int(item["start"]))),
        ):
            start = int(candidate["start"])
            end = int(candidate["end"])
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            selected.append(candidate)
            occupied.append((start, end))
        return sorted(selected, key=lambda item: (int(item["start"]), int(item["end"]), str(item["word"])))

    return ner


def load_lexicon_entries(lexicon_path: str | Path | None = None) -> tuple[tuple[str, EntityType], ...]:
    """Load lexicon entries from JSON, falling back to the built-in GBM smoke lexicon."""

    if lexicon_path is not None and Path(lexicon_path).exists():
        payload = json.loads(Path(lexicon_path).read_text(encoding="utf-8"))
        entries = []
        for item in payload.get("entries", []):
            entries.append((str(item["term"]), EntityType(str(item["label"]))))
        return tuple(entries)

    return (
        ("glioblastoma", EntityType.DISEASE),
        ("GBM", EntityType.DISEASE),
        ("MGMT methylation", EntityType.BIOMARKER),
        ("MGMT", EntityType.GENE),
        ("EGFR amplification", EntityType.BIOMARKER),
        ("EGFR", EntityType.GENE),
        ("IDH-wildtype", EntityType.BIOMARKER),
        ("IDH wildtype", EntityType.BIOMARKER),
        ("IDH-mutant", EntityType.BIOMARKER),
        ("IDH mutant", EntityType.BIOMARKER),
        ("temozolomide resistance", EntityType.OUTCOME),
        ("temozolomide response", EntityType.OUTCOME),
        ("temozolomide", EntityType.DRUG),
        ("TMZ", EntityType.DRUG),
        ("immunotherapy", EntityType.TREATMENT),
        ("CAR-T", EntityType.TREATMENT),
        ("dendritic cell vaccine", EntityType.TREATMENT),
        ("checkpoint inhibitor", EntityType.TREATMENT),
        ("blood-brain barrier", EntityType.DELIVERY_MODIFIER),
        ("focused ultrasound", EntityType.DELIVERY_MODIFIER),
        ("glioblastoma stem cells", EntityType.CELL_TYPE),
        ("stem cells", EntityType.CELL_TYPE),
        ("recurrence", EntityType.OUTCOME),
        ("survival", EntityType.OUTCOME),
        ("response", EntityType.OUTCOME),
    )


def _run_evidence_stage(pubmed_path: Path, evidence_path: Path, *, reuse_existing: bool) -> None:
    if reuse_existing and evidence_path.exists():
        LOGGER.info("Reusing existing evidence JSONL at %s", evidence_path)
        return
    classify_pubmed_jsonl(pubmed_path, evidence_path)


def _run_graph_stage(
    pubmed_path: Path,
    entities_path: Path,
    evidence_path: Path,
    graph_path: Path,
    *,
    reuse_existing: bool,
) -> None:
    if reuse_existing and graph_path.exists():
        LOGGER.info("Reusing existing graph-record JSONL at %s", graph_path)
        return
    build_graph_records_from_jsonl(
        pubmed_jsonl=pubmed_path,
        entity_jsonl=entities_path,
        output_jsonl=graph_path,
        evidence_jsonl=evidence_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
