# GBM-BERT Training Pack Leakage Audit

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs: evidence, gold, relation
- Safe: True
- Warnings: 3

## Split PMIDs
- evidence/evidence/test: PMIDs=90, examples=105
- evidence/evidence/train: PMIDs=718, examples=809
- evidence/evidence/validation: PMIDs=90, examples=102
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
- relation/relation/test: PMIDs=16, examples=33
- relation/relation/train: PMIDs=127, examples=255
- relation/relation/validation: PMIDs=16, examples=25
- gold/evidence/test: PMIDs=86, examples=96
- gold/evidence/train: PMIDs=720, examples=816
- gold/evidence/validation: PMIDs=92, examples=104
- gold/ner/test: PMIDs=88, examples=838
- gold/ner/train: PMIDs=717, examples=6881
- gold/ner/validation: PMIDs=94, examples=857
- gold/relation/test: PMIDs=21, examples=40
- gold/relation/train: PMIDs=124, examples=242
- gold/relation/validation: PMIDs=14, examples=31

## Within-Pack Warnings
- none

## Cross-Pack Warnings
- evidence/gold: 898 shared PMID(s): 10853323, 11138924, 11717820, 11939587, 12124496
- evidence/relation: 154 shared PMID(s): 15758010, 18676355, 18752056, 18757334, 19269895
- gold/relation: 159 shared PMID(s): 15758010, 16944365, 17325429, 18665745, 18676355
