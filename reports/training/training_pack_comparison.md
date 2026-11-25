# GBM-BERT Training Pack Comparison

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Packs compared: 3
- Ready packs: 0
- Warnings: 6

## Packs
### evidence
- Report: `reports\training\evidence_pack\evidence_training_pack.json`
- Dataset: `data\training\evidence_pack\annotation_dataset`
- Splits: `data\training\evidence_pack\annotation_splits`
- Label maps: `data\training\evidence_pack\label_maps`
- Ready: False
- Row counts:
- evidence: 1016
- ner: 0
- relation: 0
- Label coverage:
- evidence: 0=175, 1=114, 2=115, 3=393, 4=111, 5=108
- ner: none
- relation: none
- Leakage:
- none
- Warnings:
- evidence: 86 duplicate example(s)

### relation
- Report: `reports\training\relation_pack\relation_training_pack.json`
- Dataset: `data\training\relation_pack\annotation_dataset`
- Splits: `data\training\relation_pack\annotation_splits`
- Label maps: `data\training\relation_pack\label_maps`
- Ready: False
- Row counts:
- evidence: 0
- ner: 0
- relation: 313
- Label coverage:
- evidence: none
- ner: none
- relation: ASSOCIATED_WITH=82, ENHANCES_DELIVERY_OF=2, IMPROVES=44, NO_RELATION=74, PREDICTS=46, SYNERGIZES_WITH=5, TARGETS=2, WORSENS=58
- Leakage:
- none
- Warnings:
- 1 relation example(s) have identical head and tail endpoints
- 7 duplicate relation example(s)
- relation: 7 duplicate example(s)

### gold
- Report: `reports\training\gold_pack\gold_training_pack.json`
- Dataset: `data\training\gold_pack\annotation_dataset`
- Splits: `data\training\gold_pack\annotation_splits`
- Label maps: `data\training\gold_pack\label_maps`
- Ready: False
- Row counts:
- evidence: 1016
- ner: 8576
- relation: 313
- Label coverage:
- evidence: 0=175, 1=114, 2=115, 3=393, 4=111, 5=108
- ner: BIOMARKER=320, CELL_STATE=131, CELL_TYPE=212, DELIVERY_MODIFIER=290, DISEASE=3738, DRUG=928, GENE=672, OUTCOME=1424, PATHWAY=93, TREATMENT=638, TRIAL_PHASE=71, UNKNOWN=59
- relation: ASSOCIATED_WITH=82, ENHANCES_DELIVERY_OF=2, IMPROVES=44, NO_RELATION=74, PREDICTS=46, SYNERGIZES_WITH=5, TARGETS=2, WORSENS=58
- Leakage:
- none
- Warnings:
- evidence: 86 duplicate example(s)
- relation: 7 duplicate example(s)
