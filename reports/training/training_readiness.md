# GBM-BERT Training Readiness Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\ncbi_env_smoke_annotation_splits_pmid`
- Ready: True
- Warnings: 0
- Minimum examples per task: 1
- Minimum examples per label: 1

## Tasks
### ner
- Ready: True
- Examples: 126
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.540
- Labels:
- BIOMARKER: 5
- CELL_TYPE: 4
- DELIVERY_MODIFIER: 4
- DISEASE: 68
- DRUG: 15
- GENE: 12
- OUTCOME: 15
- TREATMENT: 3
- Warnings:
- none

### evidence
- Ready: True
- Examples: 4
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.750
- Labels:
- 0: 3
- 1: 1
- Warnings:
- none

### relation
- Ready: True
- Examples: 3
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.667
- Labels:
- ASSOCIATED_WITH: 2
- PREDICTS: 1
- Warnings:
- none

## Leakage
- none

## Warnings
- none
