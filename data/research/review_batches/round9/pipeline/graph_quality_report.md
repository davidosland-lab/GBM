# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round9\pipeline\graph_records.jsonl`
- Valid records: 35
- Invalid records: 0
- Unique PMIDs: 35
- Unique NCT IDs: 0
- Paper-only records: 0
- Node mentions: 92
- Unique nodes: 14
- Relations: 9

## Labels
- Disease: 35
- Outcome: 23
- Gene: 9
- CellType: 7
- Drug: 5
- DeliveryModifier: 5
- Treatment: 5
- Biomarker: 3

## Relation Types
- ASSOCIATED_WITH: 5
- IMPROVES: 2
- ENHANCES_DELIVERY_OF: 2

## Evidence Tiers
- tier 3: 4
- tier 0: 4
- tier 2: 1

## Top Entities
- Disease `glioblastoma`: 27
- Outcome `survival`: 13
- Disease `Glioblastoma`: 8
- Gene `MGMT`: 5
- Drug `temozolomide`: 5
- Outcome `recurrence`: 5
- Gene `EGFR`: 4
- CellType `stem cells`: 4
- Outcome `response`: 4
- DeliveryModifier `blood-brain barrier`: 3

## Top Relation Pairs
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 2
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 2
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `DeliveryModifier:Focused ultrasound` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `DeliveryModifier:blood-brain barrier` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `Biomarker:EGFR amplification` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1

## Warnings
- none
