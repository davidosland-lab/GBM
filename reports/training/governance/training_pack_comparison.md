# GBM-BERT Training Pack Comparison

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs compared: 3
- Ready packs: 2
- Warnings: 2

## Packs
### evidence
- Report: `reports\training\evidence_pack\evidence_training_pack.json`
- Dataset: `data\training\evidence_pack\annotation_dataset`
- Splits: `data\training\evidence_pack\annotation_splits`
- Label maps: `data\training\evidence_pack\label_maps`
- Ready: True
- Row counts:
- evidence: 4
- ner: 0
- relation: 0
- Label coverage:
- evidence: 0=3, 1=1
- ner: none
- relation: none
- Leakage:
- none
- Warnings:
- none

### relation
- Report: `reports\training\relation_pack\relation_training_pack.json`
- Dataset: `data\training\relation_pack\annotation_dataset`
- Splits: `data\training\relation_pack\annotation_splits`
- Label maps: `data\training\relation_pack\label_maps`
- Ready: True
- Row counts:
- evidence: 0
- ner: 0
- relation: 6
- Label coverage:
- evidence: none
- ner: none
- relation: ASSOCIATED_WITH=2, NO_RELATION=3, PREDICTS=1
- Leakage:
- none
- Warnings:
- none

### gold
- Report: `reports\training\gold_pack\gold_training_pack.json`
- Dataset: `data\training\gold_pack\annotation_dataset`
- Splits: `data\training\gold_pack\annotation_splits`
- Label maps: `data\training\gold_pack\label_maps`
- Ready: False
- Row counts:
- evidence: 1
- ner: 0
- relation: 0
- Label coverage:
- evidence: 3=1
- ner: none
- relation: none
- Leakage:
- none
- Warnings:
- ner: fewer than 1 examples
- relation: fewer than 1 examples
