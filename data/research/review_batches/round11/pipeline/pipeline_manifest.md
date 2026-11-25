# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T05:37:41+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 200
- Command: `gbmbert-run-pipeline data\research\review_batches\round11\pubmed_round11_candidates.jsonl --output-dir data\research\review_batches\round11\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round11\pubmed_round11_candidates.jsonl`: 50 records, 121858 bytes, SHA256 `AD6C57C1C64B48C054CD5E8F608A099C3A6852225D1AD20A4C41017BE20C2805`
- `data\research\review_batches\round11\pipeline\entities.jsonl`: 50 records, 96460 bytes, SHA256 `CF63103FFFB8874BCF761C311D3A8AD1873BBAB5E9A6005C1FB5360897CB73B0`
- `data\research\review_batches\round11\pipeline\evidence_claims.jsonl`: 50 records, 15390 bytes, SHA256 `CF1FDC203A8906DB8A496DC66307BC154DA8167F29D417412B838290C86E46EA`
- `data\research\review_batches\round11\pipeline\graph_records.jsonl`: 50 records, 258614 bytes, SHA256 `6EDEEEF4D5049659E4976D641FDC82E7F04292377A06F256E08F4BB0802A34A2`
- `data\research\review_batches\round11\pipeline\graph_quality_report.json`: 200 non-empty lines, 3793 bytes, SHA256 `93339D361FA3F9FDC45BD9D1DFBBB07BF37E9B9E41FC52F06DF6DB1A642658EB`
- `data\research\review_batches\round11\pipeline\graph_quality_report.md`: 55 non-empty lines, 1663 bytes, SHA256 `8ABE6EBE46AD681DC9EBD9B5F0CEBB00919DD300F60B80DD2F09C976F11ECDA5`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
