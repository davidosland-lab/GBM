"""Compact CI summary for GBM-AI verification artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


def build_ci_report_summary(root: str | Path = ".") -> str:
    root_path = Path(root)
    local = _read_json(root_path / "reports/platform_regression/local_verification.json")
    policy = _read_json(root_path / "reports/platform_regression/artifact_policy.json")
    launcher = _read_json(root_path / "reports/platform_regression/launcher_menu_check.json")
    governance = _read_json(root_path / "reports/training/governance/training_governance_suite.json")
    strict = _read_json(root_path / "reports/training/governance_strict/training_governance_suite.json")
    promotion = _read_json(root_path / "reports/training/gold_pack/gold_pack_promotion_review.json")
    lines = [
        "# GBM-AI CI Verification Summary",
        "",
        RESEARCH_WARNING,
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
        _row("Local verification", bool(local.get("passed")), f"{local.get('passed_step_count', 0)}/{local.get('step_count', 0)} steps"),
        _row("Artifact policy", bool(policy.get("safe")), f"{policy.get('finding_count', 0)} findings"),
        _row("Launcher menu", bool(launcher.get("safe")), f"{launcher.get('warning_count', 0)} warnings"),
        _row("Default governance", bool(governance.get("passed")), f"{len(governance.get('warnings') or [])} warnings"),
        _row("Strict governance audit", not bool(strict.get("passed")), f"{len(strict.get('warnings') or [])} expected audit warning(s)"),
        _row("Gold-pack promotion", bool(promotion.get("promotable")), f"{len(promotion.get('blockers') or [])} blocker(s)"),
        "",
        "Strict governance and gold-pack promotion are audit signals. A non-promotable gold pack is expected until reviewed data volume thresholds are met.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a compact Markdown summary from verification reports.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("reports/platform_regression/ci_report_summary.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = build_ci_report_summary(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")
    print(summary)
    return 0


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _row(name: str, passed: bool, detail: str) -> str:
    return f"| {name} | {'pass' if passed else 'review'} | {detail} |"


if __name__ == "__main__":
    raise SystemExit(main())
