# GBM-BERT Training Pack Comparison

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs compared: 3
- Ready packs: 3
- Warnings: 0

## Packs
### evidence
- Report: `reports\training\evidence_pack\evidence_training_pack.json`
- Dataset: `data\training\evidence_pack\annotation_dataset`
- Splits: `data\training\evidence_pack\annotation_splits`
- Label maps: `data\training\evidence_pack\label_maps`
- Ready: True
- Row counts:
- evidence: 48
- ner: 0
- relation: 0
- Label coverage:
- evidence: 0=8, 1=8, 2=8, 3=8, 4=8, 5=8
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
- relation: 48
- Label coverage:
- evidence: none
- ner: none
- relation: ASSOCIATED_WITH=16, NO_RELATION=16, PREDICTS=16
- Leakage:
- none
- Warnings:
- none

### gold
- Report: `reports\training\gold_pack\gold_training_pack.json`
- Dataset: `data\training\gold_pack\annotation_dataset`
- Splits: `data\training\gold_pack\annotation_splits`
- Label maps: `data\training\gold_pack\label_maps`
- Ready: True
- Row counts:
- evidence: 48
- ner: 96
- relation: 48
- Label coverage:
- evidence: 0=8, 1=8, 2=8, 3=8, 4=8, 5=8
- ner: BIOMARKER=8, CELL_STATE=8, CELL_TYPE=8, DELIVERY_MODIFIER=8, DISEASE=8, DRUG=7, GENE=9, OUTCOME=8, PATHWAY=8, TREATMENT=9, TRIAL_PHASE=8, UNKNOWN=7
- relation: ASSOCIATED_WITH=16, NO_RELATION=16, PREDICTS=16
- Leakage:
- none
- Warnings:
- none
