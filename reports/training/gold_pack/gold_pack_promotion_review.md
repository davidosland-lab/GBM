# Gold Pack Promotion Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Gold pack report: `reports\training\gold_pack\gold_training_pack.json`
- Threshold config: `configs\training\gold_pack_promotion_thresholds.json`
- Pack ready: True
- Promotable: False
- Minimum examples per task: 100
- Minimum examples per label: 10
- Minimum source PMIDs: 50
- Observed source PMIDs: 36
- Additional source PMIDs needed: 14

## Task Counts
- evidence: 42
- ner: 84
- relation: 42

## Promotion Deltas
- evidence: 58 additional example(s) needed
- ner: 16 additional example(s) needed
- relation: 58 additional example(s) needed

## Label Counts
### evidence
- 0: 7
- 1: 7
- 2: 7
- 3: 7
- 4: 7
- 5: 7

### ner
- BIOMARKER: 7
- CELL_STATE: 7
- CELL_TYPE: 7
- DELIVERY_MODIFIER: 7
- DISEASE: 7
- DRUG: 7
- GENE: 7
- OUTCOME: 7
- PATHWAY: 7
- TREATMENT: 7
- TRIAL_PHASE: 7
- UNKNOWN: 7

### relation
- ASSOCIATED_WITH: 14
- NO_RELATION: 14
- PREDICTS: 14

## Label Deltas
### evidence
- 0: 3 additional example(s) needed
- 1: 3 additional example(s) needed
- 2: 3 additional example(s) needed
- 3: 3 additional example(s) needed
- 4: 3 additional example(s) needed
- 5: 3 additional example(s) needed

### ner
- BIOMARKER: 3 additional example(s) needed
- CELL_STATE: 3 additional example(s) needed
- CELL_TYPE: 3 additional example(s) needed
- DELIVERY_MODIFIER: 3 additional example(s) needed
- DISEASE: 3 additional example(s) needed
- DRUG: 3 additional example(s) needed
- GENE: 3 additional example(s) needed
- OUTCOME: 3 additional example(s) needed
- PATHWAY: 3 additional example(s) needed
- TREATMENT: 3 additional example(s) needed
- TRIAL_PHASE: 3 additional example(s) needed
- UNKNOWN: 3 additional example(s) needed

### relation
- none

## Blockers
- evidence has 42 examples; needs at least 100
- evidence labels below 10 examples: 0=7, 1=7, 2=7, 3=7, 4=7, 5=7
- ner has 84 examples; needs at least 100
- ner labels below 10 examples: BIOMARKER=7, CELL_STATE=7, CELL_TYPE=7, DELIVERY_MODIFIER=7, DISEASE=7, DRUG=7, GENE=7, OUTCOME=7, PATHWAY=7, TREATMENT=7, TRIAL_PHASE=7, UNKNOWN=7
- relation has 42 examples; needs at least 100
- source PMID count is 36; needs at least 50
