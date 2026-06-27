# GBM-BERT Active Learning Batch Plan

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Candidates: `data\processed\curation_regression_pack\active_learning_candidates.jsonl`
- Batch JSONL: `data\processed\curation_regression_pack\active_learning_batches.jsonl`
- Candidates: 1
- Batches: 1
- Batch size: 10

## Reasons
- confidence < 1.0: 1
- pmid already present in graph: 1
- tier-change-sensitive evidence: 1

## Evidence Tiers
- tier 3: 1

## Checkpoints
- gbmbert_evidence_smoke: 1

## Warnings
- none
