# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T10:22:03+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 200
- Command: `gbmbert-run-pipeline data\research\review_batches\round13\pubmed_round13_candidates.jsonl --output-dir data\research\review_batches\round13\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round13\pubmed_round13_candidates.jsonl`: 50 records, 105395 bytes, SHA256 `C62934AB2438F0CD9837BEB682C246427F760B35FDAD5169C9E2FC1B50694F42`
- `data\research\review_batches\round13\pipeline\entities.jsonl`: 50 records, 74649 bytes, SHA256 `C716B12F87EABBA8A34B603DC0857B3A5442D330E514F8BAF0BA8FDBEDC1B145`
- `data\research\review_batches\round13\pipeline\evidence_claims.jsonl`: 50 records, 14756 bytes, SHA256 `ACE23A7E97F0CCBB085E3EC3CE68B5E4322F35B1BF3E430DE5974F8E9EF0CD2C`
- `data\research\review_batches\round13\pipeline\graph_records.jsonl`: 50 records, 213679 bytes, SHA256 `316A970EB275BBCBB96C93339AA928F6BFDA04390D524A5A1CD6E2BEAC91AAE3`
- `data\research\review_batches\round13\pipeline\graph_quality_report.json`: 200 non-empty lines, 3827 bytes, SHA256 `5412F6DFDC3905E2E156EA0ED71BCE7791480F02FDB5585DC2B046ACA850498F`
- `data\research\review_batches\round13\pipeline\graph_quality_report.md`: 55 non-empty lines, 1697 bytes, SHA256 `2A25A20A524E8F8A0508A23B2BC8A5D63A9872673C369406D3E9D63709EA35B7`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
