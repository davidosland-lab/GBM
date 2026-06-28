# GBM-BERT Training Readiness Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`
- Ready: True
- Warnings: 0
- Minimum examples per task: 10
- Minimum examples per label: 2

## Tasks
### ner
- Ready: True
- Examples: 96
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.094
- Labels:
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
- Warnings:
- none

### evidence
- Ready: True
- Examples: 48
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.167
- Labels:
- 0: 8
- 1: 8
- 2: 8
- 3: 8
- 4: 8
- 5: 8
- Warnings:
- none

### relation
- Ready: True
- Examples: 48
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.333
- Labels:
- ASSOCIATED_WITH: 16
- NO_RELATION: 16
- PREDICTS: 16
- Warnings:
- none

## Leakage
- none

## Warnings
- none
