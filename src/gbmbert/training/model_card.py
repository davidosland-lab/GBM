"""Local model-card generation for GBM-BERT research checkpoints."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.registry import load_registry


@dataclass(frozen=True)
class ModelCard:
    checkpoint_name: str
    task: str
    base_model: str
    checkpoint_status: str
    checkpoint_dir: str
    metrics: dict[str, Any]
    run_manifest: dict[str, Any]
    dataset_card: dict[str, Any] | None
    limitations: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_model_card(
    *,
    registry_path: str | Path,
    checkpoint_name: str,
    dataset_card_json: str | Path | None = None,
) -> ModelCard:
    """Build a local research model card from registry, metrics, and manifest artifacts."""

    checkpoint = _find_checkpoint(registry_path, checkpoint_name)
    metrics = _read_json_if_present(checkpoint.get("metrics_path"))
    run_manifest = _read_json_if_present(checkpoint.get("manifest_path"))
    dataset_card = _read_json_if_present(dataset_card_json) if dataset_card_json else None
    return ModelCard(
        checkpoint_name=checkpoint_name,
        task=str(checkpoint.get("task", "")),
        base_model=str(checkpoint.get("base_model", "")),
        checkpoint_status=str(checkpoint.get("status", "")),
        checkpoint_dir=str(checkpoint.get("checkpoint_dir", "")),
        metrics=metrics,
        run_manifest=run_manifest,
        dataset_card=dataset_card,
        limitations=[
            "Research-use only; not medical advice.",
            "Not intended for diagnosis, treatment selection, or clinical decision-making.",
            "Performance metrics are local research artifacts and do not establish clinical validity.",
            "Training data may be small, imbalanced, or manually curated for research exploration.",
        ],
    )


def save_model_card_json(card: ModelCard, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(card.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_model_card_markdown(card: ModelCard, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_model_card_markdown(card), encoding="utf-8")
    return output


def format_model_card_markdown(card: ModelCard) -> str:
    metric_lines = _format_metrics(card.metrics)
    limitation_lines = [f"- {item}" for item in card.limitations]
    lines = [
        f"# GBM-BERT Model Card: {card.checkpoint_name}",
        "",
        card.warning,
        "",
        f"- Task: {card.task}",
        f"- Base model: `{card.base_model}`",
        f"- Checkpoint status: {card.checkpoint_status}",
        f"- Checkpoint directory: `{card.checkpoint_dir}`",
        "",
        "## Metrics",
        *metric_lines,
        "",
        "## Provenance",
        f"- Metrics path: `{card.run_manifest.get('metrics_path', 'unknown')}`",
        f"- Dataset directory: `{card.run_manifest.get('dataset_dir', 'unknown')}`",
        f"- Label map directory: `{card.run_manifest.get('label_map_dir', 'unknown')}`",
        "",
        "## Limitations",
        *limitation_lines,
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local GBM-BERT research model card.")
    parser.add_argument("registry", type=Path)
    parser.add_argument("--checkpoint-name", required=True)
    parser.add_argument("--dataset-card-json", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    card = build_model_card(
        registry_path=args.registry,
        checkpoint_name=args.checkpoint_name,
        dataset_card_json=args.dataset_card_json,
    )
    if args.markdown_output:
        save_model_card_markdown(card, args.markdown_output)
    if args.json_output:
        save_model_card_json(card, args.json_output)
    if args.json:
        print(json.dumps(card.to_dict(), indent=2, sort_keys=True))
    elif not args.markdown_output:
        print(format_model_card_markdown(card))
    return 0


def _find_checkpoint(registry_path: str | Path, checkpoint_name: str) -> dict[str, Any]:
    registry = load_registry(registry_path)
    for checkpoint in registry["checkpoints"]:
        if checkpoint.get("name") == checkpoint_name:
            return checkpoint
    raise ValueError(f"Checkpoint not found in registry: {checkpoint_name}")


def _read_json_if_present(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    input_path = Path(path)
    if not input_path.exists():
        return {}
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _format_metrics(metrics: dict[str, Any]) -> list[str]:
    if not metrics:
        return ["- none"]
    lines = []
    for key in ["examples", "accuracy", "macro_f1"]:
        if key in metrics:
            lines.append(f"- {key}: {metrics[key]}")
    if not lines:
        lines.append("- see JSON metrics artifact")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
