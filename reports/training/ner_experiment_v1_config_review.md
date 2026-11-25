# GBM-BERT Training Config Review Gate

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Status: passed
- Config: `configs\training\gbmbert_ner_pubmedbert.json`
- Dataset: `data\training\gold_pack\annotation_splits`
- Label maps: `data\training\gold_pack\label_maps`
- Task: ner
- Prepared task: ner
- Base model: `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext`
- Training enabled: True
- Training enabled confirmed: True

## Split Counts
- test: 787
- train: 5598
- validation: 696

## Checks
- config_label_set_nonempty: True
- config_labels_present_in_dataset: True
- dataset_dir_exists: True
- dataset_label_set_nonempty: True
- dataset_labels_covered_by_config: True
- dataset_labels_covered_by_label_map: True
- hyperparameters_in_review_bounds: True
- label_map_labels_match_config: True
- label_map_present: True
- test_split_present: True
- train_split_nonempty: True
- train_split_present: True
- training_enabled_confirmed: True
- validation_split_present: True

## Labels
- Config: GENE, DRUG, DISEASE, PATHWAY, BIOMARKER, CELL_TYPE, CELL_STATE, TREATMENT, DELIVERY_MODIFIER, OUTCOME, TRIAL_PHASE, UNKNOWN
- Dataset: BIOMARKER, CELL_STATE, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, PATHWAY, TREATMENT, TRIAL_PHASE, UNKNOWN
- Label map: BIOMARKER, CELL_STATE, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, PATHWAY, TREATMENT, TRIAL_PHASE, UNKNOWN

## Errors
- none

## Warnings
- review gate is for research scaffolding only and does not certify model performance
- training remains separate from diagnosis, treatment selection, and clinical decision-making
