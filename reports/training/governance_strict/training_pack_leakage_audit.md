# GBM-BERT Training Pack Leakage Audit

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs: evidence, gold, relation
- Safe: True
- Warnings: 3

## Split PMIDs
- evidence/evidence/test: PMIDs=1, examples=1
- evidence/evidence/train: PMIDs=10, examples=10
- evidence/evidence/validation: PMIDs=1, examples=1
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
- relation/relation/test: PMIDs=0, examples=0
- relation/relation/train: PMIDs=1, examples=4
- relation/relation/validation: PMIDs=1, examples=2
- gold/evidence/test: PMIDs=1, examples=1
- gold/evidence/train: PMIDs=10, examples=10
- gold/evidence/validation: PMIDs=1, examples=1
- gold/ner/test: PMIDs=1, examples=2
- gold/ner/train: PMIDs=10, examples=20
- gold/ner/validation: PMIDs=1, examples=2
- gold/relation/test: PMIDs=1, examples=1
- gold/relation/train: PMIDs=10, examples=10
- gold/relation/validation: PMIDs=1, examples=1

## Within-Pack Warnings
- none

## Cross-Pack Warnings
- evidence/gold: 12 shared PMID(s): 15758010, 23209033, 29643471, 30187121, 30716120
- evidence/relation: 2 shared PMID(s): 15758010, 29643471
- gold/relation: 2 shared PMID(s): 15758010, 29643471
