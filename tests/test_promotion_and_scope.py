import json
from pathlib import Path

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.knowledge_graph.promotion import (
    build_evidence_overlay_promotion_gate_report,
    format_promotion_gate_markdown,
)
from gbmbert.platform_regression import format_platform_regression_markdown, run_platform_regression
from gbmbert.scope_monitor import format_scope_drift_markdown, monitor_scope_drift


def test_evidence_overlay_promotion_gate_requires_clean_inputs(tmp_path: Path) -> None:
    overlay = tmp_path / "overlay.jsonl"
    quality = tmp_path / "quality.json"
    diff = tmp_path / "diff.json"
    guard = tmp_path / "guard.json"
    validation = tmp_path / "validation.json"
    regression = tmp_path / "regression.json"
    overlay.write_text("", encoding="utf-8")
    quality.write_text(json.dumps({"invalid_record_count": 0, "warnings": []}), encoding="utf-8")
    diff.write_text(json.dumps({"overlay_metadata_count": 1, "warnings": []}), encoding="utf-8")
    guard.write_text(json.dumps({"safe_to_load": True, "warnings": []}), encoding="utf-8")
    validation.write_text(json.dumps({"valid": True, "warnings": []}), encoding="utf-8")
    regression.write_text(json.dumps({"warnings": []}), encoding="utf-8")

    report = build_evidence_overlay_promotion_gate_report(
        overlay_graph_jsonl=overlay,
        graph_quality_json=quality,
        overlay_diff_json=diff,
        overlay_load_guard_json=guard,
        handoff_validation_json=validation,
        regression_pack_json=regression,
    )
    markdown = format_promotion_gate_markdown(report)

    assert report.safe_to_promote is True
    assert report.failed_check_count == 0
    assert "Evidence Overlay Promotion Gate" in markdown


def test_scope_drift_monitor_flags_missing_warning(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe.md"
    safe = tmp_path / "safe.md"
    unsafe.write_text("This document lacks the boundary.", encoding="utf-8")
    safe.write_text(RESEARCH_WARNING, encoding="utf-8")

    report = monitor_scope_drift([unsafe, safe])
    markdown = format_scope_drift_markdown(report)

    assert report.safe is False
    assert report.missing_warning_count == 1
    assert "Scope Drift Monitor" in markdown


def test_platform_regression_smoke_runs_without_tests_or_pip_check(tmp_path: Path) -> None:
    report = run_platform_regression(skip_tests=True, skip_pip_check=True, reports_dir=tmp_path / "reports")
    markdown = format_platform_regression_markdown(report)

    assert any(step.name == "pytest" and step.detail == "skipped" for step in report.steps)
    assert "Platform Regression" in markdown
