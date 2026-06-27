# GBM-BERT Training Config Suite Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Configs: 5
- Current passed: 3
- Current failed: 0
- Scaffold configs: 2

## Reviews
### gbmbert_evidence_pubmedbert.json
- Status: scaffold_pending
- Governance profile: scaffold
- Blocking: False
- Task: evidence_classification
- Note: Full evidence label profile retained for future larger curated datasets; not validated against the tiny smoke evidence pack.
- Errors:
- config label_set labels missing from dataset: 2, 3, 4, 5
- label map labels do not match config label_set

### gbmbert_evidence_smoke_pubmedbert.json
- Status: passed
- Governance profile: current
- Blocking: True
- Task: evidence_classification
- Note: Current smoke evidence config aligned to the local evidence-only smoke pack.
- Errors:
- none

### gbmbert_ner_pubmedbert.json
- Status: scaffold_pending
- Governance profile: scaffold
- Blocking: False
- Task: ner
- Note: Future NER scaffold with broader vocabulary than the current tiny smoke NER labels.
- Errors:
- config label_set labels missing from dataset: CELL_STATE, PATHWAY, TRIAL_PHASE, UNKNOWN
- label map labels do not match config label_set

### gbmbert_ner_smoke_pubmedbert.json
- Status: passed
- Governance profile: current
- Blocking: True
- Task: ner
- Note: Current smoke NER config aligned to the populated local NCBI-style smoke NER splits.
- Errors:
- none

### gbmbert_relation_biobert.json
- Status: passed
- Governance profile: current
- Blocking: True
- Task: relation_extraction
- Note: Current relation config aligned to the local relation-only training pack.
- Errors:
- none

## Blocking Warnings
- none

## Scaffold Warnings
- configs\training\gbmbert_evidence_pubmedbert.json: scaffold pending (config label_set labels missing from dataset: 2, 3, 4, 5; label map labels do not match config label_set)
- configs\training\gbmbert_ner_pubmedbert.json: scaffold pending (config label_set labels missing from dataset: CELL_STATE, PATHWAY, TRIAL_PHASE, UNKNOWN; label map labels do not match config label_set)
