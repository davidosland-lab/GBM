# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-22T07:02:58+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 276
- Command: `gbmbert-run-pipeline data\research\round8_pubmed_v2_2026-07-22.jsonl --output-dir data\research\review_batches\round8\pipeline --entity-mode lexicon`
- NCBI email configured: False
- NCBI API key configured: False

## Files
- `data\research\round8_pubmed_v2_2026-07-22.jsonl`: 69 records, 159278 bytes, SHA256 `23F3EF98188F33E763CFD1D5D150B25D0421094E1249DFA77461368539859F63`
- `data\research\review_batches\round8\pipeline\entities.jsonl`: 69 records, 69681 bytes, SHA256 `637AAE93E0965C89F44AFF831366B973D4EE31ED6950E9AF14C2BAA993340F18`
- `data\research\review_batches\round8\pipeline\evidence_claims.jsonl`: 69 records, 20478 bytes, SHA256 `6F4D2AA57081EEB0A7DEA7A2AC501179E1CC8C1698AFA9A577C2BD4D3E85EF12`
- `data\research\review_batches\round8\pipeline\graph_records.jsonl`: 69 records, 247964 bytes, SHA256 `DC157EE94D1B8D8B25E8E9FABC4F38CA7B269A46715AA63C62CB4D8E27F83FDE`
- `data\research\review_batches\round8\pipeline\graph_quality_report.json`: 166 non-empty lines, 3295 bytes, SHA256 `6BC27A515E75A2E994E2FA94F032C797A5E3484A8F61CD0C42FD18E7C2E7BB82`
- `data\research\review_batches\round8\pipeline\graph_quality_report.md`: 48 non-empty lines, 1559 bytes, SHA256 `3665568CA67893B14C95D54FE7517EF8FA8844B59C706E99092F1F0E33C8172C`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
