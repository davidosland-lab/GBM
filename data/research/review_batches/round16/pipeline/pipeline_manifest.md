# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T10:39:22+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 400
- Command: `gbmbert-run-pipeline data\research\review_batches\round16\pubmed_round16_candidates.jsonl --output-dir data\research\review_batches\round16\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round16\pubmed_round16_candidates.jsonl`: 100 records, 211316 bytes, SHA256 `0D89666FE91786CD6D551B2302AC99BCDA82D8FF96E0EDD86FCC435806580DD5`
- `data\research\review_batches\round16\pipeline\entities.jsonl`: 100 records, 117061 bytes, SHA256 `6464B8BA950F14AE6A2CCDDF2AB515A798B986E3F39AC2382ED93AC4F8155B34`
- `data\research\review_batches\round16\pipeline\evidence_claims.jsonl`: 100 records, 28843 bytes, SHA256 `D46822B95B76D10FAD86D29321916A1BB1087BBF2BDCBF5244B319518A95F0EA`
- `data\research\review_batches\round16\pipeline\graph_records.jsonl`: 100 records, 357166 bytes, SHA256 `50AF803A92B91589A102ADE13F029B16A176315F4260A55DED8518F2DA759619`
- `data\research\review_batches\round16\pipeline\graph_quality_report.json`: 164 non-empty lines, 3115 bytes, SHA256 `423D2DBA0DFC1125136707CF0BE934156D2600E5D4E8E7A70AE7ECD1BCFB50D8`
- `data\research\review_batches\round16\pipeline\graph_quality_report.md`: 48 non-empty lines, 1421 bytes, SHA256 `87038DF7DE8C2BDCBC3E1D479817E86E102E6CADDDB3B20CB4ECB594755CE2D1`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
