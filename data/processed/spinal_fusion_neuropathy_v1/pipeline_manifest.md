# Corpus Manifest: spinal_fusion_neuropathy_v1

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-23T22:34:41+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 336
- Command: `gbmbert-run-pipeline data\raw\pubmed_spinal_fusion_neuropathy_v1_2026-07-24.jsonl --output-dir data\processed\spinal_fusion_neuropathy_v1 --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\raw\pubmed_spinal_fusion_neuropathy_v1_2026-07-24.jsonl`: 84 records, 195130 bytes, SHA256 `54E5AC28FC8226219DA545A1A59445308FF93E0C9A018F383821C228E831C4CB`
- `data\processed\spinal_fusion_neuropathy_v1\entities.jsonl`: 84 records, 53783 bytes, SHA256 `8ABDFED29CF1E83F5726B6B38AF6D1C5FC8BD930B41F2F2E797F08029D5AA50A`
- `data\processed\spinal_fusion_neuropathy_v1\evidence_claims.jsonl`: 84 records, 24752 bytes, SHA256 `7AA8011CC5C1E2E52E734436F13E0AF53F5952E9A59D4E5B44F4B4ADE2B15163`
- `data\processed\spinal_fusion_neuropathy_v1\graph_records.jsonl`: 84 records, 265238 bytes, SHA256 `0A71016256B969F93B9951EC9DA288F2E9594960BC18DCE8B35AAF7559618BFB`
- `data\processed\spinal_fusion_neuropathy_v1\graph_quality_report.json`: 116 non-empty lines, 2222 bytes, SHA256 `552EB95FA831A2CFCC988834DBFD4B7231D9A280DB06C4D6965E7AA657FBBCB3`
- `data\processed\spinal_fusion_neuropathy_v1\graph_quality_report.md`: 38 non-empty lines, 1093 bytes, SHA256 `60248C2C972F2338A98616D19F1DCD6761050C277302BF95BC4EE383B1D2571B`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_spinal_fusion_neuropathy_v1.json
