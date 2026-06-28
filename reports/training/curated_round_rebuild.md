# GBM-AI Curated Round Rebuild

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Observe-only research rebuild of the curated-fixture report chain. It does not promote a dataset, train a model, or claim a validated GBM-BERT model exists. Run `gbmbert-verify-local` and the CI summary afterward for platform verification.

- Created UTC: 2026-06-28T09:41:04.867178+00:00
- Curated dir: `data\training\curated_expansion`
- Import dir: `data\training\curated_import`
- Rounds: 7
- Passed: True
- Steps: 20/20 passed

## Rounds
- Round 1: `data\training\curated_expansion\evidence_full_label.jsonl`
- Round 2: `data\training\curated_expansion\evidence_round2.jsonl`
- Round 3: `data\training\curated_expansion\evidence_round3.jsonl`
- Round 4: `data\training\curated_expansion\evidence_round4.jsonl`
- Round 5: `data\training\curated_expansion\evidence_round5.jsonl`
- Round 6: `data\training\curated_expansion\evidence_round6.jsonl`
- Round 7: `data\training\curated_expansion\evidence_round7.jsonl`

## Ordered Steps
### curated_fixture_import
- Status: pass
- Return code: 0
- Detail: - reviewed_queue: `data\training\curated_import\combined_reviewed_queue.jsonl` | ## Warnings | - none

### curated_provenance_diff
- Status: pass
- Return code: 0
- Detail: - Review statuses: accepted=12 | ## Findings | - none

### gold_seed
- Status: pass
- Return code: 0
- Detail: - relation: `data\training\gold_seed\gold_relations.jsonl` | ## Warnings | - none

### gold_training_pack
- Status: pass
- Return code: 0
- Detail: - training_readiness_md: `reports\training\gold_pack\training_readiness.md` | ## Warnings | - none

### evidence_training_pack
- Status: pass
- Return code: 0
- Detail: - Label maps: `data\training\evidence_pack\label_maps` | ## Warnings | - none

### relation_training_pack
- Status: pass
- Return code: 0
- Detail: - training_readiness_md: `reports\training\relation_pack\relation_training_pack_readiness.md` | ## Warnings | - none

### relation_dataset_quality
- Status: pass
- Return code: 0
- Detail: - PREDICTS: 16 | ## Warnings | - none

### training_config_suite_review
- Status: pass
- Return code: 0
- Detail: - none | ## Scaffold Warnings | - none

### training_label_drift
- Status: pass
- Return code: 0
- Detail: - Missing from dataset: none | ## Warnings | - none

### training_pack_leakage_audit
- Status: pass
- Return code: 0
- Detail: - evidence/gold: 42 shared PMID(s): 15758010, 23209033, 26109046, 27475281, 28967586 | - evidence/relation: 42 shared PMID(s): 15758010, 23209033, 26109046, 27475281, 28967586 | - gold/relation: 42 shared PMID(s): 15758010, 23209033, 26109046, 27475281, 28967586

### training_pack_comparison
- Status: pass
- Return code: 0
- Detail: - none | - Warnings: | - none

### training_provenance_audit
- Status: pass
- Return code: 0
- Detail: - synthetic_no_relation: 3 | ## Warnings | - none

### training_readiness_snapshot
- Status: pass
- Return code: 0
- Detail: - Dashboard reports: 13 | ## Warnings | - none

### dashboard_training_manifest
- Status: pass
- Return code: 0
- Detail: - Current config failed: 0 | - Scaffold configs: 2 | - Registry audit passed: True

### gold_pack_promotion_review
- Status: pass
- Return code: 0
- Detail: - ner labels below 10 examples: BIOMARKER=8, CELL_STATE=8, CELL_TYPE=8, DELIVERY_MODIFIER=8, DISEASE=8, DRUG=7, GENE=9, OUTCOME=8, PATHWAY=8, TREATMENT=9, TRIAL_PHASE=8, UNKNOWN=7 | - relation has 48 examples; needs at least 100 | - source PMID count is 42; needs at least 50

### gold_pack_promotion_plan
- Status: pass
- Return code: 0
- Detail: - `relation-volume-003` (task_volume, relation): 4 example(s), 0 new PMID(s); balanced/general. Add balanced reviewed examples for the task-volume delta remaining after label-floor batches. | - `source-pmid-expansion-001` (source_pmid_expansion, all): 0 example(s), 6 new PMID(s); balanced/general. Select additional source PMIDs for future reviewed curation batches. | - `source-pmid-expansion-002` (source_pmid_expansion, all): 0 example(s), 2 new PMID(s); balanced/general. Select additional source PMIDs for future reviewed curation batches.

### training_governance_suite
- Status: pass
- Return code: 0
- Detail: - registry_remediation: `reports\training\governance\model_registry_remediation_plan.json` | ## Warnings | - none

### strict_training_governance
- Status: pass
- Return code: 0
- Detail: - registry_remediation: `reports\training\governance_strict\model_registry_remediation_plan.json` | ## Warnings | - strict audit includes 2 scaffold config(s) that are not promotion-ready by default

### governance_detail_export
- Status: pass
- Return code: 0
- Detail: | Training config suite | available | `reports\training\training_config_suite_review.md` | True | `reports\training\training_config_suite_review.json` | True | | | Training label drift | available | `reports\training\training_label_drift.md` | True | `reports\training\training_label_drift.json` | True | | | Training pack comparison | available | `reports\training\training_pack_comparison.md` | True | `reports\training\training_pack_comparison.json` | True |

### governance_detail_contract
- Status: pass
- Return code: 0
- Detail: - none | ## Malformed Required Rows | - none

## Warnings
- none
