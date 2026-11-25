"""Entity-span review queue for lexicon/gold NER spans (research-use only).

Flattens document-level ``gold_entities`` JSONL into span-level review rows with
accept/correct/reject status, then rebuilds document entities from decided rows.
This makes entity offsets a first-class reviewed signal alongside evidence/relations.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING

PENDING = "pending"
ACCEPTED = "accepted"
CORRECTED = "corrected"
REJECTED = "rejected"
DECISION_STATUSES = {ACCEPTED, CORRECTED, REJECTED}


@dataclass(frozen=True)
class EntitySpanReviewExportReport:
    created_at_utc: str
    input_path: str
    jsonl_output: str
    csv_output: str
    span_count: int
    document_count: int
    label_counts: dict[str, int]
    warnings: list[str] = field(default_factory=list)
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EntitySpanReviewApplyReport:
    created_at_utc: str
    review_jsonl: str
    entities_output: str
    document_count: int
    accepted_span_count: int
    rejected_span_count: int
    pending_span_count: int
    label_counts: dict[str, int]
    ready: bool
    warnings: list[str] = field(default_factory=list)
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_entity_span_review_queue(
    *,
    entities_jsonl: str | Path,
    jsonl_output: str | Path,
    csv_output: str | Path | None = None,
    reviewer: str = "",
) -> EntitySpanReviewExportReport:
    """Flatten gold_entities docs into pending span-review rows."""

    input_path = Path(entities_jsonl)
    docs = _read_jsonl(input_path)
    rows: list[dict[str, Any]] = []
    label_counts: dict[str, int] = {}
    warnings: list[str] = []
    for doc_index, doc in enumerate(docs):
        pmid = str(doc.get("pmid") or doc.get("source_pmid") or "").strip()
        if not pmid:
            warnings.append(f"document {doc_index} missing pmid; skipped")
            continue
        context = str(doc.get("text") or "")
        for ent_index, entity in enumerate(doc.get("entities") or []):
            if not isinstance(entity, dict):
                continue
            label = str(entity.get("label") or "").strip()
            start = int(entity.get("start", -1))
            end = int(entity.get("end", -1))
            mention = str(entity.get("text") or "")
            if not label or start < 0 or end <= start:
                warnings.append(f"pmid {pmid} entity {ent_index} has invalid span; skipped")
                continue
            label_counts[label] = label_counts.get(label, 0) + 1
            rows.append(
                {
                    "item_id": f"entity_span:{pmid}:{ent_index}:{start}:{end}",
                    "item_type": "entity_span",
                    "source_pmid": pmid,
                    "text": mention,
                    "context_text": context,
                    "label": label,
                    "start": start,
                    "end": end,
                    "confidence": entity.get("confidence"),
                    "normalized_text": str(entity.get("normalized_text") or mention),
                    "corrected_label": "",
                    "corrected_start": None,
                    "corrected_end": None,
                    "corrected_text": "",
                    "review_status": PENDING,
                    "reviewer": reviewer,
                    "review_notes": "",
                    "warning": RESEARCH_WARNING,
                }
            )

    jsonl_path = _write_jsonl(jsonl_output, rows)
    csv_path = ""
    if csv_output is not None:
        csv_path = str(_write_csv(csv_output, rows))
    return EntitySpanReviewExportReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        input_path=str(input_path),
        jsonl_output=str(jsonl_path),
        csv_output=csv_path,
        span_count=len(rows),
        document_count=len({row["source_pmid"] for row in rows}),
        label_counts=dict(sorted(label_counts.items())),
        warnings=warnings,
    )


def apply_entity_span_reviews(
    *,
    review_jsonl: str | Path,
    entities_output: str | Path,
    require_complete: bool = True,
) -> EntitySpanReviewApplyReport:
    """Rebuild gold_entities JSONL from accepted/corrected span reviews."""

    reviews = _read_jsonl(review_jsonl)
    pending = [row for row in reviews if str(row.get("review_status") or PENDING) == PENDING]
    rejected = [row for row in reviews if str(row.get("review_status")) == REJECTED]
    kept_rows = [row for row in reviews if str(row.get("review_status")) in {ACCEPTED, CORRECTED}]
    warnings: list[str] = []
    if pending and require_complete:
        warnings.append(f"{len(pending)} entity-span row(s) still '{PENDING}'")

    by_pmid: dict[str, list[dict[str, Any]]] = {}
    label_counts: dict[str, int] = {}
    context_by_pmid: dict[str, str] = {}
    for row in kept_rows:
        pmid = str(row.get("source_pmid") or "").strip()
        if not pmid:
            warnings.append(f"accepted span missing source_pmid: {row.get('item_id')}")
            continue
        label, start, end, text = _resolved_span(row)
        if not label or start < 0 or end <= start:
            warnings.append(f"accepted span has invalid corrected fields: {row.get('item_id')}")
            continue
        label_counts[label] = label_counts.get(label, 0) + 1
        by_pmid.setdefault(pmid, []).append(
            {
                "text": text,
                "label": label,
                "start": start,
                "end": end,
                "confidence": row.get("confidence"),
                "normalized_text": str(row.get("normalized_text") or text),
                "review_status": str(row.get("review_status")),
                "reviewer": str(row.get("reviewer") or ""),
                "review_notes": str(row.get("review_notes") or ""),
            }
        )
        context = str(row.get("context_text") or "").strip()
        if context:
            context_by_pmid[pmid] = context

    docs: list[dict[str, Any]] = []
    for pmid in sorted(by_pmid):
        doc: dict[str, Any] = {"pmid": pmid, "entities": by_pmid[pmid]}
        if pmid in context_by_pmid:
            doc["text"] = context_by_pmid[pmid]
        docs.append(doc)

    ready = not warnings
    if ready or not require_complete:
        _write_jsonl(entities_output, docs)
    return EntitySpanReviewApplyReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        review_jsonl=str(Path(review_jsonl)),
        entities_output=str(Path(entities_output)),
        document_count=len(docs),
        accepted_span_count=len(kept_rows),
        rejected_span_count=len(rejected),
        pending_span_count=len(pending),
        label_counts=dict(sorted(label_counts.items())),
        ready=ready,
        warnings=warnings,
    )


def format_export_markdown(report: EntitySpanReviewExportReport) -> str:
    lines = [
        "# Entity Span Review Export",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Input: `{report.input_path}`",
        f"- JSONL: `{report.jsonl_output}`",
        f"- CSV: `{report.csv_output or 'none'}`",
        f"- Spans: {report.span_count}",
        f"- Documents: {report.document_count}",
        "",
        "## Labels",
        *([f"- {label}: {count}" for label, count in report.label_counts.items()] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_apply_markdown(report: EntitySpanReviewApplyReport) -> str:
    lines = [
        "# Entity Span Review Apply",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Review queue: `{report.review_jsonl}`",
        f"- Entities output: `{report.entities_output}`",
        f"- Documents: {report.document_count}",
        f"- Accepted/corrected spans: {report.accepted_span_count}",
        f"- Rejected spans: {report.rejected_span_count}",
        f"- Pending spans: {report.pending_span_count}",
        f"- Ready: {report.ready}",
        "",
        "## Labels",
        *([f"- {label}: {count}" for label, count in report.label_counts.items()] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_export_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export entity spans to a human-review JSONL/CSV queue.")
    parser.add_argument("--entities-jsonl", type=Path, required=True)
    parser.add_argument("--jsonl-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def build_apply_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild gold_entities JSONL from entity-span reviews.")
    parser.add_argument("--review-jsonl", type=Path, required=True)
    parser.add_argument("--entities-output", type=Path, required=True)
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def export_main(argv: list[str] | None = None) -> int:
    args = build_export_arg_parser().parse_args(argv)
    report = export_entity_span_review_queue(
        entities_jsonl=args.entities_jsonl,
        jsonl_output=args.jsonl_output,
        csv_output=args.csv_output,
        reviewer=args.reviewer,
    )
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(format_export_markdown(report), encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_export_markdown(report))
    return 0 if report.span_count else 1


def apply_main(argv: list[str] | None = None) -> int:
    args = build_apply_arg_parser().parse_args(argv)
    report = apply_entity_span_reviews(
        review_jsonl=args.review_jsonl,
        entities_output=args.entities_output,
        require_complete=not args.allow_pending,
    )
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(format_apply_markdown(report), encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_apply_markdown(report))
    return 0 if report.ready else 1


def _resolved_span(row: dict[str, Any]) -> tuple[str, int, int, str]:
    status = str(row.get("review_status") or "")
    if status == CORRECTED:
        label = str(row.get("corrected_label") or row.get("label") or "").strip()
        start_raw = row.get("corrected_start")
        end_raw = row.get("corrected_end")
        start = int(start_raw) if start_raw is not None and str(start_raw) != "" else int(row.get("start", -1))
        end = int(end_raw) if end_raw is not None and str(end_raw) != "" else int(row.get("end", -1))
        text = str(row.get("corrected_text") or row.get("text") or "").strip()
        return label, start, end, text
    return (
        str(row.get("label") or "").strip(),
        int(row.get("start", -1)),
        int(row.get("end", -1)),
        str(row.get("text") or "").strip(),
    )


def _read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    file_path = Path(path)
    if not file_path.exists():
        return rows
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return output


def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "item_id",
        "source_pmid",
        "text",
        "label",
        "start",
        "end",
        "confidence",
        "corrected_label",
        "corrected_start",
        "corrected_end",
        "corrected_text",
        "review_status",
        "reviewer",
        "review_notes",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return output


if __name__ == "__main__":
    raise SystemExit(export_main())
