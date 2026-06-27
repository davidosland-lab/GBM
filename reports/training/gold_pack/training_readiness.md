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
- Examples: 24
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.083
- Labels:
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
- Warnings:
- none

### evidence
- Ready: True
- Examples: 12
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.167
- Labels:
- 0: 2
- 1: 2
- 2: 2
- 3: 2
- 4: 2
- 5: 2
- Warnings:
- none

### relation
- Ready: True
- Examples: 12
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.333
- Labels:
- ASSOCIATED_WITH: 4
- NO_RELATION: 4
- PREDICTS: 4
- Warnings:
- none

## Leakage
- none

## Warnings
- none
