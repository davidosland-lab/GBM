import subprocess
import sys

from gbmbert.verification import format_local_verification_markdown, run_local_verification


def test_local_verification_runs_ordered_commands(tmp_path):
    commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    report = run_local_verification(reports_dir=tmp_path / "platform", governance_dir=tmp_path / "governance", runner=runner)
    markdown = format_local_verification_markdown(report)

    assert report.passed is True
    assert [step.name for step in report.steps] == [
        "pytest",
        "pip_check",
        "scope_drift_monitor",
        "training_governance_suite",
        "platform_regression",
        "artifact_policy",
        "artifact_index",
    ]
    assert commands[0] == [sys.executable, "-m", "pytest", "-q"]
    assert commands[1] == [sys.executable, "-m", "pip", "check"]
    assert "gbmbert-run-training-governance-suite" in commands[3][0]
    assert "--skip-tests" in commands[4]
    assert "gbmbert-check-artifact-policy" in commands[5][0]
    assert "Research-use only. Not medical advice." in markdown


def test_local_verification_reports_failed_steps(tmp_path):
    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1 if command[:3] == [sys.executable, "-m", "pytest"] else 0, stdout="failed\n", stderr="")

    report = run_local_verification(reports_dir=tmp_path / "platform", governance_dir=tmp_path / "governance", runner=runner)

    assert report.passed is False
    assert report.failed_step_count == 1
    assert report.warnings == ["pytest failed: failed"]
