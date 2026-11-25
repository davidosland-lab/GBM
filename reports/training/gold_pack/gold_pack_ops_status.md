# Gold Pack Ops Status

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Created (UTC): `2026-07-21T01:16:44Z`
- Differentiation bet: Invest in gold-pack / curation / governance depth rather than lit-mining scale or clinical ranking.
- Gold pack report: `reports\training\gold_pack\gold_training_pack.json`
- Threshold config: `configs\training\gold_pack_promotion_thresholds.json`
- Pack ready: True
- Promotable (hard floors): True
- Source PMIDs: 951 (delta to floor: 0)
- Dual-review pending rows: 174
- Active-learning pending rows: 101
- Clinical validity claimed: False

## Task Counts
- evidence: 835
- ner: 8070
- relation: 294

## Sparse NER Focus
- CELL_STATE: 131
- PATHWAY: 93
- TRIAL_PHASE: 71
- UNKNOWN: 59

## Soft Densify Gaps (non-blocking)
- evidence/1: 93 (soft floor 120; need +27)
- evidence/2: 97 (soft floor 120; need +23)
- evidence/4: 101 (soft floor 120; need +19)
- evidence/5: 94 (soft floor 120; need +26)
- ner/CELL_STATE: 131 (soft floor 150; need +19)
- ner/PATHWAY: 93 (soft floor 120; need +27)
- ner/TRIAL_PHASE: 71 (soft floor 100; need +29)
- ner/UNKNOWN: 59 (soft floor 80; need +21)
- relation/IMPROVES: 40 (soft floor 60; need +20)
- relation/PREDICTS: 46 (soft floor 60; need +14)
- relation/WORSENS: 56 (soft floor 60; need +4)

## Hard Promotion Blockers
- none

## Dual-Review Backlog
- `data\research\review_batches\round33\span_review_r1_round33.jsonl` (entity_span): pending=48/48 decided=0
- `data\research\review_batches\round33\span_review_r2_round33.jsonl` (entity_span): pending=48/48 decided=0
- `data\research\review_batches\round26\gold_entities_round26_span_reviewed.jsonl` (entity_span): pending=22/22 decided=0
- `data\research\review_batches\round28\entity_span_review_round28.jsonl` (entity_span): pending=56/56 decided=0 - legacy unfinished span queue; prefer latest sparse densify round

## Active-Learning Backlog
- `data\processed\curation_regression_pack\active_learning_batches_round26.jsonl`: pending=100/100 decided=0
- `data\processed\curation_regression_pack\active_learning_batches.jsonl`: pending=1/1 decided=0

## Next Actions
- Hard promotion floors met - deepen quality via soft densify / dual-review (not lit-mining scale).
- Prioritize soft densify gaps: evidence/1(+27), evidence/2(+23), evidence/4(+19), evidence/5(+26), ner/CELL_STATE(+19), ner/PATHWAY(+27).
- Adjudicate dual-review backlog (174 pending). Start with `data\research\review_batches\round33\span_review_r1_round33.jsonl`.
- Clear active-learning pending rows (101). Queue: `data\processed\curation_regression_pack\active_learning_batches_round26.jsonl`.
- After human decisions: finalize/promote curated round -> `gbmbert-rebuild-curated-rounds`.
- Keep preferred research checkpoints (evidence v9 / relation v3 / BIO NER v6) until freeze-split compare.
- Do not claim clinical validation; promotable != patient-ready model.

## Notes
- Ops status is research-governance observability only.
- Hard promotion floors and soft densify targets are distinct; soft gaps do not block promotable.
- Do not invent dual-review labels; adjudicate pending queues as a human.

## Label Counts
### evidence
- 0: 120
- 1: 93
- 2: 97
- 3: 330
- 4: 101
- 5: 94

### ner
- BIOMARKER: 319
- CELL_STATE: 131
- CELL_TYPE: 202
- DELIVERY_MODIFIER: 248
- DISEASE: 3466
- DRUG: 886
- GENE: 654
- OUTCOME: 1356
- PATHWAY: 93
- TREATMENT: 585
- TRIAL_PHASE: 71
- UNKNOWN: 59

### relation
- ASSOCIATED_WITH: 78
- IMPROVES: 40
- NO_RELATION: 74
- PREDICTS: 46
- WORSENS: 56
