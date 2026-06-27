"""Task-aware tokenization helpers for GBM-BERT preparation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from datasets import DatasetDict
from transformers import AutoTokenizer
from transformers.tokenization_utils_base import PreTrainedTokenizerBase

from gbmbert.training.hf_datasets import PreparedTask


@dataclass(frozen=True)
class TokenizationSummary:
    task: str
    splits: dict[str, int]
    columns: list[str]
    max_length: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_tokenizer(base_model: str, *, local_files_only: bool = True) -> PreTrainedTokenizerBase:
    """Load a pretrained tokenizer, defaulting to local cache only."""

    return AutoTokenizer.from_pretrained(base_model, local_files_only=local_files_only)


def tokenize_dataset(
    dataset: DatasetDict,
    *,
    task: PreparedTask,
    tokenizer: PreTrainedTokenizerBase,
    label_to_id: dict[str, int],
    max_length: int = 256,
) -> DatasetDict:
    """Tokenize a prepared DatasetDict for the selected task."""

    if task == "ner":
        return dataset.map(
            lambda batch: _tokenize_ner_batch(batch, tokenizer=tokenizer, label_to_id=label_to_id, max_length=max_length),
            batched=True,
        )
    return dataset.map(
        lambda batch: _tokenize_classification_batch(
            batch,
            tokenizer=tokenizer,
            label_to_id=label_to_id,
            max_length=max_length,
        ),
        batched=True,
    )


def summarize_tokenized_dataset(dataset: DatasetDict, *, task: PreparedTask, max_length: int) -> TokenizationSummary:
    """Summarize tokenized split sizes and available columns."""

    first_split = next(iter(dataset.keys()), None)
    columns = list(dataset[first_split].column_names) if first_split else []
    return TokenizationSummary(
        task=task,
        splits={split: len(dataset[split]) for split in dataset},
        columns=columns,
        max_length=max_length,
    )


def _tokenize_classification_batch(
    batch: dict[str, list[Any]],
    *,
    tokenizer: PreTrainedTokenizerBase,
    label_to_id: dict[str, int],
    max_length: int,
) -> dict[str, Any]:
    tokenized = tokenizer(
        [str(text) for text in batch.get("text", [])],
        truncation=True,
        padding="max_length",
        max_length=max_length,
    )
    tokenized["labels"] = [_label_id(label, label_to_id) for label in batch.get("label", [])]
    return tokenized


def _tokenize_ner_batch(
    batch: dict[str, list[Any]],
    *,
    tokenizer: PreTrainedTokenizerBase,
    label_to_id: dict[str, int],
    max_length: int,
) -> dict[str, Any]:
    tokenized = tokenizer(
        [str(text) for text in batch.get("text", [])],
        truncation=True,
        padding="max_length",
        max_length=max_length,
    )
    attention_masks = tokenized.get("attention_mask", [])
    labels: list[list[int]] = []
    for attention_mask, label in zip(attention_masks, batch.get("label", []), strict=False):
        label_id = _label_id(label, label_to_id)
        labels.append([label_id if int(mask) == 1 else -100 for mask in attention_mask])
    tokenized["labels"] = labels
    return tokenized


def _label_id(label: Any, label_to_id: dict[str, int]) -> int:
    key = str(label)
    if key not in label_to_id:
        raise ValueError(f"Label not found in label map: {key}")
    return label_to_id[key]
