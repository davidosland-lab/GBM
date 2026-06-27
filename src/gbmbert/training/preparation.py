"""Dataset preparation reports for future GBM-BERT experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.config import load_training_config

LOGGER = logging.getLogger(__name__)

TASK_FILES = {
    "ner": "ner.jsonl",
    "evidence": "evidence.jsonl",
    "relation": "relations.jsonl",
}
SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class SplitTaskSummary:
    task: str
    source_file: str
    split_files: dict[str, str]
    split_counts: dict[str, int]
    label_counts: dict[str, dict[str, int]]


@dataclass(frozen=True)
class SplitManifest:
    input_dir: str
    output_dir: str
    seed: int
    ratios: dict[str, float]
    tasks: list[SplitTaskSummary]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PmidSplitManifest:
    input_dir: str
    output_dir: str
    seed: int
    ratios: dict[str, float]
    pmid_counts: dict[str, int]
    tasks: list[SplitTaskSummary]
    leakage_warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LabelMapSummary:
    dataset_dir: str
    output_dir: str
    files: dict[str, str]
    labels: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetCard:
    dataset_dir: str
    files: dict[str, dict[str, Any]]
    total_examples: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BaselineTaskReport:
    task: str
    evaluation_file: str
    examples: int
    majority_label: str | None
    majority_accuracy: float | None
    label_counts: dict[str, int]


@dataclass(frozen=True)
class BaselineReport:
    dataset_dir: str
    tasks: list[BaselineTaskReport]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceLabelRepairTask:
    source_file: str
    output_file: str
    row_count: int
    changed_count: int
    skipped_count: int
    label_counts: dict[str, int]


@dataclass(frozen=True)
class EvidenceLabelRepairReport:
    input_dir: str
    output_dir: str
    tasks: list[EvidenceLabelRepairTask]
    changed_count: int
    skipped_count: int
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentManifest:
    config_path: str
    dataset_dir: str
    label_map_dir: str | None
    output_dir: str
    task: str
    base_model: str
    training_enabled: bool
    checks: dict[str, bool]
    artifacts: dict[str, str]
    warning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def split_annotation_dataset(
    dataset_dir: str | Path,
    output_dir: str | Path,
    *,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 13,
) -> SplitManifest:
    """Create deterministic train/validation/test JSONL splits for exported annotation datasets."""

    _validate_ratios(train_ratio, validation_ratio, test_ratio)
    input_root = Path(dataset_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    task_summaries: list[SplitTaskSummary] = []
    for task, filename in TASK_FILES.items():
        source_file = input_root / filename
        rows = _read_jsonl(source_file)
        split_rows = _stratified_split(
            rows,
            seed=seed,
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            test_ratio=test_ratio,
        )
        split_files: dict[str, str] = {}
        split_counts: dict[str, int] = {}
        label_counts: dict[str, dict[str, int]] = {}
        for split_name in SPLITS:
            path = output_root / f"{task}_{split_name}.jsonl"
            _write_jsonl(split_rows[split_name], path)
            split_files[split_name] = str(path)
            split_counts[split_name] = len(split_rows[split_name])
            label_counts[split_name] = _count_labels(split_rows[split_name])
        task_summaries.append(
            SplitTaskSummary(
                task=task,
                source_file=str(source_file),
                split_files=split_files,
                split_counts=split_counts,
                label_counts=label_counts,
            )
        )
    manifest = SplitManifest(
        input_dir=str(input_root),
        output_dir=str(output_root),
        seed=seed,
        ratios={"train": train_ratio, "validation": validation_ratio, "test": test_ratio},
        tasks=task_summaries,
    )
    (output_root / "split_manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def split_annotation_dataset_by_pmid(
    dataset_dir: str | Path,
    output_dir: str | Path,
    *,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 13,
) -> PmidSplitManifest:
    """Create train/validation/test splits that keep each PMID in exactly one split."""

    _validate_ratios(train_ratio, validation_ratio, test_ratio)
    input_root = Path(dataset_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    rows_by_task: dict[str, list[dict[str, Any]]] = {}
    pmids: set[str] = set()
    for task, filename in TASK_FILES.items():
        rows = _read_jsonl(input_root / filename)
        rows_by_task[task] = rows
        pmids.update(_row_pmid(row) for row in rows if _row_pmid(row))

    pmid_splits = _split_pmids(
        sorted(pmids),
        seed=seed,
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
    )
    split_by_pmid = {pmid: split for split, split_pmids in pmid_splits.items() for pmid in split_pmids}
    task_summaries: list[SplitTaskSummary] = []
    leakage_warnings: list[str] = []
    for task, rows in rows_by_task.items():
        split_rows = {split: [] for split in SPLITS}
        for row in rows:
            split_name = split_by_pmid.get(_row_pmid(row), "train")
            split_rows[split_name].append(row)
        split_files: dict[str, str] = {}
        split_counts: dict[str, int] = {}
        label_counts: dict[str, dict[str, int]] = {}
        for split_name in SPLITS:
            path = output_root / f"{task}_{split_name}.jsonl"
            ordered = sorted(split_rows[split_name], key=lambda row: json.dumps(row, sort_keys=True))
            _write_jsonl(ordered, path)
            split_files[split_name] = str(path)
            split_counts[split_name] = len(ordered)
            label_counts[split_name] = _count_labels(ordered)
        task_summaries.append(
            SplitTaskSummary(
                task=task,
                source_file=str(input_root / TASK_FILES[task]),
                split_files=split_files,
                split_counts=split_counts,
                label_counts=label_counts,
            )
        )
    leakage_warnings = _split_leakage_warnings(output_root)
    manifest = PmidSplitManifest(
        input_dir=str(input_root),
        output_dir=str(output_root),
        seed=seed,
        ratios={"train": train_ratio, "validation": validation_ratio, "test": test_ratio},
        pmid_counts={split: len(values) for split, values in pmid_splits.items()},
        tasks=task_summaries,
        leakage_warnings=leakage_warnings,
    )
    (output_root / "pmid_split_manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def repair_evidence_labels(dataset_dir: str | Path, output_dir: str | Path) -> EvidenceLabelRepairReport:
    """Copy dataset files while filling missing evidence labels from evidence-tier fields."""

    input_root = Path(dataset_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    tasks: list[EvidenceLabelRepairTask] = []
    warnings: list[str] = []
    changed_total = 0
    skipped_total = 0
    for path in _dataset_jsonl_files(input_root):
        rows = _read_jsonl(path)
        output_rows: list[dict[str, Any]] = []
        changed = 0
        skipped = 0
        for row in rows:
            repaired = dict(row)
            if _task_for_dataset_path(path) == "evidence" and not _row_has_label(repaired):
                label = _evidence_label_from_row(repaired)
                if label is None:
                    skipped += 1
                else:
                    repaired["label"] = label
                    changed += 1
            output_rows.append(repaired)
        output_path = output_root / path.name
        _write_jsonl(output_rows, output_path)
        tasks.append(
            EvidenceLabelRepairTask(
                source_file=str(path),
                output_file=str(output_path),
                row_count=len(rows),
                changed_count=changed,
                skipped_count=skipped,
                label_counts=_count_labels(output_rows),
            )
        )
        changed_total += changed
        skipped_total += skipped
    if skipped_total:
        warnings.append(f"{skipped_total} evidence row(s) still missing a repairable label")
    report = EvidenceLabelRepairReport(
        input_dir=str(input_root),
        output_dir=str(output_root),
        tasks=tasks,
        changed_count=changed_total,
        skipped_count=skipped_total,
        warnings=warnings,
    )
    (output_root / "evidence_label_repair.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_root / "evidence_label_repair.md").write_text(format_evidence_label_repair_markdown(report), encoding="utf-8")
    return report


def build_label_maps(dataset_dir: str | Path, output_dir: str | Path) -> LabelMapSummary:
    """Build stable label-to-id maps from annotation dataset JSONL files."""

    root = Path(dataset_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    labels_by_task: dict[str, dict[str, int]] = {}
    for task in TASK_FILES:
        labels = sorted(_collect_task_labels(root, task))
        label_to_id = {label: index for index, label in enumerate(labels)}
        payload = {"task": task, "label_to_id": label_to_id, "id_to_label": {str(v): k for k, v in label_to_id.items()}}
        output_path = output_root / f"{task}_label_map.json"
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        files[task] = str(output_path)
        labels_by_task[task] = label_to_id
    summary = LabelMapSummary(dataset_dir=str(root), output_dir=str(output_root), files=files, labels=labels_by_task)
    (output_root / "label_maps_manifest.json").write_text(
        json.dumps(summary.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def build_dataset_card(dataset_dir: str | Path) -> DatasetCard:
    """Summarize annotation dataset files for handoff and training review."""

    root = Path(dataset_dir)
    file_summaries: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for path in _dataset_jsonl_files(root):
        rows = _read_jsonl(path)
        label_counts = _count_labels(rows)
        text_missing = sum(1 for row in rows if not str(row.get("text") or row.get("sentence") or "").strip())
        relative = path.name
        file_summaries[relative] = {
            "examples": len(rows),
            "label_counts": label_counts,
            "missing_text": text_missing,
            "sha256": _sha256_file(path),
        }
        if not rows:
            warnings.append(f"{relative}: no examples")
        if text_missing:
            warnings.append(f"{relative}: {text_missing} example(s) missing text")
    return DatasetCard(
        dataset_dir=str(root),
        files=file_summaries,
        total_examples=sum(file_summary["examples"] for file_summary in file_summaries.values()),
        warnings=warnings,
    )


def format_dataset_card_markdown(card: DatasetCard) -> str:
    warning_lines = [f"- {warning}" for warning in card.warnings] if card.warnings else ["- none"]
    lines = [
        "# GBM-BERT Dataset Card",
        "",
        RESEARCH_WARNING,
        "",
        f"- Dataset directory: `{card.dataset_dir}`",
        f"- Total examples: {card.total_examples}",
        "",
        "## Files",
    ]
    for filename, summary in sorted(card.files.items()):
        lines.extend(
            [
                f"### {filename}",
                f"- Examples: {summary['examples']}",
                f"- Missing text: {summary['missing_text']}",
                f"- SHA256: `{summary['sha256']}`",
                "- Labels:",
                *_format_counts(summary["label_counts"]),
                "",
            ]
        )
    lines.extend(["## Warnings", *warning_lines])
    return "\n".join(lines).rstrip() + "\n"


def save_dataset_card(card: DatasetCard, *, markdown_output: str | Path | None = None, json_output: str | Path | None = None) -> None:
    if markdown_output:
        output = Path(markdown_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(format_dataset_card_markdown(card), encoding="utf-8")
    if json_output:
        output = Path(json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(card.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def build_baseline_report(dataset_dir: str | Path) -> BaselineReport:
    """Build majority-label baselines for future model comparison."""

    root = Path(dataset_dir)
    reports: list[BaselineTaskReport] = []
    warnings: list[str] = []
    for task in TASK_FILES:
        evaluation_file = _preferred_evaluation_file(root, task)
        rows = _read_jsonl(evaluation_file)
        label_counts = _count_labels(rows)
        majority_label = None
        majority_accuracy = None
        if rows and label_counts:
            majority_label, majority_count = max(label_counts.items(), key=lambda item: (item[1], item[0]))
            majority_accuracy = majority_count / len(rows)
        else:
            warnings.append(f"{task}: no evaluation examples")
        reports.append(
            BaselineTaskReport(
                task=task,
                evaluation_file=str(evaluation_file),
                examples=len(rows),
                majority_label=majority_label,
                majority_accuracy=majority_accuracy,
                label_counts=label_counts,
            )
        )
    return BaselineReport(dataset_dir=str(root), tasks=reports, warnings=warnings)


def format_baseline_report_markdown(report: BaselineReport) -> str:
    warning_lines = [f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]
    lines = [
        "# GBM-BERT Baseline Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Dataset directory: `{report.dataset_dir}`",
        "",
        "## Majority-Label Baselines",
    ]
    for task in report.tasks:
        accuracy = "n/a" if task.majority_accuracy is None else f"{task.majority_accuracy:.3f}"
        lines.extend(
            [
                f"### {task.task}",
                f"- Evaluation file: `{task.evaluation_file}`",
                f"- Examples: {task.examples}",
                f"- Majority label: {task.majority_label or 'n/a'}",
                f"- Majority accuracy: {accuracy}",
                "- Labels:",
                *_format_counts(task.label_counts),
                "",
            ]
        )
    lines.extend(["## Warnings", *warning_lines])
    return "\n".join(lines).rstrip() + "\n"


def save_baseline_report(report: BaselineReport, *, markdown_output: str | Path | None = None, json_output: str | Path | None = None) -> None:
    if markdown_output:
        output = Path(markdown_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(format_baseline_report_markdown(report), encoding="utf-8")
    if json_output:
        output = Path(json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def format_pmid_split_markdown(manifest: PmidSplitManifest) -> str:
    lines = [
        "# GBM-BERT PMID-Safe Split Manifest",
        "",
        RESEARCH_WARNING,
        "",
        f"- Input directory: `{manifest.input_dir}`",
        f"- Output directory: `{manifest.output_dir}`",
        f"- Seed: {manifest.seed}",
        "",
        "## PMIDs",
        *_format_counts(manifest.pmid_counts),
        "",
        "## Tasks",
    ]
    for task in manifest.tasks:
        lines.extend(
            [
                f"### {task.task}",
                "- Split counts:",
                *_format_counts(task.split_counts),
                "",
            ]
        )
    lines.extend(
        [
            "## Leakage",
            *([f"- {warning}" for warning in manifest.leakage_warnings] if manifest.leakage_warnings else ["- none"]),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def format_evidence_label_repair_markdown(report: EvidenceLabelRepairReport) -> str:
    lines = [
        "# GBM-BERT Evidence Label Repair Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Input directory: `{report.input_dir}`",
        f"- Output directory: `{report.output_dir}`",
        f"- Changed rows: {report.changed_count}",
        f"- Skipped rows: {report.skipped_count}",
        "",
        "## Files",
    ]
    for task in report.tasks:
        lines.extend(
            [
                f"### {Path(task.output_file).name}",
                f"- Rows: {task.row_count}",
                f"- Changed: {task.changed_count}",
                f"- Skipped: {task.skipped_count}",
                "- Labels:",
                *_format_counts(task.label_counts),
                "",
            ]
        )
    lines.extend(["## Warnings", *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"])])
    return "\n".join(lines).rstrip() + "\n"


def build_experiment_manifest(
    config_path: str | Path,
    dataset_dir: str | Path,
    *,
    label_map_dir: str | Path | None = None,
) -> ExperimentManifest:
    """Tie a training config to prepared data and label maps without starting training."""

    config_file = Path(config_path)
    dataset_root = Path(dataset_dir)
    config = load_training_config(config_file)
    label_root = Path(label_map_dir) if label_map_dir else None
    task_file = _preferred_evaluation_file(dataset_root, _config_task_name(config.task.value))
    artifacts = {
        "config_sha256": _sha256_file(config_file),
        "dataset_dir": str(dataset_root),
    }
    if task_file.exists():
        artifacts["evaluation_file"] = str(task_file)
        artifacts["evaluation_file_sha256"] = _sha256_file(task_file)
    if label_root is not None:
        label_map = label_root / f"{_config_task_name(config.task.value)}_label_map.json"
        artifacts["label_map"] = str(label_map)
        if label_map.exists():
            artifacts["label_map_sha256"] = _sha256_file(label_map)
    checks = {
        "config_exists": config_file.exists(),
        "dataset_dir_exists": dataset_root.exists(),
        "evaluation_file_exists": task_file.exists(),
        "label_map_exists": (label_root / f"{_config_task_name(config.task.value)}_label_map.json").exists()
        if label_root is not None
        else False,
        "training_enabled": config.is_training_enabled,
    }
    return ExperimentManifest(
        config_path=str(config_file),
        dataset_dir=str(dataset_root),
        label_map_dir=str(label_root) if label_root is not None else None,
        output_dir=str(config.output_dir),
        task=config.task.value,
        base_model=config.base_model,
        training_enabled=config.is_training_enabled,
        checks=checks,
        artifacts=artifacts,
        warning=RESEARCH_WARNING,
    )


def save_experiment_manifest(manifest: ExperimentManifest, output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def split_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split exported GBM-BERT annotation datasets.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    manifest = split_annotation_dataset(
        args.dataset_dir,
        args.output_dir,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    LOGGER.info("Wrote split manifest to %s", Path(manifest.output_dir) / "split_manifest.json")
    return 0


def pmid_split_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split GBM-BERT annotation datasets while keeping source PMIDs in one split.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    manifest = split_annotation_dataset_by_pmid(
        args.dataset_dir,
        args.output_dir,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(format_pmid_split_markdown(manifest), encoding="utf-8")
    if args.json:
        print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_pmid_split_markdown(manifest))
    return 0 if not manifest.leakage_warnings else 1


def repair_evidence_labels_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair missing evidence labels in GBM-BERT dataset JSONL files.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-unrepaired", action="store_true")
    args = parser.parse_args(argv)
    report = repair_evidence_labels(args.dataset_dir, args.output_dir)
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(format_evidence_label_repair_markdown(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_evidence_label_repair_markdown(report))
    return 0 if report.skipped_count == 0 or args.allow_unrepaired else 1


def label_maps_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build GBM-BERT label maps from annotation datasets.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    summary = build_label_maps(args.dataset_dir, args.output_dir)
    LOGGER.info("Wrote label-map manifest to %s", Path(summary.output_dir) / "label_maps_manifest.json")
    return 0


def dataset_card_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a GBM-BERT dataset card.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    card = build_dataset_card(args.dataset_dir)
    save_dataset_card(card, markdown_output=args.markdown_output, json_output=args.json_output)
    if args.json:
        print(json.dumps(card.to_dict(), indent=2, sort_keys=True))
    elif not args.markdown_output:
        print(format_dataset_card_markdown(card))
    return 0


def baseline_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build majority-label baseline reports for GBM-BERT datasets.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = build_baseline_report(args.dataset_dir)
    save_baseline_report(report, markdown_output=args.markdown_output, json_output=args.json_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    elif not args.markdown_output:
        print(format_baseline_report_markdown(report))
    return 0


def experiment_manifest_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a no-training GBM-BERT experiment manifest.")
    parser.add_argument("config", type=Path)
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label-map-dir", type=Path)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    manifest = build_experiment_manifest(args.config, args.dataset_dir, label_map_dir=args.label_map_dir)
    save_experiment_manifest(manifest, args.output)
    LOGGER.info("Wrote experiment manifest to %s", args.output)
    return 0


def _validate_ratios(train_ratio: float, validation_ratio: float, test_ratio: float) -> None:
    ratios = [train_ratio, validation_ratio, test_ratio]
    if any(ratio < 0 for ratio in ratios):
        raise ValueError("split ratios must be non-negative")
    if abs(sum(ratios) - 1.0) > 0.000001:
        raise ValueError("split ratios must sum to 1.0")


def _stratified_split(
    rows: list[dict[str, Any]],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("label", ""))].append(row)
    splits = {split: [] for split in SPLITS}
    for label, label_rows in sorted(grouped.items()):
        label_seed = seed + int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(label_seed)
        ordered = sorted(label_rows, key=lambda row: json.dumps(row, sort_keys=True))
        rng.shuffle(ordered)
        counts = _split_counts(
            len(ordered),
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            test_ratio=test_ratio,
        )
        start = 0
        for split_name in SPLITS:
            count = counts[split_name]
            splits[split_name].extend(ordered[start : start + count])
            start += count
    _rebalance_empty_splits(splits, total=len(rows))
    for split_rows in splits.values():
        split_rows.sort(key=lambda row: json.dumps(row, sort_keys=True))
    return splits


def _split_counts(
    total: int,
    *,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> dict[str, int]:
    if total <= 0:
        return {"train": 0, "validation": 0, "test": 0}
    if total == 1:
        return {"train": 1, "validation": 0, "test": 0}
    if total == 2:
        return {"train": 1, "validation": 1, "test": 0}
    validation = max(1, round(total * validation_ratio)) if validation_ratio > 0 else 0
    test = max(1, round(total * test_ratio)) if test_ratio > 0 else 0
    train = max(1, total - validation - test)
    while train + validation + test > total:
        if train >= validation and train >= test and train > 1:
            train -= 1
        elif validation >= test and validation > 0:
            validation -= 1
        elif test > 0:
            test -= 1
        else:
            break
    return {"train": train, "validation": validation, "test": test}


def _rebalance_empty_splits(splits: dict[str, list[dict[str, Any]]], *, total: int) -> None:
    if total < len(SPLITS):
        return
    for split_name in SPLITS:
        if splits[split_name]:
            continue
        donor = max(SPLITS, key=lambda name: len(splits[name]))
        if len(splits[donor]) <= 1:
            continue
        splits[split_name].append(splits[donor].pop())


def _split_pmids(
    pmids: list[str],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> dict[str, set[str]]:
    ordered = list(pmids)
    rng = random.Random(seed)
    rng.shuffle(ordered)
    counts = _split_counts(
        len(ordered),
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
    )
    splits: dict[str, set[str]] = {}
    start = 0
    for split_name in SPLITS:
        count = counts[split_name]
        splits[split_name] = set(ordered[start : start + count])
        start += count
    return splits


def _split_leakage_warnings(root: Path) -> list[str]:
    pmids_by_split: dict[str, set[str]] = {split: set() for split in SPLITS}
    for path in _dataset_jsonl_files(root):
        split = _split_for_dataset_path(path)
        if split is None:
            continue
        for row in _read_jsonl(path):
            pmid = _row_pmid(row)
            if pmid:
                pmids_by_split[split].add(pmid)
    warnings: list[str] = []
    for left_index, left in enumerate(SPLITS):
        for right in SPLITS[left_index + 1 :]:
            overlap = pmids_by_split[left] & pmids_by_split[right]
            if overlap:
                warnings.append(f"{len(overlap)} PMID(s) appear in both {left} and {right}: {', '.join(sorted(overlap)[:5])}")
    return warnings


def _collect_task_labels(root: Path, task: str) -> set[str]:
    labels: set[str] = set()
    for path in _task_candidate_files(root, task):
        labels.update(str(row.get("label", "")) for row in _read_jsonl(path) if str(row.get("label", "")).strip())
    return labels


def _dataset_jsonl_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for filename in TASK_FILES.values():
        path = root / filename
        if path.exists():
            files.append(path)
    for task in TASK_FILES:
        for split in SPLITS:
            path = root / f"{task}_{split}.jsonl"
            if path.exists():
                files.append(path)
    return sorted(set(files))


def _task_candidate_files(root: Path, task: str) -> list[Path]:
    files = []
    base_file = root / TASK_FILES[task]
    if base_file.exists():
        files.append(base_file)
    for split in SPLITS:
        path = root / f"{task}_{split}.jsonl"
        if path.exists():
            files.append(path)
    return files


def _preferred_evaluation_file(root: Path, task: str) -> Path:
    split_test = root / f"{task}_test.jsonl"
    if split_test.exists():
        return split_test
    return root / TASK_FILES[task]


def _task_for_dataset_path(path: Path) -> str | None:
    name = path.name.casefold()
    if "ner" in name:
        return "ner"
    if "evidence" in name:
        return "evidence"
    if "relation" in name:
        return "relation"
    return None


def _split_for_dataset_path(path: Path) -> str | None:
    name = path.name.casefold()
    for split in SPLITS:
        if split in name:
            return split
    return None


def _row_pmid(row: dict[str, Any]) -> str:
    return str(row.get("source_pmid") or row.get("pmid") or "").strip()


def _evidence_label_from_row(row: dict[str, Any]) -> int | str | None:
    for key in ("corrected_evidence_tier", "evidence_tier", "predicted_evidence_tier", "evidence_level"):
        value = row.get(key)
        if value is None or value == "":
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return str(value)
    return None


def _row_has_label(row: dict[str, Any]) -> bool:
    value = row.get("label")
    return value is not None and str(value).strip() != ""


def _config_task_name(task: str) -> str:
    if task == "relation_extraction":
        return "relation"
    if task == "evidence_classification":
        return "evidence"
    return task


def _count_labels(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("label", "")) for row in rows if str(row.get("label", "")).strip()).items()))


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
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _format_counts(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {label}: {count}" for label, count in sorted(counts.items())]
