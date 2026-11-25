# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-19T10:02:38+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 320
- Command: `gbmbert-run-pipeline data\research\review_batches\round21\pubmed_round21_candidates.jsonl --output-dir data\research\review_batches\round21\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round21\pubmed_round21_candidates.jsonl`: 80 records, 172310 bytes, SHA256 `864DA75581E7A931C00ED71012C5E69BCB999FC108AF73E3DC7F096288202FA9`
- `data\research\review_batches\round21\pipeline\entities.jsonl`: 80 records, 66514 bytes, SHA256 `1B4FF0472C4D90A2A20BD388E641A6E4F4D34704DD1476EE704AD1D3A6263B9B`
- `data\research\review_batches\round21\pipeline\evidence_claims.jsonl`: 80 records, 23968 bytes, SHA256 `8D5537929722E1D80F39BBD83CFCAD840CBD6F2806D551E06738ECC7756928E8`
- `data\research\review_batches\round21\pipeline\graph_records.jsonl`: 80 records, 254958 bytes, SHA256 `997C678277D94BCC7EB89D3AEE3AC6170638319A61EFDB13AE53EFA80199B45C`
- `data\research\review_batches\round21\pipeline\graph_quality_report.json`: 134 non-empty lines, 2522 bytes, SHA256 `4337EFA08F3DF3A842B5F17BEFA3784613378A4D80DFAFE23AA6054B94373CF2`
- `data\research\review_batches\round21\pipeline\graph_quality_report.md`: 42 non-empty lines, 1183 bytes, SHA256 `AD05159EA3A02BA555D062C486BA48BA5BCFAD7AF6E73048E4CF7ABDE97C70A0`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
