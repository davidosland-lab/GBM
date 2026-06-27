"""Local checkpoint registry metadata for GBM-BERT research experiments."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


@dataclass(frozen=True)
class CheckpointRegistryEntry:
    name: str
    checkpoint_dir: str
    task: str
    base_model: str
    status: str
    registered_at: str
    metrics_path: str | None
    manifest_path: str | None
    notes: str
    warning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def register_checkpoint(
    registry_path: str | Path,
    *,
    name: str,
    checkpoint_dir: str | Path,
    task: str,
    base_model: str,
    status: str = "candidate",
    metrics_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
    notes: str = "",
) -> CheckpointRegistryEntry:
    """Append or replace one local checkpoint metadata entry."""

    entry = CheckpointRegistryEntry(
        name=name,
        checkpoint_dir=str(checkpoint_dir),
        task=task,
        base_model=base_model,
        status=status,
        registered_at=datetime.now(timezone.utc).isoformat(),
        metrics_path=str(metrics_path) if metrics_path else None,
        manifest_path=str(manifest_path) if manifest_path else None,
        notes=notes,
        warning=RESEARCH_WARNING,
    )
    registry = load_registry(registry_path)
    entries = [item for item in registry["checkpoints"] if item.get("name") != name]
    entries.append(entry.to_dict())
    registry["checkpoints"] = sorted(entries, key=lambda item: item["name"])
    output_path = Path(registry_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    return entry


def load_registry(registry_path: str | Path) -> dict[str, Any]:
    path = Path(registry_path)
    if not path.exists():
        return {"warning": RESEARCH_WARNING, "checkpoints": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Checkpoint registry must be a JSON object: {path}")
    payload.setdefault("warning", RESEARCH_WARNING)
    payload.setdefault("checkpoints", [])
    if not isinstance(payload["checkpoints"], list):
        raise ValueError(f"Checkpoint registry checkpoints must be a list: {path}")
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register local GBM-BERT checkpoint metadata.")
    parser.add_argument("registry", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--checkpoint-dir", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--status", default="candidate")
    parser.add_argument("--metrics-path", type=Path)
    parser.add_argument("--manifest-path", type=Path)
    parser.add_argument("--notes", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    register_checkpoint(
        args.registry,
        name=args.name,
        checkpoint_dir=args.checkpoint_dir,
        task=args.task,
        base_model=args.base_model,
        status=args.status,
        metrics_path=args.metrics_path,
        manifest_path=args.manifest_path,
        notes=args.notes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
