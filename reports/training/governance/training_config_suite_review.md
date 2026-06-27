# GBM-BERT Training Config Suite Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Configs: 5
- Current passed: 3
- Current failed: 0
- Scaffold configs: 2

## Reviews
### gbmbert_evidence_pubmedbert.json
- Status: scaffold_ready
- Governance profile: scaffold
- Blocking: False
- Task: evidence_classification
- Note: Full evidence label profile aligned to the local curated full-label evidence pack; retained as scaffold until more rows are curated beyond the minimal fixture.
- Errors:
- none

### gbmbert_evidence_smoke_pubmedbert.json
- Status: passed
- Governance profile: current
- Blocking: True
- Task: evidence_classification
- Note: Current smoke evidence config aligned to the local evidence-only smoke pack.
- Errors:
- none

### gbmbert_ner_pubmedbert.json
- Status: scaffold_ready
- Governance profile: scaffold
- Blocking: False
- Task: ner
- Note: Broad NER scaffold aligned to the expanded local gold pack; retained as scaffold until the curated fixture is larger.
- Errors:
- none

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
- none
