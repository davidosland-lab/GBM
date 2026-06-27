"""Artifact inventory reports for GBM-AI local outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gbmbert.paths import standard_paths


@dataclass(frozen=True)
class ArtifactEntry:
    path: str
    category: str
    artifact_type: str
    suffix: str
    byte_count: int
    line_count: int | None
    sha256: str
    modified_at_utc: str
    provenance: dict[str, str]


@dataclass(frozen=True)
class ArtifactIndex:
    root_paths: list[str]
    artifact_count: int
    total_bytes: int
    category_counts: dict[str, int]
    suffix_counts: dict[str, int]
    artifacts: list[ArtifactEntry]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactDetailReport:
    index_path: str
    query: str
    match_count: int
    artifacts: list[ArtifactEntry]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_artifact_index(
    roots: list[str | Path] | None = None,
    *,
    include_suffixes: set[str] | None = None,
) -> ArtifactIndex:
    """Scan local artifact roots and return a compact inventory."""

    paths = standard_paths()
    root_paths = [Path(root) for root in roots] if roots else [
        paths.raw_dir,
        paths.processed_dir,
        paths.review_dir,
        paths.training_dir,
        paths.examples_dir,
        paths.reports_dir,
        paths.models_dir,
    ]
    suffixes = include_suffixes or {".jsonl", ".json", ".md", ".csv"}
    entries: list[ArtifactEntry] = []
    for root in root_paths:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path.suffix.lower() not in suffixes:
                continue
            entries.append(
                ArtifactEntry(
                    path=str(path),
                    category=_category_for_path(path),
                    artifact_type=_artifact_type_for_path(path),
                    suffix=path.suffix.lower() or "<none>",
                    byte_count=path.stat().st_size,
                    line_count=_line_count(path),
                    sha256=_sha256(path),
                    modified_at_utc=_modified_at_utc(path),
                    provenance=_provenance_for_path(path),
                )
            )
    category_counts = Counter(entry.category for entry in entries)
    suffix_counts = Counter(entry.suffix for entry in entries)
    return ArtifactIndex(
        root_paths=[str(path) for path in root_paths],
        artifact_count=len(entries),
        total_bytes=sum(entry.byte_count for entry in entries),
        category_counts=dict(category_counts),
        suffix_counts=dict(suffix_counts),
        artifacts=entries,
    )


def save_artifact_index_json(index: ArtifactIndex, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_artifact_index_markdown(index: ArtifactIndex, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_artifact_index_markdown(index), encoding="utf-8")
    return output_path


def load_artifact_detail(
    query: str,
    *,
    index_json: str | Path = Path("reports/artifact_index.json"),
    exact: bool = False,
) -> ArtifactDetailReport:
    """Load artifact details from a saved artifact index."""

    index_path = Path(index_json)
    warnings: list[str] = []
    if not index_path.exists():
        return ArtifactDetailReport(
            index_path=str(index_path),
            query=query,
            match_count=0,
            artifacts=[],
            warnings=[f"Artifact index not found: {index_path}"],
        )
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    entries = [ArtifactEntry(**item) for item in payload.get("artifacts", [])]
    normalized = query.casefold()
    if exact:
        matches = [entry for entry in entries if entry.path.casefold() == normalized or Path(entry.path).name.casefold() == normalized]
    else:
        matches = [
            entry
            for entry in entries
            if normalized in entry.path.casefold()
            or normalized in entry.artifact_type.casefold()
            or normalized in entry.category.casefold()
            or normalized in entry.sha256.casefold()
        ]
    if not matches:
        warnings.append("No artifacts matched the query")
    return ArtifactDetailReport(
        index_path=str(index_path),
        query=query,
        match_count=len(matches),
        artifacts=matches,
        warnings=warnings,
    )


def format_artifact_index_markdown(index: ArtifactIndex) -> str:
    lines = [
        "# GBM-AI Artifact Index",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Artifacts: {index.artifact_count}",
        f"- Total bytes: {index.total_bytes}",
        "",
        "## Categories",
    ]
    lines.extend(_format_counts(index.category_counts))
    lines.extend(["", "## Artifact Types"])
    lines.extend(_format_counts(Counter(entry.artifact_type for entry in index.artifacts)))
    lines.extend(["", "## File Types"])
    lines.extend(_format_counts(index.suffix_counts))
    lines.extend(["", "## Artifacts"])
    if index.artifacts:
        lines.extend(
            (
                f"- `{entry.path}` ({entry.artifact_type}, {entry.category}, "
                f"{entry.byte_count} bytes, lines={entry.line_count}, SHA256 `{entry.sha256}`)"
            )
            for entry in index.artifacts
        )
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def save_artifact_detail_json(report: ArtifactDetailReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_artifact_detail_markdown(report: ArtifactDetailReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_artifact_detail_markdown(report), encoding="utf-8")
    return output_path


def format_artifact_detail_markdown(report: ArtifactDetailReport) -> str:
    lines = [
        "# GBM-AI Artifact Detail",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Index: `{report.index_path}`",
        f"- Query: `{report.query}`",
        f"- Matches: {report.match_count}",
        "",
        "## Artifacts",
    ]
    if report.artifacts:
        for entry in report.artifacts:
            lines.extend(
                [
                    f"- `{entry.path}`",
                    f"  - Type: {entry.artifact_type}",
                    f"  - Category: {entry.category}",
                    f"  - Size: {entry.byte_count} bytes",
                    f"  - Lines: {entry.line_count}",
                    f"  - Modified UTC: {entry.modified_at_utc}",
                    f"  - SHA256: `{entry.sha256}`",
                ]
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an index of local GBM-AI artifacts.")
    parser.add_argument("--root", type=Path, action="append", default=[])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    return parser


def build_detail_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show detail for artifacts in a saved GBM-AI artifact index.")
    parser.add_argument("query")
    parser.add_argument("--index-json", type=Path, default=Path("reports/artifact_index.json"))
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    index = build_artifact_index(args.root or None)
    if args.json_output:
        save_artifact_index_json(index, args.json_output)
    if args.markdown_output:
        save_artifact_index_markdown(index, args.markdown_output)
    if args.json:
        print(json.dumps(index.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_artifact_index_markdown(index))
    return 0


def detail_main(argv: list[str] | None = None) -> int:
    args = build_detail_arg_parser().parse_args(argv)
    report = load_artifact_detail(args.query, index_json=args.index_json, exact=args.exact)
    if args.json_output:
        save_artifact_detail_json(report, args.json_output)
    if args.markdown_output:
        save_artifact_detail_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_artifact_detail_markdown(report))
    return 0


def _category_for_path(path: Path) -> str:
    parts = {part.casefold() for part in path.parts}
    if "raw" in parts:
        return "raw"
    if "processed" in parts:
        return "processed"
    if "review" in parts:
        return "review"
    if "training" in parts:
        return "training"
    if "models" in parts:
        return "model"
    if "examples" in parts:
        return "examples"
    if "corpus" in parts:
        return "corpus_report"
    if "graph" in parts:
        return "graph_report"
    if "wireframes" in parts:
        return "wireframe"
    if "reports" in parts:
        return "report"
    return "other"


def _artifact_type_for_path(path: Path) -> str:
    text = path.as_posix().casefold()
    name = path.name.casefold()
    if "curated_evidence_search" in name:
        return "curated_evidence_search_report"
    if text.endswith(".jsonl"):
        if "relation_negatives" in name:
            return "relation_negative_dataset"
        if "gold_ner" in name or "gold_evidence" in name or "gold_relations" in name:
            return "gold_seed_dataset"
        if "normalized_graph_records" in name:
            return "normalized_graph_records"
        if "qualifier_enriched_graph_records" in name:
            return "qualifier_enriched_graph_records"
        if "active_learning_batches" in name:
            return "active_learning_batch_plan"
        if "active_learning_batch" in name and "reviewed_queue" in name:
            return "active_learning_batch_reviewed_queue"
        if "reverted_graph_records" in name:
            return "reverted_graph_records"
        if "prediction_reviewed_queue" in name:
            return "prediction_reviewed_queue"
        if "prediction_review_queue" in name:
            return "prediction_review_queue"
        if "active_learning" in name:
            return "active_learning_candidates"
        if "curated_evidence" in name or "curated_predictions" in name:
            return "curated_evidence_predictions"
        if "evidence_overlay" in name and "graph" in name:
            return "evidence_overlay_graph_records"
        if "prediction" in name or "scored" in name:
            return "evidence_predictions"
        if "relation_training_pack" in name:
            return "relation_training_dataset"
        if "_train" in name or "_validation" in name or "_test" in name:
            return "training_split"
        if "clinicaltrials" in text and "trial_graph" not in name:
            return "clinicaltrials_raw"
        if "trial_graph" in name:
            return "trial_graph_records"
        if "graph_records" in name:
            return "pubmed_graph_records"
        if "entities" in name:
            return "entities"
        if "evidence" in name and "queue" not in name:
            return "evidence_claims"
        if "reviewed_queue" in name:
            return "reviewed_queue"
        if "review_queue" in name:
            return "review_queue"
        if "ner" in name or "relation" in name:
            return "annotation_dataset"
        return "jsonl_artifact"
    if name.endswith(".csv"):
        if "active_learning_batch" in name:
            return "active_learning_batch_csv"
        if "prediction_reviewed_queue" in name:
            return "prediction_reviewed_queue_csv"
        if "prediction_review_queue" in name:
            return "prediction_review_queue_csv"
        if "reviewed_queue" in name:
            return "reviewed_queue_csv"
        if "review_queue" in name:
            return "review_queue_csv"
        return "csv_artifact"
    if "gold_seed" in name:
        return "gold_seed_manifest"
    if "gold_training_pack" in name:
        return "gold_training_pack_report"
    if "relation_dataset_quality" in name:
        return "relation_dataset_quality_report"
    if "relation_training_pack" in name:
        return "relation_training_pack_report"
    if "training_pack_comparison" in name:
        return "training_pack_comparison_report"
    if "model_registry_audit" in name:
        return "model_registry_audit_report"
    if "training_artifact_bundle" in name:
        return "training_artifact_bundle_manifest"
    if "training_artifact_search" in name:
        return "training_artifact_search_report"
    if "training_pack_leakage_audit" in name:
        return "training_pack_leakage_audit_report"
    if "training_config_suite_review" in name:
        return "training_config_suite_review_report"
    if "model_registry_remediation_plan" in name:
        return "model_registry_remediation_plan"
    if "training_label_drift" in name:
        return "training_label_drift_report"
    if "curated_fixture_import" in name:
        return "curated_fixture_import_report"
    if "gold_pack_promotion_review" in name:
        return "gold_pack_promotion_review"
    if "training_provenance_audit" in name:
        return "training_provenance_audit_report"
    if "training_readiness_snapshot" in name:
        return "training_readiness_snapshot"
    if "dashboard_training_manifest" in name:
        return "dashboard_training_manifest"
    if "training_governance_suite" in name:
        return "training_governance_suite_report"
    if "relation_negatives" in name:
        return "relation_negative_report"
    if "evidence_training_pack" in name:
        return "evidence_training_pack_report"
    if "training_config_review" in name:
        return "training_config_review_report"
    if "pmid_split" in name:
        return "pmid_split_manifest"
    if "evidence_label_repair" in name:
        return "evidence_label_repair_report"
    if "adjudication" in name:
        return "adjudication_report"
    if "entity_normalization" in name:
        return "entity_normalization_report"
    if "qualifier_enrichment" in name:
        return "qualifier_enrichment_report"
    if "training_readiness" in name:
        return "training_readiness_report"
    if "run_manifest" in name:
        return "training_run_manifest"
    if "manifest" in name:
        if "experiment" in name:
            return "training_experiment_manifest"
        if "label_maps" in name:
            return "label_maps_manifest"
        return "manifest"
    if "label_map" in name:
        return "label_map"
    if "dataset_card" in name:
        return "dataset_card"
    if "baseline_report" in name:
        return "baseline_report"
    if "train_gate" in name:
        return "training_gate_report"
    if "evaluation" in name or "metrics" in name:
        return "training_metrics"
    if "prediction" in name or "scored" in name:
        if "quality" in name:
            return "prediction_quality_report"
        if "summary" in name:
            return "prediction_review_summary"
        if "reviewed_queue" in name:
            return "prediction_reviewed_queue"
        if "review_queue" in name:
            return "prediction_review_queue"
        return "evidence_predictions"
    if "curation_handoff_bundle" in name:
        return "curation_handoff_bundle_manifest"
    if "curation_handoff_validation" in name:
        return "curation_handoff_validation_report"
    if "curation_run_registry" in name:
        return "curation_run_registry"
    if "curation_run_browser" in name:
        return "curation_run_browser_report"
    if "evidence_overlay_promotion_gate" in name:
        return "evidence_overlay_promotion_gate_report"
    if "relation_extraction_audit" in name:
        return "relation_extraction_audit_report"
    if "scope_drift" in name:
        return "scope_drift_report"
    if "ci_report_summary" in name:
        return "ci_report_summary"
    if "platform_regression" in name:
        return "platform_regression_report"
    if "local_verification" in name:
        return "local_verification_report"
    if "artifact_policy" in name:
        return "artifact_policy_report"
    if "launcher_menu_check" in name:
        return "launcher_menu_check_report"
    if "artifact_detail" in name:
        return "artifact_detail_report"
    if "active_learning_batch_status" in name:
        return "active_learning_batch_status_report"
    if "active_learning_batch_roundtrip" in name:
        return "active_learning_batch_roundtrip_report"
    if "active_learning_batches" in name:
        return "active_learning_batch_report"
    if "overlay_revert" in name:
        return "overlay_revert_report"
    if "curation_regression_pack" in name or "curation_regression_workflow" in name:
        return "curation_regression_pack_report"
    if "active_learning" in name:
        return "active_learning_report"
    if "curated_evidence" in name or "curated_predictions" in name:
        if "audit" in name:
            return "curated_evidence_audit"
        return "curated_evidence_report"
    if "evidence_overlay" in name:
        if "diff" in name:
            return "evidence_overlay_diff_report"
        return "evidence_overlay_report"
    if "overlay_load_guard" in name:
        return "overlay_load_guard_report"
    if "curation_smoke_workflow" in name:
        return "curation_smoke_workflow_report"
    if "model_card" in name:
        return "model_card"
    if "smoke_summary" in name:
        return "training_smoke_summary"
    if "checkpoint_registry" in name:
        return "checkpoint_registry"
    if "quality" in name:
        return "graph_quality_report"
    if "load_report" in name:
        return "graph_load_report"
    if "artifact_index" in name:
        return "artifact_index"
    if "preflight" in name:
        return "preflight_report"
    if path.suffix.lower() == ".md":
        return "markdown_report"
    if path.suffix.lower() == ".json":
        return "json_report"
    return "artifact"


def _provenance_for_path(path: Path) -> dict[str, str]:
    text = path.as_posix().casefold()
    if "clinicaltrials" in text:
        return {"source": "ClinicalTrials.gov"}
    if "pubmed" in text or "ncbi" in text:
        return {"source": "PubMed/NCBI"}
    if "sample" in text or "examples" in text:
        return {"source": "local fixture"}
    return {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _modified_at_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).replace(microsecond=0).isoformat()


def _line_count(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except UnicodeDecodeError:
        return None


def _format_counts(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {key}: {count}" for key, count in sorted(counts.items())]


if __name__ == "__main__":
    raise SystemExit(main())
