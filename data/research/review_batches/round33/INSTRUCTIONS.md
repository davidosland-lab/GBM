# Round 33 — Sparse NER densify dual-review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Goal

Human dual-review of sparse NER spans for research gold-pack deepening (CELL_STATE, PATHWAY, TRIAL_PHASE, UNKNOWN). Prefer quality multi-token PATHWAY phrases; avoid bare gene-symbol PATHWAY.

- Pending spans: **48** across **27** PMID(s)
- CELL_STATE: 12
- PATHWAY: 12
- TRIAL_PHASE: 12
- UNKNOWN: 12

## Queues (all pending — do not auto-accept)

- Reviewer 1: `data\research\review_batches\round33\span_review_r1_round33.jsonl`
- Reviewer 2: `data\research\review_batches\round33\span_review_r2_round33.jsonl`
- Shared CSV: `data\research\review_batches\round33\span_review_dual_round33.csv`

## Human steps

1. Independently set each row `review_status` to accepted / corrected / rejected.
2. For corrections, fill `corrected_label` / offsets / text.
3. Run `gbmbert-adjudication-report` on r1 vs r2 JSONL.
4. Write consensus JSONL, then promote accepted spans into `data/training/curated_expansion/gold_entities_round33.jsonl`.
5. Run `gbmbert-rebuild-curated-rounds` and `gbmbert-gold-pack-ops-status`.

## Boundary

Research-use only. Not clinical validation. Deepen governance/quality — do not scale lit-mining or claim CDS.
