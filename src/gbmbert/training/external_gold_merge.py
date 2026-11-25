"""GBM-relevance filter + external/curated gold merge (PR165).

Filters external-corpus entity/relation JSONL to GBM-adjacent documents, then
merges them with human-reviewed curated gold while preserving dual provenance:

- curated / human-reviewed rows keep reviewer fields and gain
  ``source_type=human_reviewed`` when missing
- external rows keep ``source_type=external_corpus`` + ``source_corpus``
- relation rows also keep ``relation_pack_source_type`` when already present

Observe-only, research-use only. Does not promote a dataset or claim a validated
GBM-BERT model exists.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.external_corpus_import import EXTERNAL_SOURCE_TYPE

DEFAULT_KEYWORDS = Path("configs/extraction/gbm_relevance_keywords.json")
DEFAULT_EBM_NLP_GBM_ENTITIES = Path("data/training/external_corpus/ebm_nlp_gbm/gold_entities.jsonl")
HUMAN_REVIEWED_SOURCE_TYPE = "human_reviewed"
EXTERNAL_RELATION_PACK_SOURCE = "external_corpus"


@dataclass(frozen=True)
class ExternalGoldMergeReport:
    output_dir: str
    keywords_path: str
    external_entities_input: str
    external_relations_input: str
    curated_entities_inputs: list[str]
    curated_relations_inputs: list[str]
    curated_evidence_inputs: list[str]
    external_documents_total: int
    external_documents_kept: int
    external_documents_dropped: int
    matched_patterns: dict[str, int]
    entity_document_count: int
    ner_count: int
    relation_count: int
    evidence_count: int
    provenance_counts: dict[str, int]
    entity_label_counts: dict[str, int]
    relation_label_counts: dict[str, int]
    files: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_gbm_relevance_patterns(path: str | Path = DEFAULT_KEYWORDS) -> list[re.Pattern[str]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    patterns = payload.get("patterns") or []
    if not patterns:
        raise ValueError(f"no patterns found in keywords config: {path}")
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        compiled.append(re.compile(str(pattern), re.IGNORECASE))
    return compiled


def document_is_gbm_adjacent(text: str, patterns: list[re.Pattern[str]]) -> tuple[bool, list[str]]:
    matched = [pattern.pattern for pattern in patterns if pattern.search(text or "")]
    return bool(matched), matched


def filter_external_entities(
    rows: list[dict[str, Any]],
    *,
    patterns: list[re.Pattern[str]],
) -> tuple[list[dict[str, Any]], dict[str, int], int]:
    kept: list[dict[str, Any]] = []
    matched_counts: Counter[str] = Counter()
    dropped = 0
    for row in rows:
        ok, matched = document_is_gbm_adjacent(str(row.get("text") or ""), patterns)
        if not ok:
            dropped += 1
            continue
        for pattern in matched:
            matched_counts[pattern] += 1
        kept.append(row)
    return kept, dict(sorted(matched_counts.items())), dropped


def write_gbm_filtered_external_entities(
    *,
    external_entities_jsonl: str | Path,
    output_path: str | Path = DEFAULT_EBM_NLP_GBM_ENTITIES,
    keywords_path: str | Path = DEFAULT_KEYWORDS,
) -> tuple[Path, int, int]:
    """Write only GBM-adjacent external entity docs for fold-in to gold/BIO NER packs."""

    patterns = load_gbm_relevance_patterns(keywords_path)
    rows = _read_jsonl(external_entities_jsonl)
    kept, _, dropped = filter_external_entities(rows, patterns=patterns)
    tagged = [_ensure_external_entity_doc(row) for row in kept]
    path = Path(output_path)
    _write_jsonl(tagged, path)
    return path, len(tagged), dropped


def merge_external_gold_pack(
    *,
    output_dir: str | Path,
    external_entities_jsonl: str | Path,
    external_relations_jsonl: str | Path | None = None,
    curated_entities_jsonl: list[str | Path] | None = None,
    curated_relations_jsonl: list[str | Path] | None = None,
    curated_evidence_jsonl: list[str | Path] | None = None,
    keywords_path: str | Path = DEFAULT_KEYWORDS,
    apply_gbm_filter: bool = True,
) -> ExternalGoldMergeReport:
    """Filter external corpus rows to GBM-adjacent docs and merge with curated gold."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    files = {
        "entities": str(output_root / "gold_entities.jsonl"),
        "ner": str(output_root / "gold_ner.jsonl"),
        "relations": str(output_root / "gold_relations.jsonl"),
        "evidence": str(output_root / "gold_evidence.jsonl"),
        "manifest": str(output_root / "external_gold_merge_manifest.json"),
        "markdown": str(output_root / "external_gold_merge_manifest.md"),
    }
    warnings: list[str] = []

    patterns = load_gbm_relevance_patterns(keywords_path) if apply_gbm_filter else []
    external_docs = _read_jsonl(external_entities_jsonl)
    if apply_gbm_filter:
        kept_external, matched_patterns, dropped = filter_external_entities(external_docs, patterns=patterns)
    else:
        kept_external, matched_patterns, dropped = external_docs, {}, 0
        warnings.append("GBM relevance filter disabled; all external documents kept")

    curated_entity_paths = [Path(p) for p in (curated_entities_jsonl or [])]
    curated_relation_paths = [Path(p) for p in (curated_relations_jsonl or [])]
    curated_evidence_paths = [Path(p) for p in (curated_evidence_jsonl or [])]

    curated_docs = [_tag_human_reviewed_entity_doc(row) for path in curated_entity_paths for row in _read_jsonl(path)]
    external_docs_tagged = [_ensure_external_entity_doc(row) for row in kept_external]
    entity_docs = curated_docs + external_docs_tagged

    kept_pmids = {str(row.get("pmid") or "") for row in external_docs_tagged}
    external_relations: list[dict[str, Any]] = []
    if external_relations_jsonl:
        for row in _read_jsonl(external_relations_jsonl):
            pmid = str(row.get("source_pmid") or row.get("pmid") or "")
            if apply_gbm_filter and pmid not in kept_pmids:
                continue
            external_relations.append(_tag_external_relation(row))

    curated_relations = [_tag_human_reviewed_relation(row) for path in curated_relation_paths for row in _read_jsonl(path)]
    curated_evidence = [_tag_human_reviewed_evidence(row) for path in curated_evidence_paths for row in _read_jsonl(path)]

    relations = curated_relations + external_relations
    ner_rows = [_ner_row_from_entity_doc(doc, entity) for doc in entity_docs for entity in (doc.get("entities") or [])]

    _write_jsonl(entity_docs, files["entities"])
    _write_jsonl(ner_rows, files["ner"])
    _write_jsonl(relations, files["relations"])
    _write_jsonl(curated_evidence, files["evidence"])

    provenance_counts = Counter(_provenance_key(row) for row in [*entity_docs, *ner_rows, *relations, *curated_evidence])
    entity_label_counts = Counter(str(entity.get("label") or "") for doc in entity_docs for entity in (doc.get("entities") or []))
    relation_label_counts = Counter(str(row.get("label") or "") for row in relations)

    if not kept_external:
        warnings.append("no external documents retained after GBM relevance filter")
    if not curated_docs and not curated_relations and not curated_evidence:
        warnings.append("no curated inputs were provided; output is external-only")
    if not entity_docs:
        warnings.append("combined entity document set is empty")

    report = ExternalGoldMergeReport(
        output_dir=str(output_root),
        keywords_path=str(Path(keywords_path)),
        external_entities_input=str(Path(external_entities_jsonl)),
        external_relations_input=str(Path(external_relations_jsonl)) if external_relations_jsonl else "",
        curated_entities_inputs=[str(p) for p in curated_entity_paths],
        curated_relations_inputs=[str(p) for p in curated_relation_paths],
        curated_evidence_inputs=[str(p) for p in curated_evidence_paths],
        external_documents_total=len(external_docs),
        external_documents_kept=len(kept_external),
        external_documents_dropped=dropped,
        matched_patterns=matched_patterns,
        entity_document_count=len(entity_docs),
        ner_count=len(ner_rows),
        relation_count=len(relations),
        evidence_count=len(curated_evidence),
        provenance_counts=dict(sorted(provenance_counts.items())),
        entity_label_counts=dict(sorted((k, v) for k, v in entity_label_counts.items() if k)),
        relation_label_counts=dict(sorted((k, v) for k, v in relation_label_counts.items() if k)),
        files=files,
        warnings=warnings,
    )
    Path(files["manifest"]).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    Path(files["markdown"]).write_text(format_external_gold_merge_markdown(report), encoding="utf-8")
    return report


