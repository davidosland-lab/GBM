"""No-training planning CLI for GBM-BERT fine-tuning scaffolds."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from gbmbert.training.config import load_training_config
from gbmbert.training.datasets import summarize_dataset_for_config

LOGGER = logging.getLogger(__name__)


def build_training_plan(config_path: str | Path, *, require_data: bool = False) -> dict[str, Any]:
    """Build a dry-run training plan without downloading models or training."""

    config = load_training_config(config_path)
    plan: dict[str, Any] = {
        "name": config.name,
        "task": config.task.value,
        "base_model": config.base_model,
        "output_dir": str(config.output_dir),
        "label_set": config.label_set,
        "hyperparameters": config.hyperparameters,
        "training_enabled": config.is_training_enabled,
        "status": "dry_run_only",
        "notes": [
            "This scaffold starts from PubMedBERT or BioBERT; it does not train from scratch.",
            "No model weights are downloaded and no optimizer step is run by this command.",
        ],
    }
    if require_data or config.train_path.exists():
        summaries = summarize_dataset_for_config(config)
        plan["datasets"] = {
            split: summary.to_dict() if summary is not None else None
            for split, summary in summaries.items()
        }
    else:
        plan["datasets"] = {
            "train": {"path": str(config.train_path), "status": "missing"},
            "validation": {"path": str(config.validation_path), "status": "missing"}
            if config.validation_path is not None
            else None,
        }
    return plan


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a dry-run GBM-BERT fine-tuning plan without training a model."
    )
    parser.add_argument("config", type=Path, help="Training scaffold JSON config.")
    parser.add_argument(
        "--require-data",
        action="store_true",
        help="Require and summarize the configured training dataset.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON plan.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    plan = build_training_plan(args.config, require_data=args.require_data)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"GBM-BERT training plan: {plan['name']}")
        print(f"Task: {plan['task']}")
        print(f"Base model: {plan['base_model']}")
        print("Status: dry-run only; no training or model download performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
