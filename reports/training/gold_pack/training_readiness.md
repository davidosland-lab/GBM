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
- Examples: 84
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.083
- Labels:
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
- Warnings:
- none

### evidence
- Ready: True
- Examples: 42
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.167
- Labels:
- 0: 7
- 1: 7
- 2: 7
- 3: 7
- 4: 7
- 5: 7
- Warnings:
- none

### relation
- Ready: True
- Examples: 42
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.333
- Labels:
- ASSOCIATED_WITH: 14
- NO_RELATION: 14
- PREDICTS: 14
- Warnings:
- none

## Leakage
- none

## Warnings
- none
