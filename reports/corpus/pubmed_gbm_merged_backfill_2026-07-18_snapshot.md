# PubMed Merged Backfill Snapshot - 2026-07-18

> Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Purpose

Larger PubMed backfill from curated query packs `pubmed_gbm_v1` and `pubmed_gbm_v2` after tuning five previously empty v2 queries. Intended for literature pipeline, review-queue, and research evidence-classifier scoring — not clinical use.

## Query Tuning

These `pubmed_gbm_v2` queries returned zero hits at `retmax-per-query=3` in the 2026-06-23 small snapshot and were rewritten to preserve topic intent while returning records:

| Previous (zero-hit) | Tuned |
|---|---|
| `glioblastoma SonoCloud Exablate Neuro` | `glioblastoma (SonoCloud OR Exablate)` |
| `glioblastoma oncolytic virus DNX-2401 CAN-3110 G47` | `glioblastoma ("oncolytic virus" OR DNX-2401 OR CAN-3110 OR "G47Delta" OR G47)` |
| `glioblastoma GD2 CAR-T chlorotoxin CAR-T` | `glioblastoma (GD2 OR chlorotoxin) (CAR-T OR "chimeric antigen receptor")` |
| `glioblastoma neoantigen vaccine NeoVax GAPVAC` | `glioblastoma (neoantigen OR NeoVax OR GAPVAC) vaccine` |
| `glioblastoma Neftel cell states MES NPC OPC AC` | `glioblastoma Neftel (mesenchymal OR "neural progenitor" OR OPC OR "astrocyte-like")` |

All 15 v2 queries returned at least one hit at `retmax-per-query=50`.

## Reproduction Commands

```powershell
.\.venv\Scripts\gbmbert-search-pubmed.exe --query-pack pubmed_gbm_v1 --retmax-per-query 50 --output data\raw\pubmed_gbm_v1_backfill_2026-07-18.jsonl
.\.venv\Scripts\gbmbert-search-pubmed.exe --query-pack pubmed_gbm_v2 --retmax-per-query 50 --output data\raw\pubmed_gbm_v2_backfill_2026-07-18.jsonl
# merge+dedupe by PMID -> data\raw\pubmed_gbm_merged_backfill_2026-07-18.jsonl
.\.venv\Scripts\gbmbert-run-pipeline.exe data\raw\pubmed_gbm_merged_backfill_2026-07-18.jsonl --output-dir data\processed\pubmed_gbm_merged_backfill_pipeline --entity-mode lexicon --lexicon configs\extraction\lexicon_gbm_v1.json
```

NCBI_EMAIL and NCBI_API_KEY were configured. Hugging Face offline mode must be disabled (`HF_HUB_OFFLINE=0`) and Windows symlink privileges avoided (`HF_HUB_DISABLE_SYMLINKS=1`) when downloading PubMedBERT for training.

## Counts

| Artifact | Records |
|---|---:|
| v1 backfill | 612 |
| v2 backfill | 315 |
| Merged unique PMIDs | 912 |
| Pipeline graph records | 912 (0 invalid) |
| Review-queue items exported | 512 |

Bulk raw/processed corpus files are regenerated locally and not committed by default (see `.gitignore`). Manifest: `reports/corpus/pubmed_gbm_merged_backfill_2026-07-18.md`.
