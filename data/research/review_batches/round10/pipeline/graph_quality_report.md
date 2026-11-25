# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round10\pipeline\graph_records.jsonl`
- Valid records: 50
- Invalid records: 0
- Unique PMIDs: 50
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 187
- Unique nodes: 18
- Relations: 14

## Labels
- Outcome: 67
- Disease: 48
- Treatment: 22
- Drug: 14
- Gene: 12
- DeliveryModifier: 11
- Biomarker: 9
- CellType: 4

## Relation Types
- ASSOCIATED_WITH: 7
- PREDICTS: 2
- IMPROVES: 2
- WORSENS: 2
- SYNERGIZES_WITH: 1

## Evidence Tiers
- tier 3: 9
- tier 5: 2
- tier 1: 2
- tier 0: 1

## Top Entities
- Disease `glioblastoma`: 41
- Outcome `survival`: 32
- Outcome `response`: 15
- Drug `temozolomide`: 14
- Outcome `recurrence`: 13
- Treatment `immunotherapy`: 10
- Gene `MGMT`: 8
- Disease `Glioblastoma`: 7
- Treatment `CAR-T`: 7
- DeliveryModifier `blood-brain barrier`: 6

## Top Relation Pairs
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 2
- `Biomarker:IDH-wildtype` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 2
- `Drug:temozolomide` -[WORSENS]-> `Outcome:recurrence`: 2
- `Biomarker:MGMT methylation` -[PREDICTS]-> `Outcome:survival`: 1
- `Disease:glioblastoma` -[PREDICTS]-> `Outcome:survival`: 1
- `Biomarker:IDH-mutant` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Biomarker:MGMT methylation` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Drug:temozolomide` -[SYNERGIZES_WITH]-> `Drug:temozolomide`: 1
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1

## Warnings
- none
