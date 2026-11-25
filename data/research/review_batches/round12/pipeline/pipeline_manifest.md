# Corpus Manifest: pipeline

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T10:21:52+00:00
- Source: GBM-AI literature pipeline
- Query pack: n/a
- Record count: 200
- Command: `gbmbert-run-pipeline data\research\review_batches\round12\pubmed_round12_candidates.jsonl --output-dir data\research\review_batches\round12\pipeline --entity-mode lexicon`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\research\review_batches\round12\pubmed_round12_candidates.jsonl`: 50 records, 119196 bytes, SHA256 `F44EAA83A04E3AC6A77AB5D4C5089AA728E1BDCDBB00B80362D4006CA8BBAE7B`
- `data\research\review_batches\round12\pipeline\entities.jsonl`: 50 records, 74364 bytes, SHA256 `AC38BB973E57024EED3A20FAA52A3CD49A2DD622AA42227971F552CD3771AB7A`
- `data\research\review_batches\round12\pipeline\evidence_claims.jsonl`: 50 records, 15220 bytes, SHA256 `483F4FEC4EA47F061EBC1DD45EEE624350E2B51092DE2C340CB47BC6C8F55131`
- `data\research\review_batches\round12\pipeline\graph_records.jsonl`: 50 records, 223166 bytes, SHA256 `9903058BBDFF120EB65E5F025190F88A10D3DE115FCF776D242F3FB64DC83518`
- `data\research\review_batches\round12\pipeline\graph_quality_report.json`: 200 non-empty lines, 3837 bytes, SHA256 `960A893436AD0098E5764823AAD3942FFCAD77C6680C0583F148F344231A4585`
- `data\research\review_batches\round12\pipeline\graph_quality_report.md`: 55 non-empty lines, 1707 bytes, SHA256 `DEFEF187BAFF86071B26388E059102FF021D281426F4707239F6AC7D13468414`

## Notes
- Pipeline artifact bundle: input PubMed JSONL, entity JSONL, evidence JSONL, graph JSONL, and quality reports.
- Entity mode: lexicon
- Lexicon: configs\extraction\lexicon_gbm_v1.json
