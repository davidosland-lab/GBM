# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round15\pipeline\graph_records.jsonl`
- Valid records: 55
- Invalid records: 0
- Unique PMIDs: 55
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 180
- Unique nodes: 18
- Relations: 12

## Labels
- Outcome: 66
- Disease: 52
- Treatment: 16
- Gene: 14
- Drug: 9
- CellType: 8
- Biomarker: 8
- DeliveryModifier: 7

## Relation Types
- ASSOCIATED_WITH: 8
- IMPROVES: 2
- WORSENS: 2

## Evidence Tiers
- tier 3: 11
- tier 4: 1

## Top Entities
- Outcome `survival`: 35
- Disease `glioblastoma`: 33
- Disease `Glioblastoma`: 19
- Outcome `response`: 17
- Treatment `immunotherapy`: 10
- Outcome `recurrence`: 8
- Drug `temozolomide`: 8
- Gene `EGFR`: 7
- Gene `MGMT`: 7
- DeliveryModifier `blood-brain barrier`: 5

## Top Relation Pairs
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 3
- `Treatment:CAR-T` -[IMPROVES]-> `Outcome:survival`: 1
- `Treatment:Immunotherapy` -[IMPROVES]-> `Outcome:survival`: 1
- `Biomarker:EGFR amplification` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Biomarker:EGFR amplification` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:response`: 1
- `Gene:MGMT` -[WORSENS]-> `Outcome:recurrence`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:temozolomide resistance`: 1
- `Gene:MGMT` -[WORSENS]-> `Outcome:temozolomide resistance`: 1

## Warnings
- none
