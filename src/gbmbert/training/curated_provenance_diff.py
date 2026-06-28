"""Diff curated training batches before rebuilding local packs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


WITHDRAWN_REVIEW_STATUSES = {"withdrawn", "rejected", "removed", "excluded"}


@dataclass(frozen=True)
class CuratedProvenanceObservation:
    source_file: str
    row_number: int
    record_type: str
    item_id: str
    source_pmid: str
    task: str
    label: str
    reviewer: str
    review_status: str
    text_hash: str
    content_hash: str
    original_source_file: str


@dataclass(frozen=True)
class CuratedBatchSourceSummary:
    source_file: str
    record_type: str
    row_count: int
    observation_count: int
    pmid_count: int
    task_counts: dict[str, int]
    label_counts: dict[str, int]
    reviewer_counts: dict[str, int]
    review_status_counts: dict[str, int]


@dataclass(frozen=True)
class CuratedProvenanceFinding:
    severity: str
    kind: str
    key: str
    message: str
    observations: list[CuratedProvenanceObservation]


@dataclass(frozen=True)
class CuratedProvenanceDiffReport:
    evidence_paths: list[str]
    entity_paths: list[str]
    reviewed_queue_paths: list[str]
    source_file_count: int
    observation_count: int
    pmid_count: int
    task_counts: dict[str, int]
    label_counts: dict[str, int]
    reviewer_counts: dict[str, int]
    review_status_counts: dict[str, int]
    source_summaries: list[CuratedBatchSourceSummary]
    duplicate_count: int
    changed_count: int
    withdrawn_count: int
    missing_source_count: int
    finding_count: int
    safe: bool
    findings: list[CuratedProvenanceFinding]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_curated_provenance_diff(
    *,
    evidence_jsonl: list[str | Path] | str | Path | None = None,
    entity_jsonl: list[str | Path] | str | Path | None = None,
    reviewed_queue_jsonl: list[str | Path] | str | Path | None = None,
) -> CuratedProvenanceDiffReport:
    """Compare curated fixture batches and surface provenance risks."""

    evidence_paths = _paths(evidence_jsonl)
    entity_paths = _paths(entity_jsonl)
    reviewed_paths = _paths(reviewed_queue_jsonl)
    observations: list[CuratedProvenanceObservation] = []
    source_summaries: list[CuratedBatchSourceSummary] = []
    findings: list[CuratedProvenanceFinding] = []

    for record_type, paths in (("evidence", evidence_paths), ("entities", entity_paths), ("reviewed_queue", reviewed_paths)):
        for path in paths:
            rows = _read_jsonl(path)
            if not path.exists():
                findings.append(
                    CuratedProvenanceFinding(
                        severity="error",
                        kind="missing_source",
                        key=str(path),
                        message=f"{record_type} source file not found: {path}",
                        observations=[],
                    )
                )
                continue
            file_observations = _observations_for_rows(path, record_type, rows)
            observations.extend(file_observations)
            source_summaries.append(_source_summary(path, record_type, len(rows), file_observations))

    findings.extend(_duplicate_findings(observations))
    findings.extend(_changed_findings(observations))
    findings.extend(_withdrawn_findings(observations))

    task_counts = Counter(observation.task or "unknown" for observation in observations)
    label_counts = Counter(observation.label or "unlabeled" for observation in observations)
    reviewer_counts = Counter(observation.reviewer or "unreviewed" for observation in observations)
    review_status_counts = Counter(observation.review_status or "unreviewed" for observation in observations)
    pmids = {observation.source_pmid for observation in observations if observation.source_pmid}
    error_count = sum(1 for finding in findings if finding.severity == "error")

    return CuratedProvenanceDiffReport(
        evidence_paths=[str(path) for path in evidence_paths],
        entity_paths=[str(path) for path in entity_paths],
        reviewed_queue_paths=[str(path) for path in reviewed_paths],
        source_file_count=len(evidence_paths) + len(entity_paths) + len(reviewed_paths),
        observation_count=len(observations),
        pmid_count=len(pmids),
        task_counts=dict(sorted(task_counts.items())),
        label_counts=dict(sorted(label_counts.items())),
        reviewer_counts=dict(sorted(reviewer_counts.items())),
        review_status_counts=dict(sorted(review_status_counts.items())),
        source_summaries=source_summaries,
        duplicate_count=sum(1 for finding in findings if finding.kind == "duplicate"),
        changed_count=sum(1 for finding in findings if finding.kind == "changed"),
        withdrawn_count=sum(1 for finding in findings if finding.kind == "withdrawn"),
        missing_source_count=sum(1 for finding in findings if finding.kind == "missing_source"),
        finding_count=len(findings),
        safe=error_count == 0 and not any(finding.kind in {"changed", "withdrawn"} for finding in findings),
        findings=findings,
    )


def save_curated_provenance_diff_json(report: CuratedProvenanceDiffReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_curated_provenance_diff_markdown(report: CuratedProvenanceDiffReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_curated_provenance_diff_markdown(report), encoding="utf-8")
    return output


def format_curated_provenance_diff_markdown(report: CuratedProvenanceDiffReport) -> str:
    lines = [
        "# Curated Multi-Batch Provenance Diff",
        "",
        RESEARCH_WARNING,
        "",
        f"- Safe for pack rebuild review: {report.safe}",
        f"- Source files: {report.source_file_count}",
        f"- Observations: {report.observation_count}",
        f"- Source PMIDs: {report.pmid_count}",
        f"- Findings: {report.finding_count}",
        f"- Duplicates: {report.duplicate_count}",
        f"- Changed reviewed examples: {report.changed_count}",
        f"- Withdrawn/rejected reviewed examples: {report.withdrawn_count}",
        f"- Missing source files: {report.missing_source_count}",
        "",
        "## Task Counts",
        *(_format_counts(report.task_counts) or ["- none"]),
        "",
        "## Label Counts",
        *(_format_counts(report.label_counts) or ["- none"]),
        "",
        "## Reviewer Counts",
        *(_format_counts(report.reviewer_counts) or ["- none"]),
        "",
        "## Review Status Counts",
        *(_format_counts(report.review_status_counts) or ["- none"]),
        "",
        "## Source Files",
    ]
    if report.source_summaries:
        for summary in report.source_summaries:
            lines.extend(
                [
                    f"- `{summary.source_file}` ({summary.record_type})",
                    f"  - Rows: {summary.row_count}",
                    f"  - Observations: {summary.observation_count}",
                    f"  - Source PMIDs: {summary.pmid_count}",
                    f"  - Tasks: {_inline_counts(summary.task_counts)}",
                    f"  - Labels: {_inline_counts(summary.label_counts)}",
                    f"  - Reviewers: {_inline_counts(summary.reviewer_counts)}",
                    f"  - Review statuses: {_inline_counts(summary.review_status_counts)}",
                ]
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Findings"])
    if report.findings:
        for finding in report.findings:
            lines.append(f"- [{finding.severity}] {finding.kind}: {finding.message}")
            for observation in finding.observations[:5]:
                lines.append(
                    "  - "
                    f"`{observation.source_file}` row {observation.row_number}; "
                    f"PMID `{observation.source_pmid or 'unknown'}`; "
                    f"task `{observation.task or 'unknown'}`; "
                    f"label `{observation.label or 'unlabeled'}`; "
                    f"reviewer `{observation.reviewer or 'unreviewed'}`; "
                    f"status `{observation.review_status or 'unreviewed'}`"
                )
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare curated training batches before rebuilding packs.")
    parser.add_argument("--evidence-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--entity-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--reviewed-queue-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/curated_provenance_diff.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/curated_provenance_diff.md"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-findings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_curated_provenance_diff(
        evidence_jsonl=args.evidence_jsonl,
        entity_jsonl=args.entity_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
    )
    save_curated_provenance_diff_json(report, args.json_output)
    save_curated_provenance_diff_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curated_provenance_diff_markdown(report))
    return 0 if report.safe or args.allow_findings else 1


def _observations_for_rows(path: Path, record_type: str, rows: list[dict[str, Any]]) -> list[CuratedProvenanceObservation]:
    observations: list[CuratedProvenanceObservation] = []
    for row_number, row in enumerate(rows, start=1):
        if record_type == "entities":
            observations.extend(_entity_observations(path, row_number, row))
        else:
            observations.append(_observation(path, row_number, record_type, row))
    return observations


def _entity_observations(path: Path, row_number: int, row: dict[str, Any]) -> list[CuratedProvenanceObservation]:
    observations: list[CuratedProvenanceObservation] = []
    pmid = _row_pmid(row)
    for index, entity in enumerate(row.get("entities") or [], start=1):
        if not isinstance(entity, dict):
            continue
        text = str(entity.get("text") or entity.get("normalized_text") or "").strip()
        label = str(entity.get("label") or "").strip()
        item_id = str(entity.get("item_id") or f"ner:{pmid}:{entity.get('start', '')}:{entity.get('end', '')}:{label}:{text}").strip()
        payload = {
            "entity": entity,
            "pmid": pmid,
            "row_number": row_number,
            "entity_index": index,
        }
        observations.append(
            CuratedProvenanceObservation(
                source_file=str(path),
                row_number=row_number,
                record_type="entities",
                item_id=item_id,
                source_pmid=pmid,
                task="ner",
                label=label,
                reviewer=str(row.get("reviewer") or "").strip(),
                review_status=str(row.get("review_status") or "").strip(),
                text_hash=_hash_text(text),
                content_hash=_hash_payload(payload),
                original_source_file=str(row.get("source_file") or "").strip(),
            )
        )
    return observations


def _observation(path: Path, row_number: int, record_type: str, row: dict[str, Any]) -> CuratedProvenanceObservation:
    task = _row_task(row, record_type)
    label = _row_label(row, task)
    text = str(row.get("text") or row.get("sentence") or row.get("claim") or "").strip()
    return CuratedProvenanceObservation(
        source_file=str(path),
        row_number=row_number,
        record_type=record_type,
        item_id=str(row.get("item_id") or "").strip(),
        source_pmid=_row_pmid(row),
        task=task,
        label=label,
        reviewer=str(row.get("reviewer") or "").strip(),
        review_status=str(row.get("review_status") or "").strip(),
        text_hash=_hash_text(text),
        content_hash=_hash_payload(row),
        original_source_file=str(row.get("source_file") or "").strip(),
    )


def _source_summary(
    path: Path,
    record_type: str,
    row_count: int,
    observations: list[CuratedProvenanceObservation],
) -> CuratedBatchSourceSummary:
    return CuratedBatchSourceSummary(
        source_file=str(path),
        record_type=record_type,
        row_count=row_count,
        observation_count=len(observations),
        pmid_count=len({observation.source_pmid for observation in observations if observation.source_pmid}),
        task_counts=dict(sorted(Counter(observation.task or "unknown" for observation in observations).items())),
        label_counts=dict(sorted(Counter(observation.label or "unlabeled" for observation in observations).items())),
        reviewer_counts=dict(sorted(Counter(observation.reviewer or "unreviewed" for observation in observations).items())),
        review_status_counts=dict(sorted(Counter(observation.review_status or "unreviewed" for observation in observations).items())),
    )


def _duplicate_findings(observations: list[CuratedProvenanceObservation]) -> list[CuratedProvenanceFinding]:
    groups: dict[str, list[CuratedProvenanceObservation]] = defaultdict(list)
    for observation in observations:
        groups[_duplicate_key(observation)].append(observation)
    findings: list[CuratedProvenanceFinding] = []
    for key, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        signatures = {_exact_signature(observation) for observation in group}
        if len(signatures) == 1:
            findings.append(
                CuratedProvenanceFinding(
                    severity="warning",
                    kind="duplicate",
                    key=key,
                    message=f"{len(group)} duplicate curated observations share {key}",
                    observations=group,
                )
            )
    return findings


def _changed_findings(observations: list[CuratedProvenanceObservation]) -> list[CuratedProvenanceFinding]:
    groups: dict[str, list[CuratedProvenanceObservation]] = defaultdict(list)
    for observation in observations:
        groups[_identity_key(observation)].append(observation)
    findings: list[CuratedProvenanceFinding] = []
    for key, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        changed_fields = [
            field
            for field in ("label", "reviewer", "review_status", "text_hash")
            if len({getattr(observation, field) for observation in group}) > 1
        ]
        if changed_fields:
            findings.append(
                CuratedProvenanceFinding(
                    severity="error",
                    kind="changed",
                    key=key,
                    message=f"curated observation changed across batches ({', '.join(changed_fields)}) for {key}",
                    observations=group,
                )
            )
    return findings


def _withdrawn_findings(observations: list[CuratedProvenanceObservation]) -> list[CuratedProvenanceFinding]:
    findings: list[CuratedProvenanceFinding] = []
    for observation in observations:
        status = observation.review_status.casefold()
        if observation.record_type == "reviewed_queue" and status in WITHDRAWN_REVIEW_STATUSES:
            findings.append(
                CuratedProvenanceFinding(
                    severity="error",
                    kind="withdrawn",
                    key=_identity_key(observation),
                    message=f"reviewed example is marked {observation.review_status}",
                    observations=[observation],
                )
            )
    return findings


def _duplicate_key(observation: CuratedProvenanceObservation) -> str:
    return "|".join(
        (
            observation.record_type,
            observation.item_id or observation.source_pmid,
            observation.task,
            observation.label,
            observation.text_hash,
        )
    )


def _identity_key(observation: CuratedProvenanceObservation) -> str:
    if observation.item_id:
        return f"{observation.record_type}|{observation.item_id}"
    return "|".join((observation.record_type, observation.source_pmid, observation.task, observation.text_hash))


def _exact_signature(observation: CuratedProvenanceObservation) -> tuple[str, str, str, str, str]:
    return (
        observation.source_pmid,
        observation.task,
        observation.label,
        observation.reviewer,
        observation.review_status,
    )


def _row_task(row: dict[str, Any], record_type: str) -> str:
    raw_task = str(row.get("task") or row.get("item_type") or record_type).strip()
    if raw_task == "evidence_claim":
        return "evidence"
    if raw_task == "graph_relation":
        return "relation"
    return raw_task


def _row_label(row: dict[str, Any], task: str) -> str:
    if row.get("label") is not None:
        return str(row.get("label")).strip()
    if task == "evidence":
        tier = row.get("corrected_evidence_tier")
        if tier is None or tier == "":
            tier = row.get("evidence_tier")
        return "" if tier is None else str(tier).strip()
    if task == "relation":
        relation = str(row.get("corrected_relation_type") or row.get("relation_type") or "").strip()
        return relation
    return ""


def _row_pmid(row: dict[str, Any]) -> str:
    return str(row.get("source_pmid") or row.get("pmid") or "").strip()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _paths(value: list[str | Path] | str | Path | None) -> list[Path]:
    if value is None:
        return []
    if isinstance(value, list):
        return [Path(item) for item in value]
    return [Path(value)]


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return _hash_text(encoded)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _format_counts(counts: dict[str, int]) -> list[str]:
    return [f"- {name}: {count}" for name, count in sorted(counts.items())]


def _inline_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
