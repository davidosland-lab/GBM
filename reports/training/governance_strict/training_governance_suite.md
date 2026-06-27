# GBM-BERT Training Governance Suite

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Output directory: `reports\training\governance_strict`
- Steps: 10
- Passed: False

## Artifacts
- bundle: `reports\training\governance_strict\bundle\training_artifact_bundle.json`
- config_suite: `reports\training\governance_strict\training_config_suite_review.json`
- dashboard_manifest: `reports\training\governance_strict\dashboard_training_manifest.json`
- label_drift: `reports\training\governance_strict\training_label_drift.json`
- leakage_audit: `reports\training\governance_strict\training_pack_leakage_audit.json`
- pack_comparison: `reports\training\governance_strict\training_pack_comparison.json`
- provenance_audit: `reports\training\governance_strict\training_provenance_audit.json`
- readiness_snapshot: `reports\training\governance_strict\training_readiness_snapshot.json`
- registry_audit: `reports\training\governance_strict\model_registry_audit.json`
- registry_remediation: `reports\training\governance_strict\model_registry_remediation_plan.json`

## Warnings
- configs\training\gbmbert_evidence_pubmedbert.json: scaffold pending (config label_set labels missing from dataset: 2, 3, 4, 5; label map labels do not match config label_set)
- configs\training\gbmbert_ner_pubmedbert.json: scaffold pending (config label_set labels missing from dataset: CELL_STATE, PATHWAY, TRIAL_PHASE, UNKNOWN; label map labels do not match config label_set)
