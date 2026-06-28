# GBM-BERT Training Pack Leakage Audit

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs: evidence, gold, relation
- Safe: True
- Warnings: 3

## Split PMIDs
- evidence/evidence/test: PMIDs=4, examples=4
- evidence/evidence/train: PMIDs=34, examples=39
- evidence/evidence/validation: PMIDs=4, examples=5
- evidence/ner/test: PMIDs=0, examples=0
- evidence/ner/train: PMIDs=0, examples=0
- evidence/ner/validation: PMIDs=0, examples=0
- evidence/relation/test: PMIDs=0, examples=0
- evidence/relation/train: PMIDs=0, examples=0
- evidence/relation/validation: PMIDs=0, examples=0
- relation/evidence/test: PMIDs=0, examples=0
- relation/evidence/train: PMIDs=0, examples=0
- relation/evidence/validation: PMIDs=0, examples=0
- relation/ner/test: PMIDs=0, examples=0
- relation/ner/train: PMIDs=0, examples=0
- relation/ner/validation: PMIDs=0, examples=0
- relation/relation/test: PMIDs=4, examples=4
- relation/relation/train: PMIDs=34, examples=39
- relation/relation/validation: PMIDs=4, examples=5
- gold/evidence/test: PMIDs=4, examples=4
- gold/evidence/train: PMIDs=34, examples=39
- gold/evidence/validation: PMIDs=4, examples=5
- gold/ner/test: PMIDs=4, examples=8
- gold/ner/train: PMIDs=34, examples=78
- gold/ner/validation: PMIDs=4, examples=10
- gold/relation/test: PMIDs=4, examples=4
- gold/relation/train: PMIDs=34, examples=39
- gold/relation/validation: PMIDs=4, examples=5

## Within-Pack Warnings
- none

## Cross-Pack Warnings
- evidence/gold: 42 shared PMID(s): 15758010, 23209033, 26109046, 27475281, 28967586
- evidence/relation: 42 shared PMID(s): 15758010, 23209033, 26109046, 27475281, 28967586
- gold/relation: 42 shared PMID(s): 15758010, 23209033, 26109046, 27475281, 28967586
