"""Relation-only training pack builder for GBM-BERT scaffolding."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.preparation import (
    TASK_FILES,
    build_baseline_report,
    build_dataset_card,
    build_label_maps,
    save_baseline_report,
    save_dataset_card,
    split_annotation_dataset_by_pmid,
)
from gbmbert.training.readiness import (
    build_training_readiness_report,
    save_training_readiness_json,
    save_training_readiness_markdown,
)
from gbmbert.training.relation_negatives import NO_RELATION_LABEL
from gbmbert.training.relation_quality import (
    analyze_relation_dataset_quality,
    save_relation_quality_json,
    save_relation_quality_markdown,
)


@dataclass(frozen=True)
class RelationTrainingPackReport:
    input_path: str
    output_dir: str
    reports_dir: str
    relation_rows: int
    positive_rows: int
    negative_rows: int
    annotation_dataset_dir: str
    split_dataset_dir: str
    label_map_dir: str
    ready: bool
    artifacts: dict[str, str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_relation_training_pack(
    input_relation_path: str | Path,
    *,
    output_dir: str | Path,
    reports_dir: str | Path,
    min_examples_per_task: int = 10,
    min_examples_per_label: int = 2,
    seed: int = 13,
) -> RelationTrainingPackReport:
    """Create a relation-only pack with splits, maps, cards, baselines, and quality reports."""

    input_path = Path(input_relation_path)
    output_root = Path(output_dir)
    report_root = Path(reports_dir)
    annotation_dir = output_root / "annotation_dataset"
    split_dir = output_root / "annotation_splits"
    label_map_dir = output_root / "label_maps"
    for directory in (annotation_dir, split_dir, label_map_dir, report_root):
        directory.mkdir(parents=True, exist_ok=True)

    relation_rows = _collect_relation_rows(input_path)
    _write_jsonl([], annotation_dir / TASK_FILES["evidence"])
    _write_jsonl([], annotation_dir / TASK_FILES["ner"])
    _write_jsonl(relation_rows, annotation_dir / TASK_FILES["relation"])

    split_annotation_dataset_by_pmid(annotation_dir, split_dir, seed=seed)
    build_label_maps(split_dir, label_map_dir)

    dataset_card = build_dataset_card(split_dir)
    save_dataset_card(
        dataset_card,
        markdown_output=report_root / "relation_training_pack_dataset_card.md",
        json_output=report_root / "relation_training_pack_dataset_card.json",
    )
    baseline = build_baseline_report(split_dir)
    save_baseline_report(
        baseline,
        markdown_output=report_root / "relation_training_pack_baseline.md",
        json_output=report_root / "relation_training_pack_baseline.json",
    )
    quality = analyze_relation_dataset_quality(split_dir)
    save_relation_quality_json(quality, report_root / "relation_training_pack_quality.json")
    save_relation_quality_markdown(quality, report_root / "relation_training_pack_quality.md")
    readiness = build_training_readiness_report(
        split_dir,
        min_examples_per_task=min_examples_per_task,
        min_examples_per_label=min_examples_per_label,
        tasks=("relation",),
    )
    save_training_readiness_json(readiness, report_root / "relation_training_pack_readiness.json")
    save_training_readiness_markdown(readiness, report_root / "relation_training_pack_readiness.md")

    positive_rows = sum(1 for row in relation_rows if _label_text(row) and _label_text(row) != NO_RELATION_LABEL)
    negative_rows = sum(1 for row in relation_rows if _label_text(row) == NO_RELATION_LABEL)
    warnings = list(dict.fromkeys([*quality.warnings, *readiness.warnings]))
    if not relation_rows:
        warnings.append("no relation examples found")
    if not positive_rows and "no positive relation examples found" not in warnings:
        warnings.append("no positive relation examples found")
    if not negative_rows and "no NO_RELATION negative examples found" not in warnings:
        warnings.append("no NO_RELATION negative examples found")
    ready = readiness.ready and positive_rows > 0 and negative_rows > 0 and not quality.warnings
    artifacts = {
        "dataset_card_json": str(report_root / "relation_training_pack_dataset_card.json"),
        "dataset_card_md": str(report_root / "relation_training_pack_dataset_card.md"),
        "baseline_json": str(report_root / "relation_training_pack_baseline.json"),
        "baseline_md": str(report_root / "relation_training_pack_baseline.md"),
        "relation_quality_json": str(report_root / "relation_training_pack_quality.json"),
        "relation_quality_md": str(report_root / "relation_training_pack_quality.md"),
        "training_readiness_json": str(report_root / "relation_training_pack_readiness.json"),
        "training_readiness_md": str(report_root / "relation_training_pack_readiness.md"),
        "label_maps_manifest": str(label_map_dir / "label_maps_manifest.json"),
    }
    report = RelationTrainingPackReport(
        input_path=str(input_path),
        output_dir=str(output_root),
        reports_dir=str(report_root),
        relation_rows=len(relation_rows),
        positive_rows=positive_rows,
        negative_rows=negative_rows,
        annotation_dataset_dir=str(annotation_dir),
        split_dataset_dir=str(split_dir),
        label_map_dir=str(label_map_dir),
        ready=ready,
        artifacts=artifacts,
        warnings=warnings,
    )
    save_relation_training_pack_json(report, report_root / "relation_training_pack.json")
    save_relation_training_pack_markdown(report, report_root / "relation_training_pack.md")
    return report


def save_relation_training_pack_json(report: RelationTrainingPackReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_relation_training_pack_markdown(report: RelationTrainingPackReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_relation_training_pack_markdown(report), encoding="utf-8")
    return output


def format_relation_training_pack_markdown(report: RelationTrainingPackReport) -> str:
    lines = [
        "# GBM-BERT Relation Training Pack",
        "",
        RESEARCH_WARNING,
        "",
        f"- Input: `{report.input_path}`",
        f"- Output directory: `{report.output_dir}`",
        f"- Reports directory: `{report.reports_dir}`",
        f"- Relation examples: {report.relation_rows}",
        f"- Positive examples: {report.positive_rows}",
        f"- Negative examples: {report.negative_rows}",
        f"- Ready: {report.ready}",
        "",
        "## Artifacts",
        f"- Annotation dataset: `{report.annotation_dataset_dir}`",
        f"- Splits: `{report.split_dataset_dir}`",
        f"- Label maps: `{report.label_map_dir}`",
        *[f"- {name}: `{path}`" for name, path in sorted(report.artifacts.items())],
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a relation-only GBM-BERT training pack.")
    parser.add_argument("input_relation_path", type=Path, help="Merged relation JSONL file or dataset directory.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reports-dir", type=Path, required=True)
    parser.add_argument("--min-examples-per-task", type=int, default=10)
    parser.add_argument("--min-examples-per-label", type=int, default=2)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-not-ready", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_relation_training_pack(
        args.input_relation_path,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        min_examples_per_task=args.min_examples_per_task,
        min_examples_per_label=args.min_examples_per_label,
        seed=args.seed,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_relation_training_pack_markdown(report))
    return 0 if report.ready or args.allow_not_ready else 1


def _collect_relation_rows(input_path: Path) -> list[dict[str, Any]]:
    if input_path.is_file():
        return _read_jsonl(input_path)
    rows: list[dict[str, Any]] = []
    base = input_path / TASK_FILES["relation"]
    if base.exists():
        rows.extend(_read_jsonl(base))
    for split in ("train", "validation", "test"):
        path = input_path / f"relation_{split}.jsonl"
        if path.exists():
            rows.extend(_read_jsonl(path))
    return rows


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


def _label_text(row: dict[str, Any]) -> str:
    return str(row.get("label") or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
