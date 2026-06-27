"""Evidence-only training pack builder for GBM-BERT scaffolding."""

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
    repair_evidence_labels,
    save_baseline_report,
    save_dataset_card,
    split_annotation_dataset_by_pmid,
)
from gbmbert.training.readiness import (
    build_training_readiness_report,
    save_training_readiness_json,
    save_training_readiness_markdown,
)


@dataclass(frozen=True)
class EvidenceTrainingPackReport:
    input_dir: str
    output_dir: str
    reports_dir: str
    evidence_rows: int
    annotation_dataset_dir: str
    repaired_dataset_dir: str
    split_dataset_dir: str
    label_map_dir: str
    ready: bool
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_evidence_training_pack(
    input_dataset_dir: str | Path,
    *,
    output_dir: str | Path,
    reports_dir: str | Path,
    min_examples_per_task: int = 10,
    min_examples_per_label: int = 2,
    seed: int = 13,
) -> EvidenceTrainingPackReport:
    """Create an evidence-only pack with splits, label maps, cards, baselines, and readiness."""

    input_root = Path(input_dataset_dir)
    output_root = Path(output_dir)
    report_root = Path(reports_dir)
    annotation_dir = output_root / "annotation_dataset"
    repaired_dir = output_root / "annotation_dataset_repaired"
    split_dir = output_root / "annotation_splits"
    label_map_dir = output_root / "label_maps"
    for directory in (annotation_dir, repaired_dir, split_dir, label_map_dir, report_root):
        directory.mkdir(parents=True, exist_ok=True)

    evidence_rows = _collect_evidence_rows(input_root)
    _write_jsonl(evidence_rows, annotation_dir / TASK_FILES["evidence"])
    _write_jsonl([], annotation_dir / TASK_FILES["ner"])
    _write_jsonl([], annotation_dir / TASK_FILES["relation"])

    repair_evidence_labels(annotation_dir, repaired_dir)
    split_annotation_dataset_by_pmid(repaired_dir, split_dir, seed=seed)
    build_label_maps(split_dir, label_map_dir)

    dataset_card = build_dataset_card(split_dir)
    save_dataset_card(
        dataset_card,
        markdown_output=report_root / "evidence_training_pack_dataset_card.md",
        json_output=report_root / "evidence_training_pack_dataset_card.json",
    )
    baseline = build_baseline_report(split_dir)
    save_baseline_report(
        baseline,
        markdown_output=report_root / "evidence_training_pack_baseline.md",
        json_output=report_root / "evidence_training_pack_baseline.json",
    )
    readiness = build_training_readiness_report(
        split_dir,
        min_examples_per_task=min_examples_per_task,
        min_examples_per_label=min_examples_per_label,
        tasks=("evidence",),
    )
    save_training_readiness_json(readiness, report_root / "evidence_training_pack_readiness.json")
    save_training_readiness_markdown(readiness, report_root / "evidence_training_pack_readiness.md")

    warnings = list(readiness.warnings)
    if not evidence_rows:
        warnings.append("no evidence examples found")
    report = EvidenceTrainingPackReport(
        input_dir=str(input_root),
        output_dir=str(output_root),
        reports_dir=str(report_root),
        evidence_rows=len(evidence_rows),
        annotation_dataset_dir=str(annotation_dir),
        repaired_dataset_dir=str(repaired_dir),
        split_dataset_dir=str(split_dir),
        label_map_dir=str(label_map_dir),
        ready=readiness.ready,
        warnings=warnings,
    )
    save_evidence_training_pack_json(report, report_root / "evidence_training_pack.json")
    save_evidence_training_pack_markdown(report, report_root / "evidence_training_pack.md")
    return report


def save_evidence_training_pack_json(report: EvidenceTrainingPackReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_evidence_training_pack_markdown(report: EvidenceTrainingPackReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_evidence_training_pack_markdown(report), encoding="utf-8")
    return output


def format_evidence_training_pack_markdown(report: EvidenceTrainingPackReport) -> str:
    lines = [
        "# GBM-BERT Evidence Training Pack",
        "",
        RESEARCH_WARNING,
        "",
        f"- Input directory: `{report.input_dir}`",
        f"- Output directory: `{report.output_dir}`",
        f"- Reports directory: `{report.reports_dir}`",
        f"- Evidence examples: {report.evidence_rows}",
        f"- Ready: {report.ready}",
        "",
        "## Artifacts",
        f"- Annotation dataset: `{report.annotation_dataset_dir}`",
        f"- Repaired dataset: `{report.repaired_dataset_dir}`",
        f"- Splits: `{report.split_dataset_dir}`",
        f"- Label maps: `{report.label_map_dir}`",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an evidence-only GBM-BERT training pack.")
    parser.add_argument("input_dataset_dir", type=Path)
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
    report = build_evidence_training_pack(
        args.input_dataset_dir,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        min_examples_per_task=args.min_examples_per_task,
        min_examples_per_label=args.min_examples_per_label,
        seed=args.seed,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_evidence_training_pack_markdown(report))
    return 0 if report.ready or args.allow_not_ready else 1


def _collect_evidence_rows(input_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if input_root.is_file():
        return _read_jsonl(input_root)
    base = input_root / TASK_FILES["evidence"]
    if base.exists():
        rows.extend(_read_jsonl(base))
    for split in ("train", "validation", "test"):
        path = input_root / f"evidence_{split}.jsonl"
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
