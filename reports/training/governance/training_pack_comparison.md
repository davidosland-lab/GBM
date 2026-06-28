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
- evidence: 42
- ner: 0
- relation: 0
- Label coverage:
- evidence: 0=7, 1=7, 2=7, 3=7, 4=7, 5=7
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
- relation: 42
- Label coverage:
- evidence: none
- ner: none
- relation: ASSOCIATED_WITH=14, NO_RELATION=14, PREDICTS=14
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
- evidence: 42
- ner: 84
- relation: 42
- Label coverage:
- evidence: 0=7, 1=7, 2=7, 3=7, 4=7, 5=7
- ner: BIOMARKER=7, CELL_STATE=7, CELL_TYPE=7, DELIVERY_MODIFIER=7, DISEASE=7, DRUG=7, GENE=7, OUTCOME=7, PATHWAY=7, TREATMENT=7, TRIAL_PHASE=7, UNKNOWN=7
- relation: ASSOCIATED_WITH=14, NO_RELATION=14, PREDICTS=14
- Leakage:
- none
- Warnings:
- none
