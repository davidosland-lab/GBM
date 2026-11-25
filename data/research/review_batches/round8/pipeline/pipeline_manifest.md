# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T04:48:29+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 120
- Command: `gbmbert-run-pipeline data\research\review_batches\round8\pubmed_round8_candidates.jsonl --output-dir data\research\review_batches\round8\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round8\pubmed_round8_candidates.jsonl`: 30 records, 59112 bytes, SHA256 `612406BD8AAEBCF24B3F42FF0AC517A4950FF20C8EFB6AC213A4625A1DDF7CB0`
- `data\research\review_batches\round8\pipeline\entities.jsonl`: 30 records, 31692 bytes, SHA256 `DA801085B8CFB812B1F5E70243034324657077AC7921BF2EE2EA26F9DD329996`
- `data\research\review_batches\round8\pipeline\evidence_claims.jsonl`: 30 records, 7877 bytes, SHA256 `92F713175F72881774BCBF746E230C209E074540871B0BED5C47B16D3C352D0C`
- `data\research\review_batches\round8\pipeline\graph_records.jsonl`: 30 records, 100383 bytes, SHA256 `D89A88F3A7531C0087DACEDF31E6A804C81C418E2681F24F69AF35E535891A16`
- `data\research\review_batches\round8\pipeline\graph_quality_report.json`: 130 non-empty lines, 2405 bytes, SHA256 `1D477F2F42B0D177F53925444C7581CE1923779A0D26E39AB239AC22AB18F090`
- `data\research\review_batches\round8\pipeline\graph_quality_report.md`: 41 non-empty lines, 1110 bytes, SHA256 `BE5C623B03FCB5B7FB4B4FB088BA5B2F89682076BFDAF1220D8292D21E88C489`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
