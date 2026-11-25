# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round16\pipeline\graph_records.jsonl`
- Valid records: 100
- Invalid records: 0
- Unique PMIDs: 100
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 285
- Unique nodes: 19
- Relations: 7

## Labels
- Disease: 95
- Outcome: 71
- Treatment: 40
- DeliveryModifier: 26
- Drug: 19
- Gene: 16
- CellType: 12
- Biomarker: 6

## Relation Types
- ASSOCIATED_WITH: 3
- WORSENS: 2
- TARGETS: 2

## Evidence Tiers
- tier 3: 5
- tier 4: 1
- tier 5: 1

## Top Entities
- Disease `glioblastoma`: 70
- Outcome `survival`: 36
- Disease `Glioblastoma`: 24
- Treatment `immunotherapy`: 20
- Outcome `response`: 17
- DeliveryModifier `blood-brain barrier`: 16
- Drug `temozolomide`: 13
- Outcome `recurrence`: 12
- Treatment `Immunotherapy`: 10
- Gene `EGFR`: 10

## Top Relation Pairs
- `Treatment:CAR-T` -[TARGETS]-> `Gene:EGFR`: 2
- `Gene:MGMT` -[WORSENS]-> `Outcome:temozolomide resistance`: 1
- `Biomarker:EGFR amplification` -[ASSOCIATED_WITH]-> `Outcome:response`: 1
- `Biomarker:EGFR amplification` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Gene:MGMT` -[WORSENS]-> `Outcome:survival`: 1

## Warnings
- none
