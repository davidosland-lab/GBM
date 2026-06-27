# GBM-BERT Model Registry Audit

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Registry: `models\checkpoint_registry.json`
- Reports directory: `reports\training`
- Checkpoints: 2
- Passed: False
- Errors: 1
- Warnings: 2

## Entries
### gbmbert_evidence_smoke
- Task: evidence_classification
- Status: research_candidate
- Checks:
- checkpoint_dir_exists: True
- dataset_card_present: True
- entry_warning_present: True
- manifest_path_exists_or_empty: True
- metrics_path_exists_or_empty: True
- model_card_present: True
- name_present: True
- notes_do_not_overclaim: True
- status_research_safe: True
- Model cards:
- `reports\training\evidence_smoke_fixture\evidence_smoke_model_card.json`
- Dataset cards:
- `reports\training\evidence_smoke_fixture\evidence_smoke_model_card.json`
- Errors:
- none
- Warnings:
- none

### gbmbert_ner_smoke_candidate
- Task: ner
- Status: candidate
- Checks:
- checkpoint_dir_exists: False
- dataset_card_present: False
- entry_warning_present: True
- manifest_path_exists_or_empty: True
- metrics_path_exists_or_empty: True
- model_card_present: False
- name_present: True
- notes_do_not_overclaim: True
- status_research_safe: True
- Model cards:
- none
- Dataset cards:
- none
- Errors:
- gbmbert_ner_smoke_candidate: checkpoint_dir does not exist
- Warnings:
- gbmbert_ner_smoke_candidate: no matching model card found
- gbmbert_ner_smoke_candidate: no matching dataset card found

## Errors
- gbmbert_ner_smoke_candidate: checkpoint_dir does not exist

## Warnings
- gbmbert_ner_smoke_candidate: no matching model card found
- gbmbert_ner_smoke_candidate: no matching dataset card found
