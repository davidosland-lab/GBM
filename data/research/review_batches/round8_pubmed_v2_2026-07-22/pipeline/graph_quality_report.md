# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round8\pipeline\graph_records.jsonl`
- Valid records: 69
- Invalid records: 0
- Unique PMIDs: 69
- Unique NCT IDs: 0
- Paper-only records: 2
- Node mentions: 173
- Unique nodes: 14
- Relations: 7

## Labels
- Disease: 62
- Outcome: 41
- DeliveryModifier: 26
- Drug: 22
- CellType: 7
- Gene: 7
- Treatment: 4
- Biomarker: 4

## Relation Types
- SYNERGIZES_WITH: 3
- ENHANCES_DELIVERY_OF: 2
- IMPROVES: 1
- ASSOCIATED_WITH: 1

## Evidence Tiers
- tier 3: 7

## Top Entities
- Disease `glioblastoma`: 47
- Outcome `survival`: 24
- Drug `temozolomide`: 16
- Disease `Glioblastoma`: 15
- DeliveryModifier `blood-brain barrier`: 14
- Outcome `response`: 11
- DeliveryModifier `Focused ultrasound`: 6
- Drug `Temozolomide`: 6
- Gene `MGMT`: 6
- CellType `stem cells`: 6

## Top Relation Pairs
- `DeliveryModifier:Focused ultrasound` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `DeliveryModifier:blood-brain barrier` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 1
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Treatment:immunotherapy`: 1
- `Treatment:immunotherapy` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 1

## Warnings
- none
