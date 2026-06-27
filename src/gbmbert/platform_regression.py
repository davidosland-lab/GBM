"""Top-level local regression command for GBM-AI platform checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gbmbert.artifacts import build_artifact_index, save_artifact_index_json, save_artifact_index_markdown
from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.knowledge_graph.promotion import (
    build_evidence_overlay_promotion_gate_report,
    save_promotion_gate_json,
    save_promotion_gate_markdown,
)
from gbmbert.knowledge_graph.quality import analyze_graph_records_jsonl, save_quality_report_json, save_quality_report_markdown
from gbmbert.scope_monitor import monitor_scope_drift, save_scope_drift_json, save_scope_drift_markdown
from gbmbert.training.prediction_curation import (
    run_curation_regression_pack,
    save_curation_regression_pack_json,
    save_curation_regression_pack_markdown,
)


@dataclass(frozen=True)
class PlatformRegressionStep:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class PlatformRegressionReport:
    created_at_utc: str
    passed: bool
    step_count: int
    passed_step_count: int
    failed_step_count: int
    steps: list[PlatformRegressionStep]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_platform_regression(
    *,
    skip_tests: bool = False,
    skip_pip_check: bool = False,
    reports_dir: str | Path = Path("reports/platform_regression"),
) -> PlatformRegressionReport:
    """Run the core local regression checks for the research platform."""

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    steps: list[PlatformRegressionStep] = []

    if not skip_tests:
        result = _run_command([sys.executable, "-m", "pytest", "-q"])
        steps.append(PlatformRegressionStep("pytest", result.returncode == 0, _command_detail(result)))
    else:
        steps.append(PlatformRegressionStep("pytest", True, "skipped"))

    if not skip_pip_check:
        result = _run_command([sys.executable, "-m", "pip", "check"])
        steps.append(PlatformRegressionStep("pip_check", result.returncode == 0, _command_detail(result)))
    else:
        steps.append(PlatformRegressionStep("pip_check", True, "skipped"))

    curation = run_curation_regression_pack()
    curation_json = Path("reports/review/curation_regression_pack/curation_regression_pack.json")
    curation_md = Path("reports/review/curation_regression_pack/curation_regression_pack.md")
    save_curation_regression_pack_json(curation, curation_json)
    save_curation_regression_pack_markdown(curation, curation_md)
    steps.append(PlatformRegressionStep("curation_regression_pack", not curation.warnings, f"warnings={len(curation.warnings)}"))

    overlay_graph = Path(curation.reverted_graph_path).with_name("evidence_overlay_graph_records.jsonl")
    overlay_quality_json = Path("reports/review/curation_regression_pack/overlay_graph_quality.json")
    overlay_quality_md = Path("reports/review/curation_regression_pack/overlay_graph_quality.md")
    quality = analyze_graph_records_jsonl(overlay_graph)
    save_quality_report_json(quality, overlay_quality_json)
    save_quality_report_markdown(quality, overlay_quality_md)
    steps.append(PlatformRegressionStep("overlay_graph_quality", quality.invalid_record_count == 0, f"invalid={quality.invalid_record_count}, warnings={len(quality.warnings)}"))

    promotion = build_evidence_overlay_promotion_gate_report(
        overlay_graph_jsonl=overlay_graph,
        graph_quality_json=overlay_quality_json,
        overlay_diff_json="reports/review/curation_regression_pack/evidence_overlay_diff.json",
        overlay_load_guard_json="reports/review/curation_regression_pack/overlay_load_guard.json",
        handoff_validation_json="reports/review/curation_regression_pack/curation_handoff_validation.json",
        regression_pack_json=curation_json,
    )
    save_promotion_gate_json(promotion, "reports/review/curation_regression_pack/evidence_overlay_promotion_gate.json")
    save_promotion_gate_markdown(promotion, "reports/review/curation_regression_pack/evidence_overlay_promotion_gate.md")
    steps.append(PlatformRegressionStep("evidence_overlay_promotion_gate", promotion.safe_to_promote, f"failed={promotion.failed_check_count}"))

    scope = monitor_scope_drift()
    save_scope_drift_json(scope, reports_path / "scope_drift.json")
    save_scope_drift_markdown(scope, reports_path / "scope_drift.md")
    steps.append(PlatformRegressionStep("scope_drift_monitor", scope.safe, f"findings={scope.finding_count}"))

    artifact_index = build_artifact_index()
    save_artifact_index_json(artifact_index, "reports/artifact_index.json")
    save_artifact_index_markdown(artifact_index, "reports/artifact_index.md")
    steps.append(PlatformRegressionStep("artifact_index", artifact_index.artifact_count > 0, f"artifacts={artifact_index.artifact_count}"))

    warnings = [f"{step.name} failed: {step.detail}" for step in steps if not step.passed]
    return PlatformRegressionReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        passed=not warnings,
        step_count=len(steps),
        passed_step_count=sum(1 for step in steps if step.passed),
        failed_step_count=sum(1 for step in steps if not step.passed),
        steps=steps,
        warnings=warnings,
    )


def save_platform_regression_json(report: PlatformRegressionReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_platform_regression_markdown(report: PlatformRegressionReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_platform_regression_markdown(report), encoding="utf-8")
    return output_path


def format_platform_regression_markdown(report: PlatformRegressionReport) -> str:
    lines = [
        "# GBM-AI Platform Regression",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Passed: {report.passed}",
        f"- Steps: {report.passed_step_count}/{report.step_count} passed",
        "",
        "## Steps",
        *[f"- {step.name}: {'pass' if step.passed else 'fail'} ({step.detail})" for step in report.steps],
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the core local GBM-AI platform regression checks.")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-pip-check", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/platform_regression"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = run_platform_regression(
        skip_tests=args.skip_tests,
        skip_pip_check=args.skip_pip_check,
        reports_dir=args.reports_dir,
    )
    json_output = args.json_output or Path(args.reports_dir) / "platform_regression.json"
    markdown_output = args.markdown_output or Path(args.reports_dir) / "platform_regression.md"
    save_platform_regression_json(report, json_output)
    save_platform_regression_markdown(report, markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_platform_regression_markdown(report))
    return 0 if report.passed else 1


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def _command_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    tail = " | ".join(lines[-3:])
    return tail[:500] or f"returncode={result.returncode}"


if __name__ == "__main__":
    raise SystemExit(main())
