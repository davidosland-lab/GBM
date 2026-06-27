"""Hugging Face DatasetDict loaders for prepared GBM-BERT splits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from datasets import Dataset, DatasetDict

PreparedTask = Literal["ner", "evidence", "relation"]
SPLITS = ("train", "validation", "test")


def load_prepared_dataset(dataset_dir: str | Path, task: PreparedTask) -> DatasetDict:
    """Load prepared task JSONL split files into a Hugging Face DatasetDict."""

    root = Path(dataset_dir)
    datasets: dict[str, Dataset] = {}
    for split in SPLITS:
        path = root / f"{task}_{split}.jsonl"
        rows = _read_jsonl(path)
        datasets[split] = Dataset.from_list([_normalize_row(row, task=task) for row in rows])
    return DatasetDict(datasets)


def dataset_split_counts(dataset: DatasetDict) -> dict[str, int]:
    """Return row counts for each DatasetDict split."""

    return {split: len(dataset[split]) for split in dataset}


def load_label_map(label_map_dir: str | Path, task: PreparedTask) -> dict[str, int]:
    """Load the stable label-to-id map for one task."""

    path = Path(label_map_dir) / f"{task}_label_map.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    label_to_id = payload.get("label_to_id")
    if not isinstance(label_to_id, dict):
        raise ValueError(f"Label map missing label_to_id object: {path}")
    return {str(label): int(identifier) for label, identifier in label_to_id.items()}


def _normalize_row(row: dict[str, Any], *, task: PreparedTask) -> dict[str, Any]:
    text = str(row.get("text") or row.get("sentence") or "")
    normalized = {
        "id": str(row.get("item_id") or row.get("source_pmid") or row.get("pmid") or ""),
        "source_pmid": str(row.get("source_pmid") or row.get("pmid") or ""),
        "text": text,
        "label": str(row.get("label", "")),
        "task": task,
    }
    if task == "ner":
        normalized["start"] = row.get("start")
        normalized["end"] = row.get("end")
    if task == "relation":
        normalized["head"] = row.get("head")
        normalized["tail"] = row.get("tail")
        normalized["evidence_tier"] = row.get("evidence_tier")
    return normalized


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
