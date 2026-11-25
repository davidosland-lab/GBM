from gbmbert.dashboard.app import (
    DASHBOARD_PAGES,
    RESEARCH_WARNING,
    curation_dashboard_context,
    monte_carlo_dashboard_context,
    page_titles,
    simulation_dashboard_context,
    training_artifacts_dashboard_context,
    treatment_dashboard_context,
)
from gbmbert.dashboard.visual_workspace import visual_workspace_context, visual_workspace_html


def test_dashboard_includes_prediction_curation_page() -> None:
    titles = page_titles()
    page = next(item for item in DASHBOARD_PAGES if item.key == "prediction_curation")

    assert "Prediction Curation" in titles
    assert page.status == "live-runner"
    assert "curated evidence" in page.body


def test_dashboard_includes_training_artifacts_page() -> None:
    titles = page_titles()
    page = next(item for item in DASHBOARD_PAGES if item.key == "training_artifacts")

    assert "Training Artifacts" in titles
    assert page.status == "live-runner"
    assert "packs" in page.body.lower() or "registry" in page.body.lower()


def test_dashboard_preserves_research_warning() -> None:
    assert "Research-use only" in RESEARCH_WARNING


def test_dashboard_includes_visual_workspace_page() -> None:
    titles = page_titles()
    page = next(item for item in DASHBOARD_PAGES if item.key == "visual_workspace")

    assert "Visual Workspace" in titles
    assert page.status == "live-runner"
    assert "Relationship-first" in page.body


def test_visual_workspace_context_builds_connected_article_and_lineage_views() -> None:
    context = visual_workspace_context(graph_path="data/examples/graph_records_sample.jsonl")

    assert context["mode"] == "Explore"
    assert context["graph"]["nodes"]
    assert context["article_graph"]["nodes"]
    assert any(node["kind"] == "article" for node in context["article_graph"]["nodes"])
    assert context["artifact_lineage"]["nodes"]


def test_visual_workspace_html_contains_modes_and_mount_point() -> None:
    context = visual_workspace_context(graph_path="data/examples/graph_records_sample.jsonl", mode="Curate", search="MGMT")
    html = visual_workspace_html(context)

    assert "Visual Workspace" in html
    assert "Visual Workspace Graph" in html
    assert "Explore" in html
    assert "Curate" in html
    assert "Audit" in html
    assert "article_graph" in html
    assert "three-graph" in html
    assert "https://esm.sh/three" in html
    assert "OrbitControls" in html


def test_curation_dashboard_context_loads_reports(tmp_path):
    report_dir = tmp_path / "reports" / "review" / "curation_smoke_workflow"
    report_dir.mkdir(parents=True)
    (report_dir / "prediction_quality.md").write_text("# Quality\n", encoding="utf-8")
    (report_dir / "curation_smoke_workflow.json").write_text('{"warnings":[]}\n', encoding="utf-8")
    regression_dir = tmp_path / "reports" / "review" / "curation_regression_pack"
    regression_dir.mkdir(parents=True)
    (regression_dir / "curation_handoff_validation.json").write_text('{"valid":true}\n', encoding="utf-8")
    (regression_dir / "active_learning_batches.json").write_text('{"batch_count":2}\n', encoding="utf-8")
    artifact_dir = tmp_path / "reports"
    (artifact_dir / "artifact_index.json").write_text('{"artifact_count":7}\n', encoding="utf-8")
    registry_dir = tmp_path / "reports" / "review"
    (registry_dir / "curation_run_registry.json").write_text(
        '{"entries":[{"run_id":"curation-ABC"}]}\n',
        encoding="utf-8",
    )

    context = curation_dashboard_context(tmp_path)

    assert context["available_report_count"] == 1
    assert context["payloads"]["Workflow"]["warnings"] == []
    assert context["handoff_validation_valid"] is True
    assert context["active_learning_batch_count"] == 2
    assert context["artifact_count"] == 7
    assert context["latest_run_id"] == "curation-ABC"


def test_training_artifacts_dashboard_context_loads_reports(tmp_path):
    relation_dir = tmp_path / "reports" / "training" / "relation_pack"
    relation_dir.mkdir(parents=True)
    (relation_dir / "relation_training_pack.md").write_text("# Relation\n", encoding="utf-8")
    (relation_dir / "relation_training_pack.json").write_text('{"ready":true}\n', encoding="utf-8")
    training_dir = tmp_path / "reports" / "training"
    (training_dir / "relation_training_config_review.json").write_text('{"status":"passed"}\n', encoding="utf-8")
    (training_dir / "model_registry_audit.json").write_text('{"passed":false}\n', encoding="utf-8")
    registry_dir = tmp_path / "models"
    registry_dir.mkdir()
    (registry_dir / "checkpoint_registry.json").write_text('{"checkpoints":[{"name":"x"}]}\n', encoding="utf-8")

    context = training_artifacts_dashboard_context(tmp_path)

    assert context["available_report_count"] == 1
    assert context["ready_pack_count"] == 1
    assert context["relation_config_status"] == "passed"
    assert context["registry_entry_count"] == 1
    assert context["registry_audit_passed"] is False


def test_simulation_dashboard_context_loads_phase5_reports(tmp_path):
    sim_dir = tmp_path / "reports" / "simulation"
    sim_dir.mkdir(parents=True)
    (sim_dir / "phase5_mvp_example.md").write_text("# Sim\n", encoding="utf-8")
    (sim_dir / "phase5_mvp_example.json").write_text(
        '{"comparisons":[{"scenario_id":"tmz"}],"clinical_validity_claimed":false,"resistance_enabled":false}\n',
        encoding="utf-8",
    )
    context = simulation_dashboard_context(tmp_path)
    assert context["available_report_count"] == 1
    assert context["scenario_comparison_count"] == 1
    assert context["clinical_validity_claimed"] is False


def test_treatment_and_monte_carlo_dashboard_contexts(tmp_path):
    treatment_dir = tmp_path / "reports" / "treatment"
    treatment_dir.mkdir(parents=True)
    (treatment_dir / "phase6_strategy_example.md").write_text("# Rank\n", encoding="utf-8")
    (treatment_dir / "phase6_strategy_example.json").write_text(
        '{"rankings":[{"scenario_id":"tmz_fus"}],"is_clinical_decision_support":false,"comparison_table":[]}\n',
        encoding="utf-8",
    )
    sim_dir = tmp_path / "reports" / "simulation"
    sim_dir.mkdir(parents=True)
    (sim_dir / "phase5_monte_carlo_example.md").write_text("# MC\n", encoding="utf-8")
    (sim_dir / "phase5_monte_carlo_example.json").write_text(
        '{"seed":7,"n_samples":40,"comparison_table":[{"scenario_id":"tmz"}]}\n',
        encoding="utf-8",
    )

    treatment = treatment_dashboard_context(tmp_path)
    monte = monte_carlo_dashboard_context(tmp_path)
    assert treatment["available_report_count"] == 1
    assert treatment["top_scenario"] == "tmz_fus"
    assert treatment["is_clinical_decision_support"] is False
    assert monte["seed"] == 7
    assert monte["scenario_count"] == 1
