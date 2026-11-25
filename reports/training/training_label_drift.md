# GBM-BERT Training Label Drift Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Warnings: 0

## Configs
### gbmbert_evidence_experiment_pubmedbert
- Config: `configs\training\gbmbert_evidence_experiment_pubmedbert.json`
- Governance profile: scaffold
- Dataset: `data\training\evidence_pack\annotation_splits`
- Config labels: 0, 1, 2, 3, 4, 5
- Dataset labels: test=[0, 1, 2, 3, 4, 5]; train=[0, 1, 2, 3, 4, 5]; validation=[0, 1, 2, 3, 4, 5]
- Missing from config: none
- Missing from dataset: none

### gbmbert_evidence_pubmedbert
- Config: `configs\training\gbmbert_evidence_pubmedbert.json`
- Governance profile: scaffold
- Dataset: `data\training\evidence_pack\annotation_splits`
- Config labels: 0, 1, 2, 3, 4, 5
- Dataset labels: test=[0, 1, 2, 3, 4, 5]; train=[0, 1, 2, 3, 4, 5]; validation=[0, 1, 2, 3, 4, 5]
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

### gbmbert_ner_bio_pubmedbert
- Config: `configs\training\gbmbert_ner_bio_pubmedbert.json`
- Governance profile: scaffold
- Dataset: `data\training\ner_bio_pack\annotation_splits`
- Config labels: O, B-BIOMARKER, B-CELL_STATE, B-CELL_TYPE, B-DELIVERY_MODIFIER, B-DISEASE, B-DRUG, B-GENE, B-OUTCOME, B-PATHWAY, B-TREATMENT, B-TRIAL_PHASE, I-BIOMARKER, I-CELL_STATE, I-CELL_TYPE, I-DELIVERY_MODIFIER, I-DISEASE, I-DRUG, I-GENE, I-OUTCOME, I-PATHWAY, I-TREATMENT, I-TRIAL_PHASE
- Dataset labels: test=[B-BIOMARKER, B-CELL_STATE, B-CELL_TYPE, B-DELIVERY_MODIFIER, B-DISEASE, B-DRUG, B-GENE, B-OUTCOME, B-PATHWAY, B-TREATMENT, B-TRIAL_PHASE, I-BIOMARKER, I-CELL_STATE, I-CELL_TYPE, I-DELIVERY_MODIFIER, I-DISEASE, I-DRUG, I-GENE, I-OUTCOME, I-PATHWAY, I-TREATMENT, I-TRIAL_PHASE, O]; train=[B-BIOMARKER, B-CELL_STATE, B-CELL_TYPE, B-DELIVERY_MODIFIER, B-DISEASE, B-DRUG, B-GENE, B-OUTCOME, B-PATHWAY, B-TREATMENT, B-TRIAL_PHASE, I-BIOMARKER, I-CELL_STATE, I-CELL_TYPE, I-DELIVERY_MODIFIER, I-DISEASE, I-DRUG, I-GENE, I-OUTCOME, I-PATHWAY, I-TREATMENT, I-TRIAL_PHASE, O]; validation=[B-BIOMARKER, B-CELL_STATE, B-CELL_TYPE, B-DELIVERY_MODIFIER, B-DISEASE, B-DRUG, B-GENE, B-OUTCOME, B-PATHWAY, B-TREATMENT, B-TRIAL_PHASE, I-BIOMARKER, I-CELL_STATE, I-CELL_TYPE, I-DELIVERY_MODIFIER, I-DISEASE, I-DRUG, I-GENE, I-OUTCOME, I-PATHWAY, I-TREATMENT, I-TRIAL_PHASE, O]
- Missing from config: none
- Missing from dataset: none

### gbmbert_ner_pubmedbert
- Config: `configs\training\gbmbert_ner_pubmedbert.json`
- Governance profile: scaffold
- Dataset: `data\training\gold_pack\annotation_splits`
- Config labels: GENE, DRUG, DISEASE, PATHWAY, BIOMARKER, CELL_TYPE, CELL_STATE, TREATMENT, DELIVERY_MODIFIER, OUTCOME, TRIAL_PHASE, UNKNOWN
- Dataset labels: test=[BIOMARKER, CELL_STATE, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, PATHWAY, TREATMENT, TRIAL_PHASE, UNKNOWN]; train=[BIOMARKER, CELL_STATE, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, PATHWAY, TREATMENT, TRIAL_PHASE, UNKNOWN]; validation=[BIOMARKER, CELL_STATE, CELL_TYPE, DELIVERY_MODIFIER, DISEASE, DRUG, GENE, OUTCOME, PATHWAY, TREATMENT, TRIAL_PHASE, UNKNOWN]
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
- Governance profile: scaffold
- Dataset: `data\training\relation_pack\annotation_splits`
- Config labels: ASSOCIATED_WITH, ENHANCES_DELIVERY_OF, IMPROVES, NO_RELATION, PREDICTS, SYNERGIZES_WITH, TARGETS, WORSENS
- Dataset labels: test=[ASSOCIATED_WITH, IMPROVES, NO_RELATION, PREDICTS, SYNERGIZES_WITH, WORSENS]; train=[ASSOCIATED_WITH, ENHANCES_DELIVERY_OF, IMPROVES, NO_RELATION, PREDICTS, TARGETS, WORSENS]; validation=[ASSOCIATED_WITH, IMPROVES, NO_RELATION, PREDICTS, SYNERGIZES_WITH, WORSENS]
- Missing from config: none
- Missing from dataset: none

## Warnings
- none
