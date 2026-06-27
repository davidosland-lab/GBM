"""Research-use batch inference for GBM-BERT evidence classifiers."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.registry import load_registry

PredictionFn = Callable[[list[str], dict[str, Any]], list[dict[str, Any]]]


def score_evidence_jsonl(
    *,
    input_jsonl: str | Path,
    output_jsonl: str | Path,
    registry_path: str | Path,
    checkpoint_name: str,
    predictor: PredictionFn | None = None,
    local_files_only: bool = True,
) -> int:
    """Score research evidence JSONL rows with a registered evidence classifier."""

    checkpoint = _find_checkpoint(registry_path, checkpoint_name)
    if checkpoint.get("task") != "evidence_classification":
        raise ValueError("Batch inference is currently limited to evidence_classification checkpoints")
    rows = _read_jsonl(Path(input_jsonl))
    texts = [_row_text(row) for row in rows]
    predictor_fn = predictor or _build_transformers_predictor(local_files_only=local_files_only)
    predictions = predictor_fn(texts, checkpoint)
    if len(predictions) != len(rows):
        raise ValueError("predictor returned a different number of predictions than input rows")
    output = Path(output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row, prediction in zip(rows, predictions, strict=False):
            handle.write(
                json.dumps(
                    {
                        "source_pmid": str(row.get("source_pmid") or row.get("pmid") or ""),
                        "text": _row_text(row),
                        "prediction": str(prediction["label"]),
                        "confidence": float(prediction["confidence"]),
                        "checkpoint_name": checkpoint_name,
                        "checkpoint_status": checkpoint.get("status"),
                        "checkpoint_dir": checkpoint.get("checkpoint_dir"),
                        "warning": RESEARCH_WARNING,
                    },
                    sort_keys=True,
                )
            )
            handle.write("\n")
    return len(rows)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score research evidence JSONL rows with a registered GBM-BERT checkpoint.")
    parser.add_argument("input_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--checkpoint-name", required=True)
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Allow model/tokenizer download instead of requiring local files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    score_evidence_jsonl(
        input_jsonl=args.input_jsonl,
        output_jsonl=args.output_jsonl,
        registry_path=args.registry,
        checkpoint_name=args.checkpoint_name,
        local_files_only=not args.allow_model_download,
    )
    return 0


def _find_checkpoint(registry_path: str | Path, checkpoint_name: str) -> dict[str, Any]:
    registry = load_registry(registry_path)
    for checkpoint in registry["checkpoints"]:
        if checkpoint.get("name") == checkpoint_name:
            return checkpoint
    raise ValueError(f"Checkpoint not found in registry: {checkpoint_name}")


def _build_transformers_predictor(*, local_files_only: bool) -> PredictionFn:
    def predict(texts: list[str], checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(checkpoint["checkpoint_dir"], local_files_only=local_files_only)
        model = AutoModelForSequenceClassification.from_pretrained(
            checkpoint["checkpoint_dir"],
            local_files_only=local_files_only,
        )
        classifier = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            top_k=1,
        )
        raw_predictions = classifier(texts)
        normalized: list[dict[str, Any]] = []
        for item in raw_predictions:
            best = item[0] if isinstance(item, list) else item
            normalized.append({"label": str(best["label"]), "confidence": float(best["score"])})
        return normalized

    return predict


def _row_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("claim") or row.get("sentence") or row.get("abstract") or "")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
