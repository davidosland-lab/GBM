"""No-download smoke fixture for the GBM-BERT evidence training path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gbmbert.training.config import TrainingConfig, TrainingTask
from gbmbert.training.execution import execute_evidence_training


def run_training_smoke(
    *,
    output_dir: str | Path,
    reports_dir: str | Path,
    registry_path: str | Path,
    checkpoint_name: str = "gbmbert_evidence_smoke",
) -> dict[str, Any]:
    """Create a tiny evidence fixture and execute the training path with fake components."""

    output_root = Path(output_dir)
    reports_root = Path(reports_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)
    dataset_dir = output_root / "splits"
    label_dir = output_root / "label_maps"
    checkpoint_dir = output_root / "checkpoint"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(dataset_dir / "evidence_train.jsonl", [{"task": "evidence", "source_pmid": "1", "text": "case series", "label": "0"}])
    _write_jsonl(dataset_dir / "evidence_validation.jsonl", [{"task": "evidence", "source_pmid": "2", "text": "trial", "label": "1"}])
    _write_jsonl(
        dataset_dir / "evidence_test.jsonl",
        [
            {"task": "evidence", "source_pmid": "3", "text": "case series", "label": "0"},
            {"task": "evidence", "source_pmid": "4", "text": "trial", "label": "1"},
        ],
    )
    (label_dir / "evidence_label_map.json").write_text(
        json.dumps({"task": "evidence", "label_to_id": {"0": 0, "1": 1}}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    config = TrainingConfig(
        name=checkpoint_name,
        task=TrainingTask.EVIDENCE_CLASSIFICATION,
        base_model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
        train_path=dataset_dir / "evidence_train.jsonl",
        validation_path=dataset_dir / "evidence_validation.jsonl",
        output_dir=checkpoint_dir,
        label_set=["0", "1"],
        hyperparameters={"max_length": 4, "max_steps": 1},
        training_enabled=True,
    )
    config_path = output_root / "training_config.json"
    config_path.write_text(json.dumps(config.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")
    result = execute_evidence_training(
        config=config,
        config_path=config_path,
        dataset_dir=dataset_dir,
        label_map_dir=label_dir,
        metrics_output=reports_root / "evidence_smoke_metrics.json",
        evaluation_markdown_output=reports_root / "evidence_smoke_metrics.md",
        run_manifest_output=reports_root / "evidence_smoke_run_manifest.json",
        registry_path=registry_path,
        checkpoint_name=checkpoint_name,
        tokenizer_loader=lambda base_model, local_files_only: SmokeTokenizer(),
        trainer_factory=lambda **kwargs: SmokeTrainer(),
    )
    summary = {
        "status": result.status,
        "dataset_dir": str(dataset_dir),
        "label_map_dir": str(label_dir),
        "config_path": str(config_path),
        "metrics_path": result.metrics_path,
        "run_manifest_path": result.run_manifest_path,
        "checkpoint_dir": result.checkpoint_dir,
        "registry_path": str(registry_path),
        "checkpoint_name": checkpoint_name,
    }
    (reports_root / "evidence_smoke_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a no-download GBM-BERT evidence training smoke fixture.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/training/evidence_smoke_fixture"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/training/evidence_smoke_fixture"))
    parser.add_argument("--registry", type=Path, default=Path("models/checkpoint_registry.json"))
    parser.add_argument("--checkpoint-name", default="gbmbert_evidence_smoke")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_training_smoke(
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        registry_path=args.registry,
        checkpoint_name=args.checkpoint_name,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


class SmokeTokenizer:
    def __call__(
        self,
        texts: list[str],
        *,
        truncation: bool,
        padding: str,
        max_length: int,
    ) -> dict[str, list[list[int]]]:
        del truncation, padding
        input_ids: list[list[int]] = []
        attention_mask: list[list[int]] = []
        for text in texts:
            token_count = min(max(len(text.split()), 1), max_length)
            input_ids.append(list(range(1, max_length + 1)))
            attention_mask.append([1] * token_count + [0] * (max_length - token_count))
        return {"input_ids": input_ids, "attention_mask": attention_mask}


class SmokePredictionOutput:
    predictions = [[0.9, 0.1], [0.1, 0.9]]
    label_ids = [0, 1]


class SmokeTrainer:
    def train(self) -> None:
        return None

    def save_model(self, output_dir: str) -> None:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "smoke-model.txt").write_text("smoke fixture only", encoding="utf-8")

    def predict(self, dataset: object) -> SmokePredictionOutput:
        del dataset
        return SmokePredictionOutput()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
