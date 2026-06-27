"""Evidence-classifier training execution for GBM-BERT research runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.config import TrainingConfig
from gbmbert.training.evaluation import (
    EvaluationReport,
    evaluate_predictions,
    save_evaluation_report_json,
    save_evaluation_report_markdown,
)
from gbmbert.training.hf_datasets import load_label_map, load_prepared_dataset
from gbmbert.training.registry import register_checkpoint
from gbmbert.training.tokenization import load_tokenizer, tokenize_dataset


@dataclass(frozen=True)
class TrainingRunManifest:
    run_name: str
    task: str
    base_model: str
    output_dir: str
    dataset_dir: str
    label_map_dir: str
    metrics_path: str
    evaluation_markdown_path: str | None
    checkpoint_dir: str
    started_at: str
    completed_at: str
    config_sha256: str
    dataset_hashes: dict[str, str]
    label_map_sha256: str
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingExecutionResult:
    status: str
    metrics_path: str
    run_manifest_path: str
    checkpoint_dir: str
    registry_path: str | None
    evaluation: EvaluationReport
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evaluation"] = self.evaluation.to_dict()
        return payload


TrainerFactory = Callable[..., Any]
ModelLoader = Callable[..., Any]
TokenizerLoader = Callable[..., Any]


def execute_evidence_training(
    *,
    config: TrainingConfig,
    config_path: str | Path,
    dataset_dir: str | Path,
    label_map_dir: str | Path,
    metrics_output: str | Path,
    run_manifest_output: str | Path,
    evaluation_markdown_output: str | Path | None = None,
    registry_path: str | Path | None = None,
    checkpoint_name: str | None = None,
    local_files_only: bool = True,
    trainer_factory: TrainerFactory | None = None,
    model_loader: ModelLoader | None = None,
    tokenizer_loader: TokenizerLoader | None = None,
) -> TrainingExecutionResult:
    """Train and evaluate the evidence classifier when all external gates have passed."""

    if config.task.value != "evidence_classification":
        raise ValueError("Only evidence_classification training is implemented")
    started_at = datetime.now(timezone.utc).isoformat()
    label_to_id = load_label_map(label_map_dir, "evidence")
    id_to_label = {identifier: label for label, identifier in label_to_id.items()}
    dataset = load_prepared_dataset(dataset_dir, "evidence")
    tokenizer = (tokenizer_loader or load_tokenizer)(config.base_model, local_files_only=local_files_only)
    tokenized = tokenize_dataset(
        dataset,
        task="evidence",
        tokenizer=tokenizer,
        label_to_id=label_to_id,
        max_length=int(config.hyperparameters.get("max_length", 256)),
    )
    trainer = _build_trainer(
        config=config,
        tokenized=tokenized,
        tokenizer=tokenizer,
        label_to_id=label_to_id,
        id_to_label=id_to_label,
        trainer_factory=trainer_factory,
        model_loader=model_loader,
        local_files_only=local_files_only,
    )
    trainer.train()
    if hasattr(trainer, "save_model"):
        trainer.save_model(str(config.output_dir))
    prediction_output = trainer.predict(tokenized["test"])
    true_ids = [int(label) for label in list(prediction_output.label_ids)]
    predicted_ids = [_argmax(row) for row in list(prediction_output.predictions)]
    true_labels = [id_to_label[label_id] for label_id in true_ids]
    predicted_labels = [id_to_label[label_id] for label_id in predicted_ids]
    evaluation = evaluate_predictions(
        task=config.task.value,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        label_set=config.label_set,
    )
    save_evaluation_report_json(evaluation, metrics_output)
    if evaluation_markdown_output is not None:
        save_evaluation_report_markdown(evaluation, evaluation_markdown_output)
    completed_at = datetime.now(timezone.utc).isoformat()
    manifest = TrainingRunManifest(
        run_name=config.name,
        task=config.task.value,
        base_model=config.base_model,
        output_dir=str(config.output_dir),
        dataset_dir=str(dataset_dir),
        label_map_dir=str(label_map_dir),
        metrics_path=str(metrics_output),
        evaluation_markdown_path=str(evaluation_markdown_output) if evaluation_markdown_output else None,
        checkpoint_dir=str(config.output_dir),
        started_at=started_at,
        completed_at=completed_at,
        config_sha256=_sha256_file(Path(config_path)),
        dataset_hashes=_dataset_hashes(Path(dataset_dir), "evidence"),
        label_map_sha256=_sha256_file(Path(label_map_dir) / "evidence_label_map.json"),
    )
    _save_run_manifest(manifest, run_manifest_output)
    if registry_path is not None:
        register_checkpoint(
            registry_path,
            name=checkpoint_name or config.name,
            checkpoint_dir=config.output_dir,
            task=config.task.value,
            base_model=config.base_model,
            status="research_candidate",
            metrics_path=metrics_output,
            manifest_path=run_manifest_output,
            notes="Research-use evidence classifier checkpoint; not validated for clinical use.",
        )
    return TrainingExecutionResult(
        status="completed",
        metrics_path=str(metrics_output),
        run_manifest_path=str(run_manifest_output),
        checkpoint_dir=str(config.output_dir),
        registry_path=str(registry_path) if registry_path is not None else None,
        evaluation=evaluation,
    )


def _build_trainer(
    *,
    config: TrainingConfig,
    tokenized: Any,
    tokenizer: Any,
    label_to_id: dict[str, int],
    id_to_label: dict[int, str],
    trainer_factory: TrainerFactory | None,
    model_loader: ModelLoader | None,
    local_files_only: bool,
) -> Any:
    if trainer_factory is not None:
        return trainer_factory(config=config, tokenized=tokenized, tokenizer=tokenizer, label_to_id=label_to_id)
    from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments

    loader = model_loader or AutoModelForSequenceClassification.from_pretrained
    model = loader(
        config.base_model,
        num_labels=len(label_to_id),
        id2label={identifier: label for identifier, label in id_to_label.items()},
        label2id=label_to_id,
        local_files_only=local_files_only,
    )
    args = TrainingArguments(
        output_dir=str(config.output_dir),
        num_train_epochs=float(config.hyperparameters.get("epochs", 1)),
        learning_rate=float(config.hyperparameters.get("learning_rate", 2e-5)),
        per_device_train_batch_size=int(config.hyperparameters.get("batch_size", 8)),
        per_device_eval_batch_size=int(config.hyperparameters.get("batch_size", 8)),
        max_steps=int(config.hyperparameters.get("max_steps", -1)),
        report_to=[],
        save_strategy="no",
    )
    return Trainer(
        model=model,
        args=args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
    )


def _save_run_manifest(manifest: TrainingRunManifest, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def _dataset_hashes(dataset_dir: Path, task: str) -> dict[str, str]:
    return {
        split: _sha256_file(dataset_dir / f"{task}_{split}.jsonl")
        for split in ["train", "validation", "test"]
    }


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _argmax(row: Any) -> int:
    values = list(row)
    return max(range(len(values)), key=lambda index: values[index])
