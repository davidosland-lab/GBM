# Gold Pack Promotion Planning Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This is a scaffold-only curation planning report. It does not promote a dataset, validate a trained GBM-BERT model, or support clinical decision-making.

- Promotion review: `reports\training\gold_pack\gold_pack_promotion_review.json`
- Scaffold only: True
- Promotable now: False
- Source PMIDs still needed: 0
- Suggested future batches: 1
- Overall label-floor coverage of task deltas: 100.0%

## Compact Summary
### Task Remaining Examples
- evidence: 0
- ner: 0
- relation: 0

### Label Remaining Examples
- evidence: none
- ner: none
- relation: ENHANCES_DELIVERY_OF=18, SYNERGIZES_WITH=15, TARGETS=18

### Label Balance vs Task Volume
- evidence: label-floor 0 of 0 task-volume example(s); 0 remaining after label balancing
- ner: label-floor 0 of 0 task-volume example(s); 0 remaining after label balancing
- relation: label-floor 51 of 0 task-volume example(s); 0 remaining after label balancing

### Task Delta Coverage
- evidence: 100.0% covered by label-floor batches, 0.0% remaining as raw task volume (delta 0)
- ner: 100.0% covered by label-floor batches, 0.0% remaining as raw task volume (delta 0)
- relation: 100.0% covered by label-floor batches, 0.0% remaining as raw task volume (delta 0)

### Source PMID Batches
- none

## Task Deltas
- evidence: 0 example(s)
- ner: 0 example(s)
- relation: 0 example(s)

## Suggested Batches
- `relation-label-balance-001` (label_balance, relation): 51 example(s), 0 new PMID(s); ENHANCES_DELIVERY_OF +18, SYNERGIZES_WITH +15, TARGETS +18. Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.
