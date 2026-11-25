# Corpus fill — rounds 31–32

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## What was imported (tracked)

| Artifact | Role |
| --- | --- |
| `data/training/curated_expansion/*_round31.jsonl` | BIO sparse densify (CELL_STATE/PATHWAY) |
| `data/training/curated_expansion/*_round32.jsonl` | Curated evidence fill (PMID-disjoint) |
| `data/research/review_batches/round31/` | Dual span-review + adjudication |
| `data/research/review_batches/round32/` | Evidence review queue + instructions |
| `data/examples/pubmed_records_sample.jsonl` | Offline literature UI fixture |
| `data/examples/ebm_nlp_sample/` (+ PMID `29097493`) | Tracked EBM-NLP GBM-ish sample |

## Raw bulk (local / not required in git)

| Artifact | Role |
| --- | --- |
| `data/raw/pubmed_gbm_sparse_densify_round31_2026-07-21.jsonl` | NCBI fetch for densify candidates |
| `data/raw/pubmed_gbm_evidence_round32_2026-07-21.jsonl` | NCBI fetch for evidence candidates |
| `data/raw/pubmed_gbm_fill_extra_2026-07-21.jsonl` | Extra cell-state / tier fill fetch |
| `data/raw/ebm_nlp/` (gitignored) | Full EBM-NLP bulk if re-imported |
| BioRED zip under `data/research/biored/` | External bulk (import reports already tracked) |

## Counts after rebuild

- Curated evidence: **835** (was 809); source PMIDs in evidence ~**824**
- Gold pack (promotion review): evidence **835** / NER **8070** / relation **294** / source PMIDs **951** — promotable
- Round 31 spans (consensus): CELL_STATE **26**, PATHWAY **24** (dual-review agreement **0.98**)
- BIO pack after rebuild: CELL_STATE **95**, PATHWAY **46** (gene-symbol PATHWAY→GENE remaps still applied)

## Retrain decisions

- **BIO NER**: no v7 — keep preferred **v6**; densify shipped into pack/gold
- **Evidence**: no v10 — keep preferred **v9**; +26 rows not material for tier balance
