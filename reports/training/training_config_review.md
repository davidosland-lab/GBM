# GBM-BERT Training Config Review Gate

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Status: passed
- Config: `configs\training\gbmbert_evidence_smoke_pubmedbert.json`
- Dataset: `data\training\evidence_pack\annotation_splits`
- Label maps: `data\training\evidence_pack\label_maps`
- Task: evidence_classification
- Prepared task: evidence
- Base model: `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext`
- Training enabled: False
- Training enabled confirmed: False

## Split Counts
- test: 1
- train: 2
- validation: 1

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
- Config: 0, 1
- Dataset: 0, 1
- Label map: 0, 1

## Errors
- none

## Warnings
- review gate is for research scaffolding only and does not certify model performance
- training remains separate from diagnosis, treatment selection, and clinical decision-making
- training_enabled is false; this config is review-ready but will run as a dry run unless changed
