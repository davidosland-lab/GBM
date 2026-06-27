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
- evidence: 12
- ner: 0
- relation: 0
- Label coverage:
- evidence: 0=2, 1=2, 2=2, 3=2, 4=2, 5=2
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
- Ready: True
- Row counts:
- evidence: 12
- ner: 24
- relation: 12
- Label coverage:
- evidence: 0=2, 1=2, 2=2, 3=2, 4=2, 5=2
- ner: BIOMARKER=2, CELL_STATE=2, CELL_TYPE=2, DELIVERY_MODIFIER=2, DISEASE=2, DRUG=2, GENE=2, OUTCOME=2, PATHWAY=2, TREATMENT=2, TRIAL_PHASE=2, UNKNOWN=2
- relation: ASSOCIATED_WITH=4, NO_RELATION=4, PREDICTS=4
- Leakage:
- none
- Warnings:
- none
