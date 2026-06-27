from pathlib import Path

from gbmbert.artifact_policy import check_artifact_policy, format_artifact_policy_markdown


def test_artifact_policy_accepts_required_handoff_artifacts(tmp_path: Path) -> None:
    required = [Path("reports/artifact_index.md"), Path("reports/training/governance/training_governance_suite.md")]
    for path in required:
        full_path = tmp_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("ok\n", encoding="utf-8")

    report = check_artifact_policy(root=tmp_path, required_paths=required, tracked_paths=required)
    markdown = format_artifact_policy_markdown(report)

    assert report.safe is True
    assert report.finding_count == 0
    assert "Artifact Policy Check" in markdown


def test_artifact_policy_flags_missing_required_and_model_binary(tmp_path: Path) -> None:
    model_path = Path("models/checkpoints/full_model.safetensors")
    full_model_path = tmp_path / model_path
    full_model_path.parent.mkdir(parents=True, exist_ok=True)
    full_model_path.write_text("not a real model\n", encoding="utf-8")

    report = check_artifact_policy(
        root=tmp_path,
        required_paths=[Path("reports/artifact_index.md")],
        tracked_paths=[model_path],
    )

    assert report.safe is False
    assert report.missing_required_count == 1
    assert any("model/checkpoint-style binary" in finding.message for finding in report.findings)
