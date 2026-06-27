"""Provenance audit reports for graph-record JSONL artifacts."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from gbmbert.knowledge_graph.schema import KnowledgeGraphRecord
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord

LOGGER = logging.getLogger(__name__)
RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)
RecordType = Literal["auto", "pubmed", "trial"]


@dataclass(frozen=True)
class ProvenanceIssue:
    record_id: str
    record_type: str
    issue_type: str
    detail: str
    relation_index: int | None = None


@dataclass(frozen=True)
class ProvenanceAuditReport:
    source_path: str
    record_type: str
    records_seen: int
    relations_seen: int
    issue_count: int
    issue_type_counts: dict[str, int]
    issues: list[ProvenanceIssue]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_graph_provenance(path: str | Path, *, record_type: RecordType = "auto") -> ProvenanceAuditReport:
    """Audit graph records for source traceability fields."""

    input_path = Path(path)
    issues: list[ProvenanceIssue] = []
    records_seen = 0
    relations_seen = 0
    effective_type = "pubmed"
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(
                    ProvenanceIssue(
                        record_id=f"line:{line_number}",
                        record_type="unknown",
                        issue_type="invalid_json",
                        detail=str(exc),
                    )
                )
                continue
            effective_type = _detect_record_type(payload, record_type)
            records_seen += 1
            if effective_type == "trial":
                relation_count, record_issues = _audit_trial_record(payload, line_number)
            else:
                relation_count, record_issues = _audit_pubmed_record(payload, line_number)
            relations_seen += relation_count
            issues.extend(record_issues)

    issue_counts = Counter(issue.issue_type for issue in issues)
    return ProvenanceAuditReport(
        source_path=str(input_path),
        record_type=record_type if record_type != "auto" else effective_type,
        records_seen=records_seen,
        relations_seen=relations_seen,
        issue_count=len(issues),
        issue_type_counts=dict(issue_counts),
        issues=issues,
    )


def save_provenance_audit_json(report: ProvenanceAuditReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    LOGGER.info("Saved graph provenance audit JSON to %s", output_path)
    return output_path


def save_provenance_audit_markdown(report: ProvenanceAuditReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_provenance_audit_markdown(report), encoding="utf-8")
    LOGGER.info("Saved graph provenance audit Markdown to %s", output_path)
    return output_path


def format_provenance_audit_markdown(report: ProvenanceAuditReport) -> str:
    lines = [
        "# GBM-AI Graph Provenance Audit",
        "",
        RESEARCH_WARNING,
        "",
        f"- Source: `{report.source_path}`",
        f"- Record type: {report.record_type}",
        f"- Records seen: {report.records_seen}",
        f"- Relations seen: {report.relations_seen}",
        f"- Issues: {report.issue_count}",
        "",
        "## Issue Types",
    ]
    lines.extend(_format_counts(report.issue_type_counts))
    lines.extend(["", "## Issues"])
    if report.issues:
        lines.extend(
            (
                f"- `{issue.record_id}` {issue.issue_type}: {issue.detail}"
                + (f" (relation {issue.relation_index})" if issue.relation_index is not None else "")
            )
            for issue in report.issues
        )
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit GBM-AI graph records for source provenance.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("--record-type", choices=["auto", "pubmed", "trial"], default="auto")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = audit_graph_provenance(args.graph_jsonl, record_type=args.record_type)
    if args.json_output:
        save_provenance_audit_json(report, args.json_output)
    if args.markdown_output:
        save_provenance_audit_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_provenance_audit_markdown(report))
    return 0


def _audit_pubmed_record(payload: dict[str, Any], line_number: int) -> tuple[int, list[ProvenanceIssue]]:
    try:
        record = KnowledgeGraphRecord.model_validate(payload)
    except ValueError as exc:
        return 0, [
            ProvenanceIssue(
                record_id=f"line:{line_number}",
                record_type="pubmed",
                issue_type="invalid_pubmed_record",
                detail=str(exc),
            )
        ]
    issues: list[ProvenanceIssue] = []
    for index, relation in enumerate(record.relations, start=1):
        if relation.source_pmid != record.pmid:
            issues.append(_issue(record.pmid, "pubmed", "source_pmid_mismatch", "Relation PMID does not match record PMID", index))
        if not str(relation.properties.get("sentence", "")).strip():
            issues.append(_issue(record.pmid, "pubmed", "missing_source_sentence", "Literature relation lacks source sentence", index))
        if not str(relation.properties.get("evidence_classification_method", "")).strip():
            issues.append(_issue(record.pmid, "pubmed", "missing_evidence_method", "Literature relation lacks evidence classifier provenance", index))
        if relation.evidence_tier is None:
            issues.append(_issue(record.pmid, "pubmed", "missing_evidence_tier", "Literature relation lacks evidence tier", index))
    return len(record.relations), issues


def _audit_trial_record(payload: dict[str, Any], line_number: int) -> tuple[int, list[ProvenanceIssue]]:
    try:
        record = ClinicalTrialGraphRecord.model_validate(payload)
    except ValueError as exc:
        return 0, [
            ProvenanceIssue(
                record_id=f"line:{line_number}",
                record_type="trial",
                issue_type="invalid_trial_record",
                detail=str(exc),
            )
        ]
    issues: list[ProvenanceIssue] = []
    for index, relation in enumerate(record.relations, start=1):
        if relation.source_id != record.nct_id:
            issues.append(_issue(record.nct_id, "trial", "source_id_mismatch", "Relation NCT ID does not match record NCT ID", index))
        if not str(relation.properties.get("source_url") or record.trial_properties.get("source_url", "")).strip():
            issues.append(_issue(record.nct_id, "trial", "missing_source_url", "Trial relation lacks ClinicalTrials.gov source URL", index))
        if not str(relation.properties.get("registry_field", "")).strip():
            issues.append(_issue(record.nct_id, "trial", "missing_registry_field", "Trial relation lacks registry field provenance", index))
    return len(record.relations), issues


def _detect_record_type(payload: dict[str, Any], requested: RecordType) -> Literal["pubmed", "trial"]:
    if requested in {"pubmed", "trial"}:
        return requested
    return "trial" if "nct_id" in payload else "pubmed"


def _issue(
    record_id: str,
    record_type: str,
    issue_type: str,
    detail: str,
    relation_index: int,
) -> ProvenanceIssue:
    return ProvenanceIssue(
        record_id=record_id,
        record_type=record_type,
        issue_type=issue_type,
        detail=detail,
        relation_index=relation_index,
    )


def _format_counts(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {key}: {count}" for key, count in sorted(counts.items())]


if __name__ == "__main__":
    raise SystemExit(main())
