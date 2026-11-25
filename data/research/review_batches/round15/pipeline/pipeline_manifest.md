# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T10:30:03+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 220
- Command: `gbmbert-run-pipeline data\research\review_batches\round15\pubmed_round15_candidates.jsonl --output-dir data\research\review_batches\round15\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round15\pubmed_round15_candidates.jsonl`: 55 records, 113472 bytes, SHA256 `6469957346330FB214072A2CE4390172BAE205ADFE74B2BD278E3C4D8DD8C25D`
- `data\research\review_batches\round15\pipeline\entities.jsonl`: 55 records, 64698 bytes, SHA256 `EEF32EE8B7919FC3D180541866CB26F3EC5E793B0AB27FEC25E1D07A15248A43`
- `data\research\review_batches\round15\pipeline\evidence_claims.jsonl`: 55 records, 15923 bytes, SHA256 `D0CF23127264DD38C825F27FF5A858F2F5F109F71980DB9F387690F566F40463`
- `data\research\review_batches\round15\pipeline\graph_records.jsonl`: 55 records, 203969 bytes, SHA256 `9B21412222D98E8F5DC18EC9C27060A37389707E869CA1048742FED545C2D5B4`
- `data\research\review_batches\round15\pipeline\graph_quality_report.json`: 184 non-empty lines, 3610 bytes, SHA256 `F7AF8DB8A6CEC5756B76EFA664F5FD7F270F0052A1744B34147676206E1E9A71`
- `data\research\review_batches\round15\pipeline\graph_quality_report.md`: 51 non-empty lines, 1651 bytes, SHA256 `71AA1A9E9A6A486E406747FC2213895CFDEEED90E77501FC0965E303B6EFEB25`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
