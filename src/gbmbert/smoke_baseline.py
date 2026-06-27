"""Rebuild the local GBM-AI smoke baseline artifact bundle."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.artifacts import build_artifact_index, save_artifact_index_json, save_artifact_index_markdown
from gbmbert.extraction.review_queue import (
    export_review_queue,
    initialize_reviewed_queue,
    save_review_queue_summary_json,
    save_review_queue_summary_markdown,
    save_reviewed_queue_summary_json,
    save_reviewed_queue_summary_markdown,
    summarize_review_queue,
    summarize_reviewed_queue,
)
from gbmbert.ingest.clinicaltrials import search_and_save_clinical_trials
from gbmbert.ingest.manifest import build_corpus_manifest, save_corpus_manifest, save_corpus_manifest_markdown
from gbmbert.ingest.query_packs import run_query_pack
from gbmbert.knowledge_graph.cli import GraphLoadReport, _DryRunDriver, save_load_report_json, save_load_report_markdown
from gbmbert.knowledge_graph.loader import GraphLoader, LoaderConfig
from gbmbert.knowledge_graph.provenance import (
    audit_graph_provenance,
    save_provenance_audit_json,
    save_provenance_audit_markdown,
)
from gbmbert.knowledge_graph.quality import (
    analyze_graph_records_jsonl,
    analyze_unified_graph_records,
    save_quality_report_json,
    save_quality_report_markdown,
)
from gbmbert.knowledge_graph.trials import build_trial_graph_records_from_jsonl
from gbmbert.pipeline import run_literature_pipeline

LOGGER = logging.getLogger(__name__)
RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)


@dataclass(frozen=True)
class SmokeBaselinePaths:
    pubmed_raw: Path = Path("data/raw/ncbi_env_smoke_2026-06-23.jsonl")
    pubmed_pipeline_dir: Path = Path("data/processed/ncbi_env_smoke_pipeline")
    trial_raw: Path = Path("data/raw/clinicaltrials_gbm_smoke_2026-06-23.jsonl")
    trial_pipeline_dir: Path = Path("data/processed/clinicaltrials_gbm_smoke_2026-06-23")
    review_queue_jsonl: Path = Path("data/review/ncbi_env_smoke_review_queue.jsonl")
    review_queue_csv: Path = Path("data/review/ncbi_env_smoke_review_queue.csv")
    reviewed_queue_jsonl: Path = Path("data/review/ncbi_env_smoke_reviewed_queue.jsonl")
    reviewed_queue_csv: Path = Path("data/review/ncbi_env_smoke_reviewed_queue.csv")
    reports_dir: Path = Path("reports")
    lexicon_path: Path = Path("configs/extraction/lexicon_gbm_v1.json")


@dataclass(frozen=True)
class SmokeBaselineReport:
    offline: bool
    paths: dict[str, str]
    steps: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_smoke_baseline(
    *,
    paths: SmokeBaselinePaths = SmokeBaselinePaths(),
    offline: bool = False,
    pubmed_query_pack: str = "pubmed_gbm_v2",
    retmax_per_query: int = 2,
    trial_condition: str = "glioblastoma",
    trial_max_records: int = 5,
    reviewer: str = "smoke",
    overwrite_reviewed: bool = True,
) -> SmokeBaselineReport:
    """Rebuild baseline artifacts from live services or existing local raw files."""

    steps: list[str] = []
    warnings: list[str] = []
    if offline:
        _require_existing(paths.pubmed_raw)
        _require_existing(paths.trial_raw)
    else:
        run_query_pack(pubmed_query_pack, output=paths.pubmed_raw, retmax_per_query=retmax_per_query)
        steps.append(f"Refreshed PubMed raw snapshot: {paths.pubmed_raw}")
        search_and_save_clinical_trials(
            condition=trial_condition,
            output=paths.trial_raw,
            max_records=trial_max_records,
        )
        steps.append(f"Refreshed ClinicalTrials.gov raw snapshot: {paths.trial_raw}")

    pipeline_outputs = run_literature_pipeline(
        paths.pubmed_raw,
        output_dir=paths.pubmed_pipeline_dir,
        entity_mode="lexicon",
        lexicon_path=paths.lexicon_path,
        fail_on_invalid=False,
    )
    steps.append(f"Built PubMed pipeline graph records: {pipeline_outputs.graph_jsonl}")

    export_review_queue(
        evidence_jsonl=pipeline_outputs.evidence_jsonl,
        graph_jsonl=pipeline_outputs.graph_jsonl,
        output_jsonl=paths.review_queue_jsonl,
        csv_output=paths.review_queue_csv,
    )
    steps.append(f"Exported review queue: {paths.review_queue_jsonl}")
    initialize_reviewed_queue(
        paths.review_queue_jsonl,
        paths.reviewed_queue_jsonl,
        reviewer=reviewer,
        overwrite=overwrite_reviewed,
        csv_output=paths.reviewed_queue_csv,
    )
    steps.append(f"Initialized reviewed queue: {paths.reviewed_queue_jsonl}")

    review_summary = summarize_review_queue(paths.review_queue_jsonl)
    save_review_queue_summary_json(review_summary, paths.reports_dir / "review" / "ncbi_env_smoke_review_summary.json")
    save_review_queue_summary_markdown(review_summary, paths.reports_dir / "review" / "ncbi_env_smoke_review_summary.md")
    reviewed_summary = summarize_reviewed_queue(paths.reviewed_queue_jsonl)
    save_reviewed_queue_summary_json(reviewed_summary, paths.reports_dir / "review" / "ncbi_env_smoke_reviewed_summary.json")
    save_reviewed_queue_summary_markdown(reviewed_summary, paths.reports_dir / "review" / "ncbi_env_smoke_reviewed_summary.md")
    if reviewed_summary.warnings:
        warnings.extend(reviewed_summary.warnings)

    trial_graph = paths.trial_pipeline_dir / "trial_graph_records.jsonl"
    build_trial_graph_records_from_jsonl(paths.trial_raw, trial_graph)
    steps.append(f"Built trial graph records: {trial_graph}")
    trial_quality = analyze_graph_records_jsonl(trial_graph, record_type="trial")
    save_quality_report_json(trial_quality, paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_quality.json")
    save_quality_report_markdown(trial_quality, paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_quality.md")

    unified_quality = analyze_unified_graph_records([pipeline_outputs.graph_jsonl, trial_graph])
    save_quality_report_json(unified_quality, paths.reports_dir / "graph" / "ncbi_env_smoke_unified_quality.json")
    save_quality_report_markdown(unified_quality, paths.reports_dir / "graph" / "ncbi_env_smoke_unified_quality.md")
    steps.append("Generated graph quality reports")

    _write_dry_run_load_report(
        pipeline_outputs.graph_jsonl,
        record_type="pubmed",
        json_output=paths.reports_dir / "graph" / "ncbi_env_smoke_load_report.json",
        markdown_output=paths.reports_dir / "graph" / "ncbi_env_smoke_load_report.md",
    )
    _write_dry_run_load_report(
        trial_graph,
        record_type="trial",
        json_output=paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_load_report.json",
        markdown_output=paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_load_report.md",
    )
    steps.append("Generated dry-run graph load reports")

    pubmed_audit = audit_graph_provenance(pipeline_outputs.graph_jsonl, record_type="pubmed")
    save_provenance_audit_json(pubmed_audit, paths.reports_dir / "graph" / "ncbi_env_smoke_provenance_audit.json")
    save_provenance_audit_markdown(pubmed_audit, paths.reports_dir / "graph" / "ncbi_env_smoke_provenance_audit.md")
    trial_audit = audit_graph_provenance(trial_graph, record_type="trial")
    save_provenance_audit_json(trial_audit, paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_provenance_audit.json")
    save_provenance_audit_markdown(trial_audit, paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_provenance_audit.md")
    steps.append("Generated provenance audit reports")

    trial_manifest = build_corpus_manifest(
        [
            paths.trial_raw,
            trial_graph,
            paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_quality.json",
            paths.reports_dir / "graph" / "clinicaltrials_gbm_smoke_quality.md",
        ],
        name="clinicaltrials_gbm_smoke_2026-06-23",
        source="ClinicalTrials.gov",
        command="gbmbert-run-smoke-baseline",
        notes=["Read-only ClinicalTrials.gov smoke snapshot; descriptive registry metadata only."],
    )
    save_corpus_manifest(trial_manifest, paths.reports_dir / "corpus" / "clinicaltrials_gbm_smoke_manifest.json")
    save_corpus_manifest_markdown(trial_manifest, paths.reports_dir / "corpus" / "clinicaltrials_gbm_smoke_manifest.md")
    steps.append("Generated corpus manifests")

    index = build_artifact_index(
        [
            paths.pubmed_raw.parent,
            paths.pubmed_pipeline_dir,
            paths.trial_raw.parent,
            paths.trial_pipeline_dir,
            paths.review_queue_jsonl.parent,
            paths.reports_dir,
        ]
    )
    save_artifact_index_json(index, paths.reports_dir / "artifact_index.json")
    save_artifact_index_markdown(index, paths.reports_dir / "artifact_index.md")
    steps.append("Generated artifact index")

    return SmokeBaselineReport(
        offline=offline,
        paths={
            "pubmed_raw": str(paths.pubmed_raw),
            "pubmed_graph": str(pipeline_outputs.graph_jsonl),
            "trial_raw": str(paths.trial_raw),
            "trial_graph": str(trial_graph),
            "artifact_index": str(paths.reports_dir / "artifact_index.json"),
        },
        steps=steps,
        warnings=warnings,
    )


def save_smoke_baseline_report_json(report: SmokeBaselineReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_smoke_baseline_report_markdown(report: SmokeBaselineReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_smoke_baseline_report_markdown(report), encoding="utf-8")
    return output_path


def format_smoke_baseline_report_markdown(report: SmokeBaselineReport) -> str:
    warning_lines = [f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]
    lines = [
        "# GBM-AI Smoke Baseline Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Offline mode: {report.offline}",
        "",
        "## Paths",
        *(f"- {key}: `{value}`" for key, value in report.paths.items()),
        "",
        "## Steps",
        *(f"- {step}" for step in report.steps),
        "",
        "## Warnings",
        *warning_lines,
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild the local GBM-AI smoke baseline artifact bundle.")
    parser.add_argument("--offline", action="store_true", help="Use existing local raw PubMed and trial JSONL files.")
    default_paths = SmokeBaselinePaths()
    parser.add_argument("--pubmed-raw", type=Path, default=default_paths.pubmed_raw)
    parser.add_argument("--trial-raw", type=Path, default=default_paths.trial_raw)
    parser.add_argument("--pubmed-output-dir", type=Path, default=default_paths.pubmed_pipeline_dir)
    parser.add_argument("--trial-output-dir", type=Path, default=default_paths.trial_pipeline_dir)
    parser.add_argument("--reports-dir", type=Path, default=default_paths.reports_dir)
    parser.add_argument("--lexicon", type=Path, default=default_paths.lexicon_path)
    parser.add_argument("--pubmed-query-pack", default="pubmed_gbm_v2")
    parser.add_argument("--retmax-per-query", type=int, default=2)
    parser.add_argument("--trial-condition", default="glioblastoma")
    parser.add_argument("--trial-max-records", type=int, default=5)
    parser.add_argument("--reviewer", default="smoke")
    parser.add_argument("--json-output", type=Path, default=Path("reports/smoke_baseline.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/smoke_baseline.md"))
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    paths = SmokeBaselinePaths(
        pubmed_raw=args.pubmed_raw,
        pubmed_pipeline_dir=args.pubmed_output_dir,
        trial_raw=args.trial_raw,
        trial_pipeline_dir=args.trial_output_dir,
        reports_dir=args.reports_dir,
        lexicon_path=args.lexicon,
    )
    report = run_smoke_baseline(
        paths=paths,
        offline=args.offline,
        pubmed_query_pack=args.pubmed_query_pack,
        retmax_per_query=args.retmax_per_query,
        trial_condition=args.trial_condition,
        trial_max_records=args.trial_max_records,
        reviewer=args.reviewer,
    )
    if args.json_output:
        save_smoke_baseline_report_json(report, args.json_output)
    if args.markdown_output:
        save_smoke_baseline_report_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_smoke_baseline_report_markdown(report))
    return 0


def _write_dry_run_load_report(
    graph_jsonl: str | Path,
    *,
    record_type: str,
    json_output: str | Path,
    markdown_output: str | Path,
) -> None:
    loader = GraphLoader(
        _DryRunDriver(),
        LoaderConfig(dry_run=True, apply_constraints=False),
    )
    if record_type == "trial":
        stats = loader.load_trial_jsonl(graph_jsonl)
    else:
        stats = loader.load_pubmed_jsonl(graph_jsonl)
    report = GraphLoadReport(
        source_path=str(graph_jsonl),
        record_type=record_type,
        dry_run=True,
        apply_constraints=False,
        skip_invalid_records=False,
        stats=stats,
    )
    save_load_report_json(report, json_output)
    save_load_report_markdown(report, markdown_output)


def _require_existing(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{path} is required for --offline smoke baseline rebuild")


if __name__ == "__main__":
    raise SystemExit(main())
