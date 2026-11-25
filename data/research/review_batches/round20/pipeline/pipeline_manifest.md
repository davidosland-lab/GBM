# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-19T09:02:44+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 280
- Command: `gbmbert-run-pipeline data\research\review_batches\round20\pubmed_round20_candidates.jsonl --output-dir data\research\review_batches\round20\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round20\pubmed_round20_candidates.jsonl`: 70 records, 130706 bytes, SHA256 `7732CC49732362B19906366D411123A1AE016B31FBE7F85D512E486801E4A163`
- `data\research\review_batches\round20\pipeline\entities.jsonl`: 70 records, 63657 bytes, SHA256 `33FE5A50518978A62AF46D669C4AB901A9BB6BB68CACF124B9A4A4D956871B73`
- `data\research\review_batches\round20\pipeline\evidence_claims.jsonl`: 70 records, 19661 bytes, SHA256 `435D1E5EA57DDFD45070F91AB15E337B1E2937EA9871D82E6DB609ABFF9ED9F8`
- `data\research\review_batches\round20\pipeline\graph_records.jsonl`: 70 records, 209594 bytes, SHA256 `0B833892D09AA6B12701554747B5EDE2503876B4BA3C6C23824C7F7740F120C9`
- `data\research\review_batches\round20\pipeline\graph_quality_report.json`: 128 non-empty lines, 2422 bytes, SHA256 `65E6B510874CBAFE011B378836CA3D6EFB854B5F0938EB5E64852EA2CF48D183`
- `data\research\review_batches\round20\pipeline\graph_quality_report.md`: 41 non-empty lines, 1154 bytes, SHA256 `349FE563FE522B052346D9E0DB24E59E54B155840F02AE4A11BEAE41CA3E32EF`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
