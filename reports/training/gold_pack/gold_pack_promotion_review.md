# Gold Pack Promotion Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Gold pack report: `reports\training\gold_pack\gold_training_pack.json`
- Threshold config: `configs\training\gold_pack_promotion_thresholds.json`
- Pack ready: True
- Promotable: False
- Minimum examples per task: 100
- Minimum examples per label: 10
- Minimum source PMIDs: 50
- Observed source PMIDs: 42
- Additional source PMIDs needed: 8

## Task Counts
- evidence: 48
- ner: 96
- relation: 48

## Promotion Deltas
- evidence: 52 additional example(s) needed
- ner: 4 additional example(s) needed
- relation: 52 additional example(s) needed

## Label Counts
### evidence
- 0: 8
- 1: 8
- 2: 8
- 3: 8
- 4: 8
- 5: 8

### ner
- BIOMARKER: 8
- CELL_STATE: 8
- CELL_TYPE: 8
- DELIVERY_MODIFIER: 8
- DISEASE: 8
- DRUG: 7
- GENE: 9
- OUTCOME: 8
- PATHWAY: 8
- TREATMENT: 9
- TRIAL_PHASE: 8
- UNKNOWN: 7

### relation
- ASSOCIATED_WITH: 16
- NO_RELATION: 16
- PREDICTS: 16

## Label Deltas
### evidence
- 0: 2 additional example(s) needed
- 1: 2 additional example(s) needed
- 2: 2 additional example(s) needed
- 3: 2 additional example(s) needed
- 4: 2 additional example(s) needed
- 5: 2 additional example(s) needed

### ner
- BIOMARKER: 2 additional example(s) needed
- CELL_STATE: 2 additional example(s) needed
- CELL_TYPE: 2 additional example(s) needed
- DELIVERY_MODIFIER: 2 additional example(s) needed
- DISEASE: 2 additional example(s) needed
- DRUG: 3 additional example(s) needed
- GENE: 1 additional example(s) needed
- OUTCOME: 2 additional example(s) needed
- PATHWAY: 2 additional example(s) needed
- TREATMENT: 1 additional example(s) needed
- TRIAL_PHASE: 2 additional example(s) needed
- UNKNOWN: 3 additional example(s) needed

### relation
- none

## Blockers
- evidence has 48 examples; needs at least 100
- evidence labels below 10 examples: 0=8, 1=8, 2=8, 3=8, 4=8, 5=8
- ner has 96 examples; needs at least 100
- ner labels below 10 examples: BIOMARKER=8, CELL_STATE=8, CELL_TYPE=8, DELIVERY_MODIFIER=8, DISEASE=8, DRUG=7, GENE=9, OUTCOME=8, PATHWAY=8, TREATMENT=9, TRIAL_PHASE=8, UNKNOWN=7
- relation has 48 examples; needs at least 100
- source PMID count is 42; needs at least 50
