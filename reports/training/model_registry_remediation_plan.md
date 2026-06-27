# GBM-BERT Model Registry Remediation Plan

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Audit: `reports\training\model_registry_audit.json`
- Actions: 3

## Actions
- [error] gbmbert_ner_smoke_candidate: gbmbert_ner_smoke_candidate: checkpoint_dir does not exist -> create the referenced metadata-only checkpoint directory or update the registry path
- [warning] gbmbert_ner_smoke_candidate: gbmbert_ner_smoke_candidate: no matching model card found -> generate or link a research-use model card for this checkpoint
- [warning] gbmbert_ner_smoke_candidate: gbmbert_ner_smoke_candidate: no matching dataset card found -> generate or link the dataset card used by this checkpoint
