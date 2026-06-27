from pathlib import Path

from gbmbert.artifacts import build_artifact_index, format_artifact_detail_markdown, format_artifact_index_markdown, load_artifact_detail, save_artifact_index_json


def test_build_artifact_index_scans_jsonl_and_reports_counts(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    report_dir = tmp_path / "reports" / "graph"
    raw_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    (raw_dir / "records.jsonl").write_text('{"pmid":"1"}\n', encoding="utf-8")
    (report_dir / "quality.md").write_text("# Report\n", encoding="utf-8")

    index = build_artifact_index([tmp_path / "data", tmp_path / "reports"])

    assert index.artifact_count == 2
    assert index.category_counts["raw"] == 1
    assert index.category_counts["graph_report"] == 1
    assert index.suffix_counts[".jsonl"] == 1
    assert index.artifacts[0].artifact_type == "jsonl_artifact"
    assert len(index.artifacts[0].sha256) == 64
    assert index.artifacts[0].modified_at_utc.endswith("+00:00")


def test_format_artifact_index_markdown_includes_artifacts(tmp_path: Path) -> None:
    path = tmp_path / "data" / "review"
    path.mkdir(parents=True)
    (path / "queue.csv").write_text("id\n1\n", encoding="utf-8")
    index = build_artifact_index([tmp_path])

    markdown = format_artifact_index_markdown(index)

    assert "# GBM-AI Artifact Index" in markdown
    assert "queue.csv" in markdown
    assert "Artifact Types" in markdown


def test_artifact_detail_finds_saved_index_entries(tmp_path: Path) -> None:
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    (processed_dir / "active_learning_batches.jsonl").write_text('{"batch_id":"ALBATCH-001"}\n', encoding="utf-8")
    index = build_artifact_index([tmp_path])
    index_path = tmp_path / "reports" / "artifact_index.json"
    save_artifact_index_json(index, index_path)

    report = load_artifact_detail("active_learning_batches", index_json=index_path)
    markdown = format_artifact_detail_markdown(report)

    assert report.match_count == 1
    assert report.artifacts[0].artifact_type == "active_learning_batch_plan"
    assert "Artifact Detail" in markdown


def test_artifact_index_classifies_workflow_artifacts(tmp_path: Path) -> None:
    graph_dir = tmp_path / "data" / "processed" / "trial"
    graph_dir.mkdir(parents=True)
    (graph_dir / "trial_graph_records.jsonl").write_text('{"nct_id":"NCT12345678"}\n', encoding="utf-8")
    review_dir = tmp_path / "data" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "evidence_reviewed_queue.jsonl").write_text('{"item_id":"1"}\n', encoding="utf-8")
    report_dir = tmp_path / "reports" / "graph"
    report_dir.mkdir(parents=True)
    (report_dir / "load_report.md").write_text("# Load\n", encoding="utf-8")

    index = build_artifact_index([tmp_path])
    by_name = {Path(entry.path).name: entry for entry in index.artifacts}

    assert by_name["trial_graph_records.jsonl"].artifact_type == "trial_graph_records"
    assert by_name["evidence_reviewed_queue.jsonl"].artifact_type == "reviewed_queue"
    assert by_name["load_report.md"].artifact_type == "graph_load_report"


