# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T05:02:16+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 140
- Command: `gbmbert-run-pipeline data\research\review_batches\round9\pubmed_round9_candidates.jsonl --output-dir data\research\review_batches\round9\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round9\pubmed_round9_candidates.jsonl`: 35 records, 65759 bytes, SHA256 `BC468B055F78334197AE17D79338052835A672A5BA0A4443502B5DEF26ABC27B`
- `data\research\review_batches\round9\pipeline\entities.jsonl`: 35 records, 33938 bytes, SHA256 `503ED2EBB97BA21FFD8397D7E275248C46535BF15918E387D9828E28BDFDA707`
- `data\research\review_batches\round9\pipeline\evidence_claims.jsonl`: 35 records, 9804 bytes, SHA256 `48E027A74A5A74BE94794B5A643AF2D93814B59668492FABF7D0DB54304CA787`
- `data\research\review_batches\round9\pipeline\graph_records.jsonl`: 35 records, 114734 bytes, SHA256 `061428E02699615EE23EB07372591F723849865B57E2744DB32FA9907600E7D7`
- `data\research\review_batches\round9\pipeline\graph_quality_report.json`: 170 non-empty lines, 3289 bytes, SHA256 `D9602246DA5882A32438E473AFA24B5E3ED28D4477A1EDEE7048F7FAD2F84419`
- `data\research\review_batches\round9\pipeline\graph_quality_report.md`: 49 non-empty lines, 1519 bytes, SHA256 `DFD4F03D6CEF0EB148793B73DDC11210E8BD9AED0A5428E340EA4A7AA2678425`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
