# GBM-BERT Training Pack Leakage Audit

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs: evidence, gold, relation
- Safe: True
- Warnings: 3

## Split PMIDs
- evidence/evidence/test: PMIDs=4, examples=5
- evidence/evidence/train: PMIDs=28, examples=33
- evidence/evidence/validation: PMIDs=4, examples=4
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
- relation/relation/test: PMIDs=4, examples=5
- relation/relation/train: PMIDs=28, examples=33
- relation/relation/validation: PMIDs=4, examples=4
- gold/evidence/test: PMIDs=4, examples=5
- gold/evidence/train: PMIDs=28, examples=33
- gold/evidence/validation: PMIDs=4, examples=4
- gold/ner/test: PMIDs=4, examples=10
- gold/ner/train: PMIDs=28, examples=66
- gold/ner/validation: PMIDs=4, examples=8
- gold/relation/test: PMIDs=4, examples=5
- gold/relation/train: PMIDs=28, examples=33
- gold/relation/validation: PMIDs=4, examples=4

## Within-Pack Warnings
- none

## Cross-Pack Warnings
- evidence/gold: 36 shared PMID(s): 15758010, 23209033, 26109046, 28967586, 29380516
- evidence/relation: 36 shared PMID(s): 15758010, 23209033, 26109046, 28967586, 29380516
- gold/relation: 36 shared PMID(s): 15758010, 23209033, 26109046, 28967586, 29380516
