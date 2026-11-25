# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round21\pipeline\graph_records.jsonl`
- Valid records: 80
- Invalid records: 0
- Unique PMIDs: 80
- Unique NCT IDs: 0
- Paper-only records: 12
- Node mentions: 199
- Unique nodes: 19
- Relations: 4

## Labels
- Outcome: 77
- Disease: 61
- Drug: 18
- Biomarker: 12
- Treatment: 10
- Gene: 8
- DeliveryModifier: 7
- CellType: 6

## Relation Types
- SYNERGIZES_WITH: 4

## Evidence Tiers
- tier 3: 3
- tier 5: 1

## Top Entities
- Outcome `survival`: 45
- Disease `glioblastoma`: 44
- Outcome `response`: 23
- Disease `Glioblastoma`: 17
- Drug `temozolomide`: 15
- Outcome `recurrence`: 8
- Gene `MGMT`: 7
- Biomarker `IDH-wildtype`: 6
- Treatment `immunotherapy`: 6
- CellType `stem cells`: 5

## Top Relation Pairs
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 2
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Treatment:immunotherapy`: 1
- `Treatment:immunotherapy` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 1

## Warnings
- none
