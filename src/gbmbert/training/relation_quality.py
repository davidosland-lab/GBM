"""Quality reports for GBM-BERT relation extraction datasets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.preparation import SPLITS, TASK_FILES
from gbmbert.training.relation_negatives import NO_RELATION_LABEL


@dataclass(frozen=True)
class RelationDatasetQualityReport:
    input_path: str
    relation_count: int
    positive_count: int
    negative_count: int
    missing_sentence_count: int
    missing_endpoint_count: int
    invalid_endpoint_count: int
    duplicate_count: int
    label_counts: dict[str, int]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_relation_dataset_quality(dataset_path: str | Path) -> RelationDatasetQualityReport:
    """Summarize relation extraction examples and flag common training-data defects."""

    root = Path(dataset_path)
    rows = _relation_rows(root)
    label_counts = Counter(_label_text(row) for row in rows)
    positive_count = sum(1 for row in rows if _label_text(row) and _label_text(row) != NO_RELATION_LABEL)
    negative_count = label_counts.get(NO_RELATION_LABEL, 0)
    missing_sentence_count = sum(1 for row in rows if not _sentence_text(row))
    missing_endpoint_count = sum(1 for row in rows if not _endpoint_text(row.get("head")) or not _endpoint_text(row.get("tail")))
    invalid_endpoint_count = sum(
        1
        for row in rows
        if _endpoint_text(row.get("head"))
        and _endpoint_text(row.get("tail"))
        and _endpoint_text(row.get("head")) == _endpoint_text(row.get("tail"))
    )
    duplicate_count = _duplicate_count(rows)
    warnings: list[str] = []
    if not rows:
        warnings.append("no relation examples found")
    if rows and not positive_count:
        warnings.append("no positive relation examples found")
    if rows and not negative_count:
        warnings.append("no NO_RELATION negative examples found")
    if missing_sentence_count:
        warnings.append(f"{missing_sentence_count} relation example(s) missing sentence/text")
    if missing_endpoint_count:
        warnings.append(f"{missing_endpoint_count} relation example(s) missing head or tail endpoint")
    if invalid_endpoint_count:
        warnings.append(f"{invalid_endpoint_count} relation example(s) have identical head and tail endpoints")
    if duplicate_count:
        warnings.append(f"{duplicate_count} duplicate relation example(s)")
    return RelationDatasetQualityReport(
        input_path=str(root),
        relation_count=len(rows),
        positive_count=positive_count,
        negative_count=negative_count,
        missing_sentence_count=missing_sentence_count,
        missing_endpoint_count=missing_endpoint_count,
        invalid_endpoint_count=invalid_endpoint_count,
        duplicate_count=duplicate_count,
        label_counts=dict(sorted(label_counts.items())),
        warnings=warnings,
    )


def save_relation_quality_json(report: RelationDatasetQualityReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_relation_quality_markdown(report: RelationDatasetQualityReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_relation_quality_markdown(report), encoding="utf-8")
    return output


def format_relation_quality_markdown(report: RelationDatasetQualityReport) -> str:
    lines = [
        "# GBM-BERT Relation Dataset Quality Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Input: `{report.input_path}`",
        f"- Relation examples: {report.relation_count}",
        f"- Positive examples: {report.positive_count}",
        f"- Negative examples: {report.negative_count}",
        f"- Missing sentence/text: {report.missing_sentence_count}",
        f"- Missing endpoint: {report.missing_endpoint_count}",
        f"- Invalid endpoint: {report.invalid_endpoint_count}",
        f"- Duplicates: {report.duplicate_count}",
        "",
        "## Labels",
        *([f"- {label or '<missing>'}: {count}" for label, count in report.label_counts.items()] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a quality report for relation extraction datasets.")
    parser.add_argument("dataset_path", type=Path, help="Relation JSONL file or annotation dataset directory.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-warnings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = analyze_relation_dataset_quality(args.dataset_path)
    if args.json_output:
        save_relation_quality_json(report, args.json_output)
    if args.markdown_output:
        save_relation_quality_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_relation_quality_markdown(report))
    return 1 if args.fail_on_warnings and report.warnings else 0


def _relation_rows(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        return _read_jsonl(path)
    files = []
    base = path / TASK_FILES["relation"]
    if base.exists():
        files.append(base)
    for split in SPLITS:
        split_path = path / f"relation_{split}.jsonl"
        if split_path.exists():
            files.append(split_path)
    rows: list[dict[str, Any]] = []
    for file_path in files:
        rows.extend(_read_jsonl(file_path))
    return rows


def _duplicate_count(rows: list[dict[str, Any]]) -> int:
    keys = [
        json.dumps(
            (
                str(row.get("source_pmid") or row.get("pmid") or ""),
                _sentence_text(row),
                _endpoint_text(row.get("head")),
                _endpoint_text(row.get("tail")),
                _label_text(row),
            ),
            sort_keys=True,
        )
        for row in rows
    ]
    return len(keys) - len(set(keys))


def _sentence_text(row: dict[str, Any]) -> str:
    return str(row.get("sentence") or row.get("text") or "").strip()


def _label_text(row: dict[str, Any]) -> str:
    return str(row.get("label") or "").strip()


def _endpoint_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("id", "entity_id", "text", "name", "label"):
            if value.get(key):
                return str(value[key]).strip()
        return json.dumps(value, sort_keys=True)
    return str(value).strip()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL record on line {line_number}: {path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
