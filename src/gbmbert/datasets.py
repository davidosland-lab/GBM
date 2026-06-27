"""Annotation dataset export and quality reports for future GBM-BERT training."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from gbmbert.extraction.io import load_entity_jsonl
from gbmbert.extraction.review_queue import ReviewQueueItem, load_review_queue_jsonl

LOGGER = logging.getLogger(__name__)
RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)
DatasetTask = Literal["ner", "evidence", "relation"]


@dataclass(frozen=True)
class DatasetExportSummary:
    output_dir: str
    ner_count: int
    evidence_count: int
    relation_count: int
    included_statuses: list[str]
    files: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskQuality:
    task: str
    example_count: int
    label_counts: dict[str, int]
    missing_text_count: int
    missing_offset_count: int
    duplicate_count: int
    warnings: list[str]


@dataclass(frozen=True)
class DatasetQualityReport:
    dataset_dir: str
    task_reports: list[TaskQuality]
    total_examples: int
    warning_count: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_annotation_datasets(
    *,
    reviewed_queue_jsonl: str | Path,
    output_dir: str | Path,
    entity_jsonl: str | Path | None = None,
    include_pending: bool = False,
) -> DatasetExportSummary:
    """Export reviewed curation artifacts into simple training-ready JSONL datasets."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    included_statuses = ["accepted", "corrected"]
    if include_pending:
        included_statuses.append("pending")
    items = [
        item
        for item in load_review_queue_jsonl(reviewed_queue_jsonl)
        if item.review_status in included_statuses
    ]
    evidence_examples = [_evidence_example(item) for item in items if item.item_type == "evidence_claim"]
    relation_examples = [_relation_example(item) for item in items if item.item_type == "graph_relation"]
    ner_examples = _ner_examples(entity_jsonl) if entity_jsonl else []

    files = {
        "ner": str(output_path / "ner.jsonl"),
        "evidence": str(output_path / "evidence.jsonl"),
        "relation": str(output_path / "relations.jsonl"),
        "manifest": str(output_path / "dataset_manifest.json"),
    }
    _write_jsonl(ner_examples, files["ner"])
    _write_jsonl(evidence_examples, files["evidence"])
    _write_jsonl(relation_examples, files["relation"])
    summary = DatasetExportSummary(
        output_dir=str(output_path),
        ner_count=len(ner_examples),
        evidence_count=len(evidence_examples),
        relation_count=len(relation_examples),
        included_statuses=included_statuses,
        files=files,
    )
    Path(files["manifest"]).write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return summary


def analyze_annotation_dataset(dataset_dir: str | Path) -> DatasetQualityReport:
    """Audit exported JSONL datasets for label balance and missing training fields."""

    root = Path(dataset_dir)
    task_reports = [
        _analyze_task(root / "ner.jsonl", task="ner"),
        _analyze_task(root / "evidence.jsonl", task="evidence"),
        _analyze_task(root / "relations.jsonl", task="relation"),
    ]
    warnings: list[str] = []
    for report in task_reports:
        warnings.extend(f"{report.task}: {warning}" for warning in report.warnings)
    return DatasetQualityReport(
        dataset_dir=str(root),
        task_reports=task_reports,
        total_examples=sum(report.example_count for report in task_reports),
        warning_count=len(warnings),
        warnings=warnings,
    )


