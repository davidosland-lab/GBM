# GBM-BERT Model Card: gbmbert_evidence_smoke

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Task: evidence_classification
- Base model: `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext`
- Checkpoint status: research_candidate
- Checkpoint directory: `data\training\evidence_smoke_fixture\checkpoint`

## Metrics
- examples: 2
- accuracy: 1.0
- macro_f1: 1.0

## Provenance
- Metrics path: `reports\training\evidence_smoke_fixture\evidence_smoke_metrics.json`
- Dataset directory: `data\training\evidence_smoke_fixture\splits`
- Label map directory: `data\training\evidence_smoke_fixture\label_maps`

## Limitations
- Research-use only; not medical advice.
- Not intended for diagnosis, treatment selection, or clinical decision-making.
- Performance metrics are local research artifacts and do not establish clinical validity.
- Training data may be small, imbalanced, or manually curated for research exploration.
