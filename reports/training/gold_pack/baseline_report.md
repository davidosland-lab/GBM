# GBM-BERT Baseline Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`

## Majority-Label Baselines
### ner
- Evaluation file: `data\training\gold_pack\annotation_splits\ner_test.jsonl`
- Examples: 838
- Majority label: DISEASE
- Majority accuracy: 0.426
- Labels:
- BIOMARKER: 25
- CELL_STATE: 12
- CELL_TYPE: 12
- DELIVERY_MODIFIER: 32
- DISEASE: 357
- DRUG: 114
- GENE: 93
- OUTCOME: 112
- PATHWAY: 16
- TREATMENT: 52
- TRIAL_PHASE: 9
- UNKNOWN: 4

### evidence
- Evaluation file: `data\training\gold_pack\annotation_splits\evidence_test.jsonl`
- Examples: 96
- Majority label: 3
- Majority accuracy: 0.333
- Labels:
- 0: 17
- 1: 17
- 2: 14
- 3: 32
- 4: 5
- 5: 11

### relation
- Evaluation file: `data\training\gold_pack\annotation_splits\relation_test.jsonl`
- Examples: 40
- Majority label: NO_RELATION
- Majority accuracy: 0.325
- Labels:
- ASSOCIATED_WITH: 10
- IMPROVES: 7
- NO_RELATION: 13
- PREDICTS: 1
- WORSENS: 9

## Warnings
- none
