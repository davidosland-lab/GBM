# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round13\pipeline\graph_records.jsonl`
- Valid records: 50
- Invalid records: 0
- Unique PMIDs: 50
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 180
- Unique nodes: 18
- Relations: 20

## Labels
- Outcome: 64
- Disease: 48
- Drug: 20
- Gene: 17
- Treatment: 15
- Biomarker: 7
- CellType: 7
- DeliveryModifier: 2

## Relation Types
- ASSOCIATED_WITH: 6
- WORSENS: 4
- PREDICTS: 4
- SYNERGIZES_WITH: 2
- TARGETS: 2
- IMPROVES: 2

## Evidence Tiers
- tier 3: 17
- tier 0: 2
- tier 1: 1

## Top Entities
- Disease `glioblastoma`: 34
- Outcome `survival`: 27
- Drug `temozolomide`: 17
- Outcome `response`: 16
- Disease `Glioblastoma`: 14
- Gene `MGMT`: 10
- Treatment `immunotherapy`: 9
- Outcome `recurrence`: 7
- Gene `EGFR`: 7
- Outcome `temozolomide resistance`: 5

## Top Relation Pairs
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 2
- `Gene:MGMT` -[WORSENS]-> `Outcome:temozolomide resistance`: 2
- `Treatment:immunotherapy` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 1
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Treatment:immunotherapy`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `CellType:glioblastoma stem cells` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Drug:temozolomide` -[TARGETS]-> `Gene:MGMT`: 1
- `Drug:temozolomide` -[TARGETS]-> `Gene:EGFR`: 1
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:response`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:recurrence`: 1

## Warnings
- none
