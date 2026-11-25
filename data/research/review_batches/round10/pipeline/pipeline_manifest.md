# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T05:11:52+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 200
- Command: `gbmbert-run-pipeline data\research\review_batches\round10\pubmed_round10_candidates.jsonl --output-dir data\research\review_batches\round10\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round10\pubmed_round10_candidates.jsonl`: 50 records, 165596 bytes, SHA256 `146B6AA8D9D29646BA471953050B4871ABF771BAC6C198313F6A74F23B49803D`
- `data\research\review_batches\round10\pipeline\entities.jsonl`: 50 records, 88407 bytes, SHA256 `197C935DB55D8EF5EDCFD8F8D2505EA745FFCD0FE9CB9870D0DC3145038FC79F`
- `data\research\review_batches\round10\pipeline\evidence_claims.jsonl`: 50 records, 15681 bytes, SHA256 `54C7BFBDE7ED50D036BA7A9ECEB0CA39D86217B89F7ADD2A60A01D1029651791`
- `data\research\review_batches\round10\pipeline\graph_records.jsonl`: 50 records, 283586 bytes, SHA256 `EF826440B83A8930D1B5F26258223312DD15617B2C9981B89F8476E5D91A2A41`
- `data\research\review_batches\round10\pipeline\graph_quality_report.json`: 200 non-empty lines, 3854 bytes, SHA256 `FEE7C05D0357F088011F7332B6E675F575C42B6F337F974575E6DE41B9887BB4`
- `data\research\review_batches\round10\pipeline\graph_quality_report.md`: 55 non-empty lines, 1729 bytes, SHA256 `BF95909C44FFF1984F4984BAD421E2A3AD3E006651D371732E6D3AFDB8B5907D`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
