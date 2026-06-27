# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\processed\ncbi_env_smoke_pipeline\graph_records.jsonl, data\processed\clinicaltrials_gbm_smoke_2026-06-23\trial_graph_records.jsonl`
- Valid records: 18
- Invalid records: 0
- Unique PMIDs: 13
- Unique NCT IDs: 5
- Paper-only records: 0
- Node mentions: 61
- Unique nodes: 34
- Relations: 22

## Labels
- Disease: 18
- Treatment: 15
- Outcome: 9
- Trial: 5
- Drug: 4
- DeliveryModifier: 3
- Biomarker: 3
- Gene: 2
- CellType: 2

## Relation Types
- ASSOCIATED_WITH: 21
- PREDICTS: 1

## Evidence Tiers
- tier 5: 2
- tier 3: 1

## Top Entities
- Disease `glioblastoma`: 10
- Outcome `survival`: 5
- Disease `Glioblastoma`: 4
- Drug `temozolomide`: 3
- DeliveryModifier `blood-brain barrier`: 3
- Treatment `immunotherapy`: 2
- Outcome `response`: 2
- Gene `MGMT`: 2
- CellType `stem cells`: 2
- Disease `Brain and Central Nervous System Tumors`: 2

## Top Relation Pairs
- `Disease:glioblastoma` -[PREDICTS]-> `Outcome:response`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Trial:NCT04552886` -[ASSOCIATED_WITH]-> `Disease:Glioblastoma`: 1
- `Trial:NCT04552886` -[ASSOCIATED_WITH]-> `Treatment:TH-1 Dendritic Cell Immunotherapy`: 1
- `Trial:NCT03532295` -[ASSOCIATED_WITH]-> `Disease:Glioma`: 1
- `Trial:NCT03532295` -[ASSOCIATED_WITH]-> `Disease:Glioblastoma`: 1
- `Trial:NCT03532295` -[ASSOCIATED_WITH]-> `Treatment:Epacadostat`: 1
- `Trial:NCT03532295` -[ASSOCIATED_WITH]-> `Treatment:Bevacizumab`: 1
- `Trial:NCT03532295` -[ASSOCIATED_WITH]-> `Treatment:Radiation therapy`: 1

## Warnings
- none
