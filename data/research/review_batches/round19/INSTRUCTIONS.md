# Review Batch Round 19 — Instructions

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Annotate the reviewed-queue skeleton, then finalize round 19.

1. Open `data\research\review_batches\round19\gold_reviewed_queue_round19.jsonl`. Each line is one item (evidence_claim or graph_relation).
2. For every row, set `review_status` to `accepted`, `corrected`, or `rejected` (it starts as `pending`).
   - evidence_claim: verify/correct `evidence_tier` (0-5) or set `corrected_evidence_tier`.
   - graph_relation: verify/correct `relation_type` or set `corrected_relation_type`.
   - add a one-line `review_notes` rationale.
3. Entity spans in `data\research\review_batches\round19\gold_entities_round19.jsonl` are lexicon-suggested (not span-reviewed); leave or trim as needed.
4. Run `gbmbert-finalize-review-batch --round 19`. It promotes the round into the
   curated-expansion dir only when no row is still `pending`. Accepted and corrected rows enter the corpus.
5. Run `gbmbert-rebuild-curated-rounds` then `gbmbert-verify-local`.

Research-use only. Tiers and relations are the human-reviewed signal; this does not promote a
dataset or claim a validated GBM-BERT model exists.