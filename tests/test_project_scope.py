import json
from pathlib import Path

from gbmbert.knowledge_graph.explorer import EXPLORER_HTML


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "docs" / "PROJECT_SCOPE.json"
REQUIRED_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)


def test_project_scope_lockfile_records_active_and_future_phases() -> None:
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))

    assert scope["required_user_facing_warning"] == REQUIRED_WARNING
    assert scope["active_phases"] == [
        "Phase 1: PubMed ingestion and project scaffold",
        "Phase 2: Baseline biomedical extraction pipeline",
        "Phase 3: Knowledge graph schema, loader, inspection, and local graph review",
        "Phase 4 scaffold: GBM-BERT fine-tuning configs and dataset adapters",
        "Phase 7 scaffold: Streamlit dashboard shell",
    ]
    assert "Phase 4: GBM-BERT training execution and evaluation workflow" in scope["future_phases"]
    assert "Phase 7: Full Streamlit dashboard implementation" in scope["future_phases"]
    assert "local_knowledge_graph_explorer_prototype" in scope["prototype_modules"]
    assert "streamlit_dashboard_shell" in scope["prototype_modules"]


def test_project_scope_lockfile_preserves_prohibited_behavior() -> None:
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))

    assert scope["prohibited_behavior"] == [
        "recommend_treatment_for_real_patient",
        "generate_clinical_instructions",
        "present_as_medical_device",
        "claim_predictive_clinical_accuracy",
    ]
    assert "patient_specific_treatment_recommendations" in scope["current_non_goals"]
    assert "surface_source_pmids_for_displayed_claims" in scope["evidence_guardrails"]
    assert "visually_distinguish_evidence_tiers" in scope["evidence_guardrails"]
    assert "pubmed_query_packs" in scope["implemented_modules"]
    assert "clinicaltrials_read_only_ingestion" in scope["implemented_modules"]
    assert "evidence_classification_placeholder" in scope["implemented_modules"]
    assert "knowledge_graph_relation_qualifiers" in scope["implemented_modules"]
    assert "annotation_guidelines_pack" in scope["implemented_modules"]
    assert "gold_seed_dataset_builder" in scope["implemented_modules"]
    assert "annotation_adjudication_report" in scope["implemented_modules"]
    assert "entity_normalization_scaffold" in scope["implemented_modules"]
    assert "gbmbert_training_scaffold" in scope["implemented_modules"]
    assert "gbmbert_pmid_safe_dataset_splitter" in scope["implemented_modules"]
    assert "gbmbert_evidence_label_repair" in scope["implemented_modules"]
    assert "gbmbert_gold_training_pack_workflow" in scope["implemented_modules"]
    assert "gbmbert_ner_readiness_gate_upgrade" in scope["implemented_modules"]
    assert "gbmbert_relation_negative_sampler" in scope["implemented_modules"]
    assert "gbmbert_relation_dataset_quality_v2" in scope["implemented_modules"]
    assert "gbmbert_evidence_training_pack" in scope["implemented_modules"]
    assert "gbmbert_training_config_review_gate" in scope["implemented_modules"]
    assert "gbmbert_training_readiness_gate" in scope["implemented_modules"]
    assert "gbmbert_prediction_review_queue" in scope["implemented_modules"]
    assert "gbmbert_prediction_review_csv_import" in scope["implemented_modules"]
    assert "gbmbert_active_learning_candidate_export" in scope["implemented_modules"]
    assert "gbmbert_curated_evidence_audit" in scope["implemented_modules"]
    assert "gbmbert_evidence_graph_overlay" in scope["implemented_modules"]
    assert "gbmbert_overlay_load_guard" in scope["implemented_modules"]
    assert "gbmbert_curation_smoke_workflow" in scope["implemented_modules"]
    assert "gbmbert_curation_handoff_bundle" in scope["implemented_modules"]
    assert "gbmbert_curation_handoff_validation" in scope["implemented_modules"]
    assert "gbmbert_curation_run_registry" in scope["implemented_modules"]
    assert "gbmbert_curation_run_browser" in scope["implemented_modules"]
    assert "gbmbert_curated_evidence_search" in scope["implemented_modules"]
    assert "gbmbert_prediction_decision_audit_trail" in scope["implemented_modules"]
    assert "gbmbert_active_learning_batch_planner" in scope["implemented_modules"]
    assert "gbmbert_active_learning_batch_status_tracker" in scope["implemented_modules"]
    assert "gbmbert_active_learning_batch_csv_roundtrip" in scope["implemented_modules"]
    assert "gbmbert_evidence_overlay_revert" in scope["implemented_modules"]
    assert "gbmbert_curation_regression_pack" in scope["implemented_modules"]
    assert "artifact_detail_drilldown" in scope["implemented_modules"]
    assert "gbmbert_explorer_overlay_filters" in scope["implemented_modules"]
    assert "gbmbert_evidence_overlay_promotion_gate" in scope["implemented_modules"]
    assert "gbmbert_explorer_curation_links" in scope["implemented_modules"]
    assert "relation_extraction_quality_audit" in scope["implemented_modules"]
    assert "relation_qualifier_enrichment" in scope["implemented_modules"]
    assert "scope_drift_monitor" in scope["implemented_modules"]
    assert "platform_regression_command" in scope["implemented_modules"]
    assert "local_verification_command" in scope["implemented_modules"]
    assert "gbmbert_strict_training_governance_profile" in scope["implemented_modules"]
    assert "gbmbert_current_ner_smoke_config" in scope["implemented_modules"]
    assert "gbmbert_gold_pack_expansion_plan" in scope["implemented_modules"]
    assert "gbmbert_full_evidence_label_coverage_plan" in scope["implemented_modules"]
    assert "streamlit_dashboard_shell" in scope["implemented_modules"]


def test_user_facing_docs_and_explorer_keep_research_warning() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    annotation_guidelines = (ROOT / "docs" / "ANNOTATION_GUIDELINES.md").read_text(encoding="utf-8")
    wireframe = (ROOT / "reports" / "wireframes" / "kg_explorer.md").read_text(encoding="utf-8")

    assert REQUIRED_WARNING in readme
    assert REQUIRED_WARNING in annotation_guidelines
    assert REQUIRED_WARNING in wireframe
    assert REQUIRED_WARNING in EXPLORER_HTML


def test_scope_docs_avoid_recommendation_language_outside_guardrails() -> None:
    scope_doc = (ROOT / "docs" / "RESEARCH_SCOPE_V2.md").read_text(encoding="utf-8")

    assert "biased recommendations" not in scope_doc
    assert "biased research analyses" in scope_doc
