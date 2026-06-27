"""Merge positive and synthetic-negative relation rows for training review."""

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
from gbmbert.training.relation_quality import analyze_relation_dataset_quality

CURATED_RELATION_SOURCE = "human_or_curated_positive"
SYNTHETIC_RELATION_SOURCE = "synthetic_no_relation"


@dataclass(frozen=True)
class RelationPackMergeReport:
    positive_input_path: str
    negative_input_path: str
    output_path: str
    positive_count: int
    negative_count: int
    total_count: int
    label_counts: dict[str, int]
    provenance_counts: dict[str, int]
    ready: bool
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def merge_relation_training_pack(
    positive_dataset_path: str | Path,
    negative_dataset_path: str | Path,
    output_jsonl: str | Path,
) -> RelationPackMergeReport:
    """Merge positive relation rows and synthetic NO_RELATION rows into one JSONL file."""

    positive_root = Path(positive_dataset_path)
    negative_root = Path(negative_dataset_path)
    output_path = Path(output_jsonl)
    positives = [
        _annotate_provenance(row, source_type=CURATED_RELATION_SOURCE, source_path=positive_root)
        for row in _relation_rows(positive_root)
        if _label_text(row) and _label_text(row) != NO_RELATION_LABEL
    ]
    negatives = [
        _annotate_provenance(row, source_type=SYNTHETIC_RELATION_SOURCE, source_path=negative_root)
        for row in _relation_rows(negative_root)
        if _label_text(row) == NO_RELATION_LABEL
    ]
    rows = positives + negatives
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(rows, output_path)

    quality = analyze_relation_dataset_quality(output_path)
    warnings = list(quality.warnings)
    if not positives and "no positive relation examples found" not in warnings:
        warnings.append("no positive relation examples found")
    if not negatives and "no NO_RELATION negative examples found" not in warnings:
        warnings.append("no NO_RELATION negative examples found")
    label_counts = dict(sorted(Counter(_label_text(row) for row in rows if _label_text(row)).items()))
    provenance_counts = dict(
        sorted(Counter(str(row.get("relation_pack_source_type") or "") for row in rows).items())
    )
    ready = bool(positives and negatives)
    return RelationPackMergeReport(
        positive_input_path=str(positive_root),
        negative_input_path=str(negative_root),
        output_path=str(output_path),
        positive_count=len(positives),
        negative_count=len(negatives),
        total_count=len(rows),
        label_counts=label_counts,
        provenance_counts=provenance_counts,
        ready=ready,
        warnings=warnings,
    )


def save_relation_pack_json(report: RelationPackMergeReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_relation_pack_markdown(report: RelationPackMergeReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_relation_pack_markdown(report), encoding="utf-8")
    return output


def format_relation_pack_markdown(report: RelationPackMergeReport) -> str:
    lines = [
        "# GBM-BERT Relation Pack Merger",
        "",
        RESEARCH_WARNING,
        "",
        f"- Positive input: `{report.positive_input_path}`",
        f"- Negative input: `{report.negative_input_path}`",
        f"- Output: `{report.output_path}`",
        f"- Positive examples: {report.positive_count}",
        f"- Negative examples: {report.negative_count}",
        f"- Total examples: {report.total_count}",
        f"- Ready: {report.ready}",
        "",
        "## Labels",
        *([f"- {label}: {count}" for label, count in report.label_counts.items()] or ["- none"]),
        "",
        "## Provenance",
        *([f"- {source}: {count}" for source, count in report.provenance_counts.items()] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge positive and synthetic-negative relation examples.")
    parser.add_argument("positive_dataset_path", type=Path, help="Relation JSONL file or annotation dataset directory.")
    parser.add_argument("negative_dataset_path", type=Path, help="NO_RELATION JSONL file or dataset directory.")
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-not-ready", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = merge_relation_training_pack(args.positive_dataset_path, args.negative_dataset_path, args.output_jsonl)
    if args.json_output:
        save_relation_pack_json(report, args.json_output)
    if args.markdown_output:
        save_relation_pack_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_relation_pack_markdown(report))
    return 0 if report.ready or args.allow_not_ready else 1


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


def _annotate_provenance(row: dict[str, Any], *, source_type: str, source_path: Path) -> dict[str, Any]:
    annotated = dict(row)
    annotated["relation_pack_source_type"] = source_type
    annotated["relation_pack_source_path"] = str(source_path)
    annotated["relation_pack_synthetic"] = source_type == SYNTHETIC_RELATION_SOURCE
    annotated.setdefault("warning", RESEARCH_WARNING)
    return annotated


def _label_text(row: dict[str, Any]) -> str:
    return str(row.get("label") or "").strip()


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


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
