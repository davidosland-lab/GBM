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
- Examples: 36
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.083
- Labels:
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
- Warnings:
- none

### evidence
- Ready: True
- Examples: 18
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.167
- Labels:
- 0: 3
- 1: 3
- 2: 3
- 3: 3
- 4: 3
- 5: 3
- Warnings:
- none

### relation
- Ready: True
- Examples: 18
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.333
- Labels:
- ASSOCIATED_WITH: 6
- NO_RELATION: 6
- PREDICTS: 6
- Warnings:
- none

## Leakage
- none

## Warnings
- none
