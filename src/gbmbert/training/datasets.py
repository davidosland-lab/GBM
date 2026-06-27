"""Dataset adapters for GBM-BERT fine-tuning scaffolds."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.training.config import TrainingConfig, TrainingTask


@dataclass(frozen=True)
class DatasetSummary:
    path: str
    task: str
    records: int
    labels: dict[str, int]
    missing_labels: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL record on line {line_number}: {input_path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {input_path}")
            yield payload


def adapt_ner_record(record: dict[str, Any]) -> dict[str, Any]:
    """Adapt an entity-extraction record into a token-classification scaffold row."""

    if record.get("task") == "ner" and "label" in record:
        return {
            "id": str(record.get("source_pmid", record.get("item_id", ""))),
            "text": str(record.get("text", "")),
            "labels": [str(record["label"])],
        }
    labels = [str(entity.get("label", "")) for entity in record.get("entities", []) if entity.get("label")]
    text = record.get("text") or record.get("abstract") or record.get("title") or ""
    return {"id": str(record.get("pmid", "")), "text": str(text), "labels": labels}


def adapt_relation_record(record: dict[str, Any]) -> dict[str, Any]:
    """Adapt a KnowledgeGraphRecord into a relation-classification scaffold row."""

    if record.get("task") == "relation" and "label" in record:
        return {
            "id": str(record.get("source_pmid", record.get("item_id", ""))),
            "text": str(record.get("text") or record.get("sentence") or ""),
            "labels": [str(record["label"])],
        }
    labels = [str(relation.get("relation", "")) for relation in record.get("relations", []) if relation.get("relation")]
    text = " ".join(
        str(relation.get("properties", {}).get("sentence", ""))
        for relation in record.get("relations", [])
        if relation.get("properties", {}).get("sentence")
    )
    return {"id": str(record.get("pmid", "")), "text": text, "labels": labels}


def adapt_evidence_record(record: dict[str, Any]) -> dict[str, Any]:
    """Adapt an EvidenceClaim JSONL row into a sequence-classification scaffold row."""

    if record.get("task") == "evidence" and "label" in record:
        return {
            "id": str(record.get("source_pmid", record.get("item_id", ""))),
            "text": str(record.get("text", "")),
            "labels": [str(record["label"])],
        }
    label = record.get("evidence_level", 0)
    text = record.get("claim") or record.get("title") or record.get("abstract") or ""
    return {"id": str(record.get("source_pmid", record.get("pmid", ""))), "text": str(text), "labels": [str(label)]}


def adapt_record_for_task(record: dict[str, Any], task: TrainingTask) -> dict[str, Any]:
    if task == TrainingTask.NER:
        return adapt_ner_record(record)
    if task == TrainingTask.RELATION_EXTRACTION:
        return adapt_relation_record(record)
    if task == TrainingTask.EVIDENCE_CLASSIFICATION:
        return adapt_evidence_record(record)
    raise ValueError(f"Unsupported task: {task}")


def summarize_dataset(path: str | Path, task: TrainingTask, expected_labels: list[str]) -> DatasetSummary:
    labels: Counter[str] = Counter()
    records = 0
    for record in iter_jsonl(path):
        adapted = adapt_record_for_task(record, task)
        records += 1
        labels.update(label for label in adapted["labels"] if label)
    missing = [label for label in expected_labels if label not in labels]
    return DatasetSummary(
        path=str(path),
        task=task.value,
        records=records,
        labels=dict(sorted(labels.items())),
        missing_labels=missing,
    )


def summarize_dataset_for_config(config: TrainingConfig) -> dict[str, DatasetSummary | None]:
    """Summarize train/validation datasets referenced by a config."""

    summary: dict[str, DatasetSummary | None] = {
        "train": summarize_dataset(config.train_path, config.task, config.label_set),
        "validation": None,
    }
    if config.validation_path is not None and config.validation_path.exists():
        summary["validation"] = summarize_dataset(config.validation_path, config.task, config.label_set)
    return summary
