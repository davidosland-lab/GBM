"""Curated graph export and curation diff reports."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.extraction.review_queue import ReviewQueueItem, load_review_queue_jsonl
from gbmbert.knowledge_graph.build_records import save_graph_records_jsonl
from gbmbert.knowledge_graph.schema import EvidenceTier, GraphRelation, KnowledgeGraphRecord, RelationType

LOGGER = logging.getLogger(__name__)
RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)


@dataclass(frozen=True)
class CurationChange:
    item_id: str
    source_pmid: str
    action: str
    detail: str


@dataclass(frozen=True)
class CurationExportReport:
    raw_graph_path: str
    reviewed_queue_path: str
    curated_graph_path: str
    raw_record_count: int
    curated_record_count: int
    raw_relation_count: int
    curated_relation_count: int
    accepted_count: int
    corrected_count: int
    rejected_count: int
    pending_count: int
    unchanged_reviewed_count: int
    changes: list[CurationChange]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_curated_graph_records(
    *,
    graph_jsonl: str | Path,
    reviewed_queue_jsonl: str | Path,
    output_jsonl: str | Path,
    fail_on_pending: bool = False,
) -> CurationExportReport:
    """Apply reviewed graph-relation curation decisions to a new graph JSONL artifact."""

    records = load_graph_records(graph_jsonl)
    review_items = load_review_queue_jsonl(reviewed_queue_jsonl)
    decisions = {
        item.item_id: item
        for item in review_items
        if item.item_type == "graph_relation"
    }
    status_counts = Counter(item.review_status for item in decisions.values())
    warnings: list[str] = []
    if status_counts.get("pending", 0):
        warning = f"{status_counts['pending']} graph relation item(s) still pending review"
        warnings.append(warning)
        if fail_on_pending:
            raise ValueError(warning)

    curated_records: list[KnowledgeGraphRecord] = []
    changes: list[CurationChange] = []
    unchanged_reviewed_count = 0
    for record in records:
        curated_relations: list[GraphRelation] = []
        for relation_index, relation in enumerate(record.relations, start=1):
            item_id = f"relation:{record.pmid}:{relation_index}"
            decision = decisions.get(item_id)
            if decision is None or decision.review_status == "pending":
                curated_relations.append(relation)
                continue
            if decision.review_status == "rejected":
                changes.append(
                    CurationChange(
                        item_id=item_id,
                        source_pmid=record.pmid,
                        action="rejected",
                        detail=decision.review_notes,
                    )
                )
                continue
            if decision.review_status == "accepted":
                curated_relations.append(_tag_curated_relation(relation, decision))
                unchanged_reviewed_count += 1
                continue
            corrected = _correct_relation(relation, decision)
            curated_relations.append(corrected)
            changes.append(
                CurationChange(
                    item_id=item_id,
                    source_pmid=record.pmid,
                    action="corrected",
                    detail=_correction_detail(relation, corrected),
                )
            )

        curated_records.append(record.model_copy(update={"relations": curated_relations}))

    save_graph_records_jsonl(curated_records, output_jsonl)
    return CurationExportReport(
        raw_graph_path=str(graph_jsonl),
        reviewed_queue_path=str(reviewed_queue_jsonl),
        curated_graph_path=str(output_jsonl),
        raw_record_count=len(records),
        curated_record_count=len(curated_records),
        raw_relation_count=sum(len(record.relations) for record in records),
        curated_relation_count=sum(len(record.relations) for record in curated_records),
        accepted_count=status_counts.get("accepted", 0),
        corrected_count=status_counts.get("corrected", 0),
        rejected_count=status_counts.get("rejected", 0),
        pending_count=status_counts.get("pending", 0),
        unchanged_reviewed_count=unchanged_reviewed_count,
        changes=changes,
        warnings=warnings,
    )


def build_curation_diff_report(
    *,
    graph_jsonl: str | Path,
    curated_graph_jsonl: str | Path,
    reviewed_queue_jsonl: str | Path,
) -> CurationExportReport:
    """Build a diff-style report from raw graph, curated graph, and reviewed queue artifacts."""

    raw_records = load_graph_records(graph_jsonl)
    curated_records = load_graph_records(curated_graph_jsonl)
    items = [item for item in load_review_queue_jsonl(reviewed_queue_jsonl) if item.item_type == "graph_relation"]
    status_counts = Counter(item.review_status for item in items)
    changes = [_decision_to_change(item) for item in items if item.review_status in {"corrected", "rejected"}]
    warnings = []
    if status_counts.get("pending", 0):
        warnings.append(f"{status_counts['pending']} graph relation item(s) still pending review")
    return CurationExportReport(
        raw_graph_path=str(graph_jsonl),
        reviewed_queue_path=str(reviewed_queue_jsonl),
        curated_graph_path=str(curated_graph_jsonl),
        raw_record_count=len(raw_records),
        curated_record_count=len(curated_records),
        raw_relation_count=sum(len(record.relations) for record in raw_records),
        curated_relation_count=sum(len(record.relations) for record in curated_records),
        accepted_count=status_counts.get("accepted", 0),
        corrected_count=status_counts.get("corrected", 0),
        rejected_count=status_counts.get("rejected", 0),
        pending_count=status_counts.get("pending", 0),
        unchanged_reviewed_count=status_counts.get("accepted", 0),
        changes=changes,
        warnings=warnings,
    )


def save_curation_report_json(report: CurationExportReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_curation_report_markdown(report: CurationExportReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_curation_report_markdown(report), encoding="utf-8")
    return output_path


def format_curation_report_markdown(report: CurationExportReport) -> str:
    warning_lines = [f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]
    change_lines = (
        [f"- `{change.item_id}` {change.action}: {change.detail}" for change in report.changes]
        if report.changes
        else ["- none"]
    )
    lines = [
        "# GBM-AI Curation Diff Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Raw graph: `{report.raw_graph_path}`",
        f"- Reviewed queue: `{report.reviewed_queue_path}`",
        f"- Curated graph: `{report.curated_graph_path}`",
        f"- Raw relations: {report.raw_relation_count}",
        f"- Curated relations: {report.curated_relation_count}",
        f"- Accepted: {report.accepted_count}",
        f"- Corrected: {report.corrected_count}",
        f"- Rejected: {report.rejected_count}",
        f"- Pending: {report.pending_count}",
        "",
        "## Changes",
        *change_lines,
        "",
        "## Warnings",
        *warning_lines,
    ]
    return "\n".join(lines).rstrip() + "\n"


def load_graph_records(path: str | Path) -> list[KnowledgeGraphRecord]:
    input_path = Path(path)
    records: list[KnowledgeGraphRecord] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(KnowledgeGraphRecord.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return records


def build_export_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export curated graph records from reviewed queue decisions.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("reviewed_queue_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--fail-on-pending", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_diff_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report differences between raw and curated graph records.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("curated_graph_jsonl", type=Path)
    parser.add_argument("reviewed_queue_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def export_main(argv: list[str] | None = None) -> int:
    parser = build_export_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = export_curated_graph_records(
        graph_jsonl=args.graph_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        output_jsonl=args.output_jsonl,
        fail_on_pending=args.fail_on_pending,
    )
    if args.report_json_output:
        save_curation_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_curation_report_markdown(report, args.report_markdown_output)
    LOGGER.info("Saved curated graph records to %s", args.output_jsonl)
    return 0


def diff_main(argv: list[str] | None = None) -> int:
    parser = build_diff_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = build_curation_diff_report(
        graph_jsonl=args.graph_jsonl,
        curated_graph_jsonl=args.curated_graph_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
    )
    if args.json_output:
        save_curation_report_json(report, args.json_output)
    if args.markdown_output:
        save_curation_report_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curation_report_markdown(report))
    return 0


def _correct_relation(relation: GraphRelation, decision: ReviewQueueItem) -> GraphRelation:
    payload = relation.model_dump()
    if decision.corrected_relation_type:
        payload["relation"] = RelationType(decision.corrected_relation_type)
    if decision.corrected_evidence_tier is not None:
        payload["evidence_tier"] = EvidenceTier(decision.corrected_evidence_tier)
    properties = dict(payload.get("properties") or {})
    properties.update(_curation_properties(decision))
    payload["properties"] = properties
    return GraphRelation.model_validate(payload)


def _tag_curated_relation(relation: GraphRelation, decision: ReviewQueueItem) -> GraphRelation:
    payload = relation.model_dump()
    properties = dict(payload.get("properties") or {})
    properties.update(_curation_properties(decision))
    payload["properties"] = properties
    return GraphRelation.model_validate(payload)


def _curation_properties(decision: ReviewQueueItem) -> dict[str, object]:
    return {
        "curation_status": decision.review_status,
        "curator": decision.reviewer,
        "curation_notes": decision.review_notes,
    }


def _correction_detail(original: GraphRelation, corrected: GraphRelation) -> str:
    changes = []
    if original.relation != corrected.relation:
        changes.append(f"relation {original.relation.value} -> {corrected.relation.value}")
    if original.evidence_tier != corrected.evidence_tier:
        changes.append(f"evidence tier {int(original.evidence_tier)} -> {int(corrected.evidence_tier)}")
    return "; ".join(changes) or "curation metadata added"


def _decision_to_change(item: ReviewQueueItem) -> CurationChange:
    detail = item.review_notes
    if item.review_status == "corrected":
        bits = []
        if item.corrected_relation_type:
            bits.append(f"relation -> {item.corrected_relation_type}")
        if item.corrected_evidence_tier is not None:
            bits.append(f"evidence tier -> {item.corrected_evidence_tier}")
        if bits:
            detail = "; ".join(bits)
    return CurationChange(
        item_id=item.item_id,
        source_pmid=item.source_pmid,
        action=item.review_status,
        detail=detail,
    )


if __name__ == "__main__":
    raise SystemExit(export_main())
