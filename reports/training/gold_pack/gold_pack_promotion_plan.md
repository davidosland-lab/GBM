# Gold Pack Promotion Planning Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This is a scaffold-only curation planning report. It does not promote a dataset, validate a trained GBM-BERT model, or support clinical decision-making.

- Promotion review: `reports\training\gold_pack\gold_pack_promotion_review.json`
- Scaffold only: True
- Promotable now: False
- Source PMIDs still needed: 14
- Suggested future batches: 14

## Compact Summary
### Task Remaining Examples
- evidence: 58
- ner: 16
- relation: 58

### Label Remaining Examples
- evidence: 0=3, 1=3, 2=3, 3=3, 4=3, 5=3
- ner: BIOMARKER=3, CELL_STATE=3, CELL_TYPE=3, DELIVERY_MODIFIER=3, DISEASE=3, DRUG=3, GENE=3, OUTCOME=3, PATHWAY=3, TREATMENT=3, TRIAL_PHASE=3, UNKNOWN=3
- relation: none

### Label Balance vs Task Volume
- evidence: label-floor 18 of 58 task-volume example(s); 40 remaining after label balancing
- ner: label-floor 36 of 16 task-volume example(s); 0 remaining after label balancing
- relation: label-floor 0 of 58 task-volume example(s); 58 remaining after label balancing

### Source PMID Batches
- `source-pmid-expansion-001`: 6 new PMID(s)
- `source-pmid-expansion-002`: 6 new PMID(s)
- `source-pmid-expansion-003`: 2 new PMID(s)

## Task Deltas
- evidence: 58 example(s)
- ner: 16 example(s)
- relation: 58 example(s)

## Suggested Batches
- `evidence-label-balance-001` (label_balance, evidence): 9 example(s), 0 new PMID(s); 0 +3, 1 +3, 2 +3. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
- `evidence-label-balance-002` (label_balance, evidence): 9 example(s), 0 new PMID(s); 3 +3, 4 +3, 5 +3. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
- `evidence-volume-001` (task_volume, evidence): 24 example(s), 0 new PMID(s); balanced/general. Add balanced reviewed examples for the task-volume delta remaining after label-floor batches.
- `evidence-volume-002` (task_volume, evidence): 16 example(s), 0 new PMID(s); balanced/general. Add balanced reviewed examples for the task-volume delta remaining after label-floor batches.
- `ner-label-balance-001` (label_balance, ner): 9 example(s), 0 new PMID(s); BIOMARKER +3, CELL_STATE +3, CELL_TYPE +3. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
- `ner-label-balance-002` (label_balance, ner): 9 example(s), 0 new PMID(s); DELIVERY_MODIFIER +3, DISEASE +3, DRUG +3. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
- `ner-label-balance-003` (label_balance, ner): 9 example(s), 0 new PMID(s); GENE +3, OUTCOME +3, PATHWAY +3. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
- `ner-label-balance-004` (label_balance, ner): 9 example(s), 0 new PMID(s); TREATMENT +3, TRIAL_PHASE +3, UNKNOWN +3. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
- `relation-volume-001` (task_volume, relation): 24 example(s), 0 new PMID(s); balanced/general. Add balanced reviewed examples for the task-volume delta remaining after label-floor batches.
- `relation-volume-002` (task_volume, relation): 24 example(s), 0 new PMID(s); balanced/general. Add balanced reviewed examples for the task-volume delta remaining after label-floor batches.
- `relation-volume-003` (task_volume, relation): 10 example(s), 0 new PMID(s); balanced/general. Add balanced reviewed examples for the task-volume delta remaining after label-floor batches.
- `source-pmid-expansion-001` (source_pmid_expansion, all): 0 example(s), 6 new PMID(s); balanced/general. Select additional source PMIDs for future reviewed curation batches.
- `source-pmid-expansion-002` (source_pmid_expansion, all): 0 example(s), 6 new PMID(s); balanced/general. Select additional source PMIDs for future reviewed curation batches.
- `source-pmid-expansion-003` (source_pmid_expansion, all): 0 example(s), 2 new PMID(s); balanced/general. Select additional source PMIDs for future reviewed curation batches.
