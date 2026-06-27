# GBM-BERT Baseline Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`

## Majority-Label Baselines
### ner
- Evaluation file: `data\training\gold_pack\annotation_splits\ner_test.jsonl`
- Examples: 4
- Majority label: PATHWAY
- Majority accuracy: 0.250
- Labels:
- CELL_TYPE: 1
- DRUG: 1
- OUTCOME: 1
- PATHWAY: 1

### evidence
- Evaluation file: `data\training\gold_pack\annotation_splits\evidence_test.jsonl`
- Examples: 2
- Majority label: 1
- Majority accuracy: 1.000
- Labels:
- 1: 2

### relation
- Evaluation file: `data\training\gold_pack\annotation_splits\relation_test.jsonl`
- Examples: 2
- Majority label: PREDICTS
- Majority accuracy: 1.000
- Labels:
- PREDICTS: 2

## Warnings
- none
