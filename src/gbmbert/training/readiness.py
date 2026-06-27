"""Training data readiness gate for GBM-BERT datasets."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


@dataclass(frozen=True)
class TaskReadiness:
    task: str
    example_count: int
    label_counts: dict[str, int]
    duplicate_count: int
    invalid_ner_span_count: int
    dominant_label_fraction: float | None
    ready: bool
    warnings: list[str]


@dataclass(frozen=True)
class TrainingReadinessReport:
    dataset_dir: str
    min_examples_per_task: int
    min_examples_per_label: int
    task_reports: list[TaskReadiness]
    leakage_warnings: list[str]
    warning_count: int
    ready: bool
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_training_readiness_report(
    dataset_dir: str | Path,
    *,
    min_examples_per_task: int = 10,
    min_examples_per_label: int = 2,
    max_label_fraction: float = 0.85,
    tasks: tuple[str, ...] | list[str] | None = None,
) -> TrainingReadinessReport:
    """Assess whether exported or split annotation datasets are ready for real training."""

    root = Path(dataset_dir)
    selected_tasks = tuple(tasks or ("ner", "evidence", "relation"))
    rows_by_task: dict[str, list[dict[str, Any]]] = {task: [] for task in selected_tasks}
    split_pmids: dict[str, set[str]] = defaultdict(set)
    warnings: list[str] = []
    for path in sorted(root.glob("*.jsonl")):
        task = _task_for_path(path)
        if task is None or task not in rows_by_task:
            continue
        split = _split_for_path(path)
        for row in _read_jsonl(path):
            rows_by_task[task].append(row)
            pmid = str(row.get("source_pmid") or "")
            if split and pmid:
                split_pmids[split].add(pmid)
    task_reports: list[TaskReadiness] = []
    for task, rows in rows_by_task.items():
        task_warnings: list[str] = []
        label_counts = Counter(_label_text(row) for row in rows)
        duplicate_count = _duplicate_count(rows, task)
        invalid_ner_span_count = _invalid_ner_span_count(rows) if task == "ner" else 0
        dominant_label_fraction = _dominant_label_fraction(label_counts, len(rows))
        if "" in label_counts:
            task_warnings.append("one or more examples are missing labels")
        if len(rows) < min_examples_per_task:
            task_warnings.append(f"fewer than {min_examples_per_task} examples")
        for label, count in sorted(label_counts.items()):
            if label and count < min_examples_per_label:
                task_warnings.append(f"label {label} has fewer than {min_examples_per_label} examples")
        if duplicate_count:
            task_warnings.append(f"{duplicate_count} duplicate example(s)")
        if invalid_ner_span_count:
            task_warnings.append(f"{invalid_ner_span_count} invalid NER span(s)")
        if dominant_label_fraction is not None and dominant_label_fraction > max_label_fraction and len(label_counts) > 1:
            task_warnings.append(f"dominant label fraction {dominant_label_fraction:.3f} exceeds {max_label_fraction:.3f}")
        task_reports.append(
            TaskReadiness(
                task=task,
                example_count=len(rows),
                label_counts=dict(sorted(label_counts.items())),
                duplicate_count=duplicate_count,
                invalid_ner_span_count=invalid_ner_span_count,
                dominant_label_fraction=dominant_label_fraction,
                ready=not task_warnings,
                warnings=task_warnings,
            )
        )
        warnings.extend(f"{task}: {warning}" for warning in task_warnings)
    leakage_warnings = _split_leakage_warnings(split_pmids)
    warnings.extend(leakage_warnings)
    return TrainingReadinessReport(
        dataset_dir=str(root),
        min_examples_per_task=min_examples_per_task,
        min_examples_per_label=min_examples_per_label,
        task_reports=task_reports,
        leakage_warnings=leakage_warnings,
        warning_count=len(warnings),
        ready=not warnings,
        warnings=warnings,
    )


def save_training_readiness_json(report: TrainingReadinessReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_training_readiness_markdown(report: TrainingReadinessReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_training_readiness_markdown(report), encoding="utf-8")
    return output


def format_training_readiness_markdown(report: TrainingReadinessReport) -> str:
    lines = [
        "# GBM-BERT Training Readiness Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Dataset directory: `{report.dataset_dir}`",
        f"- Ready: {report.ready}",
        f"- Warnings: {report.warning_count}",
        f"- Minimum examples per task: {report.min_examples_per_task}",
        f"- Minimum examples per label: {report.min_examples_per_label}",
        "",
        "## Tasks",
    ]
    for task in report.task_reports:
        lines.extend(
            [
                f"### {task.task}",
                f"- Ready: {task.ready}",
                f"- Examples: {task.example_count}",
                f"- Duplicates: {task.duplicate_count}",
                f"- Invalid NER spans: {task.invalid_ner_span_count}",
                f"- Dominant label fraction: {_format_fraction(task.dominant_label_fraction)}",
                "- Labels:",
                *([f"- {label or '<missing>'}: {count}" for label, count in task.label_counts.items()] or ["- none"]),
                "- Warnings:",
                *([f"- {warning}" for warning in task.warnings] if task.warnings else ["- none"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Leakage",
            *([f"- {warning}" for warning in report.leakage_warnings] if report.leakage_warnings else ["- none"]),
            "",
            "## Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gate GBM-BERT datasets for real training readiness.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--min-examples-per-task", type=int, default=10)
    parser.add_argument("--min-examples-per-label", type=int, default=2)
    parser.add_argument("--max-label-fraction", type=float, default=0.85)
    parser.add_argument("--task", choices=("ner", "evidence", "relation"), action="append")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-not-ready", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_training_readiness_report(
        args.dataset_dir,
        min_examples_per_task=args.min_examples_per_task,
        min_examples_per_label=args.min_examples_per_label,
        max_label_fraction=args.max_label_fraction,
        tasks=tuple(args.task) if args.task else None,
    )
    if args.json_output:
        save_training_readiness_json(report, args.json_output)
    if args.markdown_output:
        save_training_readiness_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_training_readiness_markdown(report))
    return 0 if report.ready or args.allow_not_ready else 1


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
    return rows


def _task_for_path(path: Path) -> str | None:
    name = path.name.casefold()
    if "ner" in name:
        return "ner"
    if "evidence" in name:
        return "evidence"
    if "relation" in name:
        return "relation"
    return None


def _split_for_path(path: Path) -> str | None:
    name = path.name.casefold()
    for split in ("train", "validation", "test"):
        if split in name:
            return split
    return None


def _split_leakage_warnings(split_pmids: dict[str, set[str]]) -> list[str]:
    warnings: list[str] = []
    splits = sorted(split_pmids)
    for left_index, left in enumerate(splits):
        for right in splits[left_index + 1 :]:
            overlap = split_pmids[left] & split_pmids[right]
            if overlap:
                warnings.append(f"{len(overlap)} PMID(s) appear in both {left} and {right}: {', '.join(sorted(overlap)[:5])}")
    return warnings


def _label_text(row: dict[str, Any]) -> str:
    value = row.get("label")
    if value is None:
        return ""
    return str(value).strip()


def _duplicate_count(rows: list[dict[str, Any]], task: str) -> int:
    if task == "ner":
        keys = [
            (row.get("source_pmid"), row.get("start"), row.get("end"), row.get("label"), row.get("text"))
            for row in rows
        ]
    elif task == "relation":
        keys = [
            (row.get("source_pmid"), row.get("head"), row.get("tail"), row.get("label"), row.get("sentence") or row.get("text"))
            for row in rows
        ]
    else:
        keys = [(row.get("source_pmid"), row.get("label"), row.get("text")) for row in rows]
    return len(keys) - len(set(json.dumps(key, sort_keys=True, default=str) for key in keys))


def _invalid_ner_span_count(rows: list[dict[str, Any]]) -> int:
    invalid = 0
    for row in rows:
        text = str(row.get("text") or "")
        start = row.get("start")
        end = row.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
            invalid += 1
            continue
        if text and end - start <= 0:
            invalid += 1
    return invalid


def _dominant_label_fraction(label_counts: Counter[str], total: int) -> float | None:
    counts = [count for label, count in label_counts.items() if label]
    if not counts or total <= 0:
        return None
    return max(counts) / total


def _format_fraction(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


if __name__ == "__main__":
    raise SystemExit(main())
