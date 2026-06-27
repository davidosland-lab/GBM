# GBM-BERT Dataset Card

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`
- Total examples: 72

## Files
### evidence_test.jsonl
- Examples: 2
- Missing text: 0
- SHA256: `6609D0E3B9F9BCA50BDD6115C31C43D28BCE2289BB590F590E2AEF5F5AB7184D`
- Labels:
- 1: 2

### evidence_train.jsonl
- Examples: 14
- Missing text: 0
- SHA256: `E8B9DF7984B025F2F6D92B1E0BB2AA5EBD8244D469A0E5D74F40223A8348AFFA`
- Labels:
- 0: 3
- 1: 1
- 2: 3
- 3: 3
- 4: 1
- 5: 3

### evidence_validation.jsonl
- Examples: 2
- Missing text: 0
- SHA256: `13E984199D5A4A849E973D1E96C4EBB17631E9597630457CE23FA72C133DBE50`
- Labels:
- 4: 2

### ner_test.jsonl
- Examples: 4
- Missing text: 0
- SHA256: `9C5BB7BA2FBFEF41769642E8FCF7139DC5D6714D32E02EDCC88EBC577E0F79E4`
- Labels:
- CELL_TYPE: 1
- DRUG: 1
- OUTCOME: 1
- PATHWAY: 1

### ner_train.jsonl
- Examples: 28
- Missing text: 0
- SHA256: `DD60D6441B99517CDCB9F390C74EFF8C62A202B8BBFCF54210D8CC19C19C4AFD`
- Labels:
- BIOMARKER: 3
- CELL_STATE: 3
- CELL_TYPE: 2
- DELIVERY_MODIFIER: 2
- DISEASE: 3
- DRUG: 2
- GENE: 3
- OUTCOME: 1
- PATHWAY: 1
- TREATMENT: 3
- TRIAL_PHASE: 2
- UNKNOWN: 3

### ner_validation.jsonl
- Examples: 4
- Missing text: 0
- SHA256: `4E2CDAF136C2F5CEF5D3DE69039EA7A1EB72BC8BD5DF0E619EA1A64A5A59637F`
- Labels:
- DELIVERY_MODIFIER: 1
- OUTCOME: 1
- PATHWAY: 1
- TRIAL_PHASE: 1

### relation_test.jsonl
- Examples: 2
- Missing text: 0
- SHA256: `736D2EB2DBF926488A5367D84B539E2AF76B7833001F9E8B91012B3D65ADE949`
- Labels:
- PREDICTS: 2

### relation_train.jsonl
- Examples: 14
- Missing text: 0
- SHA256: `C8383319B0A57EB883C7698FDD7DD3284F87A6D6C96C6CF880B8095D469E0546`
- Labels:
- ASSOCIATED_WITH: 6
- NO_RELATION: 5
- PREDICTS: 3

### relation_validation.jsonl
- Examples: 2
- Missing text: 0
- SHA256: `3DF2A9EFAC3985E30AE338F3D28AF8FCFB7A7AD8FCA65499465FB409E1992979`
- Labels:
- NO_RELATION: 1
- PREDICTS: 1

## Warnings
- none
