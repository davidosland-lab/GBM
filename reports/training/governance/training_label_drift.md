# GBM-BERT Training Label Drift Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Warnings: 0

## Configs
### gbmbert_evidence_pubmedbert
- Config: `configs\training\gbmbert_evidence_pubmedbert.json`
- Governance profile: scaffold
- Dataset: `data\training\evidence_pack\annotation_splits`
- Config labels: 0, 1, 2, 3, 4, 5
- Dataset labels: test=[1]; train=[0, 1, 2, 3, 4, 5]; validation=[4]
- Missing from config: none
- Missing from dataset: none

### gbmbert_evidence_smoke_pubmedbert
- Config: `configs\training\gbmbert_evidence_smoke_pubmedbert.json`
- Governance profile: current
- Dataset: `data\training\evidence_smoke_fixture\splits`
- Config labels: 0, 1
- Dataset labels: test=[0, 1]; train=[0]; validation=[1]
- Missing from config: none
- Missing from dataset: none

### gbmbert_ner_pubmedbert
- Config: `configs\training\gbmbert_ner_pubmedbert.json`
- Governance profile: scaffold
- Dataset: `data\training\gold_pack\annotation_splits`
- Config labels: GENE, DRUG, DISEASE, PATHWAY, BIOMARKER, CELL_TYPE, CELL_STATE, TREATMENT, DELIVERY_MODIFIER, OUTCOME, TRIAL_PHASE, UNKNOWN
- Dataset labels: test=[CELL_TYPE, DRUG, OUTCOME, PATHWAY]; train=[BIOMARKER, CELL_STATE, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, PATHWAY, TREATMENT, TRIAL_PHASE, UNKNOWN]; validation=[DELIVERY_MODIFIER, OUTCOME, PATHWAY, TRIAL_PHASE]
- Missing from config: none
- Missing from dataset: none

### gbmbert_ner_smoke_pubmedbert
- Config: `configs\training\gbmbert_ner_smoke_pubmedbert.json`
- Governance profile: current
- Dataset: `data\training\ncbi_env_smoke_annotation_splits`
- Config labels: BIOMARKER, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, TREATMENT
- Dataset labels: test=[BIOMARKER, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, TREATMENT]; train=[BIOMARKER, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, TREATMENT]; validation=[BIOMARKER, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, TREATMENT]
- Missing from config: none
- Missing from dataset: none

### gbmbert_relation_biobert
- Config: `configs\training\gbmbert_relation_biobert.json`
- Governance profile: current
- Dataset: `data\training\relation_pack\annotation_splits`
- Config labels: ASSOCIATED_WITH, NO_RELATION, PREDICTS
- Dataset labels: test=[none]; train=[ASSOCIATED_WITH, NO_RELATION]; validation=[NO_RELATION, PREDICTS]
- Missing from config: none
- Missing from dataset: none

## Warnings
- none
