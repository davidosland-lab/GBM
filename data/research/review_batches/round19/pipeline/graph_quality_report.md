# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round19\pipeline\graph_records.jsonl`
- Valid records: 70
- Invalid records: 0
- Unique PMIDs: 70
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 177
- Unique nodes: 19
- Relations: 4

## Labels
- Disease: 66
- Outcome: 30
- Treatment: 21
- CellType: 18
- Drug: 14
- DeliveryModifier: 12
- Gene: 11
- Biomarker: 5

## Relation Types
- ASSOCIATED_WITH: 1
- WORSENS: 1
- TARGETS: 1
- ENHANCES_DELIVERY_OF: 1

## Evidence Tiers
- tier 3: 4

## Top Entities
- Disease `glioblastoma`: 42
- Disease `Glioblastoma`: 24
- Outcome `survival`: 14
- Treatment `immunotherapy`: 14
- Drug `temozolomide`: 11
- Outcome `response`: 10
- CellType `stem cells`: 9
- Gene `MGMT`: 6
- Gene `EGFR`: 5
- DeliveryModifier `blood-brain barrier`: 5

## Top Relation Pairs
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Gene:MGMT` -[WORSENS]-> `Outcome:temozolomide resistance`: 1
- `Drug:temozolomide` -[TARGETS]-> `Gene:MGMT`: 1
- `DeliveryModifier:blood-brain barrier` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1

## Warnings
- none
