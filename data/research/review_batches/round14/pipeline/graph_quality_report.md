# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round14\pipeline\graph_records.jsonl`
- Valid records: 50
- Invalid records: 0
- Unique PMIDs: 50
- Unique NCT IDs: 0
- Paper-only records: 0
- Node mentions: 170
- Unique nodes: 20
- Relations: 11

## Labels
- Outcome: 50
- Disease: 48
- Treatment: 17
- Gene: 15
- Drug: 14
- DeliveryModifier: 11
- Biomarker: 9
- CellType: 6

## Relation Types
- IMPROVES: 3
- ENHANCES_DELIVERY_OF: 2
- TARGETS: 2
- ASSOCIATED_WITH: 2
- SYNERGIZES_WITH: 1
- WORSENS: 1

## Evidence Tiers
- tier 3: 5
- tier 2: 2
- tier 0: 2
- tier 5: 2

## Top Entities
- Disease `glioblastoma`: 35
- Outcome `survival`: 28
- Disease `Glioblastoma`: 13
- Drug `temozolomide`: 11
- Gene `MGMT`: 10
- Outcome `response`: 10
- Outcome `recurrence`: 10
- Treatment `immunotherapy`: 9
- DeliveryModifier `blood-brain barrier`: 8
- Biomarker `IDH-wildtype`: 5

## Top Relation Pairs
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 3
- `DeliveryModifier:Focused ultrasound` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `DeliveryModifier:blood-brain barrier` -[ENHANCES_DELIVERY_OF]-> `Drug:temozolomide`: 1
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 1
- `Treatment:CAR-T` -[TARGETS]-> `Gene:EGFR`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Biomarker:IDH-wildtype` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Drug:temozolomide` -[WORSENS]-> `Outcome:survival`: 1
- `Treatment:immunotherapy` -[TARGETS]-> `Gene:EGFR`: 1

## Warnings
- none
