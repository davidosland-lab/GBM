# GBM-BERT Training Config Review Gate

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Status: passed
- Config: `configs\training\gbmbert_relation_biobert.json`
- Dataset: `data\training\relation_pack\annotation_splits`
- Label maps: `data\training\relation_pack\label_maps`
- Task: relation_extraction
- Prepared task: relation
- Base model: `dmis-lab/biobert-base-cased-v1.2`
- Training enabled: False
- Training enabled confirmed: False

## Split Counts
- test: 0
- train: 4
- validation: 2

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
- relation_config_includes_no_relation: True
- relation_label_map_includes_no_relation: True
- test_split_present: True
- train_split_nonempty: True
- train_split_present: True
- training_enabled_confirmed: True
- validation_split_present: True

## Labels
- Config: ASSOCIATED_WITH, NO_RELATION, PREDICTS
- Dataset: ASSOCIATED_WITH, NO_RELATION, PREDICTS
- Label map: ASSOCIATED_WITH, NO_RELATION, PREDICTS

## Errors
- none

## Warnings
- review gate is for research scaffolding only and does not certify model performance
- training remains separate from diagnosis, treatment selection, and clinical decision-making
- relation_test.jsonl has no examples
- training_enabled is false; this config is review-ready but will run as a dry run unless changed
