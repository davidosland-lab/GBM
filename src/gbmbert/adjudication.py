"""Adjudication reports for multiple reviewed GBM-AI annotation passes."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING

ADJUDICATION_FIELDS = (
    "review_status",
    "corrected_relation_type",
    "corrected_evidence_tier",
    "relation_type",
    "evidence_tier",
    "predicted_evidence_tier",
)


@dataclass(frozen=True)
class AdjudicationConflict:
    item_id: str
    field: str
    values_by_source: dict[str, str]


@dataclass(frozen=True)
class AdjudicationReport:
    source_paths: list[str]
    item_count: int
    compared_item_count: int
    conflict_count: int
    conflicts: list[AdjudicationConflict]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_adjudication_report(paths: list[str | Path]) -> AdjudicationReport:
    """Compare reviewed JSONL files and surface item-level decision conflicts."""

    source_paths = [str(path) for path in paths]
    rows_by_source = {str(path): _load_jsonl_by_item_id(path) for path in paths}
    all_item_ids = sorted({item_id for rows in rows_by_source.values() for item_id in rows})
    conflicts: list[AdjudicationConflict] = []
    warnings: list[str] = []
    compared_count = 0
    for item_id in all_item_ids:
        present = {source: rows[item_id] for source, rows in rows_by_source.items() if item_id in rows}
        if len(present) < 2:
            warnings.append(f"{item_id} appears in only one source")
            continue
        compared_count += 1
        for field in ADJUDICATION_FIELDS:
            values = {
                source: _stringify_decision(row.get(field))
                for source, row in present.items()
                if _stringify_decision(row.get(field)) != ""
            }
            if len(set(values.values())) > 1:
                conflicts.append(AdjudicationConflict(item_id=item_id, field=field, values_by_source=values))
    return AdjudicationReport(
        source_paths=source_paths,
        item_count=len(all_item_ids),
        compared_item_count=compared_count,
        conflict_count=len(conflicts),
        conflicts=conflicts,
        warnings=warnings,
    )


def save_adjudication_json(report: AdjudicationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_adjudication_markdown(report: AdjudicationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_adjudication_markdown(report), encoding="utf-8")
    return output


def format_adjudication_markdown(report: AdjudicationReport) -> str:
    conflict_lines = [
        f"- `{conflict.item_id}` field `{conflict.field}`: "
        + "; ".join(f"{Path(source).name}={value}" for source, value in sorted(conflict.values_by_source.items()))
        for conflict in report.conflicts[:100]
    ] or ["- none"]
    lines = [
        "# GBM-AI Annotation Adjudication Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Sources: {len(report.source_paths)}",
        f"- Items: {report.item_count}",
        f"- Compared items: {report.compared_item_count}",
        f"- Conflicts: {report.conflict_count}",
        "",
        "## Conflicts",
        *conflict_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare reviewed GBM-AI annotation passes and surface conflicts.")
    parser.add_argument("reviewed_jsonl", type=Path, nargs="+")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_adjudication_report(args.reviewed_jsonl)
    if args.json_output:
        save_adjudication_json(report, args.json_output)
    if args.markdown_output:
        save_adjudication_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_adjudication_markdown(report))
    return 0


def _load_jsonl_by_item_id(path: str | Path) -> dict[str, dict[str, Any]]:
    input_path = Path(path)
    rows: dict[str, dict[str, Any]] = {}
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
            item_id = str(row.get("item_id") or "")
            if not item_id:
                raise ValueError(f"Missing item_id on line {line_number} of {input_path}")
            rows[item_id] = row
    return rows


def _stringify_decision(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
