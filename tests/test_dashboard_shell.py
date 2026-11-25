import sys
import json
from pathlib import Path

from gbmbert.dashboard.app import (
    DASHBOARD_PAGES,
    RESEARCH_WARNING,
    page_from_sidebar_label,
    page_sidebar_labels,
    page_titles,
    training_artifacts_dashboard_context,
)
from gbmbert.dashboard.cli import build_arg_parser, build_streamlit_command


def test_dashboard_has_required_handoff_pages() -> None:
    titles = page_titles()

    assert titles[0] == "Visual Workspace"
    assert titles[1:7] == [
        "Literature Search",
        "Entity Explorer",
        "Knowledge Graph Explorer",
        "Prediction Curation",
        "Training Artifacts",
        "Tumour Simulator",
    ]
    assert "Treatment Explorer" in titles
    assert "Monte Carlo" in titles
    assert "Monte Carlo Results" not in titles


def test_dashboard_preserves_original_handoff_pages() -> None:
    titles = set(page_titles())

    assert {
        "Literature Search",
        "Entity Explorer",
        "Knowledge Graph Explorer",
        "Tumour Simulator",
        "Treatment Explorer",
        "Monte Carlo",
    }.issubset(titles)


def test_dashboard_pages_are_live_runners_not_recommendation_surface() -> None:
    statuses = {page.key: page.status for page in DASHBOARD_PAGES}

    assert statuses["knowledge_graph_explorer"] == "live-runner"
    assert statuses["prediction_curation"] == "live-runner"
    assert statuses["training_artifacts"] == "live-runner"
    assert statuses["tumour_simulator"] == "live-runner"
    assert statuses["treatment_explorer"] == "live-runner"
    assert statuses["monte_carlo_results"] == "live-runner"
    assert statuses["literature_search"] == "live-runner"
    assert statuses["entity_explorer"] == "live-runner"
    assert "Not medical advice" in RESEARCH_WARNING


def test_dashboard_sidebar_labels_include_status() -> None:
    labels = page_sidebar_labels()
    assert any("Literature Search · live-runner" == label for label in labels)
    assert any("Monte Carlo · live-runner" == label for label in labels)
    selected = page_from_sidebar_label("Knowledge Graph Explorer · live-runner")
    assert selected.key == "knowledge_graph_explorer"


def test_dashboard_launcher_builds_streamlit_command() -> None:
    command = build_streamlit_command(host="127.0.0.1", port=8501)

    assert command[:3] == [sys.executable, "-m", "streamlit"]
    assert "run" in command
    assert "--server.address" in command
    assert "127.0.0.1" in command
    assert "--server.port" in command
    assert "8501" in command


def test_dashboard_cli_description_is_not_skeleton() -> None:
    parser = build_arg_parser()
    assert "skeleton" not in parser.description.lower()
    assert "research" in parser.description.lower()


def test_training_dashboard_context_includes_governance_status(tmp_path: Path) -> None:
    _write_json(tmp_path / "reports/training/training_label_drift.json", {"warning_count": 0})
    _write_json(tmp_path / "reports/platform_regression/launcher_menu_check.json", {"safe": True})
    _write_json(tmp_path / "reports/training/curated_fixture_import.json", {"safe": True})
    _write_json(tmp_path / "reports/training/curated_provenance_diff.json", {"safe": True})
    _write_json(tmp_path / "reports/training/gold_pack/gold_pack_promotion_review.json", {"promotable": False, "blockers": ["tiny pack"]})
    _write_json(
        tmp_path / "reports/training/gold_pack/gold_pack_ops_status.json",
        {
            "promotable": False,
            "promotion_blockers": ["tiny pack"],
            "soft_densify_gaps": [{"task": "ner", "label": "PATHWAY", "count": 3, "soft_floor": 10, "delta": 7}],
            "next_actions": ["Adjudicate dual-review backlog"],
            "dual_review_pending_total": 4,
            "active_learning_pending_total": 2,
            "task_counts": {"evidence": 1, "ner": 2, "relation": 3},
        },
    )
    for path in (
        tmp_path / "reports/training/training_label_drift.md",
        tmp_path / "reports/platform_regression/launcher_menu_check.md",
        tmp_path / "reports/training/curated_fixture_import.md",
        tmp_path / "reports/training/curated_provenance_diff.md",
        tmp_path / "reports/training/gold_pack/gold_pack_promotion_review.md",
        tmp_path / "reports/training/gold_pack/gold_pack_ops_status.md",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Report\n", encoding="utf-8")

    context = training_artifacts_dashboard_context(tmp_path)

    assert context["label_drift_warning_count"] == 0
    assert context["launcher_menu_safe"] is True
    assert context["curated_fixture_safe"] is True
    assert context["gold_pack_promotable"] is False
    assert context["promotion_blockers"] == ["tiny pack"]
    assert context["dual_review_pending_total"] == 4
    assert context["gold_pack_next_actions"][0].startswith("Adjudicate")
    details = {row["title"]: row for row in context["governance_report_details"]}
    assert details["Curated provenance diff"]["status"] == "safe"
    assert details["Gold-pack ops status"]["status"] == "blocked"
    assert details["Model registry audit"]["status"] == "missing"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
