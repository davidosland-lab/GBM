"""Training artifact governance reports for GBM-BERT scaffolding."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gbmbert.artifacts import ArtifactEntry, load_artifact_detail
from gbmbert.dashboard.app import training_artifacts_dashboard_context
from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.config import load_training_config
from gbmbert.training.config_review import review_training_config
from gbmbert.training.pack_comparison import compare_training_packs, save_training_pack_comparison_json, save_training_pack_comparison_markdown
from gbmbert.training.registry_audit import audit_checkpoint_registry, save_registry_audit_json, save_registry_audit_markdown

DEFAULT_EVIDENCE_PACK = Path("reports/training/evidence_pack/evidence_training_pack.json")
DEFAULT_RELATION_PACK = Path("reports/training/relation_pack/relation_training_pack.json")
DEFAULT_GOLD_PACK = Path("reports/training/gold_pack/gold_training_pack.json")
DEFAULT_REGISTRY = Path("models/checkpoint_registry.json")
DEFAULT_ARTIFACT_INDEX = Path("reports/artifact_index.json")


@dataclass(frozen=True)
class ArtifactBundleEntry:
    source_path: str
    bundled_path: str
    artifact_type: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class TrainingArtifactBundleReport:
    output_dir: str
    manifest_path: str
    artifact_count: int
    total_bytes: int
    entries: list[ArtifactBundleEntry]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingArtifactSearchReport:
    index_path: str
    query: str
    match_count: int
    artifacts: list[dict[str, Any]]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PackLeakageRow:
    pack: str
    task: str
    split: str
    pmid_count: int
    example_count: int


@dataclass(frozen=True)
class TrainingPackLeakageAuditReport:
    packs: list[str]
    rows: list[PackLeakageRow]
    within_pack_warnings: list[str]
    cross_pack_warnings: list[str]
    warning_count: int
    safe: bool
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConfigSuiteReviewReport:
    config_count: int
    passed_count: int
    failed_count: int
    blocking_failed_count: int
    scaffold_count: int
    reviews: list[dict[str, Any]]
    warnings: list[str]
    scaffold_warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegistryRemediationAction:
    checkpoint: str
    severity: str
    finding: str
    suggested_action: str


@dataclass(frozen=True)
class RegistryRemediationPlan:
    audit_path: str
    action_count: int
    actions: list[RegistryRemediationAction]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LabelDriftRow:
    name: str
    dataset_labels: dict[str, list[str]]
    config_labels: list[str]
    missing_from_config: list[str]
    missing_from_dataset: list[str]


@dataclass(frozen=True)
class TrainingLabelDriftReport:
    rows: list[LabelDriftRow]
    warning_count: int
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProvenanceAuditReport:
    dataset_path: str
    row_count: int
    missing_warning_count: int
    missing_pmid_count: int
    source_type_counts: dict[str, int]
    warnings: list[str]
    safe: bool
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingReadinessSnapshotReport:
    created_at_utc: str
    ready_pack_count: int
    total_pack_count: int
    relation_config_status: str
    current_config_passed_count: int
    current_config_failed_count: int
    scaffold_config_count: int
    registry_audit_passed: bool | None
    dashboard_report_count: int
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardTrainingManifestReport:
    output_path: str
    available_report_count: int
    ready_pack_count: int
    registry_entry_count: int
    relation_config_status: str
    current_config_passed_count: int
    current_config_failed_count: int
    scaffold_config_count: int
    registry_audit_passed: bool | None
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GovernanceSuiteReport:
    output_dir: str
    step_count: int
    passed: bool
    artifacts: dict[str, str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_training_artifact_bundle(
    *,
    output_dir: str | Path,
    index_json: str | Path = DEFAULT_ARTIFACT_INDEX,
    copy_files: bool = False,
) -> TrainingArtifactBundleReport:
    """Build a manifest, and optionally file copies, for training/model governance artifacts."""

    output_root = Path(output_dir)
    files_root = output_root / "files"
    output_root.mkdir(parents=True, exist_ok=True)
    if copy_files:
        files_root.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    entries: list[ArtifactBundleEntry] = []
    index = _load_artifact_entries(Path(index_json), warnings)
    for entry in index:
        if entry.category not in {"training", "model"}:
            continue
        source = Path(entry.path)
        if not source.exists():
            warnings.append(f"missing artifact: {entry.path}")
            continue
        bundled = files_root / _safe_bundle_name(source) if copy_files else source
        if copy_files:
            shutil.copy2(source, bundled)
        entries.append(
            ArtifactBundleEntry(
                source_path=str(source),
                bundled_path=str(bundled),
                artifact_type=entry.artifact_type,
                sha256=entry.sha256,
                byte_count=entry.byte_count,
            )
        )
    report = TrainingArtifactBundleReport(
        output_dir=str(output_root),
        manifest_path=str(output_root / "training_artifact_bundle.json"),
        artifact_count=len(entries),
        total_bytes=sum(entry.byte_count for entry in entries),
        entries=entries,
        warnings=warnings,
    )
    save_training_artifact_bundle_json(report, output_root / "training_artifact_bundle.json")
    save_training_artifact_bundle_markdown(report, output_root / "training_artifact_bundle.md")
    return report


def search_training_artifacts(
    query: str,
    *,
    index_json: str | Path = DEFAULT_ARTIFACT_INDEX,
) -> TrainingArtifactSearchReport:
    detail = load_artifact_detail(query, index_json=index_json)
    artifacts = [
        asdict(entry)
        for entry in detail.artifacts
        if entry.category in {"training", "model"} or "training" in entry.artifact_type or "model" in entry.artifact_type
    ]
    warnings = list(detail.warnings)
    if detail.artifacts and not artifacts:
        warnings.append("matches found, but none were training/model artifacts")
    return TrainingArtifactSearchReport(
        index_path=str(index_json),
        query=query,
        match_count=len(artifacts),
        artifacts=artifacts,
        warnings=warnings,
    )


def audit_training_pack_leakage(
    *,
    evidence_pack_report: str | Path | None = DEFAULT_EVIDENCE_PACK,
    relation_pack_report: str | Path | None = DEFAULT_RELATION_PACK,
    gold_pack_report: str | Path | None = DEFAULT_GOLD_PACK,
) -> TrainingPackLeakageAuditReport:
    pack_reports = {
        "evidence": Path(evidence_pack_report) if evidence_pack_report else None,
        "relation": Path(relation_pack_report) if relation_pack_report else None,
        "gold": Path(gold_pack_report) if gold_pack_report else None,
    }
    rows: list[PackLeakageRow] = []
    pmids_by_pack_split: dict[tuple[str, str], set[str]] = defaultdict(set)
    within_warnings: list[str] = []
    for pack, report_path in pack_reports.items():
        if not report_path or not report_path.exists():
            continue
        payload = _read_json(report_path)
        split_dir = payload.get("split_dataset_dir") or payload.get("split_dir")
        if not split_dir:
            continue
        by_task_split = _pmids_by_task_split(Path(str(split_dir)))
        split_to_pmids: dict[str, set[str]] = defaultdict(set)
        for (task, split), data in by_task_split.items():
            rows.append(PackLeakageRow(pack=pack, task=task, split=split, pmid_count=len(data["pmids"]), example_count=data["examples"]))
            split_to_pmids[split].update(data["pmids"])
            pmids_by_pack_split[(pack, split)].update(data["pmids"])
        for left, left_pmids in split_to_pmids.items():
            for right, right_pmids in split_to_pmids.items():
                if left >= right:
                    continue
                overlap = left_pmids & right_pmids
                if overlap:
                    within_warnings.append(f"{pack}: {len(overlap)} PMID(s) appear in both {left} and {right}: {', '.join(sorted(overlap)[:5])}")
    cross_warnings: list[str] = []
    pack_names = sorted({pack for pack, _ in pmids_by_pack_split})
    for index, left_pack in enumerate(pack_names):
        left_pmids = set().union(*(pmids for (pack, _), pmids in pmids_by_pack_split.items() if pack == left_pack))
        for right_pack in pack_names[index + 1 :]:
            right_pmids = set().union(*(pmids for (pack, _), pmids in pmids_by_pack_split.items() if pack == right_pack))
            overlap = left_pmids & right_pmids
            if overlap:
                cross_warnings.append(f"{left_pack}/{right_pack}: {len(overlap)} shared PMID(s): {', '.join(sorted(overlap)[:5])}")
    warnings = within_warnings + cross_warnings
    return TrainingPackLeakageAuditReport(
        packs=pack_names,
        rows=rows,
        within_pack_warnings=within_warnings,
        cross_pack_warnings=cross_warnings,
        warning_count=len(warnings),
        safe=not within_warnings,
    )


def review_training_config_suite(config_paths: list[str | Path] | None = None) -> ConfigSuiteReviewReport:
    selected_paths = sorted(Path("configs/training").glob("*.json")) if config_paths is None else config_paths
    paths = [Path(path) for path in selected_paths]
    reviews: list[dict[str, Any]] = []
    warnings: list[str] = []
    scaffold_warnings: list[str] = []
    for config_path in paths:
        metadata = _config_governance_metadata(config_path)
        profile = metadata["profile"]
        try:
            config = load_training_config(config_path)
            dataset_dir, label_map_dir = _default_dataset_and_label_maps_for_task(config.task.value)
            if metadata["dataset_dir"]:
                dataset_dir = Path(metadata["dataset_dir"])
            if metadata["label_map_dir"]:
                label_map_dir = Path(metadata["label_map_dir"])
            review = review_training_config(config_path, dataset_dir, label_map_dir=label_map_dir).to_dict()
        except Exception as exc:  # Reports should keep going across the suite.
            review = {
                "config_path": str(config_path),
                "status": "failed",
                "errors": [str(exc)],
                "warnings": [],
            }
        raw_status = str(review.get("status") or "failed")
        review["governance_profile"] = profile
        review["governance_note"] = metadata["note"]
        review["blocking"] = profile == "current"
        review["raw_status"] = raw_status
        if profile == "scaffold":
            review["status"] = "scaffold_ready" if raw_status == "passed" else "scaffold_pending"
            if raw_status != "passed":
                scaffold_warnings.append(f"{config_path}: scaffold pending ({'; '.join(str(error) for error in review.get('errors', []))})")
        elif raw_status != "passed":
            warnings.append(f"{config_path}: {raw_status}")
        reviews.append(review)
    blocking_failed_count = sum(1 for review in reviews if review.get("blocking") and review.get("raw_status") != "passed")
    return ConfigSuiteReviewReport(
        config_count=len(reviews),
        passed_count=sum(1 for review in reviews if review.get("blocking") and review.get("raw_status") == "passed"),
        failed_count=blocking_failed_count,
        blocking_failed_count=blocking_failed_count,
        scaffold_count=sum(1 for review in reviews if review.get("governance_profile") == "scaffold"),
        reviews=reviews,
        warnings=warnings,
        scaffold_warnings=scaffold_warnings,
    )


def build_registry_remediation_plan(audit_json: str | Path = Path("reports/training/model_registry_audit.json")) -> RegistryRemediationPlan:
    audit_path = Path(audit_json)
    audit = _read_json(audit_path)
    actions: list[RegistryRemediationAction] = []
    for entry in audit.get("entries", []):
        name = str(entry.get("name") or "unknown")
        for error in entry.get("errors", []):
            actions.append(RegistryRemediationAction(name, "error", str(error), _suggest_registry_action(str(error))))
        for warning in entry.get("warnings", []):
            actions.append(RegistryRemediationAction(name, "warning", str(warning), _suggest_registry_action(str(warning))))
    return RegistryRemediationPlan(audit_path=str(audit_path), action_count=len(actions), actions=actions)


def build_training_label_drift_report(
    *,
    evidence_pack_report: str | Path | None = DEFAULT_EVIDENCE_PACK,
    relation_pack_report: str | Path | None = DEFAULT_RELATION_PACK,
    gold_pack_report: str | Path | None = DEFAULT_GOLD_PACK,
) -> TrainingLabelDriftReport:
    comparison = compare_training_packs(
        evidence_pack_report=evidence_pack_report if evidence_pack_report and Path(evidence_pack_report).exists() else None,
        relation_pack_report=relation_pack_report if relation_pack_report and Path(relation_pack_report).exists() else None,
        gold_pack_report=gold_pack_report if gold_pack_report and Path(gold_pack_report).exists() else None,
    )
    config_labels_by_task = _config_labels_by_task()
    rows: list[LabelDriftRow] = []
    warnings: list[str] = []
    for pack in comparison.packs:
        config_labels = config_labels_by_task.get(pack.name, [])
        dataset_labels = {task: sorted(labels) for task, labels in ((task, counts.keys()) for task, counts in pack.label_counts.items())}
        active_dataset_labels = sorted({label for labels in dataset_labels.values() for label in labels})
        missing_from_config = sorted(set(active_dataset_labels) - set(config_labels)) if config_labels else []
        missing_from_dataset = sorted(set(config_labels) - set(active_dataset_labels)) if active_dataset_labels else []
        if missing_from_config:
            warnings.append(f"{pack.name}: dataset labels missing from config: {', '.join(missing_from_config)}")
        if missing_from_dataset:
            warnings.append(f"{pack.name}: config labels missing from dataset: {', '.join(missing_from_dataset)}")
        rows.append(
            LabelDriftRow(
                name=pack.name,
                dataset_labels=dataset_labels,
                config_labels=config_labels,
                missing_from_config=missing_from_config,
                missing_from_dataset=missing_from_dataset,
            )
        )
    return TrainingLabelDriftReport(rows=rows, warning_count=len(warnings), warnings=warnings)


def audit_training_provenance(dataset_path: str | Path = Path("data/training/relation_training_pack.jsonl")) -> TrainingProvenanceAuditReport:
    path = Path(dataset_path)
    rows = _read_jsonl(path)
    missing_warning_count = sum(1 for row in rows if row.get("warning") != RESEARCH_WARNING)
    missing_pmid_count = sum(1 for row in rows if not str(row.get("source_pmid") or row.get("pmid") or "").strip())
    source_type_counts = dict(sorted(Counter(str(row.get("relation_pack_source_type") or "<missing>") for row in rows).items()))
    warnings: list[str] = []
    if missing_warning_count:
        warnings.append(f"{missing_warning_count} row(s) missing required research-use warning")
    if missing_pmid_count:
        warnings.append(f"{missing_pmid_count} row(s) missing source PMID")
    if source_type_counts.get("<missing>"):
        warnings.append(f"{source_type_counts['<missing>']} row(s) missing relation pack source type")
    return TrainingProvenanceAuditReport(
        dataset_path=str(path),
        row_count=len(rows),
        missing_warning_count=missing_warning_count,
        missing_pmid_count=missing_pmid_count,
        source_type_counts=source_type_counts,
        warnings=warnings,
        safe=not warnings,
    )


def build_training_readiness_snapshot(root: str | Path = ".") -> TrainingReadinessSnapshotReport:
    context = training_artifacts_dashboard_context(root)
    warnings: list[str] = []
    if context["registry_audit_passed"] is False:
        warnings.append("model registry audit has findings")
    if context["relation_config_status"] and context["relation_config_status"] != "passed":
        warnings.append(f"relation config review status: {context['relation_config_status']}")
    if int(context.get("current_config_failed_count", 0)):
        warnings.append(f"current config failures: {context['current_config_failed_count']}")
    return TrainingReadinessSnapshotReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        ready_pack_count=int(context["ready_pack_count"]),
        total_pack_count=3,
        relation_config_status=str(context["relation_config_status"]),
        current_config_passed_count=int(context.get("current_config_passed_count", 0)),
        current_config_failed_count=int(context.get("current_config_failed_count", 0)),
        scaffold_config_count=int(context.get("scaffold_config_count", 0)),
        registry_audit_passed=context["registry_audit_passed"] if isinstance(context["registry_audit_passed"], bool) else None,
        dashboard_report_count=int(context["available_report_count"]),
        warnings=warnings,
    )


def build_dashboard_training_manifest(output_path: str | Path, *, root: str | Path = ".") -> DashboardTrainingManifestReport:
    context = training_artifacts_dashboard_context(root)
    report = DashboardTrainingManifestReport(
        output_path=str(output_path),
        available_report_count=int(context["available_report_count"]),
        ready_pack_count=int(context["ready_pack_count"]),
        registry_entry_count=int(context["registry_entry_count"]),
        relation_config_status=str(context["relation_config_status"]),
        current_config_passed_count=int(context.get("current_config_passed_count", 0)),
        current_config_failed_count=int(context.get("current_config_failed_count", 0)),
        scaffold_config_count=int(context.get("scaffold_config_count", 0)),
        registry_audit_passed=context["registry_audit_passed"] if isinstance(context["registry_audit_passed"], bool) else None,
    )
    save_dashboard_training_manifest_json(report, output_path)
    return report


def run_training_governance_suite(
    output_dir: str | Path = Path("reports/training/governance"),
    *,
    strict_scaffolds: bool = False,
) -> GovernanceSuiteReport:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}
    warnings: list[str] = []

    bundle = build_training_artifact_bundle(output_dir=output_root / "bundle")
    artifacts["bundle"] = bundle.manifest_path
    warnings.extend(bundle.warnings)

    leakage = audit_training_pack_leakage()
    artifacts["leakage_audit"] = str(save_training_pack_leakage_audit_json(leakage, output_root / "training_pack_leakage_audit.json"))
    save_training_pack_leakage_audit_markdown(leakage, output_root / "training_pack_leakage_audit.md")
    warnings.extend(leakage.within_pack_warnings)

    suite = review_training_config_suite()
    artifacts["config_suite"] = str(save_config_suite_review_json(suite, output_root / "training_config_suite_review.json"))
    save_config_suite_review_markdown(suite, output_root / "training_config_suite_review.md")
    warnings.extend(suite.warnings)
    if strict_scaffolds:
        warnings.extend(suite.scaffold_warnings)

    registry = audit_checkpoint_registry(DEFAULT_REGISTRY)
    artifacts["registry_audit"] = str(save_registry_audit_json(registry, output_root / "model_registry_audit.json"))
    save_registry_audit_markdown(registry, output_root / "model_registry_audit.md")
    warnings.extend(registry.errors)

    remediation = build_registry_remediation_plan(artifacts["registry_audit"])
    artifacts["registry_remediation"] = str(save_registry_remediation_plan_json(remediation, output_root / "model_registry_remediation_plan.json"))
    save_registry_remediation_plan_markdown(remediation, output_root / "model_registry_remediation_plan.md")

    drift = build_training_label_drift_report()
    artifacts["label_drift"] = str(save_training_label_drift_json(drift, output_root / "training_label_drift.json"))
    save_training_label_drift_markdown(drift, output_root / "training_label_drift.md")
    # Label drift from scaffold/full-profile configs is informational in the
    # default green path; strict audit mode can still surface it as blocking.
    if strict_scaffolds:
        warnings.extend(drift.warnings)

    provenance = audit_training_provenance()
    artifacts["provenance_audit"] = str(save_training_provenance_audit_json(provenance, output_root / "training_provenance_audit.json"))
    save_training_provenance_audit_markdown(provenance, output_root / "training_provenance_audit.md")
    warnings.extend(provenance.warnings)

    snapshot = build_training_readiness_snapshot()
    artifacts["readiness_snapshot"] = str(save_training_readiness_snapshot_json(snapshot, output_root / "training_readiness_snapshot.json"))
    save_training_readiness_snapshot_markdown(snapshot, output_root / "training_readiness_snapshot.md")
    warnings.extend(snapshot.warnings)

    dashboard_manifest = build_dashboard_training_manifest(output_root / "dashboard_training_manifest.json")
    artifacts["dashboard_manifest"] = dashboard_manifest.output_path
    save_dashboard_training_manifest_markdown(dashboard_manifest, output_root / "dashboard_training_manifest.md")

    comparison = compare_training_packs(
        evidence_pack_report=DEFAULT_EVIDENCE_PACK if DEFAULT_EVIDENCE_PACK.exists() else None,
        relation_pack_report=DEFAULT_RELATION_PACK if DEFAULT_RELATION_PACK.exists() else None,
        gold_pack_report=DEFAULT_GOLD_PACK if DEFAULT_GOLD_PACK.exists() else None,
    )
    artifacts["pack_comparison"] = str(save_training_pack_comparison_json(comparison, output_root / "training_pack_comparison.json"))
    save_training_pack_comparison_markdown(comparison, output_root / "training_pack_comparison.md")

    report = GovernanceSuiteReport(
        output_dir=str(output_root),
        step_count=len(artifacts),
        passed=not warnings,
        artifacts=artifacts,
        warnings=warnings,
    )
    save_governance_suite_json(report, output_root / "training_governance_suite.json")
    save_governance_suite_markdown(report, output_root / "training_governance_suite.md")
    return report


def save_training_artifact_bundle_json(report: TrainingArtifactBundleReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_training_artifact_bundle_markdown(report: TrainingArtifactBundleReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Artifact Bundle",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- Artifacts: {report.artifact_count}",
        f"- Total bytes: {report.total_bytes}",
        "",
        "## Artifacts",
        *([f"- `{entry.source_path}` -> `{entry.bundled_path}` ({entry.artifact_type})" for entry in report.entries] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return _write_text(lines, path)


def save_training_artifact_search_json(report: TrainingArtifactSearchReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_training_artifact_search_markdown(report: TrainingArtifactSearchReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Artifact Search",
        "",
        RESEARCH_WARNING,
        "",
        f"- Index: `{report.index_path}`",
        f"- Query: `{report.query}`",
        f"- Matches: {report.match_count}",
        "",
        "## Artifacts",
        *([f"- `{item['path']}` ({item['artifact_type']})" for item in report.artifacts] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return _write_text(lines, path)


def save_training_pack_leakage_audit_json(report: TrainingPackLeakageAuditReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_training_pack_leakage_audit_markdown(report: TrainingPackLeakageAuditReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Pack Leakage Audit",
        "",
        RESEARCH_WARNING,
        "",
        f"- Packs: {', '.join(report.packs) if report.packs else 'none'}",
        f"- Safe: {report.safe}",
        f"- Warnings: {report.warning_count}",
        "",
        "## Split PMIDs",
        *([f"- {row.pack}/{row.task}/{row.split}: PMIDs={row.pmid_count}, examples={row.example_count}" for row in report.rows] or ["- none"]),
        "",
        "## Within-Pack Warnings",
        *([f"- {warning}" for warning in report.within_pack_warnings] if report.within_pack_warnings else ["- none"]),
        "",
        "## Cross-Pack Warnings",
        *([f"- {warning}" for warning in report.cross_pack_warnings] if report.cross_pack_warnings else ["- none"]),
    ]
    return _write_text(lines, path)


def save_config_suite_review_json(report: ConfigSuiteReviewReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_config_suite_review_markdown(report: ConfigSuiteReviewReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Config Suite Review",
        "",
        RESEARCH_WARNING,
        "",
        f"- Configs: {report.config_count}",
        f"- Current passed: {report.passed_count}",
        f"- Current failed: {report.blocking_failed_count}",
        f"- Scaffold configs: {report.scaffold_count}",
        "",
        "## Reviews",
    ]
    for review in report.reviews:
        lines.extend(
            [
                f"### {Path(str(review.get('config_path', 'unknown'))).name}",
                f"- Status: {review.get('status')}",
                f"- Governance profile: {review.get('governance_profile', 'current')}",
                f"- Blocking: {review.get('blocking', True)}",
                f"- Task: {review.get('task', 'n/a')}",
                f"- Note: {review.get('governance_note') or 'none'}",
                "- Errors:",
                *([f"- {error}" for error in review.get("errors", [])] if review.get("errors") else ["- none"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Blocking Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
            "",
            "## Scaffold Warnings",
            *([f"- {warning}" for warning in report.scaffold_warnings] if report.scaffold_warnings else ["- none"]),
        ]
    )
    return _write_text(lines, path)


def save_registry_remediation_plan_json(report: RegistryRemediationPlan, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_registry_remediation_plan_markdown(report: RegistryRemediationPlan, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Model Registry Remediation Plan",
        "",
        RESEARCH_WARNING,
        "",
        f"- Audit: `{report.audit_path}`",
        f"- Actions: {report.action_count}",
        "",
        "## Actions",
        *([f"- [{action.severity}] {action.checkpoint}: {action.finding} -> {action.suggested_action}" for action in report.actions] or ["- none"]),
    ]
    return _write_text(lines, path)


def save_training_label_drift_json(report: TrainingLabelDriftReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_training_label_drift_markdown(report: TrainingLabelDriftReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Label Drift Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Warnings: {report.warning_count}",
        "",
        "## Packs",
    ]
    for row in report.rows:
        lines.extend(
            [
                f"### {row.name}",
                f"- Config labels: {', '.join(row.config_labels) if row.config_labels else 'none'}",
                f"- Missing from config: {', '.join(row.missing_from_config) if row.missing_from_config else 'none'}",
                f"- Missing from dataset: {', '.join(row.missing_from_dataset) if row.missing_from_dataset else 'none'}",
                "",
            ]
        )
    lines.extend(["## Warnings", *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"])])
    return _write_text(lines, path)


def save_training_provenance_audit_json(report: TrainingProvenanceAuditReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_training_provenance_audit_markdown(report: TrainingProvenanceAuditReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Provenance Audit",
        "",
        RESEARCH_WARNING,
        "",
        f"- Dataset: `{report.dataset_path}`",
        f"- Rows: {report.row_count}",
        f"- Safe: {report.safe}",
        "",
        "## Source Types",
        *([f"- {name}: {count}" for name, count in report.source_type_counts.items()] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return _write_text(lines, path)


def save_training_readiness_snapshot_json(report: TrainingReadinessSnapshotReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_training_readiness_snapshot_markdown(report: TrainingReadinessSnapshotReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Readiness Snapshot",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Ready packs: {report.ready_pack_count}/{report.total_pack_count}",
        f"- Relation config status: {report.relation_config_status or 'n/a'}",
        f"- Current config passed: {report.current_config_passed_count}",
        f"- Current config failed: {report.current_config_failed_count}",
        f"- Scaffold configs: {report.scaffold_config_count}",
        f"- Registry audit passed: {report.registry_audit_passed}",
        f"- Dashboard reports: {report.dashboard_report_count}",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return _write_text(lines, path)


def save_dashboard_training_manifest_json(report: DashboardTrainingManifestReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_dashboard_training_manifest_markdown(report: DashboardTrainingManifestReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Dashboard Training Manifest",
        "",
        RESEARCH_WARNING,
        "",
        f"- Available reports: {report.available_report_count}",
        f"- Ready packs: {report.ready_pack_count}",
        f"- Registry entries: {report.registry_entry_count}",
        f"- Relation config status: {report.relation_config_status or 'n/a'}",
        f"- Current config passed: {report.current_config_passed_count}",
        f"- Current config failed: {report.current_config_failed_count}",
        f"- Scaffold configs: {report.scaffold_config_count}",
        f"- Registry audit passed: {report.registry_audit_passed}",
    ]
    return _write_text(lines, path)


def save_governance_suite_json(report: GovernanceSuiteReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_governance_suite_markdown(report: GovernanceSuiteReport, path: str | Path) -> Path:
    lines = [
        "# GBM-BERT Training Governance Suite",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- Steps: {report.step_count}",
        f"- Passed: {report.passed}",
        "",
        "## Artifacts",
        *[f"- {name}: `{path}`" for name, path in sorted(report.artifacts.items())],
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return _write_text(lines, path)


def artifact_bundle_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a manifest bundle of training artifacts.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/training_artifact_bundle"))
    parser.add_argument("--index-json", type=Path, default=DEFAULT_ARTIFACT_INDEX)
    parser.add_argument("--copy-files", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_training_artifact_bundle(output_dir=args.output_dir, index_json=args.index_json, copy_files=args.copy_files)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else (Path(report.output_dir) / "training_artifact_bundle.md").read_text(encoding="utf-8"))
    return 0


def artifact_search_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search training artifacts in the artifact index.")
    parser.add_argument("query")
    parser.add_argument("--index-json", type=Path, default=DEFAULT_ARTIFACT_INDEX)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = search_training_artifacts(args.query, index_json=args.index_json)
    if args.json_output:
        save_training_artifact_search_json(report, args.json_output)
    if args.markdown_output:
        save_training_artifact_search_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_training_artifact_search_markdown))
    return 0


def leakage_audit_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit PMID leakage across training packs.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-warnings", action="store_true")
    args = parser.parse_args(argv)
    report = audit_training_pack_leakage()
    if args.json_output:
        save_training_pack_leakage_audit_json(report, args.json_output)
    if args.markdown_output:
        save_training_pack_leakage_audit_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_training_pack_leakage_audit_markdown))
    return 0 if report.safe or args.allow_warnings else 1


def config_suite_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review all GBM-BERT training configs against local prepared packs.")
    parser.add_argument("--config", type=Path, action="append")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-failed", action="store_true")
    parser.add_argument("--strict-scaffolds", action="store_true")
    args = parser.parse_args(argv)
    report = review_training_config_suite(args.config)
    if args.json_output:
        save_config_suite_review_json(report, args.json_output)
    if args.markdown_output:
        save_config_suite_review_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_config_suite_review_markdown))
    has_findings = report.failed_count > 0 or (args.strict_scaffolds and bool(report.scaffold_warnings))
    return 0 if not has_findings or args.allow_failed else 1


def registry_remediation_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a remediation plan from a model registry audit.")
    parser.add_argument("--audit-json", type=Path, default=Path("reports/training/model_registry_audit.json"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_registry_remediation_plan(args.audit_json)
    if args.json_output:
        save_registry_remediation_plan_json(report, args.json_output)
    if args.markdown_output:
        save_registry_remediation_plan_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_registry_remediation_plan_markdown))
    return 0


def label_drift_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare dataset labels against training config labels.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-warnings", action="store_true")
    args = parser.parse_args(argv)
    report = build_training_label_drift_report()
    if args.json_output:
        save_training_label_drift_json(report, args.json_output)
    if args.markdown_output:
        save_training_label_drift_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_training_label_drift_markdown))
    return 0 if not report.warnings or args.allow_warnings else 1


def provenance_audit_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit training row provenance fields.")
    parser.add_argument("dataset_path", type=Path, nargs="?", default=Path("data/training/relation_training_pack.jsonl"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-warnings", action="store_true")
    args = parser.parse_args(argv)
    report = audit_training_provenance(args.dataset_path)
    if args.json_output:
        save_training_provenance_audit_json(report, args.json_output)
    if args.markdown_output:
        save_training_provenance_audit_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_training_provenance_audit_markdown))
    return 0 if report.safe or args.allow_warnings else 1


def readiness_snapshot_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize current training readiness artifacts.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_training_readiness_snapshot()
    if args.json_output:
        save_training_readiness_snapshot_json(report, args.json_output)
    if args.markdown_output:
        save_training_readiness_snapshot_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_training_readiness_snapshot_markdown))
    return 0


def dashboard_manifest_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the dashboard training artifacts context as a manifest.")
    parser.add_argument("--output", type=Path, default=Path("reports/training/dashboard_training_manifest.json"))
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_dashboard_training_manifest(args.output)
    if args.markdown_output:
        save_dashboard_training_manifest_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else _format_tmp_markdown(report, save_dashboard_training_manifest_markdown))
    return 0


def governance_suite_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the GBM-BERT training governance report suite.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/training/governance"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-findings", action="store_true")
    parser.add_argument("--strict-scaffolds", action="store_true")
    args = parser.parse_args(argv)
    report = run_training_governance_suite(args.output_dir, strict_scaffolds=args.strict_scaffolds)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else (Path(report.output_dir) / "training_governance_suite.md").read_text(encoding="utf-8"))
    return 0 if report.passed or args.allow_findings else 1


def _load_artifact_entries(index_json: Path, warnings: list[str]) -> list[ArtifactEntry]:
    if not index_json.exists():
        warnings.append(f"artifact index not found: {index_json}")
        return []
    payload = json.loads(index_json.read_text(encoding="utf-8"))
    return [ArtifactEntry(**item) for item in payload.get("artifacts", [])]


def _safe_bundle_name(path: Path) -> str:
    return "__".join(path.parts[-5:])


def _pmids_by_task_split(split_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:
    data: dict[tuple[str, str], dict[str, Any]] = {}
    for path in split_dir.glob("*.jsonl"):
        task, split = _task_split_from_name(path.name)
        if task is None or split is None:
            continue
        rows = _read_jsonl(path)
        data[(task, split)] = {
            "examples": len(rows),
            "pmids": {str(row.get("source_pmid") or row.get("pmid") or "").strip() for row in rows if str(row.get("source_pmid") or row.get("pmid") or "").strip()},
        }
    return data


def _task_split_from_name(name: str) -> tuple[str | None, str | None]:
    stem = Path(name).stem
    for task in ("evidence", "ner", "relation"):
        for split in ("train", "validation", "test"):
            if stem == f"{task}_{split}":
                return task, split
    return None, None


def _default_dataset_and_label_maps_for_task(task: str) -> tuple[Path, Path]:
    if task == "evidence_classification":
        return Path("data/training/evidence_pack/annotation_splits"), Path("data/training/evidence_pack/label_maps")
    if task == "relation_extraction":
        return Path("data/training/relation_pack/annotation_splits"), Path("data/training/relation_pack/label_maps")
    return Path("data/training/ncbi_env_smoke_annotation_splits"), Path("data/training/ncbi_env_smoke_label_maps")


def _config_governance_metadata(path: str | Path) -> dict[str, str]:
    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"profile": "current", "note": "", "dataset_dir": "", "label_map_dir": ""}
    if not isinstance(payload, dict):
        return {"profile": "current", "note": "", "dataset_dir": "", "label_map_dir": ""}
    profile = str(payload.get("governance_profile") or "current").strip().casefold()
    if profile not in {"current", "scaffold"}:
        profile = "current"
    return {
        "profile": profile,
        "note": str(payload.get("governance_note") or ""),
        "dataset_dir": str(payload.get("governance_dataset_dir") or ""),
        "label_map_dir": str(payload.get("governance_label_map_dir") or ""),
    }


def _config_labels_by_task() -> dict[str, list[str]]:
    labels: dict[str, list[str]] = {}
    profiles: dict[str, str] = {}
    for path in Path("configs/training").glob("*.json"):
        try:
            config = load_training_config(path)
        except Exception:
            continue
        profile = _config_governance_metadata(path)["profile"]
        if config.task.value == "evidence_classification":
            task_key = "evidence"
        elif config.task.value == "relation_extraction":
            task_key = "relation"
        elif config.task.value == "ner":
            task_key = "ner"
        else:
            continue
        if task_key not in labels or profiles.get(task_key) != "current" or profile == "current":
            labels[task_key] = list(config.label_set)
            profiles[task_key] = profile
    return labels


def _suggest_registry_action(finding: str) -> str:
    folded = finding.casefold()
    if "checkpoint_dir" in folded:
        return "create the referenced metadata-only checkpoint directory or update the registry path"
    if "model card" in folded:
        return "generate or link a research-use model card for this checkpoint"
    if "dataset card" in folded:
        return "generate or link the dataset card used by this checkpoint"
    if "status" in folded:
        return "replace the status with an explicit research-safe scaffold status"
    if "warning" in folded:
        return "add the required research-use warning text"
    return "review the registry entry and update metadata"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON report must be an object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _write_json(payload: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output


def _write_text(lines: list[str], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def _format_tmp_markdown(report: object, writer: Any) -> str:
    tmp = Path(tempfile.gettempdir()) / f"gbmbert_governance_preview_{id(report)}.md"
    writer(report, tmp)
    text = tmp.read_text(encoding="utf-8")
    tmp.unlink(missing_ok=True)
    return text
