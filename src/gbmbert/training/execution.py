"""Task training execution for GBM-BERT research runs (evidence, relation, NER)."""

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
    evaluate_bio_spans,
    evaluate_predictions,
    save_evaluation_report_json,
    save_evaluation_report_markdown,
)
from gbmbert.training.hf_datasets import load_label_map, load_prepared_dataset
from gbmbert.training.ner_bio import bio_label_map_is_bio, spans_from_bio_ids
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


_EXECUTABLE_TASKS = {
    "evidence_classification": "evidence",
    "relation_extraction": "relation",
    "ner": "ner",
}


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
    """Backward-compatible wrapper around multi-task research training execution."""

    return execute_task_training(
        config=config,
        config_path=config_path,
        dataset_dir=dataset_dir,
        label_map_dir=label_map_dir,
        metrics_output=metrics_output,
        run_manifest_output=run_manifest_output,
        evaluation_markdown_output=evaluation_markdown_output,
        registry_path=registry_path,
        checkpoint_name=checkpoint_name,
        local_files_only=local_files_only,
        trainer_factory=trainer_factory,
        model_loader=model_loader,
        tokenizer_loader=tokenizer_loader,
    )


def execute_task_training(
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
    """Train and evaluate an evidence, relation, or NER research model when gates pass."""

    prepared_task = _EXECUTABLE_TASKS.get(config.task.value)
    if prepared_task is None:
        raise ValueError(f"Unsupported training task for execution: {config.task.value}")
    started_at = datetime.now(timezone.utc).isoformat()
    label_to_id = load_label_map(label_map_dir, prepared_task)
    id_to_label = {identifier: label for label, identifier in label_to_id.items()}
    dataset = load_prepared_dataset(dataset_dir, prepared_task)
    tokenizer = (tokenizer_loader or load_tokenizer)(config.base_model, local_files_only=local_files_only)
    tokenized = tokenize_dataset(
        dataset,
        task=prepared_task,
        tokenizer=tokenizer,
        label_to_id=label_to_id,
        max_length=int(config.hyperparameters.get("max_length", 256)),
    )
    trainer = _build_trainer(
        config=config,
        prepared_task=prepared_task,
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
    if prepared_task == "ner" and bio_label_map_is_bio(label_to_id):
        true_spans, predicted_spans = _decode_bio_span_predictions(
            label_ids=list(prediction_output.label_ids),
            predictions=list(prediction_output.predictions),
            id_to_label=id_to_label,
        )
        entity_types = sorted({label[2:] for label in label_to_id if label.startswith("B-")})
        evaluation = evaluate_bio_spans(
            task=config.task.value,
            true_spans_by_doc=true_spans,
            predicted_spans_by_doc=predicted_spans,
            entity_types=entity_types or [label for label in config.label_set if not label.startswith(("B-", "I-")) and label != "O"],
        )
    else:
        true_labels, predicted_labels = _decode_predictions(
            prepared_task=prepared_task,
            label_ids=list(prediction_output.label_ids),
            predictions=list(prediction_output.predictions),
            id_to_label=id_to_label,
        )
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
        dataset_hashes=_dataset_hashes(Path(dataset_dir), prepared_task),
        label_map_sha256=_sha256_file(Path(label_map_dir) / f"{prepared_task}_label_map.json"),
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
            notes=f"Research-use {config.task.value} checkpoint; not validated for clinical use.",
        )
    return TrainingExecutionResult(
        status="completed",
        metrics_path=str(metrics_output),
        run_manifest_path=str(run_manifest_output),
        checkpoint_dir=str(config.output_dir),
        registry_path=str(registry_path) if registry_path is not None else None,
        evaluation=evaluation,
    )


def compute_inverse_frequency_class_weights(
    label_ids: list[int],
    *,
    num_labels: int,
    power: float = 1.0,
    max_ratio: float | None = None,
) -> list[float]:
    """Return inverse-frequency class weights with optional tempering.

    Base weight is ``(n_samples / (n_classes * count_c)) ** power``.
    ``power < 1`` (e.g. 0.5) reduces rare-class over-emphasis that drives
    BIO false positives. When ``max_ratio`` is set, clamp present-class
    weights so ``max(w) / min(w) <= max_ratio``.
    """

    if num_labels <= 0:
        raise ValueError("num_labels must be positive")
    if power <= 0:
        raise ValueError("power must be positive")
    if max_ratio is not None and max_ratio < 1.0:
        raise ValueError("max_ratio must be >= 1.0 when set")
    counts = [0] * num_labels
    for label_id in label_ids:
        if label_id < 0 or label_id >= num_labels:
            raise ValueError(f"label id out of range: {label_id}")
        counts[label_id] += 1
    total = len(label_ids)
    if total <= 0:
        return [1.0] * num_labels
    weights: list[float] = []
    for count in counts:
        # Absent labels keep weight 1.0 so they do not dominate unused logits.
        if count > 0:
            weights.append((float(total) / float(num_labels * count)) ** float(power))
        else:
            weights.append(1.0)
    if max_ratio is not None:
        present = [weight for weight, count in zip(weights, counts, strict=False) if count > 0]
        if present:
            floor = min(present)
            ceiling = floor * float(max_ratio)
            weights = [
                min(max(weight, floor), ceiling) if count > 0 else weight
                for weight, count in zip(weights, counts, strict=False)
            ]
    return weights


def _build_trainer(
    *,
    config: TrainingConfig,
    prepared_task: str,
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
    from transformers import (
        AutoModelForSequenceClassification,
        AutoModelForTokenClassification,
        Trainer,
        TrainingArguments,
    )

    model_cls = AutoModelForTokenClassification if prepared_task == "ner" else AutoModelForSequenceClassification
    loader = model_loader or model_cls.from_pretrained
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
        seed=int(config.hyperparameters.get("seed", 13)),
    )
    use_class_weights = bool(config.hyperparameters.get("use_class_weights", False))
    if not use_class_weights:
        return Trainer(
            model=model,
            args=args,
            train_dataset=tokenized["train"],
            eval_dataset=tokenized["validation"],
            tokenizer=tokenizer,
        )

    train_labels = _flatten_train_label_ids(tokenized["train"]["labels"], prepared_task=prepared_task)
    class_weight_power = float(config.hyperparameters.get("class_weight_power", 1.0))
    raw_max_ratio = config.hyperparameters.get("class_weight_max_ratio")
    class_weight_max_ratio = float(raw_max_ratio) if raw_max_ratio is not None else None
    class_weights = compute_inverse_frequency_class_weights(
        train_labels,
        num_labels=len(label_to_id),
        power=class_weight_power,
        max_ratio=class_weight_max_ratio,
    )

    class WeightedTrainer(Trainer):
        def __init__(self, *trainer_args: Any, class_weights: list[float], **trainer_kwargs: Any) -> None:
            super().__init__(*trainer_args, **trainer_kwargs)
            import torch

            self._class_weights = torch.tensor(class_weights, dtype=torch.float32)

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):  # type: ignore[no-untyped-def]
            from torch.nn import CrossEntropyLoss

            labels = inputs.get("labels")
            outputs = model(**{key: value for key, value in inputs.items() if key != "labels"})
            logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
            weight = self._class_weights.to(device=logits.device, dtype=logits.dtype)
            loss = CrossEntropyLoss(weight=weight, ignore_index=-100)(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
            )
            return (loss, outputs) if return_outputs else loss

    return WeightedTrainer(
        model=model,
        args=args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
        class_weights=class_weights,
    )


