# GBM-BERT Training Readiness Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack_backfill_batch1\annotation_splits`
- Ready: False
- Warnings: 3
- Minimum examples per task: 10
- Minimum examples per label: 2

## Tasks
### ner
- Ready: False
- Examples: 0
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: n/a
- Labels:
- none
- Warnings:
- fewer than 10 examples

### evidence
- Ready: False
- Examples: 7
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 0.571
- Labels:
- 0: 4
- 1: 2
- 3: 1
- Warnings:
- fewer than 10 examples
- label 3 has fewer than 2 examples

### relation
- Ready: True
- Examples: 12
- Duplicates: 0
- Invalid NER spans: 0
- Dominant label fraction: 1.000
- Labels:
- ASSOCIATED_WITH: 12
- Warnings:
- none

## Leakage
- none

## Warnings
- ner: fewer than 10 examples
- evidence: fewer than 10 examples
- evidence: label 3 has fewer than 2 examples
