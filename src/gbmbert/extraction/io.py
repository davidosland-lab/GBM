"""JSONL input/output helpers for entity extraction."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from gbmbert.annotation.schema import Paper
from gbmbert.extraction.entities import EntityExtractionResult


def load_pubmed_jsonl(path: str | Path) -> Iterator[Paper]:
    """Load PubMed JSONL records as validated Paper objects."""

    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield Paper.model_validate(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc


def save_entity_jsonl(
    results: Iterable[EntityExtractionResult],
    path: str | Path,
) -> Path:
    """Write entity extraction results as newline-delimited JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(result.model_dump_json())
            handle.write("\n")
    return output_path


def load_entity_jsonl(path: str | Path) -> Iterator[EntityExtractionResult]:
    """Load entity extraction JSONL output."""

    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield EntityExtractionResult.model_validate(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
