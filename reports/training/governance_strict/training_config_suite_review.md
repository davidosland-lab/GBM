# GBM-BERT Training Config Suite Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Configs: 7
- Current passed: 2
- Current failed: 0
- Scaffold configs: 5

## Reviews
### gbmbert_evidence_experiment_pubmedbert.json
- Status: scaffold_ready
- Governance profile: scaffold
- Blocking: False
- Task: evidence_classification
- Note: Preferred baseline remains evidence v9 (macro-F1 0.59; tier-4 F1 0.71). Round 32 added +26 PMID-disjoint curated evidence rows (835 total; tiers 0–5 present). Volume/tier-balance change not material vs v9 — skip retrain. training_enabled=false. Research-use only; not a validated clinical model. Run artifacts under reports/training/evidence_experiment_v9_*.
- Errors:
- none

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

### gbmbert_ner_bio_pubmedbert.json
- Status: scaffold_ready
- Governance profile: scaffold
- Blocking: False
- Task: ner
- Note: Preferred baseline remains BIO NER v6 (span 0.987 / type macro-F1 0.691). Round 31 span-reviewed sparse densify added quality CELL_STATE/PATHWAY (dual-review agreement 0.98); BIO pack now ~95 CELL_STATE / ~46 PATHWAY after gene-symbol PATHWAY→GENE remap. No v7 retrain in this polish — densify is material for sparse types but freeze-split comparison vs v6 was not run; keep v6 until a controlled experiment. training_enabled=false. Research-use only; not a validated clinical model. Run artifacts under reports/training/ner_bio_experiment_v6_*.
- Errors:
- none

### gbmbert_ner_pubmedbert.json
- Status: scaffold_ready
- Governance profile: scaffold
- Blocking: False
- Task: ner
- Note: Completed NER scaffold research experiment (max_steps=200, class-weighted CE) on the expanded local gold pack. Metrics use majority-token decode over span examples (not span-level BIO). Re-enable training_enabled and pass --confirm-training-enabled to repeat. Research-use only; not a validated clinical model. Run artifacts under reports/training/ner_experiment_v1_*.
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
- Status: scaffold_ready
- Governance profile: scaffold
- Blocking: False
- Task: relation_extraction
- Note: Completed Round 25 PREDICTS/WORSENS fill + class-weighted BioBERT relation experiment (v3). Macro-F1 0.59 (was 0.58 on v2). Re-enable training_enabled and pass --confirm-training-enabled to repeat. Research-use only; not a validated clinical model. Run artifacts under reports/training/relation_experiment_v3_*.
- Errors:
- none

## Blocking Warnings
- none

## Scaffold Warnings
- none