def save_dataset_export_summary_json(summary: DatasetExportSummary, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_dataset_quality_json(report: DatasetQualityReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_dataset_quality_markdown(report: DatasetQualityReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_dataset_quality_markdown(report), encoding="utf-8")
    return output_path


def format_dataset_quality_markdown(report: DatasetQualityReport) -> str:
    warning_lines = [f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]
    lines = [
        "# GBM-AI Annotation Dataset Quality Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Dataset directory: `{report.dataset_dir}`",
        f"- Total examples: {report.total_examples}",
        f"- Warnings: {report.warning_count}",
        "",
        "## Tasks",
    ]
    for task in report.task_reports:
        lines.extend(
            [
                f"### {task.task}",
                f"- Examples: {task.example_count}",
                f"- Missing text: {task.missing_text_count}",
                f"- Missing offsets: {task.missing_offset_count}",
                f"- Duplicates: {task.duplicate_count}",
                "- Labels:",
                *_format_counts(task.label_counts),
                "",
            ]
        )
    lines.extend(["## Warnings", *warning_lines])
    return "\n".join(lines).rstrip() + "\n"


def build_export_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export reviewed annotations into GBM-BERT dataset JSONL files.")
    parser.add_argument("reviewed_queue_jsonl", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--entity-jsonl", type=Path)
    parser.add_argument("--include-pending", action="store_true")
    parser.add_argument("--summary-json-output", type=Path)
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_quality_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit exported GBM-BERT annotation datasets.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def export_main(argv: list[str] | None = None) -> int:
    parser = build_export_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    summary = export_annotation_datasets(
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        output_dir=args.output_dir,
        entity_jsonl=args.entity_jsonl,
        include_pending=args.include_pending,
    )
    if args.summary_json_output:
        save_dataset_export_summary_json(summary, args.summary_json_output)
    LOGGER.info("Exported annotation datasets to %s", args.output_dir)
    return 0


def quality_main(argv: list[str] | None = None) -> int:
    parser = build_quality_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = analyze_annotation_dataset(args.dataset_dir)
    if args.json_output:
        save_dataset_quality_json(report, args.json_output)
    if args.markdown_output:
        save_dataset_quality_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_dataset_quality_markdown(report))
    return 0


def _evidence_example(item: ReviewQueueItem) -> dict[str, Any]:
    label = item.corrected_evidence_tier if item.corrected_evidence_tier is not None else item.evidence_tier
    return {
        "task": "evidence",
        "item_id": item.item_id,
        "source_pmid": item.source_pmid,
        "text": item.text,
        "label": int(label),
        "review_status": item.review_status,
        "reviewer": item.reviewer,
        "review_notes": item.review_notes,
    }


def _relation_example(item: ReviewQueueItem) -> dict[str, Any]:
    label = item.corrected_relation_type or item.relation_type
    evidence_tier = item.corrected_evidence_tier if item.corrected_evidence_tier is not None else item.evidence_tier
    return {
        "task": "relation",
        "item_id": item.item_id,
        "source_pmid": item.source_pmid,
        "sentence": item.text,
        "text": item.text,
        "head": item.head,
        "tail": item.tail,
        "label": label,
        "evidence_tier": int(evidence_tier),
        "review_status": item.review_status,
        "reviewer": item.reviewer,
        "review_notes": item.review_notes,
    }


def _ner_examples(entity_jsonl: str | Path) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for result in load_entity_jsonl(entity_jsonl):
        for entity in result.entities:
            examples.append(
                {
                    "task": "ner",
                    "source_pmid": result.pmid,
                    "text": entity.text,
                    "label": entity.label.value,
                    "start": entity.start,
                    "end": entity.end,
                    "confidence": entity.confidence,
                    "normalized_text": entity.normalized_text,
                }
            )
    return examples


def _analyze_task(path: Path, *, task: DatasetTask) -> TaskQuality:
    examples = _read_jsonl(path)
    label_counts: Counter[str] = Counter(str(example.get("label", "")) for example in examples)
    missing_text_count = sum(1 for example in examples if not str(example.get("text") or example.get("sentence") or "").strip())
    missing_offset_count = 0
    if task == "ner":
        missing_offset_count = sum(
            1
            for example in examples
            if example.get("start") is None or example.get("end") is None
        )
    duplicate_count = len(examples) - len({_example_key(example, task) for example in examples})
    warnings: list[str] = []
    if not examples:
        warnings.append("no examples exported")
    if len(label_counts) < 2 and examples:
        warnings.append("fewer than two labels present")
    if missing_text_count:
        warnings.append(f"{missing_text_count} example(s) missing text")
    if missing_offset_count:
        warnings.append(f"{missing_offset_count} NER example(s) missing offsets")
    if duplicate_count:
        warnings.append(f"{duplicate_count} duplicate example(s)")
    return TaskQuality(
        task=task,
        example_count=len(examples),
        label_counts=dict(label_counts),
        missing_text_count=missing_text_count,
        missing_offset_count=missing_offset_count,
        duplicate_count=duplicate_count,
        warnings=warnings,
    )


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _example_key(example: dict[str, Any], task: str) -> tuple[Any, ...]:
    if task == "ner":
        return (example.get("source_pmid"), example.get("start"), example.get("end"), example.get("label"))
    if task == "relation":
        return (example.get("source_pmid"), example.get("head"), example.get("tail"), example.get("label"), example.get("sentence"))
    return (example.get("source_pmid"), example.get("label"), example.get("text"))


def _format_counts(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {key}: {count}" for key, count in sorted(counts.items())]


if __name__ == "__main__":
    raise SystemExit(export_main())
