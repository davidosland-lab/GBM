# GBM-BERT Model Card: gbmbert_evidence_experiment_pubmedbert_v4

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Task: evidence_classification
- Base model: `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext`
- Checkpoint status: research_candidate
- Checkpoint directory: `models\checkpoints\gbmbert_evidence_experiment_pubmedbert_v4`

## Metrics
- examples: 57
- accuracy: 0.40350877192982454
- macro_f1: 0.25831649831649833

## Provenance
- Metrics path: `reports\training\evidence_experiment_v4_metrics.json`
- Dataset directory: `data\training\evidence_pack\annotation_splits`
- Label map directory: `data\training\evidence_pack\label_maps`

## Limitations
- Research-use only; not medical advice.
- Not intended for diagnosis, treatment selection, or clinical decision-making.
- Performance metrics are local research artifacts and do not establish clinical validity.
- Training data may be small, imbalanced, or manually curated for research exploration.
