# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-19T03:25:35+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 280
- Command: `gbmbert-run-pipeline data\research\review_batches\round19\pubmed_round19_candidates.jsonl --output-dir data\research\review_batches\round19\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round19\pubmed_round19_candidates.jsonl`: 70 records, 143365 bytes, SHA256 `4A83C2C0192283C37DBFC8B488DE2AF8D33D65C2E0EF2100FAFE95B6D5DE4FEE`
- `data\research\review_batches\round19\pipeline\entities.jsonl`: 70 records, 77163 bytes, SHA256 `038C3BB1CD5CD78024AE41F96A9F11817570AB90B64ACBD78F2D413D0366F96A`
- `data\research\review_batches\round19\pipeline\evidence_claims.jsonl`: 70 records, 20246 bytes, SHA256 `BC7C57787F2211E270E5DB3A6183CEE0651059C2457993C888F2577F62BA92D9`
- `data\research\review_batches\round19\pipeline\graph_records.jsonl`: 70 records, 237745 bytes, SHA256 `EF342CCFD7447A1637BFA72CB6F2FA3F4F58140404024FEA6261C0BF8A6D6F2C`
- `data\research\review_batches\round19\pipeline\graph_quality_report.json`: 148 non-empty lines, 2796 bytes, SHA256 `762E307669D5248B11B4A93FC5701ADC7EC63D4504563B7057BFD3314C93D56E`
- `data\research\review_batches\round19\pipeline\graph_quality_report.md`: 45 non-empty lines, 1288 bytes, SHA256 `E76A88CA093B6F830D345CEC71EC4F9C7FFB22663D70AD4002B9A8169543C59F`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
