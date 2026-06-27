# Gold Pack Promotion Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Gold pack report: `reports\training\gold_pack\gold_training_pack.json`
- Pack ready: True
- Promotable: False
- Minimum examples per task: 100
- Minimum examples per label: 10
- Minimum source PMIDs: 50
- Observed source PMIDs: 12

## Task Counts
- evidence: 12
- ner: 24
- relation: 12

## Label Counts
### evidence
- 0: 2
- 1: 2
- 2: 2
- 3: 2
- 4: 2
- 5: 2

### ner
- BIOMARKER: 2
- CELL_STATE: 2
- CELL_TYPE: 2
- DELIVERY_MODIFIER: 2
- DISEASE: 2
- DRUG: 2
- GENE: 2
- OUTCOME: 2
- PATHWAY: 2
- TREATMENT: 2
- TRIAL_PHASE: 2
- UNKNOWN: 2

### relation
- ASSOCIATED_WITH: 4
- NO_RELATION: 4
- PREDICTS: 4

## Blockers
- evidence has 12 examples; needs at least 100
- evidence labels below 10 examples: 0=2, 1=2, 2=2, 3=2, 4=2, 5=2
- ner has 24 examples; needs at least 100
- ner labels below 10 examples: BIOMARKER=2, CELL_STATE=2, CELL_TYPE=2, DELIVERY_MODIFIER=2, DISEASE=2, DRUG=2, GENE=2, OUTCOME=2, PATHWAY=2, TREATMENT=2, TRIAL_PHASE=2, UNKNOWN=2
- relation has 12 examples; needs at least 100
- relation labels below 10 examples: ASSOCIATED_WITH=4, NO_RELATION=4, PREDICTS=4
- source PMID count is 12; needs at least 50
