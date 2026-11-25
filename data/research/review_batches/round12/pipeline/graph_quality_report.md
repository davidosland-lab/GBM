# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round12\pipeline\graph_records.jsonl`
- Valid records: 50
- Invalid records: 0
- Unique PMIDs: 50
- Unique NCT IDs: 0
- Paper-only records: 0
- Node mentions: 173
- Unique nodes: 20
- Relations: 17

## Labels
- Outcome: 57
- Disease: 50
- Drug: 17
- Gene: 14
- Treatment: 13
- Biomarker: 12
- DeliveryModifier: 5
- CellType: 5

## Relation Types
- ASSOCIATED_WITH: 6
- WORSENS: 4
- PREDICTS: 3
- IMPROVES: 2
- TARGETS: 1
- ENHANCES_DELIVERY_OF: 1

## Evidence Tiers
- tier 3: 12
- tier 0: 4
- tier 5: 1

## Top Entities
- Disease `glioblastoma`: 33
- Outcome `survival`: 32
- Disease `Glioblastoma`: 17
- Drug `temozolomide`: 13
- Outcome `response`: 10
- Outcome `recurrence`: 9
- Treatment `immunotherapy`: 9
- Gene `MGMT`: 8
- Gene `EGFR`: 6
- CellType `stem cells`: 5

## Top Relation Pairs
- `Drug:temozolomide` -[WORSENS]-> `Outcome:recurrence`: 2
- `Treatment:immunotherapy` -[IMPROVES]-> `Outcome:survival`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Biomarker:MGMT methylation` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Biomarker:MGMT methylation` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Treatment:CAR-T` -[IMPROVES]-> `Outcome:survival`: 1
- `Biomarker:EGFR amplification` -[PREDICTS]-> `Outcome:response`: 1
- `Disease:glioblastoma` -[PREDICTS]-> `Outcome:response`: 1
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1

## Warnings
- none
