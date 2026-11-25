# Gold Pack Promotion Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Gold pack report: `reports\training\gold_pack\gold_training_pack.json`
- Threshold config: `configs\training\gold_pack_promotion_thresholds.json`
- Pack ready: False
- Promotable: False
- Minimum examples per task: 200
- Minimum examples per label: 20
- Minimum source PMIDs: 100
- Observed source PMIDs: 1014
- Additional source PMIDs needed: 0

## Task Counts
- evidence: 1016
- ner: 8576
- relation: 313

## Promotion Deltas
- evidence: 0 additional example(s) needed
- ner: 0 additional example(s) needed
- relation: 0 additional example(s) needed

## Label Counts
### evidence
- 0: 175
- 1: 114
- 2: 115
- 3: 393
- 4: 111
- 5: 108

### ner
- BIOMARKER: 320
- CELL_STATE: 131
- CELL_TYPE: 212
- DELIVERY_MODIFIER: 290
- DISEASE: 3738
- DRUG: 928
- GENE: 672
- OUTCOME: 1424
- PATHWAY: 93
- TREATMENT: 638
- TRIAL_PHASE: 71
- UNKNOWN: 59

### relation
- ASSOCIATED_WITH: 82
- ENHANCES_DELIVERY_OF: 2
- IMPROVES: 44
- NO_RELATION: 74
- PREDICTS: 46
- SYNERGIZES_WITH: 5
- TARGETS: 2
- WORSENS: 58

## Label Deltas
### evidence
- none

### ner
- none

### relation
- ENHANCES_DELIVERY_OF: 18 additional example(s) needed
- SYNERGIZES_WITH: 15 additional example(s) needed
- TARGETS: 18 additional example(s) needed

## Blockers
- gold pack readiness report is not ready
- relation labels below 20 examples: ENHANCES_DELIVERY_OF=2, SYNERGIZES_WITH=5, TARGETS=2
