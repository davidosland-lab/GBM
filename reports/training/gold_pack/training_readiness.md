# GBM-BERT Training Readiness Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`
- Ready: False
- Warnings: 2
- Minimum examples per task: 10
- Minimum examples per label: 2

## Tasks
### ner
- Ready: True
- Examples: 8576
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.436
- Labels:
- BIOMARKER: 320
- CELL_STATE: 131
- CELL_TYPE: 212
- DELIVERY_MODIFIER: 290
- DISEASE: 3738
- DRUG: 928
- GENE: 672
- OUTCOME: 1424
- PATHWAY: 93
- TREATMENT: 638
- TRIAL_PHASE: 71
- UNKNOWN: 59
- Warnings:
- none

### evidence
- Ready: False
- Examples: 1016
- Duplicates: 86
- Invalid NER spans: 0
- Dominant label fraction: 0.387
- Labels:
- 0: 175
- 1: 114
- 2: 115
- 3: 393
- 4: 111
- 5: 108
- Warnings:
- 86 duplicate example(s)

### relation
- Ready: False
- Examples: 313
- Duplicates: 7
- Invalid NER spans: 0
- Dominant label fraction: 0.262
- Labels:
- ASSOCIATED_WITH: 82
- ENHANCES_DELIVERY_OF: 2
- IMPROVES: 44
- NO_RELATION: 74
- PREDICTS: 46
- SYNERGIZES_WITH: 5
- TARGETS: 2
- WORSENS: 58
- Warnings:
- 7 duplicate example(s)

## Leakage
- none

## Warnings
- evidence: 86 duplicate example(s)
- relation: 7 duplicate example(s)
