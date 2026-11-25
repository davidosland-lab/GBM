# GBM-AI Curated Round Rebuild

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Observe-only research rebuild of the curated-fixture report chain. It does not promote a dataset, train a model, or claim a validated GBM-BERT model exists. Run `gbmbert-verify-local` and the CI summary afterward for platform verification.

- Created UTC: 2026-07-23T07:32:49.584797+00:00
- Curated dir: `data\training\curated_expansion`
- Import dir: `data\training\curated_import`
- Rounds: 33
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
- Round 8: `data\training\curated_expansion\evidence_round8.jsonl`
- Round 9: `data\training\curated_expansion\evidence_round9.jsonl`
- Round 10: `data\training\curated_expansion\evidence_round10.jsonl`
- Round 11: `data\training\curated_expansion\evidence_round11.jsonl`
- Round 12: `data\training\curated_expansion\evidence_round12.jsonl`
- Round 13: `data\training\curated_expansion\evidence_round13.jsonl`
- Round 14: `data\training\curated_expansion\evidence_round14.jsonl`
- Round 15: `data\training\curated_expansion\evidence_round15.jsonl`
- Round 16: `data\training\curated_expansion\evidence_round16.jsonl`
- Round 17: `data\training\curated_expansion\evidence_round17.jsonl`
- Round 18: `data\training\curated_expansion\evidence_round18.jsonl`
- Round 19: `data\training\curated_expansion\evidence_round19.jsonl`
- Round 20: `data\training\curated_expansion\evidence_round20.jsonl`
- Round 21: `data\training\curated_expansion\evidence_round21.jsonl`
- Round 22: `data\training\curated_expansion\evidence_round22.jsonl`
- Round 23: `data\training\curated_expansion\evidence_round23.jsonl`
- Round 24: `data\training\curated_expansion\evidence_round24.jsonl`
- Round 25: `data\training\curated_expansion\evidence_round25.jsonl`
- Round 26: `data\training\curated_expansion\evidence_round26.jsonl`
- Round 27: `data\training\curated_expansion\evidence_round27.jsonl`
- Round 28: `data\training\curated_expansion\evidence_round28.jsonl`
- Round 29: `data\training\curated_expansion\evidence_round29.jsonl`
- Round 30: `data\training\curated_expansion\evidence_round30.jsonl`
- Round 31: `data\training\curated_expansion\evidence_round31.jsonl`
- Round 32: `data\training\curated_expansion\evidence_round32.jsonl`
- Round 34: `data\training\curated_expansion\evidence_round34.jsonl`

## Ordered Steps
### curated_fixture_import
- Status: pass
- Return code: 0
- Detail: - reviewed_queue: `data\training\curated_import\combined_reviewed_queue.jsonl` | ## Warnings | - none

### curated_provenance_diff
- Status: pass
- Return code: 0
- Detail: - [error] changed: curated observation changed across batches (reviewer) for reviewed_queue|relation:42399440:3 | - `data\training\curated_expansion\gold_reviewed_queue_round14.jsonl` row 53; PMID `42399440`; task `relation`; label `IMPROVES`; reviewer `agent-curation`; status `accepted` | - `data\training\curated_expansion\gold_reviewed_queue_round34.jsonl` row 184; PMID `42399440`; task `relation`; label `IMPROVES`; reviewer `david`; status `accepted`

### gold_seed
- Status: pass
- Return code: 0
- Detail: - relation: `data\training\gold_seed\gold_relations.jsonl` | ## Warnings | - none

### gold_training_pack
- Status: pass
- Return code: 0
- Detail: ## Warnings | - evidence: 86 duplicate example(s) | - relation: 7 duplicate example(s)

### evidence_training_pack
- Status: pass
- Return code: 0
- Detail: - Label maps: `data\training\evidence_pack\label_maps` | ## Warnings | - evidence: 86 duplicate example(s)

### relation_training_pack
- Status: pass
- Return code: 0
- Detail: - 1 relation example(s) have identical head and tail endpoints | - 7 duplicate relation example(s) | - relation: 7 duplicate example(s)

### relation_dataset_quality
- Status: pass
- Return code: 0
- Detail: ## Warnings | - 1 relation example(s) have identical head and tail endpoints | - 7 duplicate relation example(s)

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
- Detail: - evidence/gold: 898 shared PMID(s): 10853323, 11138924, 11717820, 11939587, 12124496 | - evidence/relation: 154 shared PMID(s): 15758010, 18676355, 18752056, 18757334, 19269895 | - gold/relation: 159 shared PMID(s): 15758010, 16944365, 17325429, 18665745, 18676355

### training_pack_comparison
- Status: pass
- Return code: 0
- Detail: - Warnings: | - evidence: 86 duplicate example(s) | - relation: 7 duplicate example(s)

### training_provenance_audit
- Status: pass
- Return code: 0
- Detail: - synthetic_no_relation: 3 | ## Warnings | - none

### training_readiness_snapshot
- Status: pass
- Return code: 0
- Detail: - Dashboard reports: 14 | ## Warnings | - none

### dashboard_training_manifest
- Status: pass
- Return code: 0
- Detail: - Current config failed: 0 | - Scaffold configs: 5 | - Registry audit passed: True

### gold_pack_promotion_review
- Status: pass
- Return code: 0
- Detail: ## Blockers | - gold pack readiness report is not ready | - relation labels below 20 examples: ENHANCES_DELIVERY_OF=2, SYNERGIZES_WITH=5, TARGETS=2

### gold_pack_promotion_plan
- Status: pass
- Return code: 0
- Detail: - relation: 0 example(s) | ## Suggested Batches | - `relation-label-balance-001` (label_balance, relation): 51 example(s), 0 new PMID(s); ENHANCES_DELIVERY_OF +18, SYNERGIZES_WITH +15, TARGETS +18. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.

### training_governance_suite
- Status: pass
- Return code: 0
- Detail: - registry_remediation: `reports\training\governance\model_registry_remediation_plan.json` | ## Warnings | - none

### strict_training_governance
- Status: pass
- Return code: 0
- Detail: - registry_remediation: `reports\training\governance_strict\model_registry_remediation_plan.json` | ## Warnings | - strict audit includes 5 scaffold config(s) that are not promotion-ready by default

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
