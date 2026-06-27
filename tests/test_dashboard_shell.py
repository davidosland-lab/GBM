import sys
import json
from pathlib import Path

from gbmbert.dashboard.app import DASHBOARD_PAGES, RESEARCH_WARNING, page_titles, training_artifacts_dashboard_context
from gbmbert.dashboard.cli import build_streamlit_command


def test_dashboard_has_required_handoff_pages() -> None:
    titles = page_titles()

    assert titles[:6] == [
        "Literature Search",
        "Entity Explorer",
        "Knowledge Graph Explorer",
        "Prediction Curation",
        "Training Artifacts",
        "Tumour Simulator",
    ]
    assert "Treatment Explorer" in titles
    assert "Monte Carlo Results" in titles


def test_dashboard_preserves_original_handoff_pages() -> None:
    titles = set(page_titles())

    assert {
        "Literature Search",
        "Entity Explorer",
        "Knowledge Graph Explorer",
        "Tumour Simulator",
        "Treatment Explorer",
        "Monte Carlo Results",
    }.issubset(titles)


def test_dashboard_pages_are_scaffold_or_future_not_recommendation_surface() -> None:
    statuses = {page.key: page.status for page in DASHBOARD_PAGES}

    assert statuses["knowledge_graph_explorer"] == "prototype-linked"
    assert statuses["treatment_explorer"] == "future"
    assert "Not medical advice" in RESEARCH_WARNING


def test_dashboard_launcher_builds_streamlit_command() -> None:
    command = build_streamlit_command(host="127.0.0.1", port=8501)

    assert command[:3] == [sys.executable, "-m", "streamlit"]
    assert "run" in command
    assert "--server.address" in command
    assert "127.0.0.1" in command
    assert "--server.port" in command
    assert "8501" in command


def test_training_dashboard_context_includes_governance_status(tmp_path: Path) -> None:
    _write_json(tmp_path / "reports/training/training_label_drift.json", {"warning_count": 0})
    _write_json(tmp_path / "reports/platform_regression/launcher_menu_check.json", {"safe": True})
    _write_json(tmp_path / "reports/training/curated_fixture_import.json", {"safe": True})
    _write_json(tmp_path / "reports/training/gold_pack/gold_pack_promotion_review.json", {"promotable": False})
    for path in (
        tmp_path / "reports/training/training_label_drift.md",
        tmp_path / "reports/platform_regression/launcher_menu_check.md",
        tmp_path / "reports/training/curated_fixture_import.md",
        tmp_path / "reports/training/gold_pack/gold_pack_promotion_review.md",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Report\n", encoding="utf-8")

    context = training_artifacts_dashboard_context(tmp_path)

    assert context["label_drift_warning_count"] == 0
    assert context["launcher_menu_safe"] is True
    assert context["curated_fixture_safe"] is True
    assert context["gold_pack_promotable"] is False


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
