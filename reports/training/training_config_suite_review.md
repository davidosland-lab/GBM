# GBM-BERT Training Config Suite Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Configs: 3
- Passed: 1
- Failed: 2

## Reviews
### gbmbert_evidence_pubmedbert.json
- Status: failed
- Task: evidence_classification
- Errors:
- config label_set labels missing from dataset: 2, 3, 4, 5
- label map labels do not match config label_set

### gbmbert_ner_pubmedbert.json
- Status: failed
- Task: ner
- Errors:
- config label_set labels missing from dataset: CELL_STATE, PATHWAY, TRIAL_PHASE, UNKNOWN
- label map labels do not match config label_set

### gbmbert_relation_biobert.json
- Status: passed
- Task: relation_extraction
- Errors:
- none

## Warnings
- configs\training\gbmbert_evidence_pubmedbert.json: failed
- configs\training\gbmbert_ner_pubmedbert.json: failed
