# GBM-BERT Dataset Card

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`
- Total examples: 192

## Files
### evidence_test.jsonl
- Examples: 4
- Missing text: 0
- SHA256: `B0313B01615A88595B4FD04C9A93F5F2D5219E0F8FED5A039C8145ACE91352E6`
- Labels:
- 2: 1
- 3: 3

### evidence_train.jsonl
- Examples: 39
- Missing text: 0
- SHA256: `AC0097104F0E36F3F140BDA591F6BB154DE19B967832D2F77A274355AFDB9493`
- Labels:
- 0: 8
- 1: 8
- 2: 7
- 3: 2
- 4: 7
- 5: 7

### evidence_validation.jsonl
- Examples: 5
- Missing text: 0
- SHA256: `A8801C622FF467FA9A3C0A8EA7E3F3CC2F15CEB33FFE5623E3B5CA21531CE9C6`
- Labels:
- 3: 3
- 4: 1
- 5: 1

### ner_test.jsonl
- Examples: 8
- Missing text: 0
- SHA256: `5259D76DF276326E72773E9C5152A78E11B18C5D053F0735474E3D7379D6C95C`
- Labels:
- CELL_STATE: 2
- DISEASE: 1
- DRUG: 2
- TREATMENT: 1
- UNKNOWN: 2

### ner_train.jsonl
- Examples: 78
- Missing text: 0
- SHA256: `5AC070C6F6C721CB379223F576F5E8B09D9711D7399ED126917F88FD53B70A38`
- Labels:
- BIOMARKER: 7
- CELL_STATE: 6
- CELL_TYPE: 8
- DELIVERY_MODIFIER: 7
- DISEASE: 5
- DRUG: 4
- GENE: 6
- OUTCOME: 7
- PATHWAY: 8
- TREATMENT: 8
- TRIAL_PHASE: 8
- UNKNOWN: 4

### ner_validation.jsonl
- Examples: 10
- Missing text: 0
- SHA256: `7620181C7E1607CCFC935F8FD526148B1C8E0280A57204C1EB88B3907A70DB97`
- Labels:
- BIOMARKER: 1
- DELIVERY_MODIFIER: 1
- DISEASE: 2
- DRUG: 1
- GENE: 3
- OUTCOME: 1
- UNKNOWN: 1

### relation_test.jsonl
- Examples: 4
- Missing text: 0
- SHA256: `440F352594574E371F20DD90A5C020080B8C7C8A7DF526C82680699108B0DFBE`
- Labels:
- ASSOCIATED_WITH: 2
- NO_RELATION: 1
- PREDICTS: 1

### relation_train.jsonl
- Examples: 39
- Missing text: 0
- SHA256: `91CF9D3E327624E5F611B13A31B6FC34AC529C0F168F523A9B15FA15CAFE97C7`
- Labels:
- ASSOCIATED_WITH: 11
- NO_RELATION: 14
- PREDICTS: 14

### relation_validation.jsonl
- Examples: 5
- Missing text: 0
- SHA256: `B9BAB9DFB731E67C7E42EB2686FB9B423618095E6BFC24C34DCC5C6BEF693822`
- Labels:
- ASSOCIATED_WITH: 3
- NO_RELATION: 1
- PREDICTS: 1

## Warnings
- none
