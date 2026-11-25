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
        "Phase 4: GBM-BERT research training criteria satisfied (deepen gold-pack ops / curation / governance)",
        "Phase 5: Tumour simulation research prototype (post-MVP deepening + toy fitting stub)",
        "Phase 6: Treatment scenario ranking research prototype (trade-off scores)",
        "Phase 7: Streamlit research operations console with live runners (literature → extract → graph → curation → training artifacts → sim/rank)",
    ]
    assert "Phase 6: Treatment strategy expansions beyond toy ranking (real eligibility/CDS remain out of scope)" in scope["future_phases"]
    assert "Phase 7: Further research-console UX polish (production clinical / hospital CDS dashboard remains out of scope)" in scope["future_phases"]
    assert "local_knowledge_graph_explorer_prototype" in scope["prototype_modules"]
    assert "streamlit_dashboard_shell" in scope["prototype_modules"]
    assert "phase5_tumour_simulation_mvp" in scope["prototype_modules"]
    assert "phase6_treatment_scenario_ranking" in scope["prototype_modules"]
    assert "dashboard_live_research_runners" in scope["prototype_modules"]
    assert "dashboard_research_operations_console" in scope["prototype_modules"]
    assert "phase5_tumour_simulation_mvp" in scope["implemented_modules"]
    assert "phase5_monte_carlo_sweeps" in scope["implemented_modules"]
    assert "phase5_toy_parameter_fitting_stub" in scope["implemented_modules"]
    assert "phase6_treatment_strategy_cli" in scope["implemented_modules"]
    assert "phase6_toy_toxicity_tradeoff_scores" in scope["implemented_modules"]
    assert "dashboard_live_research_runners" in scope["implemented_modules"]
    assert "dashboard_knowledge_graph_live_runner" in scope["implemented_modules"]
    assert "dashboard_prediction_curation_live_runner" in scope["implemented_modules"]
    assert "dashboard_training_artifacts_live_runner" in scope["implemented_modules"]
    assert "dashboard_research_operations_console" in scope["implemented_modules"]
    assert "clinically_validated_tumour_simulator" in scope["current_non_goals"]
    assert "treatment_optimizer" in scope["current_non_goals"]
    assert "real_pk_pd_modelling" in scope["current_non_goals"]
    assert "patient_eligibility_cds" in scope["current_non_goals"]
    assert "tumour_simulator" not in scope["current_non_goals"]


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
    assert "local_verification_ci_workflow" in scope["implemented_modules"]
    assert "ci_verification_artifact_reporting" in scope["implemented_modules"]
    assert "artifact_policy_check" in scope["implemented_modules"]
    assert "launcher_menu_workflow_groups" in scope["implemented_modules"]
    assert "launcher_menu_smoke_check" in scope["implemented_modules"]
    assert "gbmbert_strict_training_governance_profile" in scope["implemented_modules"]
    assert "gbmbert_strict_label_drift_alignment" in scope["implemented_modules"]
    assert "gbmbert_curated_fixture_import" in scope["implemented_modules"]
    assert "gbmbert_gold_pack_promotion_review" in scope["implemented_modules"]
    assert "gbmbert_gold_pack_ops_status" in scope["implemented_modules"]
    assert "gbmbert_sparse_densify_dual_review_batch" in scope["implemented_modules"]
    assert "gold_pack_ops_runbook" in scope["implemented_modules"]
    assert "lit_mining_scale_as_primary_differentiation" in scope["current_non_goals"]
    assert "clinical_ranking_cds_competition" in scope["current_non_goals"]
    assert "gold-pack" in scope["differentiation_bet"].lower()
    assert "gbmbert_curated_multi_file_import" in scope["implemented_modules"]
    assert "gbmbert_curated_provenance_diff" in scope["implemented_modules"]
    assert "gbmbert_promotion_threshold_delta_review" in scope["implemented_modules"]
    assert "ci_report_summary_input_hardening" in scope["implemented_modules"]
    assert "dashboard_governance_detail_links" in scope["implemented_modules"]
    assert "gbmbert_third_curated_expansion_round" in scope["implemented_modules"]
    assert "gbmbert_fourth_curated_expansion_round" in scope["implemented_modules"]
    assert "dashboard_governance_detail_export" in scope["implemented_modules"]
    assert "ci_summary_artifact_contract" in scope["implemented_modules"]
    assert "gbmbert_promotion_planning_report" in scope["implemented_modules"]
    assert "gbmbert_fifth_curated_expansion_round" in scope["implemented_modules"]
    assert "gbmbert_promotion_planning_ux_refinement" in scope["implemented_modules"]
    assert "dashboard_governance_detail_contract" in scope["implemented_modules"]
    assert "launcher_report_shortcuts" in scope["implemented_modules"]
    assert "gbmbert_promotion_threshold_config" in scope["implemented_modules"]
    assert "ci_markdown_report_summary" in scope["implemented_modules"]
    assert "dashboard_governance_status_refresh" in scope["implemented_modules"]
    assert "gbmbert_larger_gold_pack_curation_round" in scope["implemented_modules"]
    assert "gbmbert_current_ner_smoke_config" in scope["implemented_modules"]
    assert "gbmbert_gold_pack_expansion_plan" in scope["implemented_modules"]
    assert "gbmbert_full_evidence_label_coverage_plan" in scope["implemented_modules"]
    assert "gbmbert_curated_evidence_label_expansion" in scope["implemented_modules"]
    assert "gbmbert_gold_ner_expansion" in scope["implemented_modules"]
    assert "gbmbert_gold_relation_expansion" in scope["implemented_modules"]
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
