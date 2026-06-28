# GBM-BERT Baseline Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`

## Majority-Label Baselines
### ner
- Evaluation file: `data\training\gold_pack\annotation_splits\ner_test.jsonl`
- Examples: 8
- Majority label: UNKNOWN
- Majority accuracy: 0.250
- Labels:
- CELL_STATE: 2
- DISEASE: 1
- DRUG: 2
- TREATMENT: 1
- UNKNOWN: 2

### evidence
- Evaluation file: `data\training\gold_pack\annotation_splits\evidence_test.jsonl`
- Examples: 4
- Majority label: 3
- Majority accuracy: 0.750
- Labels:
- 2: 1
- 3: 3

### relation
- Evaluation file: `data\training\gold_pack\annotation_splits\relation_test.jsonl`
- Examples: 4
- Majority label: ASSOCIATED_WITH
- Majority accuracy: 0.500
- Labels:
- ASSOCIATED_WITH: 2
- NO_RELATION: 1
- PREDICTS: 1

## Warnings
- none
