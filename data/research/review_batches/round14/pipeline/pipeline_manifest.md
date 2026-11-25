# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T10:22:14+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 200
- Command: `gbmbert-run-pipeline data\research\review_batches\round14\pubmed_round14_candidates.jsonl --output-dir data\research\review_batches\round14\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round14\pubmed_round14_candidates.jsonl`: 50 records, 109959 bytes, SHA256 `23A5B797875C7EF58CED52A1B5194953EFACB69AB1DE3ECAA203B84559214DE4`
- `data\research\review_batches\round14\pipeline\entities.jsonl`: 50 records, 67328 bytes, SHA256 `3ECBDED20E90BA9441C5057D7FE07A90B0624C352755D542B19C94E4B2526733`
- `data\research\review_batches\round14\pipeline\evidence_claims.jsonl`: 50 records, 14607 bytes, SHA256 `7C2664438DFF0D6B3BB28330DCAFB267E85174D9762BA5EE4B99236CA29FA7E4`
- `data\research\review_batches\round14\pipeline\graph_records.jsonl`: 50 records, 202207 bytes, SHA256 `19A5385FDE074EF8D7FCB33E6D7ADCFCA626463767D2A4FAC7F33DFE5FD0749B`
- `data\research\review_batches\round14\pipeline\graph_quality_report.json`: 198 non-empty lines, 3809 bytes, SHA256 `1C8A29BC62565ADEE499D0FC839F1E8310BDD087FC188BD95B37DC0F49AAF3D9`
- `data\research\review_batches\round14\pipeline\graph_quality_report.md`: 55 non-empty lines, 1716 bytes, SHA256 `9F3AC85A07013A49A55A62768A4764764D0607535FC4B846197DE7E5A76A8609`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
