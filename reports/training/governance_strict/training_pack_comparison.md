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
- evidence: 18
- ner: 0
- relation: 0
- Label coverage:
- evidence: 0=3, 1=3, 2=3, 3=3, 4=3, 5=3
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
- evidence: 18
- ner: 36
- relation: 18
- Label coverage:
- evidence: 0=3, 1=3, 2=3, 3=3, 4=3, 5=3
- ner: BIOMARKER=3, CELL_STATE=3, CELL_TYPE=3, DELIVERY_MODIFIER=3, DISEASE=3, DRUG=3, GENE=3, OUTCOME=3, PATHWAY=3, TREATMENT=3, TRIAL_PHASE=3, UNKNOWN=3
- relation: ASSOCIATED_WITH=6, NO_RELATION=6, PREDICTS=6
- Leakage:
- none
- Warnings:
- none
