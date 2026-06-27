# GBM-BERT Baseline Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\ncbi_env_smoke_annotation_splits`

## Majority-Label Baselines
### ner
- Evaluation file: `data\training\ncbi_env_smoke_annotation_splits\ner_test.jsonl`
- Examples: 16
- Majority label: DISEASE
- Majority accuracy: 0.438
- Labels:
- BIOMARKER: 1
- CELL_TYPE: 1
- DELIVERY_MODIFIER: 1
- DISEASE: 7
- DRUG: 2
- GENE: 1
- OUTCOME: 2
- TREATMENT: 1

### evidence
- Evaluation file: `data\training\ncbi_env_smoke_annotation_splits\evidence_test.jsonl`
- Examples: 1
- Majority label: 0
- Majority accuracy: 1.000
- Labels:
- 0: 1

### relation
- Evaluation file: `data\training\ncbi_env_smoke_annotation_splits\relation_test.jsonl`
- Examples: 1
- Majority label: PREDICTS
- Majority accuracy: 1.000
- Labels:
- PREDICTS: 1

## Warnings
- none
