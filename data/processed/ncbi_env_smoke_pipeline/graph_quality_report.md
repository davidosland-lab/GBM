# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\processed\ncbi_env_smoke_pipeline\graph_records.jsonl`
- Valid records: 13
- Invalid records: 0
- Unique PMIDs: 13
- Unique NCT IDs: 0
- Paper-only records: 0
- Node mentions: 37
- Unique nodes: 13
- Relations: 3

## Labels
- Disease: 12
- Outcome: 9
- Drug: 4
- DeliveryModifier: 3
- Biomarker: 3
- Treatment: 2
- Gene: 2
- CellType: 2

## Relation Types
- ASSOCIATED_WITH: 2
- PREDICTS: 1

## Evidence Tiers
- tier 5: 2
- tier 3: 1

## Top Entities
- Disease `glioblastoma`: 10
- Outcome `survival`: 5
- Drug `temozolomide`: 3
- DeliveryModifier `blood-brain barrier`: 3
- Treatment `immunotherapy`: 2
- Outcome `response`: 2
- Gene `MGMT`: 2
- Disease `Glioblastoma`: 2
- CellType `stem cells`: 2
- Biomarker `EGFR amplification`: 1

## Top Relation Pairs
- `Disease:glioblastoma` -[PREDICTS]-> `Outcome:response`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1

## Warnings
- none
