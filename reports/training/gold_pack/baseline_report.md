# GBM-BERT Baseline Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`

## Majority-Label Baselines
### ner
- Evaluation file: `data\training\gold_pack\annotation_splits\ner_test.jsonl`
- Examples: 10
- Majority label: CELL_STATE
- Majority accuracy: 0.300
- Labels:
- BIOMARKER: 1
- CELL_STATE: 3
- DELIVERY_MODIFIER: 2
- GENE: 1
- PATHWAY: 1
- TRIAL_PHASE: 1
- UNKNOWN: 1

### evidence
- Evaluation file: `data\training\gold_pack\annotation_splits\evidence_test.jsonl`
- Examples: 5
- Majority label: 2
- Majority accuracy: 0.400
- Labels:
- 2: 2
- 3: 1
- 4: 1
- 5: 1

### relation
- Evaluation file: `data\training\gold_pack\annotation_splits\relation_test.jsonl`
- Examples: 5
- Majority label: NO_RELATION
- Majority accuracy: 0.600
- Labels:
- ASSOCIATED_WITH: 1
- NO_RELATION: 3
- PREDICTS: 1

## Warnings
- none
