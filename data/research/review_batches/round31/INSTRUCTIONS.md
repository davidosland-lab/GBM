# Round 31 — BIO sparse-type densify

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Goal

Span-reviewed gold for `CELL_STATE` and `PATHWAY` (quality multi-token pathway phrases; avoid bare gene-symbol PATHWAY dumps that BIO pack remaps to GENE).

## Dual review

- `span_review_r1_round31.jsonl` / `span_review_r2_round31.jsonl`
- Consensus: `span_review_consensus_round31.jsonl`
- Adjudication: `adjudication_round31_spans.json` (agreement ~0.98)

## Promotion

Accepted consensus spans live in:

- `data/training/curated_expansion/gold_entities_round31.jsonl`
- Empty evidence/queue trio files so `gbmbert-rebuild-curated-rounds` discovers the round

## Provenance

PubMed fetch (raw bulk; may be local-only):

- `data/raw/pubmed_gbm_sparse_densify_round31_2026-07-21.jsonl`
- `data/raw/pubmed_gbm_fill_extra_2026-07-21.jsonl`