def test_artifact_index_classifies_training_artifacts(tmp_path: Path) -> None:
    split_dir = tmp_path / "data" / "training" / "splits"
    split_dir.mkdir(parents=True)
    (split_dir / "ner_train.jsonl").write_text('{"label":"GENE"}\n', encoding="utf-8")
    label_dir = tmp_path / "data" / "training" / "label_maps"
    label_dir.mkdir(parents=True)
    (label_dir / "ner_label_map.json").write_text('{"label_to_id":{"GENE":0}}\n', encoding="utf-8")
    report_dir = tmp_path / "reports" / "training"
    report_dir.mkdir(parents=True)
    (report_dir / "baseline_report.md").write_text("# Baseline\n", encoding="utf-8")
    (report_dir / "train_gate.json").write_text('{"status":"dry_run_ready"}\n', encoding="utf-8")
    (report_dir / "evidence_metrics.json").write_text('{"accuracy":1.0}\n', encoding="utf-8")
    (report_dir / "evidence_run_manifest.json").write_text('{"task":"evidence_classification"}\n', encoding="utf-8")
    (report_dir / "evidence_predictions.jsonl").write_text('{"prediction":"1"}\n', encoding="utf-8")
    (report_dir / "evidence_model_card.md").write_text("# Model Card\n", encoding="utf-8")
    (report_dir / "evidence_smoke_summary.json").write_text('{"status":"completed"}\n', encoding="utf-8")
    (report_dir / "evidence_prediction_quality.md").write_text("# Quality\n", encoding="utf-8")
    (report_dir / "evidence_prediction_review_summary.md").write_text("# Summary\n", encoding="utf-8")
    (report_dir / "active_learning_candidates.md").write_text("# Active\n", encoding="utf-8")
    (report_dir / "pmid_split_manifest.md").write_text("# Split\n", encoding="utf-8")
    (report_dir / "evidence_label_repair.md").write_text("# Repair\n", encoding="utf-8")
    (report_dir / "gold_training_pack.md").write_text("# Gold Pack\n", encoding="utf-8")
    (report_dir / "relation_negatives.md").write_text("# Negatives\n", encoding="utf-8")
    (report_dir / "relation_dataset_quality.md").write_text("# Relation Quality\n", encoding="utf-8")
    (report_dir / "relation_training_pack.md").write_text("# Relation Pack\n", encoding="utf-8")
    (report_dir / "training_pack_comparison.md").write_text("# Comparison\n", encoding="utf-8")
    (report_dir / "model_registry_audit.md").write_text("# Audit\n", encoding="utf-8")
    (report_dir / "training_artifact_bundle.md").write_text("# Bundle\n", encoding="utf-8")
    (report_dir / "training_artifact_search.md").write_text("# Search\n", encoding="utf-8")
    (report_dir / "training_pack_leakage_audit.md").write_text("# Leakage\n", encoding="utf-8")
    (report_dir / "training_config_suite_review.md").write_text("# Suite\n", encoding="utf-8")
    (report_dir / "model_registry_remediation_plan.md").write_text("# Plan\n", encoding="utf-8")
    (report_dir / "training_label_drift.md").write_text("# Drift\n", encoding="utf-8")
    (report_dir / "training_provenance_audit.md").write_text("# Provenance\n", encoding="utf-8")
    (report_dir / "training_readiness_snapshot.md").write_text("# Snapshot\n", encoding="utf-8")
    (report_dir / "dashboard_training_manifest.md").write_text("# Dashboard\n", encoding="utf-8")
    (report_dir / "training_governance_suite.md").write_text("# Governance\n", encoding="utf-8")
    (report_dir / "evidence_training_pack.md").write_text("# Evidence Pack\n", encoding="utf-8")
    (report_dir / "training_config_review.md").write_text("# Config Review\n", encoding="utf-8")
    (split_dir / "relation_negatives.jsonl").write_text('{"label":"NO_RELATION"}\n', encoding="utf-8")
    (split_dir / "relation_training_pack.jsonl").write_text('{"label":"NO_RELATION"}\n', encoding="utf-8")
    review_dir = tmp_path / "data" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "evidence_prediction_review_queue.jsonl").write_text('{"item_id":"1"}\n', encoding="utf-8")
    (review_dir / "evidence_prediction_reviewed_queue.csv").write_text("item_id\n1\n", encoding="utf-8")
    (review_dir / "active_learning_candidates.jsonl").write_text('{"item_id":"1"}\n', encoding="utf-8")
    (review_dir / "active_learning_batch_reviewed_queue.jsonl").write_text('{"item_id":"1"}\n', encoding="utf-8")
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "curated_evidence_predictions.jsonl").write_text('{"source_pmid":"1"}\n', encoding="utf-8")
    (processed_dir / "evidence_overlay_graph_records.jsonl").write_text('{"pmid":"1"}\n', encoding="utf-8")
    (processed_dir / "normalized_graph_records.jsonl").write_text('{"pmid":"1"}\n', encoding="utf-8")
    (processed_dir / "qualifier_enriched_graph_records.jsonl").write_text('{"pmid":"1"}\n', encoding="utf-8")
    review_report_dir = tmp_path / "reports" / "review"
    review_report_dir.mkdir(parents=True)
    (review_report_dir / "curated_evidence_audit.md").write_text("# Audit\n", encoding="utf-8")
    (review_report_dir / "curation_smoke_workflow.md").write_text("# Smoke\n", encoding="utf-8")
    (review_report_dir / "curation_handoff_bundle.md").write_text("# Handoff\n", encoding="utf-8")
    (review_report_dir / "curation_handoff_validation.md").write_text("# Validation\n", encoding="utf-8")
    (review_report_dir / "curation_run_registry.json").write_text('{"entries":[]}\n', encoding="utf-8")
    (review_report_dir / "curation_run_browser.md").write_text("# Runs\n", encoding="utf-8")
    (review_report_dir / "curated_evidence_search.md").write_text("# Search\n", encoding="utf-8")
    (review_report_dir / "active_learning_batches.md").write_text("# Batches\n", encoding="utf-8")
    (review_report_dir / "active_learning_batch_status.md").write_text("# Status\n", encoding="utf-8")
    (review_report_dir / "active_learning_batch_roundtrip_import.md").write_text("# Roundtrip\n", encoding="utf-8")
    (review_report_dir / "artifact_detail.md").write_text("# Detail\n", encoding="utf-8")
    (review_report_dir / "evidence_overlay_promotion_gate.md").write_text("# Gate\n", encoding="utf-8")
    (review_report_dir / "overlay_revert.md").write_text("# Revert\n", encoding="utf-8")
    (review_report_dir / "scope_drift.md").write_text("# Scope\n", encoding="utf-8")
    (review_report_dir / "platform_regression.md").write_text("# Regression\n", encoding="utf-8")
    (review_report_dir / "adjudication_report.md").write_text("# Adjudication\n", encoding="utf-8")
    (review_report_dir / "curation_regression_pack.md").write_text("# Regression\n", encoding="utf-8")
    (review_report_dir / "gold_seed_manifest.md").write_text("# Gold\n", encoding="utf-8")
    (review_report_dir / "training_readiness.md").write_text("# Readiness\n", encoding="utf-8")
    (processed_dir / "active_learning_batches.jsonl").write_text('{"batch_id":"ALBATCH-001"}\n', encoding="utf-8")
    (processed_dir / "reverted_graph_records.jsonl").write_text('{"pmid":"1"}\n', encoding="utf-8")
    graph_report_dir = tmp_path / "reports" / "graph"
    graph_report_dir.mkdir(parents=True)
    (graph_report_dir / "evidence_overlay_diff.md").write_text("# Diff\n", encoding="utf-8")
    (graph_report_dir / "overlay_load_guard.md").write_text("# Guard\n", encoding="utf-8")
    (graph_report_dir / "relation_extraction_audit.md").write_text("# Audit\n", encoding="utf-8")
    (graph_report_dir / "entity_normalization.md").write_text("# Normalize\n", encoding="utf-8")
    (graph_report_dir / "qualifier_enrichment.md").write_text("# Qualifiers\n", encoding="utf-8")
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "checkpoint_registry.json").write_text('{"checkpoints":[]}\n', encoding="utf-8")

    index = build_artifact_index([tmp_path])
    by_name = {Path(entry.path).name: entry for entry in index.artifacts}

    assert by_name["ner_train.jsonl"].category == "training"
    assert by_name["ner_train.jsonl"].artifact_type == "training_split"
    assert by_name["ner_label_map.json"].artifact_type == "label_map"
    assert by_name["baseline_report.md"].artifact_type == "baseline_report"
    assert by_name["train_gate.json"].artifact_type == "training_gate_report"
    assert by_name["evidence_metrics.json"].artifact_type == "training_metrics"
    assert by_name["evidence_run_manifest.json"].artifact_type == "training_run_manifest"
    assert by_name["evidence_predictions.jsonl"].artifact_type == "evidence_predictions"
    assert by_name["evidence_model_card.md"].artifact_type == "model_card"
    assert by_name["evidence_smoke_summary.json"].artifact_type == "training_smoke_summary"
    assert by_name["evidence_prediction_quality.md"].artifact_type == "prediction_quality_report"
    assert by_name["evidence_prediction_review_summary.md"].artifact_type == "prediction_review_summary"
    assert by_name["active_learning_candidates.md"].artifact_type == "active_learning_report"
    assert by_name["pmid_split_manifest.md"].artifact_type == "pmid_split_manifest"
    assert by_name["evidence_label_repair.md"].artifact_type == "evidence_label_repair_report"
    assert by_name["gold_training_pack.md"].artifact_type == "gold_training_pack_report"
    assert by_name["relation_negatives.md"].artifact_type == "relation_negative_report"
    assert by_name["relation_dataset_quality.md"].artifact_type == "relation_dataset_quality_report"
    assert by_name["relation_training_pack.md"].artifact_type == "relation_training_pack_report"
    assert by_name["training_pack_comparison.md"].artifact_type == "training_pack_comparison_report"
    assert by_name["model_registry_audit.md"].artifact_type == "model_registry_audit_report"
    assert by_name["training_artifact_bundle.md"].artifact_type == "training_artifact_bundle_manifest"
    assert by_name["training_artifact_search.md"].artifact_type == "training_artifact_search_report"
    assert by_name["training_pack_leakage_audit.md"].artifact_type == "training_pack_leakage_audit_report"
    assert by_name["training_config_suite_review.md"].artifact_type == "training_config_suite_review_report"
    assert by_name["model_registry_remediation_plan.md"].artifact_type == "model_registry_remediation_plan"
    assert by_name["training_label_drift.md"].artifact_type == "training_label_drift_report"
    assert by_name["training_provenance_audit.md"].artifact_type == "training_provenance_audit_report"
    assert by_name["training_readiness_snapshot.md"].artifact_type == "training_readiness_snapshot"
    assert by_name["dashboard_training_manifest.md"].artifact_type == "dashboard_training_manifest"
    assert by_name["training_governance_suite.md"].artifact_type == "training_governance_suite_report"
    assert by_name["evidence_training_pack.md"].artifact_type == "evidence_training_pack_report"
    assert by_name["training_config_review.md"].artifact_type == "training_config_review_report"
    assert by_name["relation_negatives.jsonl"].artifact_type == "relation_negative_dataset"
    assert by_name["relation_training_pack.jsonl"].artifact_type == "relation_training_dataset"
    assert by_name["active_learning_candidates.jsonl"].artifact_type == "active_learning_candidates"
    assert by_name["active_learning_batch_reviewed_queue.jsonl"].artifact_type == "active_learning_batch_reviewed_queue"
    assert by_name["evidence_prediction_review_queue.jsonl"].artifact_type == "prediction_review_queue"
    assert by_name["evidence_prediction_reviewed_queue.csv"].artifact_type == "prediction_reviewed_queue_csv"
    assert by_name["curated_evidence_predictions.jsonl"].artifact_type == "curated_evidence_predictions"
    assert by_name["curated_evidence_audit.md"].artifact_type == "curated_evidence_audit"
    assert by_name["evidence_overlay_graph_records.jsonl"].artifact_type == "evidence_overlay_graph_records"
    assert by_name["normalized_graph_records.jsonl"].artifact_type == "normalized_graph_records"
    assert by_name["qualifier_enriched_graph_records.jsonl"].artifact_type == "qualifier_enriched_graph_records"
    assert by_name["evidence_overlay_diff.md"].artifact_type == "evidence_overlay_diff_report"
    assert by_name["overlay_load_guard.md"].artifact_type == "overlay_load_guard_report"
    assert by_name["curation_smoke_workflow.md"].artifact_type == "curation_smoke_workflow_report"
    assert by_name["curation_handoff_bundle.md"].artifact_type == "curation_handoff_bundle_manifest"
    assert by_name["curation_handoff_validation.md"].artifact_type == "curation_handoff_validation_report"
    assert by_name["curation_run_registry.json"].artifact_type == "curation_run_registry"
    assert by_name["curation_run_browser.md"].artifact_type == "curation_run_browser_report"
    assert by_name["curated_evidence_search.md"].artifact_type == "curated_evidence_search_report"
    assert by_name["active_learning_batches.md"].artifact_type == "active_learning_batch_report"
    assert by_name["active_learning_batches.jsonl"].artifact_type == "active_learning_batch_plan"
    assert by_name["active_learning_batch_status.md"].artifact_type == "active_learning_batch_status_report"
    assert by_name["active_learning_batch_roundtrip_import.md"].artifact_type == "active_learning_batch_roundtrip_report"
    assert by_name["artifact_detail.md"].artifact_type == "artifact_detail_report"
    assert by_name["evidence_overlay_promotion_gate.md"].artifact_type == "evidence_overlay_promotion_gate_report"
    assert by_name["relation_extraction_audit.md"].artifact_type == "relation_extraction_audit_report"
    assert by_name["scope_drift.md"].artifact_type == "scope_drift_report"
    assert by_name["platform_regression.md"].artifact_type == "platform_regression_report"
    assert by_name["gold_seed_manifest.md"].artifact_type == "gold_seed_manifest"
    assert by_name["adjudication_report.md"].artifact_type == "adjudication_report"
    assert by_name["entity_normalization.md"].artifact_type == "entity_normalization_report"
    assert by_name["qualifier_enrichment.md"].artifact_type == "qualifier_enrichment_report"
    assert by_name["training_readiness.md"].artifact_type == "training_readiness_report"
    assert by_name["overlay_revert.md"].artifact_type == "overlay_revert_report"
    assert by_name["reverted_graph_records.jsonl"].artifact_type == "reverted_graph_records"
    assert by_name["curation_regression_pack.md"].artifact_type == "curation_regression_pack_report"
    assert by_name["checkpoint_registry.json"].category == "model"
    assert by_name["checkpoint_registry.json"].artifact_type == "checkpoint_registry"