def _flatten_train_label_ids(raw_labels: Any, *, prepared_task: str) -> list[int]:
    if prepared_task != "ner":
        return [int(label) for label in raw_labels]
    flat: list[int] = []
    for row in raw_labels:
        for label in row:
            label_id = int(label)
            if label_id != -100:
                flat.append(label_id)
    return flat


def _decode_predictions(
    *,
    prepared_task: str,
    label_ids: list[Any],
    predictions: list[Any],
    id_to_label: dict[int, str],
) -> tuple[list[str], list[str]]:
    if prepared_task != "ner":
        true_ids = [int(label) for label in label_ids]
        predicted_ids = [_argmax(row) for row in predictions]
        return (
            [id_to_label[label_id] for label_id in true_ids],
            [id_to_label[label_id] for label_id in predicted_ids],
        )

    true_labels: list[str] = []
    predicted_labels: list[str] = []
    for true_row, pred_row in zip(label_ids, predictions, strict=False):
        true_labels.append(id_to_label[_majority_label_id(true_row, ignore_index=-100)])
        # Align prediction argmax per token, then majority over attended tokens.
        token_pred_ids = [_argmax(token_logits) for token_logits in pred_row]
        mask = [int(value) != -100 for value in true_row]
        attended = [pred for pred, keep in zip(token_pred_ids, mask, strict=False) if keep]
        if not attended:
            attended = token_pred_ids
        predicted_labels.append(id_to_label[_majority_from_ids(attended)])
    return true_labels, predicted_labels


def _decode_bio_span_predictions(
    *,
    label_ids: list[Any],
    predictions: list[Any],
    id_to_label: dict[int, str],
) -> tuple[list[list[tuple[int, int, str]]], list[list[tuple[int, int, str]]]]:
    true_spans_by_doc: list[list[tuple[int, int, str]]] = []
    predicted_spans_by_doc: list[list[tuple[int, int, str]]] = []
    for true_row, pred_row in zip(label_ids, predictions, strict=False):
        true_ids = [int(value) for value in true_row]
        pred_ids: list[int] = []
        for true_id, token_logits in zip(true_ids, pred_row, strict=False):
            if true_id == -100:
                pred_ids.append(-100)
            else:
                pred_ids.append(_argmax(token_logits))
        true_spans_by_doc.append(spans_from_bio_ids(true_ids, id_to_label))
        predicted_spans_by_doc.append(spans_from_bio_ids(pred_ids, id_to_label))
    return true_spans_by_doc, predicted_spans_by_doc


def _majority_label_id(row: Any, *, ignore_index: int) -> int:
    values = [int(value) for value in row if int(value) != ignore_index]
    if not values:
        raise ValueError("NER example has no supervised token labels")
    return _majority_from_ids(values)


def _majority_from_ids(values: list[int]) -> int:
    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts.items(), key=lambda item: (item[1], -item[0]))[0]


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
