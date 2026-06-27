"""Review gate for GBM-BERT training configuration files."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.config import TrainingConfig, TrainingTask, load_training_config
from gbmbert.training.hf_datasets import load_label_map
from gbmbert.training.relation_negatives import NO_RELATION_LABEL

TASK_TO_PREPARED = {
    TrainingTask.NER: "ner",
    TrainingTask.RELATION_EXTRACTION: "relation",
    TrainingTask.EVIDENCE_CLASSIFICATION: "evidence",
}


@dataclass(frozen=True)
class TrainingConfigReviewReport:
    config_path: str
    dataset_dir: str
    label_map_dir: str | None
    task: str
    prepared_task: str
    base_model: str
    training_enabled: bool
    training_enabled_confirmed: bool
    split_counts: dict[str, int]
    config_labels: list[str]
    dataset_labels: list[str]
    label_map_labels: list[str]
    checks: dict[str, bool]
    status: str
    errors: list[str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def review_training_config(
    config_path: str | Path,
    dataset_dir: str | Path,
    *,
    label_map_dir: str | Path | None = None,
    confirm_training_enabled: bool = False,
) -> TrainingConfigReviewReport:
    """Validate config, prepared splits, label maps, and explicit training intent."""

    config = load_training_config(config_path)
    root = Path(dataset_dir)
    prepared_task = TASK_TO_PREPARED[config.task]
    split_counts = {split: len(_read_jsonl(root / f"{prepared_task}_{split}.jsonl")) for split in ("train", "validation", "test")}
    dataset_labels = sorted(
        {
            str(row.get("label")).strip()
            for split in ("train", "validation", "test")
            for row in _read_jsonl(root / f"{prepared_task}_{split}.jsonl")
            if row.get("label") is not None and str(row.get("label")).strip()
        }
    )
    label_map_labels: list[str] = []
    label_root = Path(label_map_dir) if label_map_dir else None
    if label_root is not None:
        label_map_labels = sorted(load_label_map(label_root, prepared_task).keys())

    errors: list[str] = []
    warnings: list[str] = [
        "review gate is for research scaffolding only and does not certify model performance",
        "training remains separate from diagnosis, treatment selection, and clinical decision-making",
    ]
    checks = {
        "dataset_dir_exists": root.exists(),
        "train_split_present": (root / f"{prepared_task}_train.jsonl").exists(),
        "validation_split_present": (root / f"{prepared_task}_validation.jsonl").exists(),
        "test_split_present": (root / f"{prepared_task}_test.jsonl").exists(),
        "train_split_nonempty": split_counts["train"] > 0,
        "config_label_set_nonempty": bool(config.label_set),
        "dataset_label_set_nonempty": bool(dataset_labels),
        "dataset_labels_covered_by_config": set(dataset_labels).issubset(set(config.label_set)),
        "config_labels_present_in_dataset": set(config.label_set).issubset(set(dataset_labels)),
        "label_map_present": label_root is None or (label_root / f"{prepared_task}_label_map.json").exists(),
        "dataset_labels_covered_by_label_map": not label_root or set(dataset_labels).issubset(set(label_map_labels)),
        "label_map_labels_match_config": not label_root or set(label_map_labels) == set(config.label_set),
        "hyperparameters_in_review_bounds": _hyperparameters_in_review_bounds(config),
        "training_enabled_confirmed": not config.training_enabled or confirm_training_enabled,
    }
    if prepared_task == "relation":
        checks["relation_config_includes_no_relation"] = NO_RELATION_LABEL in set(config.label_set)
        checks["relation_label_map_includes_no_relation"] = not label_root or NO_RELATION_LABEL in set(label_map_labels)
    if not checks["dataset_dir_exists"]:
        errors.append(f"dataset directory not found: {root}")
    for split, count in split_counts.items():
        if not (root / f"{prepared_task}_{split}.jsonl").exists():
            errors.append(f"missing {prepared_task}_{split}.jsonl")
        elif split == "train" and count == 0:
            errors.append(f"{prepared_task}_{split}.jsonl has no examples")
        elif count == 0:
            warnings.append(f"{prepared_task}_{split}.jsonl has no examples")
    missing_config_labels = sorted(set(dataset_labels) - set(config.label_set))
    if missing_config_labels:
        errors.append(f"dataset labels missing from config label_set: {', '.join(missing_config_labels)}")
    unused_config_labels = sorted(set(config.label_set) - set(dataset_labels))
    if unused_config_labels:
        errors.append(f"config label_set labels missing from dataset: {', '.join(unused_config_labels)}")
    if label_root is not None:
        missing_map_labels = sorted(set(dataset_labels) - set(label_map_labels))
        if missing_map_labels:
            errors.append(f"dataset labels missing from label map: {', '.join(missing_map_labels)}")
        if set(label_map_labels) != set(config.label_set):
            errors.append("label map labels do not match config label_set")
    if prepared_task == "relation" and NO_RELATION_LABEL not in set(config.label_set):
        errors.append("relation extraction config must include NO_RELATION")
    if prepared_task == "relation" and label_root is not None and NO_RELATION_LABEL not in set(label_map_labels):
        errors.append("relation label map must include NO_RELATION")
    if not checks["hyperparameters_in_review_bounds"]:
        errors.append("hyperparameters outside review bounds")
    if config.training_enabled and not confirm_training_enabled:
        errors.append("training_enabled is true but --confirm-training-enabled was not supplied")
    if not config.training_enabled:
        warnings.append("training_enabled is false; this config is review-ready but will run as a dry run unless changed")

    status = "passed" if not errors else "failed"
    return TrainingConfigReviewReport(
        config_path=str(config_path),
        dataset_dir=str(root),
        label_map_dir=str(label_root) if label_root else None,
        task=str(config.task),
        prepared_task=prepared_task,
        base_model=config.base_model,
        training_enabled=config.training_enabled,
        training_enabled_confirmed=confirm_training_enabled,
        split_counts=split_counts,
        config_labels=list(config.label_set),
        dataset_labels=dataset_labels,
        label_map_labels=label_map_labels,
        checks=checks,
        status=status,
        errors=errors,
        warnings=warnings,
    )


def save_training_config_review_json(report: TrainingConfigReviewReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_training_config_review_markdown(report: TrainingConfigReviewReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_training_config_review_markdown(report), encoding="utf-8")
    return output


def format_training_config_review_markdown(report: TrainingConfigReviewReport) -> str:
    lines = [
        "# GBM-BERT Training Config Review Gate",
        "",
        RESEARCH_WARNING,
        "",
        f"- Status: {report.status}",
        f"- Config: `{report.config_path}`",
        f"- Dataset: `{report.dataset_dir}`",
        f"- Label maps: `{report.label_map_dir or 'not provided'}`",
        f"- Task: {report.task}",
        f"- Prepared task: {report.prepared_task}",
        f"- Base model: `{report.base_model}`",
        f"- Training enabled: {report.training_enabled}",
        f"- Training enabled confirmed: {report.training_enabled_confirmed}",
        "",
        "## Split Counts",
        *[f"- {split}: {count}" for split, count in sorted(report.split_counts.items())],
        "",
        "## Checks",
        *[f"- {name}: {value}" for name, value in sorted(report.checks.items())],
        "",
        "## Labels",
        "- Config: " + _format_inline_list(report.config_labels),
        "- Dataset: " + _format_inline_list(report.dataset_labels),
        "- Label map: " + _format_inline_list(report.label_map_labels),
        "",
        "## Errors",
        *([f"- {error}" for error in report.errors] if report.errors else ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GBM-BERT training config before execution.")
    parser.add_argument("config_path", type=Path)
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--label-map-dir", type=Path)
    parser.add_argument("--confirm-training-enabled", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-failed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = review_training_config(
        args.config_path,
        args.dataset_dir,
        label_map_dir=args.label_map_dir,
        confirm_training_enabled=args.confirm_training_enabled,
    )
    if args.json_output:
        save_training_config_review_json(report, args.json_output)
    if args.markdown_output:
        save_training_config_review_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_training_config_review_markdown(report))
    return 0 if report.status == "passed" or args.allow_failed else 1


def _hyperparameters_in_review_bounds(config: TrainingConfig) -> bool:
    params = config.hyperparameters
    return (
        _numeric_in_range(params.get("epochs"), lower=1, upper=20)
        and _numeric_in_range(params.get("learning_rate"), lower=0, upper=0.001, lower_inclusive=False)
        and _numeric_in_range(params.get("batch_size"), lower=1, upper=64)
        and _numeric_in_range(params.get("max_length"), lower=32, upper=512)
    )


def _numeric_in_range(value: Any, *, lower: float, upper: float, lower_inclusive: bool = True) -> bool:
    if not isinstance(value, (int, float)):
        return False
    if lower_inclusive and value < lower:
        return False
    if not lower_inclusive and value <= lower:
        return False
    return value <= upper


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


def _format_inline_list(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


if __name__ == "__main__":
    raise SystemExit(main())
