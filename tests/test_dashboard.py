from gbmbert.dashboard.app import DASHBOARD_PAGES, RESEARCH_WARNING, curation_dashboard_context, page_titles, training_artifacts_dashboard_context


def test_dashboard_includes_prediction_curation_page() -> None:
    titles = page_titles()
    page = next(item for item in DASHBOARD_PAGES if item.key == "prediction_curation")

    assert "Prediction Curation" in titles
    assert page.status == "workflow-linked"
    assert "curated evidence" in page.body


def test_dashboard_includes_training_artifacts_page() -> None:
    titles = page_titles()
    page = next(item for item in DASHBOARD_PAGES if item.key == "training_artifacts")

    assert "Training Artifacts" in titles
    assert page.status == "workflow-linked"
    assert "training packs" in page.body


def test_dashboard_preserves_research_warning() -> None:
    assert "Research-use only" in RESEARCH_WARNING


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
