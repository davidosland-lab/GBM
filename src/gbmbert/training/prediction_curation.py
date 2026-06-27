"""Human review and curation bridge for GBM-BERT evidence predictions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gbmbert.curation import load_graph_records
from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.knowledge_graph.build_records import save_graph_records_jsonl
from gbmbert.knowledge_graph.overlay_guard import (
    build_overlay_load_guard_report,
    save_overlay_load_guard_json,
    save_overlay_load_guard_markdown,
)
from gbmbert.knowledge_graph.schema import EvidenceTier, GraphRelation, KnowledgeGraphRecord

LOGGER = logging.getLogger(__name__)
ReviewStatus = Literal["pending", "accepted", "corrected", "rejected"]


class PredictionReviewItem(BaseModel):
    """One GBM-BERT evidence prediction prepared for manual review."""

    model_config = ConfigDict(str_strip_whitespace=True)

    item_id: str
    item_type: Literal["evidence_prediction"] = "evidence_prediction"
    source_pmid: str
    text: str
    predicted_evidence_tier: int | None = None
    prediction_label: str = ""
    confidence: float = Field(..., ge=0.0, le=1.0)
    checkpoint_name: str = ""
    checkpoint_status: str = ""
    checkpoint_dir: str = ""
    reasons: list[str] = Field(default_factory=list)
    source_file: str = ""
    warning: str = RESEARCH_WARNING
    review_status: ReviewStatus = "pending"
    reviewer: str = ""
    review_notes: str = ""
    corrected_evidence_tier: int | None = None
    decision_timestamp_utc: str = ""
    reviewer_id: str = ""
    source_queue_sha256: str = ""
    imported_csv_sha256: str = ""

    @model_validator(mode="after")
    def curation_fields_must_be_consistent(self) -> "PredictionReviewItem":
        if self.predicted_evidence_tier is not None:
            _coerce_evidence_tier(self.predicted_evidence_tier)
        if self.corrected_evidence_tier is not None:
            _coerce_evidence_tier(self.corrected_evidence_tier)
        if self.review_status == "corrected":
            if not self.review_notes.strip():
                raise ValueError("corrected predictions require review_notes")
            if self.corrected_evidence_tier is None:
                raise ValueError("corrected predictions require corrected_evidence_tier")
        if self.review_status == "accepted":
            if self.corrected_evidence_tier is not None:
                raise ValueError("accepted predictions must not include corrected_evidence_tier")
            if self.predicted_evidence_tier is None:
                raise ValueError("accepted predictions require a valid predicted evidence tier")
        if self.review_status == "rejected" and not self.review_notes.strip():
            raise ValueError("rejected predictions require review_notes")
        return self


@dataclass(frozen=True)
class CountItem:
    key: str
    count: int


@dataclass(frozen=True)
class PredictionQualityReport:
    predictions_path: str
    prediction_count: int
    missing_pmid_count: int
    missing_text_count: int
    low_confidence_count: int
    invalid_prediction_count: int
    missing_warning_count: int
    label_counts: list[CountItem]
    evidence_tier_counts: list[CountItem]
    confidence_bucket_counts: list[CountItem]
    checkpoint_status_counts: list[CountItem]
    checkpoint_name_counts: list[CountItem]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CuratedEvidenceReport:
    predictions_path: str
    reviewed_queue_path: str
    curated_evidence_path: str
    prediction_count: int
    curated_row_count: int
    accepted_count: int
    corrected_count: int
    rejected_count: int
    pending_count: int
    missing_decision_count: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionReviewSummary:
    reviewed_queue_path: str
    item_count: int
    pending_count: int
    warning_count: int
    status_counts: list[CountItem]
    predicted_tier_counts: list[CountItem]
    corrected_tier_counts: list[CountItem]
    tier_shift_counts: list[CountItem]
    checkpoint_status_counts: list[CountItem]
    checkpoint_name_counts: list[CountItem]
    top_pmids: list[CountItem]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CuratedEvidenceAuditReport:
    curated_evidence_path: str
    row_count: int
    accepted_count: int
    corrected_count: int
    pending_count: int
    missing_pmid_count: int
    missing_item_id_count: int
    missing_warning_count: int
    missing_checkpoint_count: int
    missing_reviewer_count: int
    invalid_tier_count: int
    linkage_warning_count: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceOverlayChange:
    source_pmid: str
    relation_index: int
    original_evidence_tier: int
    overlaid_evidence_tier: int
    review_status: str


@dataclass(frozen=True)
class EvidenceOverlayReport:
    graph_path: str
    curated_evidence_path: str
    overlay_graph_path: str
    graph_record_count: int
    relation_count: int
    curated_evidence_count: int
    changed_relation_count: int
    unchanged_relation_count: int
    skipped_pending_count: int
    unmatched_evidence_count: int
    changes: list[EvidenceOverlayChange]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActiveLearningCandidateReport:
    predictions_path: str
    graph_path: str
    candidate_path: str
    prediction_count: int
    candidate_count: int
    reason_counts: list[CountItem]
    top_pmids: list[CountItem]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OverlayDiffChange:
    source_pmid: str
    relation_index: int
    action: str
    raw_evidence_tier: int | None
    overlay_evidence_tier: int | None
    detail: str


@dataclass(frozen=True)
class OverlayDiffReport:
    raw_graph_path: str
    overlay_graph_path: str
    raw_relation_count: int
    overlay_relation_count: int
    changed_relation_count: int
    increased_tier_count: int
    decreased_tier_count: int
    unchanged_relation_count: int
    added_relation_count: int
    removed_relation_count: int
    overlay_metadata_count: int
    changes: list[OverlayDiffChange]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurationSmokeWorkflowReport:
    predictions_path: str
    graph_path: str
    output_dir: str
    reports_dir: str
    candidate_path: str
    review_queue_path: str
    reviewed_queue_path: str
    curated_evidence_path: str
    overlay_graph_path: str
    quality_report_path: str
    review_summary_path: str
    curated_audit_path: str
    overlay_report_path: str
    overlay_diff_path: str
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurationHandoffArtifact:
    source_path: str
    bundled_path: str
    artifact_role: str
    suffix: str
    byte_count: int
    line_count: int | None
    sha256: str


@dataclass(frozen=True)
class CurationHandoffBundleReport:
    bundle_dir: str
    created_at_utc: str
    warning: str
    artifact_count: int
    total_bytes: int
    copied_artifact_count: int
    artifacts: list[CurationHandoffArtifact]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurationHandoffValidationReport:
    manifest_path: str
    valid: bool
    artifact_count: int
    checked_artifact_count: int
    missing_artifact_count: int
    checksum_mismatch_count: int
    missing_warning_count: int
    required_role_missing_count: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurationRunRegistryEntry:
    run_id: str
    created_at_utc: str
    predictions_path: str
    graph_path: str
    reviewed_queue_path: str
    overlay_graph_path: str
    handoff_bundle_path: str
    warning_count: int
    artifact_hashes: dict[str, str]


@dataclass(frozen=True)
class CurationRunRegistryReport:
    registry_path: str
    run_count: int
    latest_run_id: str
    entries: list[CurationRunRegistryEntry]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurationRunBrowserReport:
    registry_path: str
    run_count: int
    match_count: int
    latest_run_id: str
    filters: dict[str, str]
    runs: list[CurationRunRegistryEntry]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CuratedEvidenceSearchReport:
    curated_evidence_path: str
    row_count: int
    match_count: int
    matches: list[dict[str, Any]]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActiveLearningBatchPlanReport:
    candidates_path: str
    batch_jsonl_path: str
    candidate_count: int
    batch_count: int
    batch_size: int
    reason_counts: list[CountItem]
    evidence_tier_counts: list[CountItem]
    checkpoint_counts: list[CountItem]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActiveLearningBatchStatusItem:
    batch_id: str
    batch_index: int
    assigned_reviewer: str
    batch_status: str
    item_count: int
    reviewed_count: int
    pending_count: int
    accepted_count: int
    corrected_count: int
    rejected_count: int


@dataclass(frozen=True)
class ActiveLearningBatchStatusReport:
    batch_jsonl_path: str
    reviewed_queue_path: str
    batch_count: int
    item_count: int
    reviewed_count: int
    pending_count: int
    batches: list[ActiveLearningBatchStatusItem]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActiveLearningBatchRoundtripReport:
    action: str
    batch_id: str
    input_path: str
    output_path: str
    reviewed_queue_path: str
    row_count: int
    input_sha256: str
    output_sha256: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OverlayRevertReport:
    overlay_graph_path: str
    reverted_graph_path: str
    graph_record_count: int
    relation_count: int
    reverted_relation_count: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurationRegressionPackReport:
    output_dir: str
    reports_dir: str
    workflow_report_path: str
    handoff_manifest_path: str
    validation_report_path: str
    batch_report_path: str
    overlay_guard_path: str
    reverted_graph_path: str
    registry_path: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_prediction_review_queue(
    predictions_jsonl: str | Path,
    *,
    min_confidence: float = 0.75,
    queue_all: bool = False,
) -> list[PredictionReviewItem]:
    """Build a review queue from GBM-BERT evidence prediction JSONL output."""

    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0.0 and 1.0")
    rows = _read_jsonl(Path(predictions_jsonl))
    items: list[PredictionReviewItem] = []
    for index, row in enumerate(rows, start=1):
        reasons = _prediction_review_reasons(row, min_confidence=min_confidence)
        if not queue_all and not reasons:
            continue
        prediction_label = str(row.get("prediction") or "")
        items.append(
            PredictionReviewItem(
                item_id=_prediction_item_id(row, index),
                source_pmid=str(row.get("source_pmid") or row.get("pmid") or ""),
                text=str(row.get("text") or ""),
                prediction_label=prediction_label,
                predicted_evidence_tier=_parse_evidence_tier_or_none(prediction_label),
                confidence=float(row.get("confidence") or 0.0),
                checkpoint_name=str(row.get("checkpoint_name") or ""),
                checkpoint_status=str(row.get("checkpoint_status") or ""),
                checkpoint_dir=str(row.get("checkpoint_dir") or ""),
                reasons=reasons,
                source_file=str(predictions_jsonl),
                warning=str(row.get("warning") or RESEARCH_WARNING),
            )
        )
    return items


def export_prediction_review_queue(
    predictions_jsonl: str | Path,
    output_jsonl: str | Path,
    *,
    csv_output: str | Path | None = None,
    min_confidence: float = 0.75,
    queue_all: bool = False,
) -> list[PredictionReviewItem]:
    items = build_prediction_review_queue(
        predictions_jsonl,
        min_confidence=min_confidence,
        queue_all=queue_all,
    )
    save_prediction_review_queue_jsonl(items, output_jsonl)
    if csv_output:
        save_prediction_review_queue_csv(items, csv_output)
    return items


def export_active_learning_candidates(
    *,
    predictions_jsonl: str | Path,
    output_jsonl: str | Path,
    csv_output: str | Path | None = None,
    graph_jsonl: str | Path | None = None,
    min_confidence: float = 0.8,
    limit: int | None = None,
) -> ActiveLearningCandidateReport:
    """Export high-value prediction rows for human review prioritization."""

    rows = _read_jsonl(Path(predictions_jsonl))
    graph_pmids = _graph_pmids(graph_jsonl) if graph_jsonl else set()
    candidates: list[PredictionReviewItem] = []
    reason_counts: Counter[str] = Counter()
    pmid_counts: Counter[str] = Counter()

    for index, row in enumerate(rows, start=1):
        reasons = _active_learning_reasons(row, min_confidence=min_confidence, graph_pmids=graph_pmids)
        if not reasons:
            continue
        label = str(row.get("prediction") or "")
        item = PredictionReviewItem(
            item_id=_prediction_item_id(row, index),
            source_pmid=str(row.get("source_pmid") or row.get("pmid") or ""),
            text=str(row.get("text") or ""),
            predicted_evidence_tier=_parse_evidence_tier_or_none(label),
            prediction_label=label,
            confidence=float(row.get("confidence") or 0.0),
            checkpoint_name=str(row.get("checkpoint_name") or ""),
            checkpoint_status=str(row.get("checkpoint_status") or ""),
            checkpoint_dir=str(row.get("checkpoint_dir") or ""),
            reasons=reasons,
            source_file=str(predictions_jsonl),
            warning=str(row.get("warning") or RESEARCH_WARNING),
        )
        candidates.append(item)
        pmid_counts[item.source_pmid or "<missing>"] += 1
        for reason in reasons:
            reason_counts[reason] += 1

    candidates.sort(key=lambda item: (-_candidate_priority(item), item.source_pmid, item.item_id))
    if limit is not None:
        candidates = candidates[:limit]
    save_prediction_review_queue_jsonl(candidates, output_jsonl)
    if csv_output:
        save_prediction_review_queue_csv(candidates, csv_output)
    warnings = []
    if not candidates:
        warnings.append("No active learning candidates matched the configured criteria")
    return ActiveLearningCandidateReport(
        predictions_path=str(predictions_jsonl),
        graph_path=str(graph_jsonl or ""),
        candidate_path=str(output_jsonl),
        prediction_count=len(rows),
        candidate_count=len(candidates),
        reason_counts=_count_items(reason_counts),
        top_pmids=_count_items(pmid_counts),
        warnings=warnings,
    )


def initialize_prediction_reviewed_queue(
    input_jsonl: str | Path,
    output_jsonl: str | Path,
    *,
    reviewer: str = "",
    overwrite: bool = False,
    csv_output: str | Path | None = None,
) -> list[PredictionReviewItem]:
    """Create a reviewed prediction queue scaffold without modifying raw predictions."""

    output_path = Path(output_jsonl)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} already exists; pass overwrite=True to replace it")
    source_hash = _sha256_file(Path(input_jsonl))
    items = [
        item.model_copy(
            update={
                "review_status": "pending",
                "reviewer": reviewer,
                "reviewer_id": reviewer,
                "source_queue_sha256": source_hash,
            }
        )
        for item in load_prediction_review_queue_jsonl(input_jsonl)
    ]
    save_prediction_review_queue_jsonl(items, output_path)
    if csv_output:
        save_prediction_review_queue_csv(items, csv_output)
    return items


def analyze_prediction_quality(
    predictions_jsonl: str | Path,
    *,
    low_confidence_threshold: float = 0.75,
) -> PredictionQualityReport:
    """Summarize prediction quality and readiness for human review."""

    rows = _read_jsonl(Path(predictions_jsonl))
    label_counts: Counter[str] = Counter()
    evidence_tier_counts: Counter[str] = Counter()
    confidence_bucket_counts: Counter[str] = Counter()
    checkpoint_status_counts: Counter[str] = Counter()
    checkpoint_name_counts: Counter[str] = Counter()
    missing_pmid_count = 0
    missing_text_count = 0
    low_confidence_count = 0
    invalid_prediction_count = 0
    missing_warning_count = 0
    warnings: list[str] = []

    for row in rows:
        label = str(row.get("prediction") or "<missing>")
        label_counts[label] += 1
        tier = _parse_evidence_tier_or_none(label)
        if tier is None:
            invalid_prediction_count += 1
        else:
            evidence_tier_counts[str(tier)] += 1
        confidence = float(row.get("confidence") or 0.0)
        confidence_bucket_counts[_confidence_bucket(confidence)] += 1
        if confidence < low_confidence_threshold:
            low_confidence_count += 1
        if not str(row.get("source_pmid") or "").strip():
            missing_pmid_count += 1
        if not str(row.get("text") or "").strip():
            missing_text_count += 1
        if str(row.get("warning") or "") != RESEARCH_WARNING:
            missing_warning_count += 1
        checkpoint_status_counts[str(row.get("checkpoint_status") or "<missing>")] += 1
        checkpoint_name_counts[str(row.get("checkpoint_name") or "<missing>")] += 1

    if not rows:
        warnings.append("No predictions found")
    if low_confidence_count:
        warnings.append(f"{low_confidence_count} prediction(s) below confidence {low_confidence_threshold}")
    if invalid_prediction_count:
        warnings.append(f"{invalid_prediction_count} prediction(s) have labels outside evidence tiers 0-5")
    if missing_warning_count:
        warnings.append(f"{missing_warning_count} prediction row(s) are missing the research-use warning")
    for status in checkpoint_status_counts:
        if status not in {"research_candidate", "candidate"}:
            warnings.append(f"Checkpoint status observed: {status}")

    return PredictionQualityReport(
        predictions_path=str(predictions_jsonl),
        prediction_count=len(rows),
        missing_pmid_count=missing_pmid_count,
        missing_text_count=missing_text_count,
        low_confidence_count=low_confidence_count,
        invalid_prediction_count=invalid_prediction_count,
        missing_warning_count=missing_warning_count,
        label_counts=_count_items(label_counts),
        evidence_tier_counts=_count_items(evidence_tier_counts),
        confidence_bucket_counts=_count_items(confidence_bucket_counts),
        checkpoint_status_counts=_count_items(checkpoint_status_counts),
        checkpoint_name_counts=_count_items(checkpoint_name_counts),
        warnings=warnings,
    )


def summarize_prediction_review_queue(
    reviewed_queue_jsonl: str | Path,
) -> PredictionReviewSummary:
    """Summarize reviewed GBM-BERT prediction decisions for curation planning."""

    items = load_prediction_review_queue_jsonl(reviewed_queue_jsonl)
    status_counts: Counter[str] = Counter()
    predicted_tier_counts: Counter[str] = Counter()
    corrected_tier_counts: Counter[str] = Counter()
    tier_shift_counts: Counter[str] = Counter()
    checkpoint_status_counts: Counter[str] = Counter()
    checkpoint_name_counts: Counter[str] = Counter()
    pmid_counts: Counter[str] = Counter()
    warnings: list[str] = []

    for item in items:
        status_counts[item.review_status] += 1
        if item.predicted_evidence_tier is not None:
            predicted_tier_counts[str(item.predicted_evidence_tier)] += 1
        if item.corrected_evidence_tier is not None:
            corrected_tier_counts[str(item.corrected_evidence_tier)] += 1
            if item.predicted_evidence_tier is not None:
                shift = item.corrected_evidence_tier - item.predicted_evidence_tier
                tier_shift_counts[_tier_shift_label(item.predicted_evidence_tier, item.corrected_evidence_tier)] += 1
                if shift > 0:
                    tier_shift_counts["increased"] += 1
                elif shift < 0:
                    tier_shift_counts["decreased"] += 1
                else:
                    tier_shift_counts["unchanged"] += 1
        checkpoint_status_counts[item.checkpoint_status or "<missing>"] += 1
        checkpoint_name_counts[item.checkpoint_name or "<missing>"] += 1
        pmid_counts[item.source_pmid or "<missing>"] += 1

    pending_count = status_counts.get("pending", 0)
    if pending_count:
        warnings.append(f"{pending_count} prediction item(s) still pending review")
    if status_counts.get("corrected", 0) and not corrected_tier_counts:
        warnings.append("Corrected items exist but no corrected tier counts were recorded")
    if checkpoint_status_counts.get("<missing>", 0):
        warnings.append(f"{checkpoint_status_counts['<missing>']} item(s) missing checkpoint status")
    if checkpoint_name_counts.get("<missing>", 0):
        warnings.append(f"{checkpoint_name_counts['<missing>']} item(s) missing checkpoint name")

    return PredictionReviewSummary(
        reviewed_queue_path=str(reviewed_queue_jsonl),
        item_count=len(items),
        pending_count=pending_count,
        warning_count=len(warnings),
        status_counts=_count_items(status_counts),
        predicted_tier_counts=_count_items(predicted_tier_counts),
        corrected_tier_counts=_count_items(corrected_tier_counts),
        tier_shift_counts=_count_items(tier_shift_counts),
        checkpoint_status_counts=_count_items(checkpoint_status_counts),
        checkpoint_name_counts=_count_items(checkpoint_name_counts),
        top_pmids=_count_items(pmid_counts),
        warnings=warnings,
    )


def audit_curated_evidence(
    curated_evidence_jsonl: str | Path,
) -> CuratedEvidenceAuditReport:
    """Audit curated prediction rows before graph overlays or handoff."""

    rows = _read_jsonl(Path(curated_evidence_jsonl))
    status_counts: Counter[str] = Counter()
    missing_pmid_count = 0
    missing_item_id_count = 0
    missing_warning_count = 0
    missing_checkpoint_count = 0
    missing_reviewer_count = 0
    invalid_tier_count = 0
    linkage_warning_count = 0
    warnings: list[str] = []

    for line_number, row in enumerate(rows, start=1):
        status = str(row.get("review_status") or "pending")
        status_counts[status] += 1
        pmid = str(row.get("source_pmid") or "").strip()
        item_id = str(row.get("item_id") or "").strip()
        if not pmid:
            missing_pmid_count += 1
        if not item_id:
            missing_item_id_count += 1
        elif pmid and not item_id.startswith(f"prediction:{pmid}:"):
            linkage_warning_count += 1
            warnings.append(f"Line {line_number}: item_id does not match source_pmid")
        if str(row.get("warning") or "") != RESEARCH_WARNING:
            missing_warning_count += 1
        if not str(row.get("checkpoint_name") or "").strip() or not str(row.get("checkpoint_status") or "").strip():
            missing_checkpoint_count += 1
        if status in {"accepted", "corrected"} and not str(row.get("reviewer") or "").strip():
            missing_reviewer_count += 1
        if _parse_evidence_tier_or_none(row.get("curated_evidence_tier")) is None:
            invalid_tier_count += 1
        if "original_prediction" not in row or "original_predicted_evidence_tier" not in row:
            linkage_warning_count += 1
            warnings.append(f"Line {line_number}: missing original prediction linkage")

    if missing_pmid_count:
        warnings.append(f"{missing_pmid_count} curated evidence row(s) missing source_pmid")
    if missing_item_id_count:
        warnings.append(f"{missing_item_id_count} curated evidence row(s) missing item_id")
    if missing_warning_count:
        warnings.append(f"{missing_warning_count} curated evidence row(s) missing the research-use warning")
    if missing_checkpoint_count:
        warnings.append(f"{missing_checkpoint_count} curated evidence row(s) missing checkpoint metadata")
    if missing_reviewer_count:
        warnings.append(f"{missing_reviewer_count} accepted/corrected row(s) missing reviewer")
    if invalid_tier_count:
        warnings.append(f"{invalid_tier_count} curated evidence row(s) have invalid evidence tier")

    return CuratedEvidenceAuditReport(
        curated_evidence_path=str(curated_evidence_jsonl),
        row_count=len(rows),
        accepted_count=status_counts.get("accepted", 0),
        corrected_count=status_counts.get("corrected", 0),
        pending_count=status_counts.get("pending", 0),
        missing_pmid_count=missing_pmid_count,
        missing_item_id_count=missing_item_id_count,
        missing_warning_count=missing_warning_count,
        missing_checkpoint_count=missing_checkpoint_count,
        missing_reviewer_count=missing_reviewer_count,
        invalid_tier_count=invalid_tier_count,
        linkage_warning_count=linkage_warning_count,
        warnings=warnings,
    )


def export_curated_evidence(
    *,
    predictions_jsonl: str | Path,
    reviewed_queue_jsonl: str | Path,
    output_jsonl: str | Path,
    fail_on_pending: bool = False,
) -> CuratedEvidenceReport:
    """Export reviewed evidence predictions to a separate curated evidence JSONL artifact."""

    rows = _read_jsonl(Path(predictions_jsonl))
    decisions = {
        item.item_id: item
        for item in load_prediction_review_queue_jsonl(reviewed_queue_jsonl)
    }
    status_counts = Counter(item.review_status for item in decisions.values())
    missing_decision_count = 0
    curated_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    pending_count = status_counts.get("pending", 0)
    if pending_count:
        warning = f"{pending_count} prediction item(s) still pending review"
        warnings.append(warning)
        if fail_on_pending:
            raise ValueError(warning)

    for index, row in enumerate(rows, start=1):
        item_id = _prediction_item_id(row, index)
        decision = decisions.get(item_id)
        if decision is None:
            missing_decision_count += 1
            decision = _decision_from_prediction_row(row, index, status="pending", source_file=str(predictions_jsonl))
        if decision.review_status == "rejected":
            continue
        curated = _curated_evidence_row(row, decision)
        curated_rows.append(curated)

    output_path = Path(output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in curated_rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")

    return CuratedEvidenceReport(
        predictions_path=str(predictions_jsonl),
        reviewed_queue_path=str(reviewed_queue_jsonl),
        curated_evidence_path=str(output_jsonl),
        prediction_count=len(rows),
        curated_row_count=len(curated_rows),
        accepted_count=status_counts.get("accepted", 0),
        corrected_count=status_counts.get("corrected", 0),
        rejected_count=status_counts.get("rejected", 0),
        pending_count=status_counts.get("pending", 0) + missing_decision_count,
        missing_decision_count=missing_decision_count,
        warnings=warnings,
    )


def import_prediction_review_csv(
    input_csv: str | Path,
    output_jsonl: str | Path,
    *,
    overwrite: bool = False,
) -> list[PredictionReviewItem]:
    """Import a manually edited prediction review CSV into validated JSONL."""

    output_path = Path(output_jsonl)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} already exists; pass overwrite=True to replace it")
    items: list[PredictionReviewItem] = []
    csv_hash = _sha256_file(Path(input_csv))
    imported_at = datetime.now(UTC).isoformat()
    with Path(input_csv).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            try:
                payload = _csv_row_to_prediction_review_item(row)
                payload["imported_csv_sha256"] = payload.get("imported_csv_sha256") or csv_hash
                if payload.get("review_status") in {"accepted", "corrected", "rejected"}:
                    payload["decision_timestamp_utc"] = payload.get("decision_timestamp_utc") or imported_at
                payload["reviewer_id"] = payload.get("reviewer_id") or payload.get("reviewer", "")
                items.append(PredictionReviewItem.model_validate(payload))
            except ValueError as exc:
                raise ValueError(f"Invalid prediction review CSV row {line_number}: {exc}") from exc
    save_prediction_review_queue_jsonl(items, output_path)
    return items


def apply_evidence_overlay_to_graph(
    *,
    graph_jsonl: str | Path,
    curated_evidence_jsonl: str | Path,
    output_jsonl: str | Path,
    include_pending: bool = False,
) -> EvidenceOverlayReport:
    """Apply curated evidence tiers to a new graph JSONL artifact by PMID."""

    records = load_graph_records(graph_jsonl)
    curated_rows = _read_jsonl(Path(curated_evidence_jsonl))
    evidence_by_pmid: dict[str, dict[str, Any]] = {}
    skipped_pending_count = 0
    for row in curated_rows:
        status = str(row.get("review_status") or "pending")
        if status == "pending" and not include_pending:
            skipped_pending_count += 1
            continue
        pmid = str(row.get("source_pmid") or "")
        tier = _parse_evidence_tier_or_none(row.get("curated_evidence_tier"))
        if not pmid or tier is None:
            continue
        existing = evidence_by_pmid.get(pmid)
        if existing is None or int(row["curated_evidence_tier"]) > int(existing["curated_evidence_tier"]):
            evidence_by_pmid[pmid] = row

    changes: list[EvidenceOverlayChange] = []
    changed_pmids: set[str] = set()
    output_records: list[KnowledgeGraphRecord] = []
    relation_count = 0
    unchanged_relation_count = 0

    for record in records:
        evidence = evidence_by_pmid.get(record.pmid)
        if evidence is None:
            output_records.append(record)
            relation_count += len(record.relations)
            unchanged_relation_count += len(record.relations)
            continue
        overlaid_relations: list[GraphRelation] = []
        overlaid_tier = _coerce_evidence_tier(evidence["curated_evidence_tier"])
        for relation_index, relation in enumerate(record.relations, start=1):
            relation_count += 1
            if relation.evidence_tier == overlaid_tier:
                unchanged_relation_count += 1
                overlaid_relations.append(relation)
                continue
            changed_pmids.add(record.pmid)
            changes.append(
                EvidenceOverlayChange(
                    source_pmid=record.pmid,
                    relation_index=relation_index,
                    original_evidence_tier=int(relation.evidence_tier),
                    overlaid_evidence_tier=int(overlaid_tier),
                    review_status=str(evidence.get("review_status") or ""),
                )
            )
            overlaid_relations.append(_overlay_relation(relation, evidence, overlaid_tier))
        output_records.append(record.model_copy(update={"relations": overlaid_relations}))

    save_graph_records_jsonl(output_records, output_jsonl)
    unmatched_evidence_count = len(set(evidence_by_pmid) - {record.pmid for record in records})
    warnings = []
    if skipped_pending_count:
        warnings.append(f"{skipped_pending_count} pending curated evidence row(s) skipped")
    if unmatched_evidence_count:
        warnings.append(f"{unmatched_evidence_count} curated evidence PMID(s) did not match graph records")

    return EvidenceOverlayReport(
        graph_path=str(graph_jsonl),
        curated_evidence_path=str(curated_evidence_jsonl),
        overlay_graph_path=str(output_jsonl),
        graph_record_count=len(records),
        relation_count=relation_count,
        curated_evidence_count=len(curated_rows),
        changed_relation_count=len(changes),
        unchanged_relation_count=unchanged_relation_count,
        skipped_pending_count=skipped_pending_count,
        unmatched_evidence_count=unmatched_evidence_count,
        changes=changes,
        warnings=warnings,
    )


def build_overlay_diff_report(
    *,
    raw_graph_jsonl: str | Path,
    overlay_graph_jsonl: str | Path,
) -> OverlayDiffReport:
    """Compare raw graph records against an evidence-overlay graph artifact."""

    raw_records = load_graph_records(raw_graph_jsonl)
    overlay_records = load_graph_records(overlay_graph_jsonl)
    raw_relations = _indexed_relations(raw_records)
    overlay_relations = _indexed_relations(overlay_records)
    changes: list[OverlayDiffChange] = []
    increased = 0
    decreased = 0
    unchanged = 0
    overlay_metadata_count = 0

    for key in sorted(set(raw_relations) | set(overlay_relations)):
        raw_relation = raw_relations.get(key)
        overlay_relation = overlay_relations.get(key)
        pmid, relation_index = key
        if raw_relation is None and overlay_relation is not None:
            changes.append(
                OverlayDiffChange(
                    source_pmid=pmid,
                    relation_index=relation_index,
                    action="added",
                    raw_evidence_tier=None,
                    overlay_evidence_tier=int(overlay_relation.evidence_tier),
                    detail="Relation exists only in overlay graph",
                )
            )
            continue
        if raw_relation is not None and overlay_relation is None:
            changes.append(
                OverlayDiffChange(
                    source_pmid=pmid,
                    relation_index=relation_index,
                    action="removed",
                    raw_evidence_tier=int(raw_relation.evidence_tier),
                    overlay_evidence_tier=None,
                    detail="Relation exists only in raw graph",
                )
            )
            continue
        if raw_relation is None or overlay_relation is None:
            continue
        if "evidence_overlay_tier" in overlay_relation.properties:
            overlay_metadata_count += 1
        raw_tier = int(raw_relation.evidence_tier)
        overlay_tier = int(overlay_relation.evidence_tier)
        if raw_tier == overlay_tier:
            unchanged += 1
            continue
        action = "increased" if overlay_tier > raw_tier else "decreased"
        if action == "increased":
            increased += 1
        else:
            decreased += 1
        changes.append(
            OverlayDiffChange(
                source_pmid=pmid,
                relation_index=relation_index,
                action=action,
                raw_evidence_tier=raw_tier,
                overlay_evidence_tier=overlay_tier,
                detail=f"Evidence tier {raw_tier} -> {overlay_tier}",
            )
        )

    added_count = sum(1 for change in changes if change.action == "added")
    removed_count = sum(1 for change in changes if change.action == "removed")
    warnings = []
    if overlay_metadata_count == 0:
        warnings.append("Overlay graph does not contain evidence overlay metadata")
    return OverlayDiffReport(
        raw_graph_path=str(raw_graph_jsonl),
        overlay_graph_path=str(overlay_graph_jsonl),
        raw_relation_count=len(raw_relations),
        overlay_relation_count=len(overlay_relations),
        changed_relation_count=len([change for change in changes if change.action in {"increased", "decreased"}]),
        increased_tier_count=increased,
        decreased_tier_count=decreased,
        unchanged_relation_count=unchanged,
        added_relation_count=added_count,
        removed_relation_count=removed_count,
        overlay_metadata_count=overlay_metadata_count,
        changes=changes,
        warnings=warnings,
    )


def run_curation_smoke_workflow(
    *,
    predictions_jsonl: str | Path,
    graph_jsonl: str | Path,
    reviewed_queue_jsonl: str | Path,
    output_dir: str | Path,
    reports_dir: str | Path,
) -> CurationSmokeWorkflowReport:
    """Run the local prediction curation workflow on existing smoke artifacts."""

    output_path = Path(output_dir)
    reports_path = Path(reports_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    candidates_path = output_path / "active_learning_candidates.jsonl"
    review_queue_path = output_path / "prediction_review_queue.jsonl"
    reviewed_copy_path = output_path / "prediction_reviewed_queue.jsonl"
    curated_evidence_path = output_path / "curated_evidence_predictions.jsonl"
    overlay_graph_path = output_path / "evidence_overlay_graph_records.jsonl"

    quality_md = reports_path / "prediction_quality.md"
    review_summary_md = reports_path / "prediction_review_summary.md"
    curated_audit_md = reports_path / "curated_evidence_audit.md"
    overlay_report_md = reports_path / "evidence_overlay.md"
    overlay_diff_md = reports_path / "evidence_overlay_diff.md"

    export_active_learning_candidates(
        predictions_jsonl=predictions_jsonl,
        output_jsonl=candidates_path,
        graph_jsonl=graph_jsonl,
        min_confidence=1.0,
    )
    export_prediction_review_queue(
        predictions_jsonl,
        review_queue_path,
        queue_all=True,
    )
    reviewed_items = load_prediction_review_queue_jsonl(reviewed_queue_jsonl)
    save_prediction_review_queue_jsonl(reviewed_items, reviewed_copy_path)

    quality = analyze_prediction_quality(predictions_jsonl)
    save_prediction_quality_markdown(quality, quality_md)
    save_prediction_quality_json(quality, reports_path / "prediction_quality.json")

    summary = summarize_prediction_review_queue(reviewed_copy_path)
    save_prediction_review_summary_markdown(summary, review_summary_md)
    save_prediction_review_summary_json(summary, reports_path / "prediction_review_summary.json")

    export_curated_evidence(
        predictions_jsonl=predictions_jsonl,
        reviewed_queue_jsonl=reviewed_copy_path,
        output_jsonl=curated_evidence_path,
    )
    audit = audit_curated_evidence(curated_evidence_path)
    save_curated_evidence_audit_markdown(audit, curated_audit_md)
    save_curated_evidence_audit_json(audit, reports_path / "curated_evidence_audit.json")

    overlay = apply_evidence_overlay_to_graph(
        graph_jsonl=graph_jsonl,
        curated_evidence_jsonl=curated_evidence_path,
        output_jsonl=overlay_graph_path,
    )
    save_overlay_report_markdown(overlay, overlay_report_md)
    save_overlay_report_json(overlay, reports_path / "evidence_overlay.json")

    diff = build_overlay_diff_report(raw_graph_jsonl=graph_jsonl, overlay_graph_jsonl=overlay_graph_path)
    save_overlay_diff_markdown(diff, overlay_diff_md)
    save_overlay_diff_json(diff, reports_path / "evidence_overlay_diff.json")

    warnings = [*quality.warnings, *summary.warnings, *audit.warnings, *overlay.warnings, *diff.warnings]
    return CurationSmokeWorkflowReport(
        predictions_path=str(predictions_jsonl),
        graph_path=str(graph_jsonl),
        output_dir=str(output_path),
        reports_dir=str(reports_path),
        candidate_path=str(candidates_path),
        review_queue_path=str(review_queue_path),
        reviewed_queue_path=str(reviewed_copy_path),
        curated_evidence_path=str(curated_evidence_path),
        overlay_graph_path=str(overlay_graph_path),
        quality_report_path=str(quality_md),
        review_summary_path=str(review_summary_md),
        curated_audit_path=str(curated_audit_md),
        overlay_report_path=str(overlay_report_md),
        overlay_diff_path=str(overlay_diff_md),
        warnings=warnings,
    )


def build_curation_handoff_bundle(
    *,
    artifact_paths: list[str | Path] | None = None,
    output_dir: str | Path,
    copy_artifacts: bool = True,
) -> CurationHandoffBundleReport:
    """Create a manifest and optional file bundle for curation workflow handoff."""

    bundle_dir = Path(output_dir)
    files_dir = bundle_dir / "files"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    if copy_artifacts:
        files_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[CurationHandoffArtifact] = []
    warnings: list[str] = []
    seen_targets: Counter[str] = Counter()
    for source in artifact_paths or _default_curation_handoff_artifacts():
        source_path = Path(source)
        if not source_path.exists():
            warnings.append(f"Missing artifact: {source_path}")
            continue
        target_path = source_path
        if copy_artifacts:
            target_path = files_dir / _bundle_artifact_name(source_path, seen_targets)
            shutil.copy2(source_path, target_path)
        artifacts.append(
            CurationHandoffArtifact(
                source_path=str(source_path),
                bundled_path=str(target_path),
                artifact_role=_curation_artifact_role(source_path),
                suffix=source_path.suffix.lower() or "<none>",
                byte_count=source_path.stat().st_size,
                line_count=_line_count(source_path),
                sha256=_sha256_file(source_path),
            )
        )

    if not artifacts:
        warnings.append("No curation handoff artifacts were found")
    return CurationHandoffBundleReport(
        bundle_dir=str(bundle_dir),
        created_at_utc=datetime.now(UTC).isoformat(),
        warning=RESEARCH_WARNING,
        artifact_count=len(artifacts),
        total_bytes=sum(artifact.byte_count for artifact in artifacts),
        copied_artifact_count=len(artifacts) if copy_artifacts else 0,
        artifacts=artifacts,
        warnings=warnings,
    )


def validate_curation_handoff_bundle(
    manifest_json: str | Path,
    *,
    required_roles: set[str] | None = None,
) -> CurationHandoffValidationReport:
    """Validate a curation handoff manifest and the files it references."""

    manifest_path = Path(manifest_json)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts", [])
    expected_roles = _required_handoff_roles() if required_roles is None else required_roles
    observed_roles = {str(item.get("artifact_role") or "") for item in artifacts}
    warnings: list[str] = []
    checked = 0
    missing = 0
    mismatched = 0
    missing_warning = 0

    if payload.get("artifact_count") != len(artifacts):
        warnings.append("Manifest artifact_count does not match artifact list length")
    for role in sorted(expected_roles - observed_roles):
        warnings.append(f"Missing required artifact role: {role}")

    manifest_text = manifest_path.read_text(encoding="utf-8")
    if RESEARCH_WARNING not in manifest_text:
        missing_warning += 1
        warnings.append("Manifest JSON is missing the research-use warning")

    for item in artifacts:
        bundled_path = Path(str(item.get("bundled_path") or ""))
        role = str(item.get("artifact_role") or "curation_artifact")
        if not bundled_path.exists():
            missing += 1
            warnings.append(f"Missing bundled artifact for {role}: {bundled_path}")
            continue
        checked += 1
        expected_sha = str(item.get("sha256") or "").upper()
        actual_sha = _sha256_file(bundled_path)
        if expected_sha and actual_sha != expected_sha:
            mismatched += 1
            warnings.append(f"SHA256 mismatch for {bundled_path}")
        if bundled_path.suffix.lower() in {".md", ".json"}:
            try:
                if RESEARCH_WARNING not in bundled_path.read_text(encoding="utf-8"):
                    missing_warning += 1
                    warnings.append(f"Research-use warning missing from {bundled_path}")
            except UnicodeDecodeError:
                pass

    return CurationHandoffValidationReport(
        manifest_path=str(manifest_path),
        valid=not warnings,
        artifact_count=len(artifacts),
        checked_artifact_count=checked,
        missing_artifact_count=missing,
        checksum_mismatch_count=mismatched,
        missing_warning_count=missing_warning,
        required_role_missing_count=len(expected_roles - observed_roles),
        warnings=warnings,
    )


def update_curation_run_registry(
    *,
    registry_json: str | Path,
    workflow_report_json: str | Path,
    handoff_manifest_json: str | Path | None = None,
) -> CurationRunRegistryReport:
    """Append a curation workflow run entry to a local run registry."""

    registry_path = Path(registry_json)
    workflow_path = Path(workflow_report_json)
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    artifact_hashes: dict[str, str] = {"workflow_report": _sha256_file(workflow_path)}
    handoff_path = Path(handoff_manifest_json) if handoff_manifest_json else None
    if handoff_path and handoff_path.exists():
        artifact_hashes["handoff_bundle"] = _sha256_file(handoff_path)
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        for artifact in handoff.get("artifacts", []):
            role = str(artifact.get("artifact_role") or "curation_artifact")
            artifact_hashes[role] = str(artifact.get("sha256") or "")

    created_at = datetime.now(UTC).isoformat()
    run_id = _curation_run_id(workflow, created_at, artifact_hashes)
    entry = CurationRunRegistryEntry(
        run_id=run_id,
        created_at_utc=created_at,
        predictions_path=str(workflow.get("predictions_path") or ""),
        graph_path=str(workflow.get("graph_path") or ""),
        reviewed_queue_path=str(workflow.get("reviewed_queue_path") or ""),
        overlay_graph_path=str(workflow.get("overlay_graph_path") or ""),
        handoff_bundle_path=str(handoff_path or ""),
        warning_count=len(workflow.get("warnings") or []),
        artifact_hashes=artifact_hashes,
    )
    entries = _load_curation_registry_entries(registry_path)
    entries = [
        item
        for item in entries
        if item.run_id != entry.run_id
        and not (
            item.predictions_path == entry.predictions_path
            and item.graph_path == entry.graph_path
            and item.handoff_bundle_path == entry.handoff_bundle_path
        )
    ]
    entries.append(entry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "warning": RESEARCH_WARNING,
                "run_count": len(entries),
                "entries": [asdict(item) for item in entries],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return CurationRunRegistryReport(
        registry_path=str(registry_path),
        run_count=len(entries),
        latest_run_id=entry.run_id,
        entries=entries,
        warnings=[],
    )


def search_curated_evidence(
    curated_evidence_jsonl: str | Path,
    *,
    pmid: str = "",
    evidence_tier: int | None = None,
    reviewer: str = "",
    review_status: str = "",
    checkpoint: str = "",
    text: str = "",
    limit: int | None = None,
) -> CuratedEvidenceSearchReport:
    """Search curated evidence rows by provenance, decision, tier, and text."""

    rows = _read_jsonl(Path(curated_evidence_jsonl))
    matches: list[dict[str, Any]] = []
    text_query = text.casefold()
    for row in rows:
        if pmid and str(row.get("source_pmid") or "") != str(pmid):
            continue
        if evidence_tier is not None and _parse_evidence_tier_or_none(row.get("curated_evidence_tier")) != evidence_tier:
            continue
        if reviewer and reviewer.casefold() not in str(row.get("reviewer") or "").casefold():
            continue
        if review_status and str(row.get("review_status") or "") != review_status:
            continue
        if checkpoint and checkpoint.casefold() not in str(row.get("checkpoint_name") or "").casefold():
            continue
        if text_query and text_query not in str(row.get("text") or "").casefold():
            continue
        matches.append(row)
        if limit is not None and len(matches) >= limit:
            break
    warnings = []
    if not matches:
        warnings.append("No curated evidence rows matched the search filters")
    return CuratedEvidenceSearchReport(
        curated_evidence_path=str(curated_evidence_jsonl),
        row_count=len(rows),
        match_count=len(matches),
        matches=matches,
        warnings=warnings,
    )


def browse_curation_runs(
    registry_json: str | Path = Path("reports/review/curation_run_registry.json"),
    *,
    run_id: str = "",
    path_contains: str = "",
    warnings_only: bool = False,
    limit: int | None = None,
) -> CurationRunBrowserReport:
    """List and filter registered curation workflow runs."""

    registry_path = Path(registry_json)
    warnings: list[str] = []
    if not registry_path.exists():
        return CurationRunBrowserReport(
            registry_path=str(registry_path),
            run_count=0,
            match_count=0,
            latest_run_id="",
            filters={
                "run_id": run_id,
                "path_contains": path_contains,
                "warnings_only": str(warnings_only),
            },
            runs=[],
            warnings=[f"Registry not found: {registry_path}"],
        )
    entries = _load_curation_registry_entries(registry_path)
    latest_run_id = entries[-1].run_id if entries else ""
    matches = list(reversed(entries))
    if run_id:
        query = run_id.casefold()
        matches = [entry for entry in matches if query in entry.run_id.casefold()]
    if path_contains:
        query = path_contains.casefold()
        matches = [
            entry
            for entry in matches
            if query
            in " ".join(
                [
                    entry.predictions_path,
                    entry.graph_path,
                    entry.reviewed_queue_path,
                    entry.overlay_graph_path,
                    entry.handoff_bundle_path,
                ]
            ).casefold()
        ]
    if warnings_only:
        matches = [entry for entry in matches if entry.warning_count > 0]
    if limit is not None:
        matches = matches[:limit]
    if not entries:
        warnings.append("No curation runs are registered")
    if entries and not matches:
        warnings.append("No curation runs matched the filters")
    return CurationRunBrowserReport(
        registry_path=str(registry_path),
        run_count=len(entries),
        match_count=len(matches),
        latest_run_id=latest_run_id,
        filters={
            "run_id": run_id,
            "path_contains": path_contains,
            "warnings_only": str(warnings_only),
        },
        runs=matches,
        warnings=warnings,
    )


def plan_active_learning_batches(
    candidates_jsonl: str | Path,
    output_jsonl: str | Path,
    *,
    csv_output: str | Path | None = None,
    batch_size: int = 25,
) -> ActiveLearningBatchPlanReport:
    """Group active learning candidates into reviewer-sized batches."""

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    candidates = load_prediction_review_queue_jsonl(candidates_jsonl)
    output_path = Path(output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    reason_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    checkpoint_counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(candidates, start=1):
        batch_number = ((index - 1) // batch_size) + 1
        row = item.model_dump()
        row.update(
            {
                "batch_id": f"ALBATCH-{batch_number:03d}",
                "batch_index": batch_number,
                "batch_position": ((index - 1) % batch_size) + 1,
                "batch_status": "pending",
                "assigned_reviewer": item.reviewer_id or item.reviewer,
            }
        )
        rows.append(row)
        for reason in item.reasons:
            reason_counts[reason] += 1
        tier_counts[str(item.predicted_evidence_tier if item.predicted_evidence_tier is not None else "<missing>")] += 1
        checkpoint_counts[item.checkpoint_name or "<missing>"] += 1
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")
    if csv_output:
        csv_path = Path(csv_output)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["batch_id", "batch_index", "batch_position", "batch_status", "assigned_reviewer", *PredictionReviewItem.model_fields]
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                csv_row = {field: row.get(field, "") for field in fieldnames}
                csv_row["reasons"] = "; ".join(row.get("reasons") or [])
                writer.writerow(csv_row)
    warnings = []
    if not rows:
        warnings.append("No active learning candidates were available for batching")
    return ActiveLearningBatchPlanReport(
        candidates_path=str(candidates_jsonl),
        batch_jsonl_path=str(output_jsonl),
        candidate_count=len(rows),
        batch_count=(len(rows) + batch_size - 1) // batch_size,
        batch_size=batch_size,
        reason_counts=_count_items(reason_counts),
        evidence_tier_counts=_count_items(tier_counts),
        checkpoint_counts=_count_items(checkpoint_counts),
        warnings=warnings,
    )


def summarize_active_learning_batch_status(
    batch_jsonl: str | Path,
    *,
    reviewed_queue_jsonl: str | Path | None = None,
) -> ActiveLearningBatchStatusReport:
    """Summarize active learning batch review progress."""

    rows = _read_jsonl(Path(batch_jsonl))
    reviewed_by_id: dict[str, PredictionReviewItem] = {}
    if reviewed_queue_jsonl:
        reviewed_by_id = {item.item_id: item for item in load_prediction_review_queue_jsonl(reviewed_queue_jsonl)}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        item_id = str(row.get("item_id") or "")
        reviewed = reviewed_by_id.get(item_id)
        if reviewed is not None:
            row = {**row, **reviewed.model_dump()}
        batch_id = str(row.get("batch_id") or "UNBATCHED")
        grouped.setdefault(batch_id, []).append(row)

    batch_items: list[ActiveLearningBatchStatusItem] = []
    total_reviewed = 0
    total_pending = 0
    for batch_id, batch_rows in sorted(grouped.items(), key=lambda item: _batch_sort_key(item[0], item[1])):
        status_counts = Counter(str(row.get("review_status") or "pending") for row in batch_rows)
        reviewed_count = status_counts.get("accepted", 0) + status_counts.get("corrected", 0) + status_counts.get("rejected", 0)
        pending_count = status_counts.get("pending", 0)
        total_reviewed += reviewed_count
        total_pending += pending_count
        assigned = next((str(row.get("assigned_reviewer") or row.get("reviewer_id") or row.get("reviewer") or "") for row in batch_rows if str(row.get("assigned_reviewer") or row.get("reviewer_id") or row.get("reviewer") or "").strip()), "")
        explicit_status = next((str(row.get("batch_status") or "") for row in batch_rows if str(row.get("batch_status") or "").strip() and str(row.get("batch_status")) != "pending"), "")
        if reviewed_count == len(batch_rows) and batch_rows:
            batch_status = "complete"
        elif reviewed_count:
            batch_status = "in_progress"
        else:
            batch_status = explicit_status or "pending"
        batch_items.append(
            ActiveLearningBatchStatusItem(
                batch_id=batch_id,
                batch_index=int(batch_rows[0].get("batch_index") or 0),
                assigned_reviewer=assigned,
                batch_status=batch_status,
                item_count=len(batch_rows),
                reviewed_count=reviewed_count,
                pending_count=pending_count,
                accepted_count=status_counts.get("accepted", 0),
                corrected_count=status_counts.get("corrected", 0),
                rejected_count=status_counts.get("rejected", 0),
            )
        )
    warnings: list[str] = []
    if not rows:
        warnings.append("No active learning batch rows were found")
    if rows and total_pending:
        warnings.append(f"{total_pending} active learning batch item(s) still pending review")
    return ActiveLearningBatchStatusReport(
        batch_jsonl_path=str(batch_jsonl),
        reviewed_queue_path=str(reviewed_queue_jsonl or ""),
        batch_count=len(batch_items),
        item_count=len(rows),
        reviewed_count=total_reviewed,
        pending_count=total_pending,
        batches=batch_items,
        warnings=warnings,
    )


def export_active_learning_batch_csv(
    batch_jsonl: str | Path,
    batch_id: str,
    output_csv: str | Path,
    *,
    assigned_reviewer: str = "",
    batch_status: str = "in_review",
) -> ActiveLearningBatchRoundtripReport:
    """Export one active learning batch to a curator-editable CSV."""

    rows = [row for row in _read_jsonl(Path(batch_jsonl)) if str(row.get("batch_id") or "") == batch_id]
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["batch_id", "batch_index", "batch_position", "batch_status", "assigned_reviewer", *PredictionReviewItem.model_fields]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = {field: row.get(field, "") for field in fieldnames}
            csv_row["assigned_reviewer"] = assigned_reviewer or csv_row.get("assigned_reviewer") or csv_row.get("reviewer_id") or csv_row.get("reviewer")
            csv_row["batch_status"] = batch_status or csv_row.get("batch_status") or "in_review"
            csv_row["reasons"] = "; ".join(row.get("reasons") or [])
            writer.writerow(csv_row)
    warnings = []
    if not rows:
        warnings.append(f"No rows found for batch {batch_id}")
    return ActiveLearningBatchRoundtripReport(
        action="export",
        batch_id=batch_id,
        input_path=str(batch_jsonl),
        output_path=str(output_path),
        reviewed_queue_path="",
        row_count=len(rows),
        input_sha256=_sha256_file(Path(batch_jsonl)),
        output_sha256=_sha256_file(output_path),
        warnings=warnings,
    )


def import_active_learning_batch_csv(
    input_csv: str | Path,
    output_jsonl: str | Path,
    *,
    reviewed_queue_jsonl: str | Path | None = None,
    overwrite: bool = False,
) -> ActiveLearningBatchRoundtripReport:
    """Import one curator-edited active learning batch CSV into a reviewed queue JSONL."""

    output_path = Path(output_jsonl)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} already exists; pass overwrite=True to replace it")
    imported: list[PredictionReviewItem] = []
    batch_ids: set[str] = set()
    csv_hash = _sha256_file(Path(input_csv))
    imported_at = datetime.now(UTC).isoformat()
    with Path(input_csv).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            try:
                payload = _csv_row_to_prediction_review_item(row)
                payload["imported_csv_sha256"] = payload.get("imported_csv_sha256") or csv_hash
                if payload.get("review_status") in {"accepted", "corrected", "rejected"}:
                    payload["decision_timestamp_utc"] = payload.get("decision_timestamp_utc") or imported_at
                assigned = str(row.get("assigned_reviewer") or "")
                payload["reviewer"] = payload.get("reviewer") or assigned
                payload["reviewer_id"] = payload.get("reviewer_id") or payload.get("reviewer", "") or assigned
                imported.append(PredictionReviewItem.model_validate(payload))
                if row.get("batch_id"):
                    batch_ids.add(str(row["batch_id"]))
            except ValueError as exc:
                raise ValueError(f"Invalid active learning batch CSV row {line_number}: {exc}") from exc
    merged_by_id: dict[str, PredictionReviewItem] = {}
    if reviewed_queue_jsonl and Path(reviewed_queue_jsonl).exists():
        merged_by_id.update({item.item_id: item for item in load_prediction_review_queue_jsonl(reviewed_queue_jsonl)})
    merged_by_id.update({item.item_id: item for item in imported})
    save_prediction_review_queue_jsonl(list(merged_by_id.values()), output_path)
    return ActiveLearningBatchRoundtripReport(
        action="import",
        batch_id=", ".join(sorted(batch_ids)),
        input_path=str(input_csv),
        output_path=str(output_path),
        reviewed_queue_path=str(reviewed_queue_jsonl or ""),
        row_count=len(imported),
        input_sha256=csv_hash,
        output_sha256=_sha256_file(output_path),
        warnings=[] if imported else ["No active learning batch rows were imported"],
    )


def revert_evidence_overlay_graph(
    overlay_graph_jsonl: str | Path,
    output_jsonl: str | Path,
) -> OverlayRevertReport:
    """Reconstruct graph evidence tiers from overlay metadata without mutating the overlay artifact."""

    records = load_graph_records(overlay_graph_jsonl)
    output_records: list[KnowledgeGraphRecord] = []
    relation_count = 0
    reverted_count = 0
    for record in records:
        relations: list[GraphRelation] = []
        for relation in record.relations:
            relation_count += 1
            original_tier = relation.properties.get("evidence_overlay_original_tier")
            if original_tier is None:
                relations.append(relation)
                continue
            payload = relation.model_dump()
            properties = {
                key: value
                for key, value in dict(payload.get("properties") or {}).items()
                if not key.startswith("evidence_overlay_")
            }
            payload["properties"] = properties
            payload["evidence_tier"] = _coerce_evidence_tier(original_tier)
            relations.append(GraphRelation.model_validate(payload))
            reverted_count += 1
        output_records.append(record.model_copy(update={"relations": relations}))
    save_graph_records_jsonl(output_records, output_jsonl)
    warnings = []
    if reverted_count == 0:
        warnings.append("No evidence overlay metadata was found to revert")
    return OverlayRevertReport(
        overlay_graph_path=str(overlay_graph_jsonl),
        reverted_graph_path=str(output_jsonl),
        graph_record_count=len(records),
        relation_count=relation_count,
        reverted_relation_count=reverted_count,
        warnings=warnings,
    )


def run_curation_regression_pack(
    *,
    predictions_jsonl: str | Path = Path("reports/training/evidence_smoke_fixture/sample_graph_predictions.jsonl"),
    graph_jsonl: str | Path = Path("data/examples/graph_records_sample.jsonl"),
    reviewed_queue_jsonl: str | Path = Path("data/review/sample_graph_prediction_reviewed_queue.jsonl"),
    output_dir: str | Path = Path("data/processed/curation_regression_pack"),
    reports_dir: str | Path = Path("reports/review/curation_regression_pack"),
    registry_json: str | Path = Path("reports/review/curation_run_registry.json"),
) -> CurationRegressionPackReport:
    """Run a no-download curation regression pack across review, overlay, handoff, and validation."""

    output_path = Path(output_dir)
    reports_path = Path(reports_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)
    workflow = run_curation_smoke_workflow(
        predictions_jsonl=predictions_jsonl,
        graph_jsonl=graph_jsonl,
        reviewed_queue_jsonl=reviewed_queue_jsonl,
        output_dir=output_path,
        reports_dir=reports_path,
    )
    workflow_json = reports_path / "curation_regression_workflow.json"
    save_curation_smoke_report_json(workflow, workflow_json)
    save_curation_smoke_report_markdown(workflow, reports_path / "curation_regression_workflow.md")

    batch_report = plan_active_learning_batches(
        workflow.candidate_path,
        output_path / "active_learning_batches.jsonl",
        csv_output=output_path / "active_learning_batches.csv",
        batch_size=10,
    )
    save_active_learning_batch_report_json(batch_report, reports_path / "active_learning_batches.json")
    save_active_learning_batch_report_markdown(batch_report, reports_path / "active_learning_batches.md")

    guard = build_overlay_load_guard_report(workflow.overlay_graph_path)
    overlay_guard_json = reports_path / "overlay_load_guard.json"
    overlay_guard_md = reports_path / "overlay_load_guard.md"
    save_overlay_load_guard_json(guard, overlay_guard_json)
    save_overlay_load_guard_markdown(guard, overlay_guard_md)

    revert = revert_evidence_overlay_graph(workflow.overlay_graph_path, output_path / "reverted_graph_records.jsonl")
    save_overlay_revert_report_json(revert, reports_path / "overlay_revert.json")
    save_overlay_revert_report_markdown(revert, reports_path / "overlay_revert.md")

    artifact_paths = [
        workflow.candidate_path,
        workflow.review_queue_path,
        workflow.reviewed_queue_path,
        workflow.curated_evidence_path,
        workflow.overlay_graph_path,
        workflow.quality_report_path,
        workflow.review_summary_path,
        workflow.curated_audit_path,
        workflow.overlay_report_path,
        workflow.overlay_diff_path,
        workflow_json,
        overlay_guard_md,
        reports_path / "overlay_revert.md",
        reports_path / "active_learning_batches.md",
    ]
    handoff = build_curation_handoff_bundle(
        artifact_paths=artifact_paths,
        output_dir=output_path / "handoff_bundle",
    )
    handoff_json = output_path / "handoff_bundle" / "curation_handoff_bundle.json"
    handoff_md = output_path / "handoff_bundle" / "curation_handoff_bundle.md"
    save_curation_handoff_bundle_json(handoff, handoff_json)
    save_curation_handoff_bundle_markdown(handoff, handoff_md)
    validation = validate_curation_handoff_bundle(handoff_json, required_roles=set())
    validation_json = reports_path / "curation_handoff_validation.json"
    save_curation_handoff_validation_json(validation, validation_json)
    save_curation_handoff_validation_markdown(validation, reports_path / "curation_handoff_validation.md")
    registry = update_curation_run_registry(
        registry_json=registry_json,
        workflow_report_json=workflow_json,
        handoff_manifest_json=handoff_json,
    )
    save_curation_run_registry_report_markdown(registry, reports_path / "curation_run_registry.md")

    warnings = [
        *workflow.warnings,
        *batch_report.warnings,
        *guard.warnings,
        *revert.warnings,
        *handoff.warnings,
        *validation.warnings,
        *registry.warnings,
    ]
    return CurationRegressionPackReport(
        output_dir=str(output_path),
        reports_dir=str(reports_path),
        workflow_report_path=str(workflow_json),
        handoff_manifest_path=str(handoff_json),
        validation_report_path=str(validation_json),
        batch_report_path=str(reports_path / "active_learning_batches.md"),
        overlay_guard_path=str(overlay_guard_md),
        reverted_graph_path=str(output_path / "reverted_graph_records.jsonl"),
        registry_path=str(registry_json),
        warnings=warnings,
    )


def save_prediction_review_queue_jsonl(items: list[PredictionReviewItem], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(item.model_dump_json())
            handle.write("\n")
    return output_path


def save_prediction_review_queue_csv(items: list[PredictionReviewItem], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [item.model_dump() for item in items]
    fieldnames = list(PredictionReviewItem.model_fields)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row["reasons"] = "; ".join(row["reasons"])
            writer.writerow(row)
    return output_path


def load_prediction_review_queue_jsonl(path: str | Path) -> list[PredictionReviewItem]:
    input_path = Path(path)
    items: list[PredictionReviewItem] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                items.append(PredictionReviewItem.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return items


def save_prediction_quality_json(report: PredictionQualityReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_prediction_quality_markdown(report: PredictionQualityReport, path: str | Path) -> Path:
    return _save_report_markdown(format_prediction_quality_markdown(report), path)


def save_curated_evidence_report_json(report: CuratedEvidenceReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curated_evidence_report_markdown(report: CuratedEvidenceReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curated_evidence_report_markdown(report), path)


def save_prediction_review_summary_json(report: PredictionReviewSummary, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_prediction_review_summary_markdown(report: PredictionReviewSummary, path: str | Path) -> Path:
    return _save_report_markdown(format_prediction_review_summary_markdown(report), path)


def save_curated_evidence_audit_json(report: CuratedEvidenceAuditReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curated_evidence_audit_markdown(report: CuratedEvidenceAuditReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curated_evidence_audit_markdown(report), path)


def save_active_learning_report_json(report: ActiveLearningCandidateReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_active_learning_report_markdown(report: ActiveLearningCandidateReport, path: str | Path) -> Path:
    return _save_report_markdown(format_active_learning_report_markdown(report), path)


def save_overlay_report_json(report: EvidenceOverlayReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_overlay_report_markdown(report: EvidenceOverlayReport, path: str | Path) -> Path:
    return _save_report_markdown(format_overlay_report_markdown(report), path)


def save_overlay_diff_json(report: OverlayDiffReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_overlay_diff_markdown(report: OverlayDiffReport, path: str | Path) -> Path:
    return _save_report_markdown(format_overlay_diff_markdown(report), path)


def save_curation_smoke_report_json(report: CurationSmokeWorkflowReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curation_smoke_report_markdown(report: CurationSmokeWorkflowReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curation_smoke_report_markdown(report), path)


def save_curation_handoff_bundle_json(report: CurationHandoffBundleReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curation_handoff_bundle_markdown(report: CurationHandoffBundleReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curation_handoff_bundle_markdown(report), path)


def save_curation_handoff_validation_json(report: CurationHandoffValidationReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curation_handoff_validation_markdown(report: CurationHandoffValidationReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curation_handoff_validation_markdown(report), path)


def save_curation_run_registry_report_json(report: CurationRunRegistryReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curation_run_registry_report_markdown(report: CurationRunRegistryReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curation_run_registry_markdown(report), path)


def save_curation_run_browser_json(report: CurationRunBrowserReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curation_run_browser_markdown(report: CurationRunBrowserReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curation_run_browser_markdown(report), path)


def save_curated_evidence_search_json(report: CuratedEvidenceSearchReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curated_evidence_search_markdown(report: CuratedEvidenceSearchReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curated_evidence_search_markdown(report), path)


def save_active_learning_batch_report_json(report: ActiveLearningBatchPlanReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_active_learning_batch_report_markdown(report: ActiveLearningBatchPlanReport, path: str | Path) -> Path:
    return _save_report_markdown(format_active_learning_batch_report_markdown(report), path)


def save_active_learning_batch_status_json(report: ActiveLearningBatchStatusReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_active_learning_batch_status_markdown(report: ActiveLearningBatchStatusReport, path: str | Path) -> Path:
    return _save_report_markdown(format_active_learning_batch_status_markdown(report), path)


def save_active_learning_batch_roundtrip_json(report: ActiveLearningBatchRoundtripReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_active_learning_batch_roundtrip_markdown(report: ActiveLearningBatchRoundtripReport, path: str | Path) -> Path:
    return _save_report_markdown(format_active_learning_batch_roundtrip_markdown(report), path)


def save_overlay_revert_report_json(report: OverlayRevertReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_overlay_revert_report_markdown(report: OverlayRevertReport, path: str | Path) -> Path:
    return _save_report_markdown(format_overlay_revert_report_markdown(report), path)


def save_curation_regression_pack_json(report: CurationRegressionPackReport, path: str | Path) -> Path:
    return _save_report_json(report.to_dict(), path)


def save_curation_regression_pack_markdown(report: CurationRegressionPackReport, path: str | Path) -> Path:
    return _save_report_markdown(format_curation_regression_pack_markdown(report), path)


def format_prediction_quality_markdown(report: PredictionQualityReport) -> str:
    lines = [
        "# GBM-BERT Prediction Quality Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Predictions: `{report.predictions_path}`",
        f"- Prediction rows: {report.prediction_count}",
        f"- Low confidence rows: {report.low_confidence_count}",
        f"- Invalid prediction labels: {report.invalid_prediction_count}",
        f"- Missing PMIDs: {report.missing_pmid_count}",
        f"- Missing text: {report.missing_text_count}",
        f"- Missing warning rows: {report.missing_warning_count}",
        "",
        "## Prediction Labels",
        *_format_counts(report.label_counts),
        "",
        "## Evidence Tiers",
        *_format_counts(report.evidence_tier_counts, prefix="tier "),
        "",
        "## Confidence Buckets",
        *_format_counts(report.confidence_bucket_counts),
        "",
        "## Checkpoint Status",
        *_format_counts(report.checkpoint_status_counts),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_active_learning_report_markdown(report: ActiveLearningCandidateReport) -> str:
    lines = [
        "# GBM-BERT Active Learning Candidate Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Predictions: `{report.predictions_path}`",
        f"- Graph: `{report.graph_path or 'not provided'}`",
        f"- Candidates: `{report.candidate_path}`",
        f"- Prediction rows: {report.prediction_count}",
        f"- Candidate rows: {report.candidate_count}",
        "",
        "## Reasons",
        *_format_counts(report.reason_counts),
        "",
        "## Top PMIDs",
        *_format_counts(report.top_pmids),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curated_evidence_report_markdown(report: CuratedEvidenceReport) -> str:
    lines = [
        "# GBM-BERT Curated Evidence Export Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Predictions: `{report.predictions_path}`",
        f"- Reviewed queue: `{report.reviewed_queue_path}`",
        f"- Curated evidence: `{report.curated_evidence_path}`",
        f"- Prediction rows: {report.prediction_count}",
        f"- Curated rows: {report.curated_row_count}",
        f"- Accepted: {report.accepted_count}",
        f"- Corrected: {report.corrected_count}",
        f"- Rejected: {report.rejected_count}",
        f"- Pending: {report.pending_count}",
        f"- Missing decisions: {report.missing_decision_count}",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_prediction_review_summary_markdown(report: PredictionReviewSummary) -> str:
    lines = [
        "# GBM-BERT Prediction Review Summary",
        "",
        RESEARCH_WARNING,
        "",
        f"- Reviewed queue: `{report.reviewed_queue_path}`",
        f"- Items: {report.item_count}",
        f"- Pending: {report.pending_count}",
        f"- Warnings: {report.warning_count}",
        "",
        "## Review Status",
        *_format_counts(report.status_counts),
        "",
        "## Predicted Evidence Tiers",
        *_format_counts(report.predicted_tier_counts, prefix="tier "),
        "",
        "## Corrected Evidence Tiers",
        *_format_counts(report.corrected_tier_counts, prefix="tier "),
        "",
        "## Tier Shifts",
        *_format_counts(report.tier_shift_counts),
        "",
        "## Checkpoint Status",
        *_format_counts(report.checkpoint_status_counts),
        "",
        "## Top PMIDs",
        *_format_counts(report.top_pmids),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curated_evidence_audit_markdown(report: CuratedEvidenceAuditReport) -> str:
    lines = [
        "# GBM-BERT Curated Evidence Audit",
        "",
        RESEARCH_WARNING,
        "",
        f"- Curated evidence: `{report.curated_evidence_path}`",
        f"- Rows: {report.row_count}",
        f"- Accepted: {report.accepted_count}",
        f"- Corrected: {report.corrected_count}",
        f"- Pending: {report.pending_count}",
        f"- Missing PMIDs: {report.missing_pmid_count}",
        f"- Missing item IDs: {report.missing_item_id_count}",
        f"- Missing warnings: {report.missing_warning_count}",
        f"- Missing checkpoint metadata: {report.missing_checkpoint_count}",
        f"- Missing reviewers: {report.missing_reviewer_count}",
        f"- Invalid tiers: {report.invalid_tier_count}",
        f"- Linkage warnings: {report.linkage_warning_count}",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_overlay_report_markdown(report: EvidenceOverlayReport) -> str:
    change_lines = (
        [
            (
                f"- PMID {change.source_pmid} relation {change.relation_index}: "
                f"tier {change.original_evidence_tier} -> {change.overlaid_evidence_tier}"
            )
            for change in report.changes
        ]
        if report.changes
        else ["- none"]
    )
    lines = [
        "# GBM-AI Evidence Overlay Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Graph: `{report.graph_path}`",
        f"- Curated evidence: `{report.curated_evidence_path}`",
        f"- Overlay graph: `{report.overlay_graph_path}`",
        f"- Graph records: {report.graph_record_count}",
        f"- Relations: {report.relation_count}",
        f"- Changed relations: {report.changed_relation_count}",
        f"- Unchanged relations: {report.unchanged_relation_count}",
        f"- Pending evidence skipped: {report.skipped_pending_count}",
        f"- Unmatched curated evidence PMIDs: {report.unmatched_evidence_count}",
        "",
        "## Changes",
        *change_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_overlay_diff_markdown(report: OverlayDiffReport) -> str:
    change_lines = (
        [
            (
                f"- PMID {change.source_pmid} relation {change.relation_index}: "
                f"{change.action} ({change.detail})"
            )
            for change in report.changes
        ]
        if report.changes
        else ["- none"]
    )
    lines = [
        "# GBM-AI Evidence Overlay Diff Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Raw graph: `{report.raw_graph_path}`",
        f"- Overlay graph: `{report.overlay_graph_path}`",
        f"- Raw relations: {report.raw_relation_count}",
        f"- Overlay relations: {report.overlay_relation_count}",
        f"- Changed relations: {report.changed_relation_count}",
        f"- Tier increases: {report.increased_tier_count}",
        f"- Tier decreases: {report.decreased_tier_count}",
        f"- Unchanged relations: {report.unchanged_relation_count}",
        f"- Added relations: {report.added_relation_count}",
        f"- Removed relations: {report.removed_relation_count}",
        f"- Relations with overlay metadata: {report.overlay_metadata_count}",
        "",
        "## Changes",
        *change_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curation_smoke_report_markdown(report: CurationSmokeWorkflowReport) -> str:
    lines = [
        "# GBM-BERT Curation Smoke Workflow",
        "",
        RESEARCH_WARNING,
        "",
        f"- Predictions: `{report.predictions_path}`",
        f"- Graph: `{report.graph_path}`",
        f"- Output dir: `{report.output_dir}`",
        f"- Reports dir: `{report.reports_dir}`",
        f"- Active learning candidates: `{report.candidate_path}`",
        f"- Review queue: `{report.review_queue_path}`",
        f"- Reviewed queue: `{report.reviewed_queue_path}`",
        f"- Curated evidence: `{report.curated_evidence_path}`",
        f"- Overlay graph: `{report.overlay_graph_path}`",
        f"- Quality report: `{report.quality_report_path}`",
        f"- Review summary: `{report.review_summary_path}`",
        f"- Curated evidence audit: `{report.curated_audit_path}`",
        f"- Overlay report: `{report.overlay_report_path}`",
        f"- Overlay diff: `{report.overlay_diff_path}`",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curation_handoff_bundle_markdown(report: CurationHandoffBundleReport) -> str:
    artifact_lines = (
        [
            (
                f"- `{artifact.bundled_path}` ({artifact.artifact_role}, {artifact.byte_count} bytes, "
                f"lines={artifact.line_count}, SHA256 `{artifact.sha256}`; source `{artifact.source_path}`)"
            )
            for artifact in report.artifacts
        ]
        if report.artifacts
        else ["- none"]
    )
    lines = [
        "# GBM-BERT Curation Handoff Bundle",
        "",
        RESEARCH_WARNING,
        "",
        f"- Bundle dir: `{report.bundle_dir}`",
        f"- Created UTC: {report.created_at_utc}",
        f"- Artifacts: {report.artifact_count}",
        f"- Copied artifacts: {report.copied_artifact_count}",
        f"- Total bytes: {report.total_bytes}",
        "",
        "## Artifacts",
        *artifact_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curation_handoff_validation_markdown(report: CurationHandoffValidationReport) -> str:
    lines = [
        "# GBM-BERT Curation Handoff Validation",
        "",
        RESEARCH_WARNING,
        "",
        f"- Manifest: `{report.manifest_path}`",
        f"- Valid: {report.valid}",
        f"- Artifacts: {report.artifact_count}",
        f"- Checked artifacts: {report.checked_artifact_count}",
        f"- Missing artifacts: {report.missing_artifact_count}",
        f"- Checksum mismatches: {report.checksum_mismatch_count}",
        f"- Missing warning count: {report.missing_warning_count}",
        f"- Missing required roles: {report.required_role_missing_count}",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curation_run_registry_markdown(report: CurationRunRegistryReport) -> str:
    run_lines = (
        [
            (
                f"- `{entry.run_id}` {entry.created_at_utc}: predictions `{entry.predictions_path}`, "
                f"overlay `{entry.overlay_graph_path}`, warnings {entry.warning_count}"
            )
            for entry in report.entries
        ]
        if report.entries
        else ["- none"]
    )
    lines = [
        "# GBM-BERT Curation Run Registry",
        "",
        RESEARCH_WARNING,
        "",
        f"- Registry: `{report.registry_path}`",
        f"- Runs: {report.run_count}",
        f"- Latest run: `{report.latest_run_id or 'none'}`",
        "",
        "## Runs",
        *run_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curation_run_browser_markdown(report: CurationRunBrowserReport) -> str:
    run_lines = (
        [
            (
                f"- `{entry.run_id}` {entry.created_at_utc}: warnings {entry.warning_count}, "
                f"graph `{entry.graph_path}`, handoff `{entry.handoff_bundle_path}`"
            )
            for entry in report.runs
        ]
        if report.runs
        else ["- none"]
    )
    lines = [
        "# GBM-BERT Curation Run Browser",
        "",
        RESEARCH_WARNING,
        "",
        f"- Registry: `{report.registry_path}`",
        f"- Runs: {report.run_count}",
        f"- Matches: {report.match_count}",
        f"- Latest run: `{report.latest_run_id or 'none'}`",
        "",
        "## Filters",
        *[f"- {key}: `{value or 'not set'}`" for key, value in report.filters.items()],
        "",
        "## Runs",
        *run_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curated_evidence_search_markdown(report: CuratedEvidenceSearchReport) -> str:
    match_lines = (
        [
            (
                f"- `{row.get('item_id', '')}` PMID {row.get('source_pmid', '')}: "
                f"tier {row.get('curated_evidence_tier', '')}, {row.get('review_status', '')}, "
                f"{str(row.get('text', ''))[:160]}"
            )
            for row in report.matches
        ]
        if report.matches
        else ["- none"]
    )
    lines = [
        "# GBM-BERT Curated Evidence Search",
        "",
        RESEARCH_WARNING,
        "",
        f"- Curated evidence: `{report.curated_evidence_path}`",
        f"- Rows: {report.row_count}",
        f"- Matches: {report.match_count}",
        "",
        "## Matches",
        *match_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_active_learning_batch_report_markdown(report: ActiveLearningBatchPlanReport) -> str:
    lines = [
        "# GBM-BERT Active Learning Batch Plan",
        "",
        RESEARCH_WARNING,
        "",
        f"- Candidates: `{report.candidates_path}`",
        f"- Batch JSONL: `{report.batch_jsonl_path}`",
        f"- Candidates: {report.candidate_count}",
        f"- Batches: {report.batch_count}",
        f"- Batch size: {report.batch_size}",
        "",
        "## Reasons",
        *_format_counts(report.reason_counts),
        "",
        "## Evidence Tiers",
        *_format_counts(report.evidence_tier_counts, prefix="tier "),
        "",
        "## Checkpoints",
        *_format_counts(report.checkpoint_counts),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_active_learning_batch_status_markdown(report: ActiveLearningBatchStatusReport) -> str:
    batch_lines = (
        [
            (
                f"- `{batch.batch_id}` {batch.batch_status}: {batch.reviewed_count}/{batch.item_count} reviewed, "
                f"pending {batch.pending_count}, accepted {batch.accepted_count}, corrected {batch.corrected_count}, "
                f"rejected {batch.rejected_count}, reviewer `{batch.assigned_reviewer or 'unassigned'}`"
            )
            for batch in report.batches
        ]
        if report.batches
        else ["- none"]
    )
    lines = [
        "# GBM-BERT Active Learning Batch Status",
        "",
        RESEARCH_WARNING,
        "",
        f"- Batch JSONL: `{report.batch_jsonl_path}`",
        f"- Reviewed queue: `{report.reviewed_queue_path or 'not provided'}`",
        f"- Batches: {report.batch_count}",
        f"- Items: {report.item_count}",
        f"- Reviewed: {report.reviewed_count}",
        f"- Pending: {report.pending_count}",
        "",
        "## Batches",
        *batch_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_active_learning_batch_roundtrip_markdown(report: ActiveLearningBatchRoundtripReport) -> str:
    lines = [
        "# GBM-BERT Active Learning Batch Roundtrip",
        "",
        RESEARCH_WARNING,
        "",
        f"- Action: {report.action}",
        f"- Batch: `{report.batch_id or 'not recorded'}`",
        f"- Input: `{report.input_path}`",
        f"- Output: `{report.output_path}`",
        f"- Reviewed queue: `{report.reviewed_queue_path or 'not provided'}`",
        f"- Rows: {report.row_count}",
        f"- Input SHA256: `{report.input_sha256}`",
        f"- Output SHA256: `{report.output_sha256}`",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_overlay_revert_report_markdown(report: OverlayRevertReport) -> str:
    lines = [
        "# GBM-AI Evidence Overlay Revert Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Overlay graph: `{report.overlay_graph_path}`",
        f"- Reverted graph: `{report.reverted_graph_path}`",
        f"- Graph records: {report.graph_record_count}",
        f"- Relations: {report.relation_count}",
        f"- Reverted relations: {report.reverted_relation_count}",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_curation_regression_pack_markdown(report: CurationRegressionPackReport) -> str:
    lines = [
        "# GBM-BERT Curation Regression Pack",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output dir: `{report.output_dir}`",
        f"- Reports dir: `{report.reports_dir}`",
        f"- Workflow report: `{report.workflow_report_path}`",
        f"- Handoff manifest: `{report.handoff_manifest_path}`",
        f"- Handoff validation: `{report.validation_report_path}`",
        f"- Batch report: `{report.batch_report_path}`",
        f"- Overlay load guard: `{report.overlay_guard_path}`",
        f"- Reverted graph: `{report.reverted_graph_path}`",
        f"- Run registry: `{report.registry_path}`",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_review_queue_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export GBM-BERT evidence predictions for human review.")
    parser.add_argument("predictions_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--min-confidence", type=float, default=0.75)
    parser.add_argument("--queue-all", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_active_learning_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export high-value GBM-BERT prediction rows for active learning review.")
    parser.add_argument("predictions_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--graph-jsonl", type=Path)
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_initialize_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a reviewed GBM-BERT prediction queue scaffold.")
    parser.add_argument("input_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_summary_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a reviewed GBM-BERT prediction queue.")
    parser.add_argument("reviewed_queue_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_import_csv_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a reviewed GBM-BERT prediction CSV into JSONL.")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_quality_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a quality report for GBM-BERT evidence predictions.")
    parser.add_argument("predictions_jsonl", type=Path)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.75)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_audit_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit curated GBM-BERT evidence prediction rows.")
    parser.add_argument("curated_evidence_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_curated_export_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export curated GBM-BERT evidence predictions.")
    parser.add_argument("predictions_jsonl", type=Path)
    parser.add_argument("reviewed_queue_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--fail-on-pending", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_overlay_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply curated evidence tiers to a new graph JSONL artifact.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("curated_evidence_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--include-pending", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_overlay_diff_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare raw graph records against evidence-overlay graph records.")
    parser.add_argument("raw_graph_jsonl", type=Path)
    parser.add_argument("overlay_graph_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_smoke_workflow_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local GBM-BERT curation smoke workflow.")
    parser.add_argument("--predictions-jsonl", type=Path, default=Path("reports/training/evidence_smoke_fixture/sample_graph_predictions.jsonl"))
    parser.add_argument("--graph-jsonl", type=Path, default=Path("data/examples/graph_records_sample.jsonl"))
    parser.add_argument("--reviewed-queue-jsonl", type=Path, default=Path("data/review/sample_graph_prediction_reviewed_queue.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/curation_smoke_workflow"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/review/curation_smoke_workflow"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_handoff_bundle_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local GBM-BERT curation handoff bundle manifest.")
    parser.add_argument("--artifact", type=Path, action="append", default=[], help="Artifact path to include. Repeat for multiple files.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/curation_handoff_bundle"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--no-copy", action="store_true", help="Only write a manifest; do not copy artifacts into the bundle.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_handoff_validation_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a GBM-BERT curation handoff bundle manifest.")
    parser.add_argument("manifest_json", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_run_registry_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register a GBM-BERT curation workflow run.")
    parser.add_argument("workflow_report_json", type=Path)
    parser.add_argument("--handoff-manifest-json", type=Path)
    parser.add_argument("--registry-json", type=Path, default=Path("reports/review/curation_run_registry.json"))
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_run_browser_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browse registered GBM-BERT curation workflow runs.")
    parser.add_argument("--registry-json", type=Path, default=Path("reports/review/curation_run_registry.json"))
    parser.add_argument("--run-id", default="")
    parser.add_argument("--path-contains", default="")
    parser.add_argument("--warnings-only", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_curated_search_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search curated GBM-BERT evidence rows.")
    parser.add_argument("curated_evidence_jsonl", type=Path)
    parser.add_argument("--pmid", default="")
    parser.add_argument("--evidence-tier", type=int)
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--review-status", default="")
    parser.add_argument("--checkpoint", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_active_learning_batch_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan reviewer batches from active learning candidate JSONL.")
    parser.add_argument("candidates_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_active_learning_batch_status_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize active learning batch review status.")
    parser.add_argument("batch_jsonl", type=Path)
    parser.add_argument("--reviewed-queue-jsonl", type=Path)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_active_learning_batch_export_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export one active learning batch to curator-editable CSV.")
    parser.add_argument("batch_jsonl", type=Path)
    parser.add_argument("batch_id")
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--assigned-reviewer", default="")
    parser.add_argument("--batch-status", default="in_review")
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_active_learning_batch_import_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import an edited active learning batch CSV into a reviewed queue JSONL.")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--reviewed-queue-jsonl", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_overlay_revert_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Revert evidence overlay graph tiers using stored original-tier metadata.")
    parser.add_argument("overlay_graph_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_regression_pack_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local GBM-BERT curation regression pack.")
    parser.add_argument("--predictions-jsonl", type=Path, default=Path("reports/training/evidence_smoke_fixture/sample_graph_predictions.jsonl"))
    parser.add_argument("--graph-jsonl", type=Path, default=Path("data/examples/graph_records_sample.jsonl"))
    parser.add_argument("--reviewed-queue-jsonl", type=Path, default=Path("data/review/sample_graph_prediction_reviewed_queue.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/curation_regression_pack"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/review/curation_regression_pack"))
    parser.add_argument("--registry-json", type=Path, default=Path("reports/review/curation_run_registry.json"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def review_queue_main(argv: list[str] | None = None) -> int:
    args = build_review_queue_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    items = export_prediction_review_queue(
        args.predictions_jsonl,
        args.output_jsonl,
        csv_output=args.csv_output,
        min_confidence=args.min_confidence,
        queue_all=args.queue_all,
    )
    LOGGER.info("Queued %d prediction item(s)", len(items))
    return 0


def active_learning_main(argv: list[str] | None = None) -> int:
    args = build_active_learning_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = export_active_learning_candidates(
        predictions_jsonl=args.predictions_jsonl,
        output_jsonl=args.output_jsonl,
        csv_output=args.csv_output,
        graph_jsonl=args.graph_jsonl,
        min_confidence=args.min_confidence,
        limit=args.limit,
    )
    if args.report_json_output:
        save_active_learning_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_active_learning_report_markdown(report, args.report_markdown_output)
    LOGGER.info("Exported %d active learning candidate(s)", report.candidate_count)
    return 0


def initialize_main(argv: list[str] | None = None) -> int:
    parser = build_initialize_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        items = initialize_prediction_reviewed_queue(
            args.input_jsonl,
            args.output_jsonl,
            reviewer=args.reviewer,
            overwrite=args.overwrite,
            csv_output=args.csv_output,
        )
    except FileExistsError as exc:
        parser.error(str(exc))
    LOGGER.info("Initialized %d reviewed prediction item(s)", len(items))
    return 0


def summary_main(argv: list[str] | None = None) -> int:
    args = build_summary_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = summarize_prediction_review_queue(args.reviewed_queue_jsonl)
    if args.json_output:
        save_prediction_review_summary_json(report, args.json_output)
    if args.markdown_output:
        save_prediction_review_summary_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_prediction_review_summary_markdown(report))
    return 0


def import_csv_main(argv: list[str] | None = None) -> int:
    parser = build_import_csv_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        items = import_prediction_review_csv(args.input_csv, args.output_jsonl, overwrite=args.overwrite)
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    LOGGER.info("Imported %d reviewed prediction item(s)", len(items))
    return 0


def quality_main(argv: list[str] | None = None) -> int:
    args = build_quality_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = analyze_prediction_quality(
        args.predictions_jsonl,
        low_confidence_threshold=args.low_confidence_threshold,
    )
    if args.json_output:
        save_prediction_quality_json(report, args.json_output)
    if args.markdown_output:
        save_prediction_quality_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_prediction_quality_markdown(report))
    return 0


def audit_main(argv: list[str] | None = None) -> int:
    args = build_audit_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = audit_curated_evidence(args.curated_evidence_jsonl)
    if args.json_output:
        save_curated_evidence_audit_json(report, args.json_output)
    if args.markdown_output:
        save_curated_evidence_audit_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curated_evidence_audit_markdown(report))
    return 0


def curated_export_main(argv: list[str] | None = None) -> int:
    args = build_curated_export_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = export_curated_evidence(
        predictions_jsonl=args.predictions_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        output_jsonl=args.output_jsonl,
        fail_on_pending=args.fail_on_pending,
    )
    if args.report_json_output:
        save_curated_evidence_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_curated_evidence_report_markdown(report, args.report_markdown_output)
    LOGGER.info("Saved curated evidence to %s", args.output_jsonl)
    return 0


def overlay_main(argv: list[str] | None = None) -> int:
    args = build_overlay_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = apply_evidence_overlay_to_graph(
        graph_jsonl=args.graph_jsonl,
        curated_evidence_jsonl=args.curated_evidence_jsonl,
        output_jsonl=args.output_jsonl,
        include_pending=args.include_pending,
    )
    if args.report_json_output:
        save_overlay_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_overlay_report_markdown(report, args.report_markdown_output)
    LOGGER.info("Saved evidence overlay graph to %s", args.output_jsonl)
    return 0


def overlay_diff_main(argv: list[str] | None = None) -> int:
    args = build_overlay_diff_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = build_overlay_diff_report(raw_graph_jsonl=args.raw_graph_jsonl, overlay_graph_jsonl=args.overlay_graph_jsonl)
    if args.json_output:
        save_overlay_diff_json(report, args.json_output)
    if args.markdown_output:
        save_overlay_diff_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_overlay_diff_markdown(report))
    return 0


def smoke_workflow_main(argv: list[str] | None = None) -> int:
    args = build_smoke_workflow_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = run_curation_smoke_workflow(
        predictions_jsonl=args.predictions_jsonl,
        graph_jsonl=args.graph_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
    )
    json_output = args.json_output or Path(args.reports_dir) / "curation_smoke_workflow.json"
    markdown_output = args.markdown_output or Path(args.reports_dir) / "curation_smoke_workflow.md"
    save_curation_smoke_report_json(report, json_output)
    save_curation_smoke_report_markdown(report, markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_smoke_report_markdown(report))
    return 0


def handoff_bundle_main(argv: list[str] | None = None) -> int:
    args = build_handoff_bundle_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = build_curation_handoff_bundle(
        artifact_paths=args.artifact or None,
        output_dir=args.output_dir,
        copy_artifacts=not args.no_copy,
    )
    json_output = args.json_output or Path(args.output_dir) / "curation_handoff_bundle.json"
    markdown_output = args.markdown_output or Path(args.output_dir) / "curation_handoff_bundle.md"
    save_curation_handoff_bundle_json(report, json_output)
    save_curation_handoff_bundle_markdown(report, markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_handoff_bundle_markdown(report))
    return 0


def handoff_validation_main(argv: list[str] | None = None) -> int:
    args = build_handoff_validation_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = validate_curation_handoff_bundle(args.manifest_json)
    if args.json_output:
        save_curation_handoff_validation_json(report, args.json_output)
    if args.markdown_output:
        save_curation_handoff_validation_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_handoff_validation_markdown(report))
    return 0


def run_registry_main(argv: list[str] | None = None) -> int:
    args = build_run_registry_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = update_curation_run_registry(
        registry_json=args.registry_json,
        workflow_report_json=args.workflow_report_json,
        handoff_manifest_json=args.handoff_manifest_json,
    )
    if args.report_json_output:
        save_curation_run_registry_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_curation_run_registry_report_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_run_registry_markdown(report))
    return 0


def run_browser_main(argv: list[str] | None = None) -> int:
    args = build_run_browser_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = browse_curation_runs(
        registry_json=args.registry_json,
        run_id=args.run_id,
        path_contains=args.path_contains,
        warnings_only=args.warnings_only,
        limit=args.limit,
    )
    if args.report_json_output:
        save_curation_run_browser_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_curation_run_browser_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_run_browser_markdown(report))
    return 0


def curated_search_main(argv: list[str] | None = None) -> int:
    args = build_curated_search_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = search_curated_evidence(
        args.curated_evidence_jsonl,
        pmid=args.pmid,
        evidence_tier=args.evidence_tier,
        reviewer=args.reviewer,
        review_status=args.review_status,
        checkpoint=args.checkpoint,
        text=args.text,
        limit=args.limit,
    )
    if args.json_output:
        save_curated_evidence_search_json(report, args.json_output)
    if args.markdown_output:
        save_curated_evidence_search_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curated_evidence_search_markdown(report))
    return 0


def active_learning_batch_main(argv: list[str] | None = None) -> int:
    args = build_active_learning_batch_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = plan_active_learning_batches(
        args.candidates_jsonl,
        args.output_jsonl,
        csv_output=args.csv_output,
        batch_size=args.batch_size,
    )
    if args.report_json_output:
        save_active_learning_batch_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_active_learning_batch_report_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_active_learning_batch_report_markdown(report))
    return 0


def active_learning_batch_status_main(argv: list[str] | None = None) -> int:
    args = build_active_learning_batch_status_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = summarize_active_learning_batch_status(
        args.batch_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
    )
    if args.report_json_output:
        save_active_learning_batch_status_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_active_learning_batch_status_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_active_learning_batch_status_markdown(report))
    return 0


def active_learning_batch_export_main(argv: list[str] | None = None) -> int:
    args = build_active_learning_batch_export_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = export_active_learning_batch_csv(
        args.batch_jsonl,
        args.batch_id,
        args.output_csv,
        assigned_reviewer=args.assigned_reviewer,
        batch_status=args.batch_status,
    )
    if args.report_json_output:
        save_active_learning_batch_roundtrip_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_active_learning_batch_roundtrip_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_active_learning_batch_roundtrip_markdown(report))
    return 0


def active_learning_batch_import_main(argv: list[str] | None = None) -> int:
    parser = build_active_learning_batch_import_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        report = import_active_learning_batch_csv(
            args.input_csv,
            args.output_jsonl,
            reviewed_queue_jsonl=args.reviewed_queue_jsonl,
            overwrite=args.overwrite,
        )
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    if args.report_json_output:
        save_active_learning_batch_roundtrip_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_active_learning_batch_roundtrip_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_active_learning_batch_roundtrip_markdown(report))
    return 0


def overlay_revert_main(argv: list[str] | None = None) -> int:
    args = build_overlay_revert_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = revert_evidence_overlay_graph(args.overlay_graph_jsonl, args.output_jsonl)
    if args.report_json_output:
        save_overlay_revert_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_overlay_revert_report_markdown(report, args.report_markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_overlay_revert_report_markdown(report))
    return 0


def regression_pack_main(argv: list[str] | None = None) -> int:
    args = build_regression_pack_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = run_curation_regression_pack(
        predictions_jsonl=args.predictions_jsonl,
        graph_jsonl=args.graph_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        registry_json=args.registry_json,
    )
    json_output = args.json_output or Path(args.reports_dir) / "curation_regression_pack.json"
    markdown_output = args.markdown_output or Path(args.reports_dir) / "curation_regression_pack.md"
    save_curation_regression_pack_json(report, json_output)
    save_curation_regression_pack_markdown(report, markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_regression_pack_markdown(report))
    return 0


def _active_learning_reasons(
    row: dict[str, Any],
    *,
    min_confidence: float,
    graph_pmids: set[str],
) -> list[str]:
    reasons = _prediction_review_reasons(row, min_confidence=min_confidence)
    pmid = str(row.get("source_pmid") or row.get("pmid") or "")
    if pmid in graph_pmids:
        reasons.append("pmid already present in graph")
    tier = _parse_evidence_tier_or_none(row.get("prediction"))
    if tier is not None and tier >= int(EvidenceTier.RETROSPECTIVE_HUMAN):
        reasons.append("tier-change-sensitive evidence")
    if not str(row.get("source_pmid") or "").strip():
        reasons.append("missing source PMID")
    if not str(row.get("text") or "").strip():
        reasons.append("missing evidence text")
    return list(dict.fromkeys(reasons))


def _candidate_priority(item: PredictionReviewItem) -> int:
    weights = {
        "invalid evidence prediction label": 50,
        "missing research-use warning": 40,
        "missing source PMID": 35,
        "missing evidence text": 30,
        "tier-change-sensitive evidence": 25,
        "pmid already present in graph": 20,
    }
    score = 0
    for reason in item.reasons:
        score += weights.get(reason, 0)
        if reason.startswith("confidence <"):
            score += 15
        if reason.startswith("checkpoint status:"):
            score += 10
    return score


def _graph_pmids(graph_jsonl: str | Path | None) -> set[str]:
    if graph_jsonl is None:
        return set()
    return {record.pmid for record in load_graph_records(graph_jsonl)}


def _batch_sort_key(batch_id: str, rows: list[dict[str, Any]]) -> tuple[int, str]:
    first_index = int(rows[0].get("batch_index") or 0) if rows else 0
    return (first_index, batch_id)


def _indexed_relations(records: list[KnowledgeGraphRecord]) -> dict[tuple[str, int], GraphRelation]:
    indexed: dict[tuple[str, int], GraphRelation] = {}
    for record in records:
        for index, relation in enumerate(record.relations, start=1):
            indexed[(record.pmid, index)] = relation
    return indexed


def _prediction_review_reasons(row: dict[str, Any], *, min_confidence: float) -> list[str]:
    reasons: list[str] = []
    confidence = float(row.get("confidence") or 0.0)
    if confidence < min_confidence:
        reasons.append(f"confidence < {min_confidence}")
    status = str(row.get("checkpoint_status") or "")
    if status and status not in {"research_candidate", "candidate"}:
        reasons.append(f"checkpoint status: {status}")
    if _parse_evidence_tier_or_none(row.get("prediction")) is None:
        reasons.append("invalid evidence prediction label")
    if str(row.get("warning") or "") != RESEARCH_WARNING:
        reasons.append("missing research-use warning")
    return reasons


def _decision_from_prediction_row(
    row: dict[str, Any],
    index: int,
    *,
    status: ReviewStatus,
    source_file: str,
) -> PredictionReviewItem:
    label = str(row.get("prediction") or "")
    return PredictionReviewItem(
        item_id=_prediction_item_id(row, index),
        source_pmid=str(row.get("source_pmid") or row.get("pmid") or ""),
        text=str(row.get("text") or ""),
        predicted_evidence_tier=_parse_evidence_tier_or_none(label),
        prediction_label=label,
        confidence=float(row.get("confidence") or 0.0),
        checkpoint_name=str(row.get("checkpoint_name") or ""),
        checkpoint_status=str(row.get("checkpoint_status") or ""),
        checkpoint_dir=str(row.get("checkpoint_dir") or ""),
        source_file=source_file,
        review_status=status,
    )


def _curated_evidence_row(row: dict[str, Any], decision: PredictionReviewItem) -> dict[str, Any]:
    if decision.review_status == "corrected":
        curated_tier = _coerce_evidence_tier(decision.corrected_evidence_tier)
    else:
        curated_tier = _coerce_evidence_tier(decision.predicted_evidence_tier)
    return {
        "item_id": decision.item_id,
        "source_pmid": decision.source_pmid,
        "text": decision.text,
        "curated_evidence_tier": int(curated_tier),
        "original_prediction": str(row.get("prediction") or decision.prediction_label),
        "original_predicted_evidence_tier": decision.predicted_evidence_tier,
        "confidence": decision.confidence,
        "checkpoint_name": decision.checkpoint_name,
        "checkpoint_status": decision.checkpoint_status,
        "checkpoint_dir": decision.checkpoint_dir,
        "review_status": decision.review_status,
        "reviewer": decision.reviewer,
        "reviewer_id": decision.reviewer_id,
        "decision_timestamp_utc": decision.decision_timestamp_utc,
        "source_queue_sha256": decision.source_queue_sha256,
        "imported_csv_sha256": decision.imported_csv_sha256,
        "review_notes": decision.review_notes,
        "warning": RESEARCH_WARNING,
    }


def _overlay_relation(
    relation: GraphRelation,
    evidence: dict[str, Any],
    overlaid_tier: EvidenceTier,
) -> GraphRelation:
    payload = relation.model_dump()
    properties = dict(payload.get("properties") or {})
    properties.update(
        {
            "evidence_overlay_source": "curated_gbmbert_prediction",
            "evidence_overlay_original_tier": int(relation.evidence_tier),
            "evidence_overlay_tier": int(overlaid_tier),
            "evidence_overlay_item_id": evidence.get("item_id", ""),
            "evidence_overlay_checkpoint": evidence.get("checkpoint_name", ""),
            "evidence_overlay_review_status": evidence.get("review_status", ""),
        }
    )
    payload["properties"] = properties
    payload["evidence_tier"] = overlaid_tier
    return GraphRelation.model_validate(payload)


def _prediction_item_id(row: dict[str, Any], index: int) -> str:
    pmid = str(row.get("source_pmid") or row.get("pmid") or "unknown")
    return f"prediction:{pmid}:{index}"


def _csv_row_to_prediction_review_item(row: dict[str, str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in PredictionReviewItem.model_fields:
        if field not in row:
            continue
        value = row.get(field)
        if field == "reasons":
            payload[field] = _split_reasons(value or "")
        elif field in {"predicted_evidence_tier", "corrected_evidence_tier"}:
            payload[field] = _optional_int(value)
        elif field == "confidence":
            payload[field] = float(value or 0.0)
        elif field == "warning":
            payload[field] = value or RESEARCH_WARNING
        else:
            payload[field] = value or ""
    payload.setdefault("item_type", "evidence_prediction")
    payload.setdefault("warning", RESEARCH_WARNING)
    payload.setdefault("reasons", [])
    return payload


def _split_reasons(value: str) -> list[str]:
    text = value.strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in text.split(";") if item.strip()]


def _optional_int(value: str | None) -> int | None:
    if value is None or not str(value).strip():
        return None
    return int(str(value).strip())


def _tier_shift_label(predicted: int, corrected: int) -> str:
    return f"{predicted} -> {corrected}"


def _parse_evidence_tier_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, EvidenceTier):
        return int(value)
    if isinstance(value, int):
        try:
            return int(EvidenceTier(value))
        except ValueError:
            return None
    text = str(value).strip()
    if text.isdigit():
        return _parse_evidence_tier_or_none(int(text))
    match = re.fullmatch(r"LABEL_(\d+)", text, flags=re.IGNORECASE)
    if match:
        return _parse_evidence_tier_or_none(int(match.group(1)))
    return None


def _coerce_evidence_tier(value: Any) -> EvidenceTier:
    tier = _parse_evidence_tier_or_none(value)
    if tier is None:
        raise ValueError(f"Unknown evidence tier: {value}")
    return EvidenceTier(tier)


def _confidence_bucket(confidence: float) -> str:
    if confidence < 0.5:
        return "<0.50"
    if confidence < 0.75:
        return "0.50-0.74"
    if confidence < 0.9:
        return "0.75-0.89"
    return "0.90-1.00"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _default_curation_handoff_artifacts() -> list[Path]:
    return [
        Path("data/processed/curation_smoke_workflow/active_learning_candidates.jsonl"),
        Path("data/processed/curation_smoke_workflow/prediction_review_queue.jsonl"),
        Path("data/processed/curation_smoke_workflow/prediction_reviewed_queue.jsonl"),
        Path("data/processed/curation_smoke_workflow/curated_evidence_predictions.jsonl"),
        Path("data/processed/curation_smoke_workflow/evidence_overlay_graph_records.jsonl"),
        Path("reports/review/curation_smoke_workflow/prediction_quality.md"),
        Path("reports/review/curation_smoke_workflow/prediction_review_summary.md"),
        Path("reports/review/curation_smoke_workflow/curated_evidence_audit.md"),
        Path("reports/review/curation_smoke_workflow/evidence_overlay.md"),
        Path("reports/review/curation_smoke_workflow/evidence_overlay_diff.md"),
        Path("reports/review/curation_smoke_workflow/curation_smoke_workflow.md"),
    ]


def _required_handoff_roles() -> set[str]:
    return {
        "active_learning_candidates",
        "prediction_review_queue",
        "reviewed_prediction_queue",
        "curated_evidence_predictions",
        "evidence_overlay_graph",
        "prediction_quality_report",
        "prediction_review_summary",
        "curated_evidence_audit",
        "evidence_overlay_report",
        "evidence_overlay_diff",
        "curation_smoke_workflow_report",
    }


def _curation_run_id(workflow: dict[str, Any], created_at: str, artifact_hashes: dict[str, str]) -> str:
    payload = json.dumps(
        {
            "predictions_path": workflow.get("predictions_path", ""),
            "graph_path": workflow.get("graph_path", ""),
            "artifact_hashes": artifact_hashes,
        },
        sort_keys=True,
    )
    return f"curation-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12].upper()}"


def _load_curation_registry_entries(path: Path) -> list[CurationRunRegistryEntry]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    return [CurationRunRegistryEntry(**item) for item in entries]


def _bundle_artifact_name(source_path: Path, seen_targets: Counter[str]) -> str:
    parent = source_path.parent.name
    stem = source_path.stem
    suffix = source_path.suffix
    base = f"{parent}_{stem}{suffix}" if parent else source_path.name
    seen_targets[base] += 1
    if seen_targets[base] == 1:
        return base
    return f"{Path(base).stem}_{seen_targets[base]}{Path(base).suffix}"


def _curation_artifact_role(path: Path) -> str:
    name = path.name.casefold()
    if "active_learning" in name:
        return "active_learning_candidates"
    if "prediction_reviewed_queue" in name:
        return "reviewed_prediction_queue"
    if "prediction_review_queue" in name:
        return "prediction_review_queue"
    if "curated_evidence" in name and name.endswith(".jsonl"):
        return "curated_evidence_predictions"
    if "evidence_overlay_graph" in name:
        return "evidence_overlay_graph"
    if "prediction_quality" in name:
        return "prediction_quality_report"
    if "prediction_review_summary" in name:
        return "prediction_review_summary"
    if "curated_evidence_audit" in name:
        return "curated_evidence_audit"
    if "evidence_overlay_diff" in name:
        return "evidence_overlay_diff"
    if "evidence_overlay" in name:
        return "evidence_overlay_report"
    if "curation_smoke_workflow" in name:
        return "curation_smoke_workflow_report"
    return "curation_artifact"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _line_count(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _line in handle)
    except UnicodeDecodeError:
        return None


def _save_report_json(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def _save_report_markdown(markdown: str, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _count_items(counter: Counter[str]) -> list[CountItem]:
    return [CountItem(key=key, count=count) for key, count in counter.most_common()]


def _format_counts(items: list[CountItem], prefix: str = "") -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {prefix}{item.key}: {item.count}" for item in items]


if __name__ == "__main__":
    raise SystemExit(review_queue_main())