def format_external_gold_merge_markdown(report: ExternalGoldMergeReport) -> str:
    lines = [
        "# External Gold Pack Merge (GBM Filter)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- Keywords: `{report.keywords_path}`",
        f"- External entities: `{report.external_entities_input}`",
        f"- External relations: `{report.external_relations_input or 'none'}`",
        f"- External documents: {report.external_documents_total} total, {report.external_documents_kept} kept, {report.external_documents_dropped} dropped",
        f"- Entity documents (combined): {report.entity_document_count}",
        f"- NER rows: {report.ner_count}",
        f"- Relation rows: {report.relation_count}",
        f"- Evidence rows: {report.evidence_count}",
        "",
        "## Curated Inputs",
        *(
            (
                [f"- entities: `{path}`" for path in report.curated_entities_inputs]
                + [f"- relations: `{path}`" for path in report.curated_relations_inputs]
                + [f"- evidence: `{path}`" for path in report.curated_evidence_inputs]
            )
            or ["- none"]
        ),
        "",
        "## Matched GBM Patterns",
        *([f"- `{pattern}`: {count}" for pattern, count in report.matched_patterns.items()] or ["- none"]),
        "",
        "## Provenance",
        *([f"- {name}: {count}" for name, count in report.provenance_counts.items()] or ["- none"]),
        "",
        "## Entity Labels",
        *([f"- {label}: {count}" for label, count in report.entity_label_counts.items()] or ["- none"]),
        "",
        "## Relation Labels",
        *([f"- {label}: {count}" for label, count in report.relation_label_counts.items()] or ["- none"]),
        "",
        "## Files",
        *[f"- {key}: `{value}`" for key, value in sorted(report.files.items())],
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Filter external corpus rows to GBM-adjacent documents and merge with curated gold."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--external-entities-jsonl", type=Path, required=True)
    parser.add_argument("--external-relations-jsonl", type=Path)
    parser.add_argument("--curated-entities-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--curated-relations-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--curated-evidence-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS)
    parser.add_argument(
        "--no-gbm-filter",
        action="store_true",
        help="Keep all external documents (debug only; not recommended for GBM packs).",
    )
    parser.add_argument(
        "--filtered-entities-output",
        type=Path,
        help="Also write GBM-filtered external entity docs only (for gold/BIO NER fold-in).",
    )
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = merge_external_gold_pack(
        output_dir=args.output_dir,
        external_entities_jsonl=args.external_entities_jsonl,
        external_relations_jsonl=args.external_relations_jsonl,
        curated_entities_jsonl=args.curated_entities_jsonl,
        curated_relations_jsonl=args.curated_relations_jsonl,
        curated_evidence_jsonl=args.curated_evidence_jsonl,
        keywords_path=args.keywords,
        apply_gbm_filter=not args.no_gbm_filter,
    )
    if args.filtered_entities_output is not None and not args.no_gbm_filter:
        path, kept, dropped = write_gbm_filtered_external_entities(
            external_entities_jsonl=args.external_entities_jsonl,
            output_path=args.filtered_entities_output,
            keywords_path=args.keywords,
        )
        report.files["filtered_entities"] = str(path)
        report.warnings.append(f"wrote GBM-filtered external entities: {kept} kept, {dropped} dropped -> {path}")
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(format_external_gold_merge_markdown(report), encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_external_gold_merge_markdown(report))
    return 0 if report.entity_document_count else 1


# ------------------------------------------------------------------ helpers


def _tag_human_reviewed_entity_doc(row: dict[str, Any]) -> dict[str, Any]:
    tagged = dict(row)
    tagged.setdefault("source_type", HUMAN_REVIEWED_SOURCE_TYPE)
    tagged.setdefault("warning", RESEARCH_WARNING)
    return tagged


def _ensure_external_entity_doc(row: dict[str, Any]) -> dict[str, Any]:
    tagged = dict(row)
    tagged["source_type"] = str(tagged.get("source_type") or EXTERNAL_SOURCE_TYPE)
    tagged.setdefault("source_corpus", "")
    tagged.setdefault("warning", RESEARCH_WARNING)
    return tagged


def _tag_human_reviewed_relation(row: dict[str, Any]) -> dict[str, Any]:
    tagged = dict(row)
    tagged.setdefault("source_type", HUMAN_REVIEWED_SOURCE_TYPE)
    tagged.setdefault("warning", RESEARCH_WARNING)
    if not tagged.get("relation_pack_source_type"):
        label = str(tagged.get("label") or "")
        tagged["relation_pack_source_type"] = (
            "curated_no_relation" if label == "NO_RELATION" else "human_or_curated_positive"
        )
    tagged.setdefault("relation_pack_synthetic", False)
    return tagged


def _tag_external_relation(row: dict[str, Any]) -> dict[str, Any]:
    tagged = dict(row)
    tagged["source_type"] = str(tagged.get("source_type") or EXTERNAL_SOURCE_TYPE)
    tagged.setdefault("source_corpus", "")
    tagged.setdefault("relation_pack_source_type", EXTERNAL_RELATION_PACK_SOURCE)
    tagged.setdefault("relation_pack_synthetic", False)
    tagged.setdefault("warning", RESEARCH_WARNING)
    if not tagged.get("source_pmid") and tagged.get("pmid"):
        tagged["source_pmid"] = tagged["pmid"]
    tagged.setdefault("task", "relation")
    return tagged


def _tag_human_reviewed_evidence(row: dict[str, Any]) -> dict[str, Any]:
    tagged = dict(row)
    tagged.setdefault("source_type", HUMAN_REVIEWED_SOURCE_TYPE)
    tagged.setdefault("task", "evidence")
    tagged.setdefault("warning", RESEARCH_WARNING)
    return tagged


def _ner_row_from_entity_doc(doc: dict[str, Any], entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": "ner",
        "source_pmid": str(doc.get("pmid") or ""),
        "text": entity.get("text") or "",
        "label": entity.get("label") or "",
        "start": entity.get("start"),
        "end": entity.get("end"),
        "confidence": entity.get("confidence", 1.0),
        "normalized_text": entity.get("normalized_text") or entity.get("text") or "",
        "source_type": doc.get("source_type") or "",
        "source_corpus": doc.get("source_corpus") or "",
        "warning": RESEARCH_WARNING,
    }


def _provenance_key(row: dict[str, Any]) -> str:
    if row.get("relation_pack_source_type"):
        return str(row["relation_pack_source_type"])
    if row.get("source_type"):
        return str(row["source_type"])
    return "<missing>"


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
