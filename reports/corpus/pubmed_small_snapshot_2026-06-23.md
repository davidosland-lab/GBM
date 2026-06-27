# PubMed Small Corpus Snapshot - 2026-06-23

> Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Purpose

This snapshot is the first small real PubMed corpus built from the curated GBM-AI query packs. It is intended to exercise the ingestion, extraction, evidence classification, and graph-building pipeline on real literature records before larger backfills.

## Reproduction Commands

Run from `C:\Users\david\GBM` with the project virtual environment:

```powershell
.\.venv\Scripts\gbmbert-search-pubmed.exe --query-pack pubmed_gbm_v1 --retmax-per-query 3 --output data\raw\pubmed_gbm_v1_small_2026-06-23.jsonl
.\.venv\Scripts\gbmbert-search-pubmed.exe --query-pack pubmed_gbm_v2 --retmax-per-query 3 --output data\raw\pubmed_gbm_v2_small_2026-06-23.jsonl
```

NCBI returned records successfully. The local environment emitted the expected warning that `NCBI_EMAIL` is not set; set `NCBI_EMAIL` in `.env` before larger backfills.

## Files

| File | Query pack | Retmax/query | Records | Unique PMIDs | SHA256 |
|---|---:|---:|---:|---:|---|
| `data/raw/pubmed_gbm_v1_small_2026-06-23.jsonl` | `pubmed_gbm_v1` | 3 | 39 | 39 | `1D45FEF4DB5EDFBE3B3AF36E698DAD176396DC4C28EFC4670E5E37C73DB3EF21` |
| `data/raw/pubmed_gbm_v2_small_2026-06-23.jsonl` | `pubmed_gbm_v2` | 3 | 26 | 26 | `CBC9FB363803FBAE77A5EC9E663BAA3E319909556EFB999DB41293B1C43AD760` |

Combined unique PMIDs across both files: 65.

## Year Coverage

### `pubmed_gbm_v1`

| Year | Records |
|---:|---:|
| 2005 | 1 |
| 2013 | 1 |
| 2015 | 1 |
| 2016 | 2 |
| 2018 | 4 |
| 2019 | 4 |
| 2021 | 5 |
| 2022 | 5 |
| 2023 | 6 |
| 2024 | 6 |
| 2025 | 4 |

### `pubmed_gbm_v2`

| Year | Records |
|---:|---:|
| 2013 | 1 |
| 2016 | 1 |
| 2019 | 1 |
| 2020 | 1 |
| 2021 | 6 |
| 2022 | 4 |
| 2023 | 5 |
| 2024 | 3 |
| 2025 | 2 |
| 2026 | 2 |

## Query Coverage

All 13 `pubmed_gbm_v1` queries returned records at `retmax-per-query=3`.

The following `pubmed_gbm_v2` queries returned no records in this small run and should be tuned before larger backfills:

- `glioblastoma SonoCloud Exablate Neuro`
- `glioblastoma oncolytic virus DNX-2401 CAN-3110 G47`
- `glioblastoma GD2 CAR-T chlorotoxin CAR-T`
- `glioblastoma neoantigen vaccine NeoVax GAPVAC`
- `glioblastoma Neftel cell states MES NPC OPC AC`

## Sample Titles

### `pubmed_gbm_v1`

- PMID `23209033`: The definition of primary and secondary glioblastoma.
- PMID `33223018`: Perioperative Management of Patients with Glioblastoma.
- PMID `41403931`: Shaping the glioblastoma microenvironment to enhance CAR-NK immunotherapy.
- PMID `29643471`: Current state of immunotherapy for glioblastoma.
- PMID `39406966`: Immunotherapy for glioblastoma: current state, challenges, and future perspectives.

### `pubmed_gbm_v2`

- PMID `36116720`: Ultrasound-mediated blood-brain barrier opening: An effective drug delivery system for theranostics of brain diseases.
- PMID `35337938`: Translation of focused ultrasound for blood-brain barrier opening in glioma.
- PMID `36537034`: Characteristics of Focused Ultrasound Mediated Blood-Brain Barrier Opening in Magnetic Resonance Images.
- PMID `38647018`: Ultrasmall iron oxide nanoparticles with MRgFUS for enhanced magnetic resonance imaging of orthotopic glioblastoma.
- PMID `32492056`: Focused ultrasound for safe and effective release of brain tumor biomarkers into the peripheral circulation.

## Next Use

Use these files as the input for the next end-to-end pipeline PR:

```powershell
.\.venv\Scripts\gbmbert-extract-entities.exe data\raw\pubmed_gbm_v1_small_2026-06-23.jsonl data\processed\entities_gbm_v1_small_2026-06-23.jsonl
.\.venv\Scripts\gbmbert-classify-evidence.exe data\raw\pubmed_gbm_v1_small_2026-06-23.jsonl data\processed\evidence_gbm_v1_small_2026-06-23.jsonl
```
