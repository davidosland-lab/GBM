"""Canonical local verification runner for GBM-AI project checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from gbmbert.datasets import RESEARCH_WARNING


DEFAULT_REPORTS_DIR = Path("reports/platform_regression")
DEFAULT_GOVERNANCE_DIR = Path("reports/training/governance")


@dataclass(frozen=True)
class VerificationStep:
    name: str
    command: list[str]
    passed: bool
    returncode: int
    detail: str


@dataclass(frozen=True)
class LocalVerificationReport:
    created_at_utc: str
    passed: bool
    step_count: int
    passed_step_count: int
    failed_step_count: int
    steps: list[VerificationStep]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def run_local_verification(
    *,
    reports_dir: str | Path = DEFAULT_REPORTS_DIR,
    governance_dir: str | Path = DEFAULT_GOVERNANCE_DIR,
    runner: CommandRunner | None = None,
) -> LocalVerificationReport:
    """Run the ordered local verification sequence and return a report."""

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    command_runner = runner or _run_command
    steps: list[VerificationStep] = []

    ordered_commands = [
        (
            "pytest",
            [sys.executable, "-m", "pytest", "-q"],
        ),
        (
            "pip_check",
            [sys.executable, "-m", "pip", "check"],
        ),
        (
            "scope_drift_monitor",
            [
                _console_script("gbmbert-scope-drift-monitor"),
                "--markdown-output",
                str(reports_path / "scope_drift.md"),
                "--json-output",
                str(reports_path / "scope_drift.json"),
            ],
        ),
        (
            "training_governance_suite",
            [
                _console_script("gbmbert-run-training-governance-suite"),
                "--output-dir",
                str(governance_dir),
            ],
        ),
        (
            "platform_regression",
            [
                _console_script("gbmbert-platform-regression"),
                "--skip-tests",
                "--skip-pip-check",
                "--reports-dir",
                str(reports_path),
            ],
        ),
        (
            "artifact_index",
            [
                _console_script("gbmbert-artifact-index"),
                "--markdown-output",
                "reports/artifact_index.md",
                "--json-output",
                "reports/artifact_index.json",
            ],
        ),
    ]

    for name, command in ordered_commands:
        result = command_runner(command)
        steps.append(
            VerificationStep(
                name=name,
                command=command,
                passed=result.returncode == 0,
                returncode=result.returncode,
                detail=_command_detail(result),
            )
        )

    warnings = [f"{step.name} failed: {step.detail}" for step in steps if not step.passed]
    return LocalVerificationReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        passed=not warnings,
        step_count=len(steps),
        passed_step_count=sum(1 for step in steps if step.passed),
        failed_step_count=sum(1 for step in steps if not step.passed),
        steps=steps,
        warnings=warnings,
    )


def save_local_verification_json(report: LocalVerificationReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_local_verification_markdown(report: LocalVerificationReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_local_verification_markdown(report), encoding="utf-8")
    return output_path


def format_local_verification_markdown(report: LocalVerificationReport) -> str:
    lines = [
        "# GBM-AI Local Verification",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Passed: {report.passed}",
        f"- Steps: {report.passed_step_count}/{report.step_count} passed",
        "",
        "## Ordered Steps",
    ]
    for step in report.steps:
        lines.extend(
            [
                f"### {step.name}",
                f"- Status: {'pass' if step.passed else 'fail'}",
                f"- Return code: {step.returncode}",
                f"- Command: `{_format_command(step.command)}`",
                f"- Detail: {step.detail or 'none'}",
                "",
            ]
        )
    lines.extend(["## Warnings", *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"])])
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the canonical local GBM-AI verification sequence.")
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--governance-dir", type=Path, default=DEFAULT_GOVERNANCE_DIR)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = run_local_verification(reports_dir=args.reports_dir, governance_dir=args.governance_dir)
    json_output = args.json_output or Path(args.reports_dir) / "local_verification.json"
    markdown_output = args.markdown_output or Path(args.reports_dir) / "local_verification.md"
    save_local_verification_json(report, json_output)
    save_local_verification_markdown(report, markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_local_verification_markdown(report))
    return 0 if report.passed else 1


def _console_script(name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    script = Path(sys.executable).parent / f"{name}{suffix}"
    return str(script) if script.exists() else name


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def _command_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    tail = " | ".join(lines[-4:])
    return tail[:800] or f"returncode={result.returncode}"


def _format_command(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)


if __name__ == "__main__":
    raise SystemExit(main())
