# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round34\pipeline\graph_records.jsonl`
- Valid records: 181
- Invalid records: 0
- Unique PMIDs: 181
- Unique NCT IDs: 0
- Paper-only records: 4
- Node mentions: 480
- Unique nodes: 16
- Relations: 19

## Labels
- Disease: 165
- Outcome: 123
- DeliveryModifier: 61
- Treatment: 47
- Drug: 37
- CellType: 22
- Gene: 20
- Biomarker: 5

## Relation Types
- SYNERGIZES_WITH: 5
- IMPROVES: 4
- ASSOCIATED_WITH: 4
- ENHANCES_DELIVERY_OF: 2
- TARGETS: 2
- WORSENS: 2

## Evidence Tiers
- tier 3: 14
- tier 5: 4
- tier 0: 1

## Top Entities
- Disease `glioblastoma`: 128
- Outcome `survival`: 76
- Disease `Glioblastoma`: 37
- DeliveryModifier `blood-brain barrier`: 34
- Treatment `immunotherapy`: 30
- Drug `temozolomide`: 28
- Outcome `response`: 23
- Outcome `recurrence`: 20
- CellType `stem cells`: 16
- DeliveryModifier `focused ultrasound`: 14

## Top Relation Pairs
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 3
- `Treatment:CAR-T` -[TARGETS]-> `Gene:EGFR`: 2
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 2
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 2
- `Treatment:immunotherapy` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 2
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Treatment:immunotherapy`: 2
- `DeliveryModifier:Focused ultrasound` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `DeliveryModifier:blood-brain barrier` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `Treatment:immunotherapy` -[IMPROVES]-> `Outcome:survival`: 1
- `Gene:MGMT` -[WORSENS]-> `Outcome:survival`: 1

## Warnings
- none
