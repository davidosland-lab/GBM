# Corpus Manifest: gallbladder_v1

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-09-08T06:26:22+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 632
- Command: `gbmbert-run-pipeline data\raw\pubmed_gallbladder_v1_2026-09-08.jsonl --output-dir data\processed\gallbladder_v1 --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\raw\pubmed_gallbladder_v1_2026-09-08.jsonl`: 158 records, 361781 bytes, SHA256 `814048B3AD954C9AC0A2745DE2E0F8EDA51CD00ACADF4701A8D9AE8ADF0A024F`
- `data\processed\gallbladder_v1\entities.jsonl`: 158 records, 201550 bytes, SHA256 `9DE51B2CB25E5677E9ED5BF053A639B58A11AB572ED8CBB220108DC508B57510`
- `data\processed\gallbladder_v1\evidence_claims.jsonl`: 158 records, 45052 bytes, SHA256 `4B1DFEC42F3BB43D579423EBBF0337FCBB25A608BBD77B13DAEF0C9B668E9E24`
- `data\processed\gallbladder_v1\graph_records.jsonl`: 158 records, 647581 bytes, SHA256 `467E80C888EF9B943879268758C8CB27086A3798AC0FE52E7CD0F7648C2F9D7C`
- `data\processed\gallbladder_v1\graph_quality_report.json`: 140 non-empty lines, 2893 bytes, SHA256 `1DEC08362926F8900979C9F9A75A23D162D9F5EC5F31547DBE18CF5936876A5A`
- `data\processed\gallbladder_v1\graph_quality_report.md`: 42 non-empty lines, 1476 bytes, SHA256 `77DD9AA512BCD75B77C5EFB0E4F898C06A19568DF339B7752BADAFA623ED2378`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gallbladder_v1.json
