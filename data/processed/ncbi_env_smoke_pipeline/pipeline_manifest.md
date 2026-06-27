# Corpus Manifest: ncbi_env_smoke_pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-06-23T03:00:23+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 52
- Command: `gbmbert-run-pipeline data\raw\ncbi_env_smoke_2026-06-23.jsonl --output-dir data\processed\ncbi_env_smoke_pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\raw\ncbi_env_smoke_2026-06-23.jsonl`: 13 records, 25846 bytes, SHA256 `8E9BA49933D152A7FDBDDFF8835DDF73A781DC5C805F58F8DD8E98E486877107`
- `data\processed\ncbi_env_smoke_pipeline\entities.jsonl`: 13 records, 14414 bytes, SHA256 `1096665318DFD6706A0A06149428A667AC6BF88413CA07883A1124240DB5EC7A`
- `data\processed\ncbi_env_smoke_pipeline\evidence_claims.jsonl`: 13 records, 3518 bytes, SHA256 `32A30BE5E9C9414CF86800F43FA00A9E7F1781482C700A88D84E73E92DBA323B`
- `data\processed\ncbi_env_smoke_pipeline\graph_records.jsonl`: 13 records, 46277 bytes, SHA256 `E9A4C9B7D1810171DA98A995A0EB4B5C14BB735EC0E0E2B137131070DCA2CCDD`
- `data\processed\ncbi_env_smoke_pipeline\graph_quality_report.json`: 138 non-empty lines, 2555 bytes, SHA256 `601DC4BE9C10581FB76FC42CC33BE0473DEB025625676690DD4AE9F182B289E1`
- `data\processed\ncbi_env_smoke_pipeline\graph_quality_report.md`: 43 non-empty lines, 1174 bytes, SHA256 `F6D03C9C9CDFFE65CE7C1D4E3BB828F964F73BDC073D2DF4B53CFAE317C363F2`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
