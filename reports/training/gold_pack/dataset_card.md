# GBM-BERT Dataset Card

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Dataset directory: `data\training\gold_pack\annotation_splits`
- Total examples: 168

## Files
### evidence_test.jsonl
- Examples: 5
- Missing text: 0
- SHA256: `6A2849479302CC495AFD4F93CA873B0529F278A57BD4B7998AA82BA6C0CE94C7`
- Labels:
- 2: 2
- 3: 1
- 4: 1
- 5: 1

### evidence_train.jsonl
- Examples: 33
- Missing text: 0
- SHA256: `8E2F240412F8CA19ABB95C3342B44274D4F577B7617E30E7ADDAD72FA66A6371`
- Labels:
- 0: 6
- 1: 6
- 2: 4
- 3: 6
- 4: 5
- 5: 6

### evidence_validation.jsonl
- Examples: 4
- Missing text: 0
- SHA256: `A7C62DB80936F811DC061F0F71E3B7472DED315E5188B1043779E70428225007`
- Labels:
- 0: 1
- 1: 1
- 2: 1
- 4: 1

### ner_test.jsonl
- Examples: 10
- Missing text: 0
- SHA256: `014E4366869969F0DFE10CBCBFD04275954B54997F08DBE657479695DB32AB8B`
- Labels:
- BIOMARKER: 1
- CELL_STATE: 3
- DELIVERY_MODIFIER: 2
- GENE: 1
- PATHWAY: 1
- TRIAL_PHASE: 1
- UNKNOWN: 1

### ner_train.jsonl
- Examples: 66
- Missing text: 0
- SHA256: `D1458DA048598874CABB24DFCF09CBC35794B2577A5D538176F715EB81D49876`
- Labels:
- BIOMARKER: 4
- CELL_STATE: 4
- CELL_TYPE: 6
- DELIVERY_MODIFIER: 5
- DISEASE: 6
- DRUG: 6
- GENE: 5
- OUTCOME: 6
- PATHWAY: 6
- TREATMENT: 6
- TRIAL_PHASE: 6
- UNKNOWN: 6

### ner_validation.jsonl
- Examples: 8
- Missing text: 0
- SHA256: `D5D88F35A47045505B13413CFFD6E0CEDC416F941AC7D44DC628406C5E657D2D`
- Labels:
- BIOMARKER: 2
- CELL_TYPE: 1
- DISEASE: 1
- DRUG: 1
- GENE: 1
- OUTCOME: 1
- TREATMENT: 1

### relation_test.jsonl
- Examples: 5
- Missing text: 0
- SHA256: `69BB1EB9BF7DBE101E480771FBF24F9BF310E08B35F6E87D47C1D2B635B16A61`
- Labels:
- ASSOCIATED_WITH: 1
- NO_RELATION: 3
- PREDICTS: 1

### relation_train.jsonl
- Examples: 33
- Missing text: 0
- SHA256: `8F20887E4755B9600D9AECE64BB47203913E45BD4617682ABB9A2B27EF76A57C`
- Labels:
- ASSOCIATED_WITH: 12
- NO_RELATION: 10
- PREDICTS: 11

### relation_validation.jsonl
- Examples: 4
- Missing text: 0
- SHA256: `E8A43840EF5446E402D26AA51FD6C3F205EC0F84CF06A83E55855C1FD9C7E4B1`
- Labels:
- ASSOCIATED_WITH: 1
- NO_RELATION: 1
- PREDICTS: 2

## Warnings
- none
