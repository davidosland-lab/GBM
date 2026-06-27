# Gold Pack Promotion Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Gold pack report: `reports\training\gold_pack\gold_training_pack.json`
- Threshold config: `configs\training\gold_pack_promotion_thresholds.json`
- Pack ready: True
- Promotable: False
- Minimum examples per task: 100
- Minimum examples per label: 10
- Minimum source PMIDs: 50
- Observed source PMIDs: 12

## Task Counts
- evidence: 18
- ner: 36
- relation: 18

## Label Counts
### evidence
- 0: 3
- 1: 3
- 2: 3
- 3: 3
- 4: 3
- 5: 3

### ner
- BIOMARKER: 3
- CELL_STATE: 3
- CELL_TYPE: 3
- DELIVERY_MODIFIER: 3
- DISEASE: 3
- DRUG: 3
- GENE: 3
- OUTCOME: 3
- PATHWAY: 3
- TREATMENT: 3
- TRIAL_PHASE: 3
- UNKNOWN: 3

### relation
- ASSOCIATED_WITH: 6
- NO_RELATION: 6
- PREDICTS: 6

## Blockers
- evidence has 18 examples; needs at least 100
- evidence labels below 10 examples: 0=3, 1=3, 2=3, 3=3, 4=3, 5=3
- ner has 36 examples; needs at least 100
- ner labels below 10 examples: BIOMARKER=3, CELL_STATE=3, CELL_TYPE=3, DELIVERY_MODIFIER=3, DISEASE=3, DRUG=3, GENE=3, OUTCOME=3, PATHWAY=3, TREATMENT=3, TRIAL_PHASE=3, UNKNOWN=3
- relation has 18 examples; needs at least 100
- relation labels below 10 examples: ASSOCIATED_WITH=6, NO_RELATION=6, PREDICTS=6
- source PMID count is 12; needs at least 50
