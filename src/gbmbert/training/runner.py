"""Gated GBM-BERT training runner scaffold."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.config import TrainingConfig, load_training_config
from gbmbert.training.execution import TrainingExecutionResult, execute_evidence_training
from gbmbert.training.hf_datasets import (
    PreparedTask,
    dataset_split_counts,
    load_label_map,
    load_prepared_dataset,
)
from gbmbert.training.preparation import build_experiment_manifest
from gbmbert.training.tokenization import (
    load_tokenizer,
    summarize_tokenized_dataset,
    tokenize_dataset,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainingGateReport:
    config_path: str
    dataset_dir: str
    label_map_dir: str
    experiment_manifest_path: str | None
    task: str
    execute_training_requested: bool
    dry_run: bool
    status: str
    checks: dict[str, bool]
    dataset_splits: dict[str, int]
    tokenization: dict[str, Any] | None
    execution: dict[str, Any] | None
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_training_gate_report(
    *,
    config_path: str | Path,
    dataset_dir: str | Path,
    label_map_dir: str | Path,
    experiment_manifest_path: str | Path | None = None,
    execute_training: bool = False,
    tokenize: bool = False,
    local_files_only: bool = True,
    metrics_output: str | Path | None = None,
    evaluation_markdown_output: str | Path | None = None,
    run_manifest_output: str | Path | None = None,
    registry_path: str | Path | None = None,
    checkpoint_name: str | None = None,
) -> TrainingGateReport:
    """Validate training inputs and optionally tokenize without running optimization."""

    config_file = Path(config_path)
    dataset_root = Path(dataset_dir)
    label_root = Path(label_map_dir)
    manifest_file = Path(experiment_manifest_path) if experiment_manifest_path else None
    config = load_training_config(config_file)
    task = _prepared_task_for_config(config)
    warnings: list[str] = []
    label_map_exists = (label_root / f"{task}_label_map.json").exists()
    dataset = load_prepared_dataset(dataset_root, task) if dataset_root.exists() else None
    split_counts = dataset_split_counts(dataset) if dataset is not None else {}
    checks = {
        "config_exists": config_file.exists(),
        "dataset_dir_exists": dataset_root.exists(),
        "label_map_exists": label_map_exists,
        "train_split_has_rows": split_counts.get("train", 0) > 0,
        "validation_split_has_rows": split_counts.get("validation", 0) > 0,
        "test_split_has_rows": split_counts.get("test", 0) > 0,
        "experiment_manifest_exists": manifest_file.exists() if manifest_file is not None else False,
        "training_enabled_by_config": config.is_training_enabled,
    }
    if any(count == 0 for count in split_counts.values()):
        warnings.append("one or more dataset splits are empty")
    tokenization_summary = None
    execution_result: TrainingExecutionResult | None = None
    if tokenize and dataset is not None and label_map_exists:
        label_map = load_label_map(label_root, task)
        tokenizer = load_tokenizer(config.base_model, local_files_only=local_files_only)
        max_length = int(config.hyperparameters.get("max_length", 256))
        tokenized = tokenize_dataset(
            dataset,
            task=task,
            tokenizer=tokenizer,
            label_to_id=label_map,
            max_length=max_length,
        )
        tokenization_summary = summarize_tokenized_dataset(tokenized, task=task, max_length=max_length).to_dict()
    base_gate_ready = all(
        checks[key]
        for key in [
            "config_exists",
            "dataset_dir_exists",
            "label_map_exists",
            "train_split_has_rows",
            "validation_split_has_rows",
            "test_split_has_rows",
        ]
    )
    execute_gate_ready = base_gate_ready and manifest_file is not None and checks["experiment_manifest_exists"]
    status = "dry_run_ready" if base_gate_ready else "blocked"
    if execute_training:
        if execute_gate_ready and config.is_training_enabled:
            if config.task.value != "evidence_classification":
                status = "blocked"
                warnings.append("training execution currently supports evidence_classification only")
            elif metrics_output is None or run_manifest_output is None:
                status = "blocked"
                warnings.append("training execution requires --metrics-output and --run-manifest-output")
            else:
                execution_result = execute_evidence_training(
                    config=config,
                    config_path=config_file,
                    dataset_dir=dataset_root,
                    label_map_dir=label_root,
                    metrics_output=metrics_output,
                    run_manifest_output=run_manifest_output,
                    evaluation_markdown_output=evaluation_markdown_output,
                    registry_path=registry_path,
                    checkpoint_name=checkpoint_name,
                    local_files_only=local_files_only,
                )
                status = "training_completed"
        elif base_gate_ready and not config.is_training_enabled:
            status = "blocked"
            warnings.append("training execution refused because the config still disables training")
        elif manifest_file is None or not checks["experiment_manifest_exists"]:
            status = "blocked"
            warnings.append("training execution refused because an experiment manifest was not provided or found")
        else:
            status = "blocked"
            warnings.append("training execution refused because required gates did not pass")
    if manifest_file is not None and not manifest_file.exists():
        generated_manifest = build_experiment_manifest(config_file, dataset_root, label_map_dir=label_root)
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.write_text(json.dumps(generated_manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        checks["experiment_manifest_exists"] = True
    return TrainingGateReport(
        config_path=str(config_file),
        dataset_dir=str(dataset_root),
        label_map_dir=str(label_root),
        experiment_manifest_path=str(manifest_file) if manifest_file is not None else None,
        task=config.task.value,
        execute_training_requested=execute_training,
        dry_run=not execute_training,
        status=status,
        checks=checks,
        dataset_splits=split_counts,
        tokenization=tokenization_summary,
        execution=execution_result.to_dict() if execution_result is not None else None,
        warnings=warnings,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate GBM-BERT training gates without training by default.")
    parser.add_argument("config", type=Path)
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("label_map_dir", type=Path)
    parser.add_argument("--experiment-manifest", type=Path)
    parser.add_argument("--execute-training", action="store_true")
    parser.add_argument("--metrics-output", type=Path)
    parser.add_argument("--evaluation-markdown-output", type=Path)
    parser.add_argument("--run-manifest-output", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--checkpoint-name")
    parser.add_argument("--tokenize", action="store_true", help="Also run local tokenizer preparation.")
    parser.add_argument(
        "--allow-tokenizer-download",
        action="store_true",
        help="Allow tokenizer download instead of requiring the local Hugging Face cache.",
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = build_training_gate_report(
        config_path=args.config,
        dataset_dir=args.dataset_dir,
        label_map_dir=args.label_map_dir,
        experiment_manifest_path=args.experiment_manifest,
        execute_training=args.execute_training,
        tokenize=args.tokenize,
        local_files_only=not args.allow_tokenizer_download,
        metrics_output=args.metrics_output,
        evaluation_markdown_output=args.evaluation_markdown_output,
        run_manifest_output=args.run_manifest_output,
        registry_path=args.registry,
        checkpoint_name=args.checkpoint_name,
    )
    payload = report.to_dict()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"GBM-BERT training gate: {report.status}")
        print(f"Task: {report.task}")
        print(f"Dry run: {report.dry_run}")
        print(RESEARCH_WARNING)
    return 0 if report.status != "blocked" else 2


def _prepared_task_for_config(config: TrainingConfig) -> PreparedTask:
    if config.task.value == "relation_extraction":
        return "relation"
    if config.task.value == "evidence_classification":
        return "evidence"
    return "ner"


if __name__ == "__main__":
    raise SystemExit(main())
