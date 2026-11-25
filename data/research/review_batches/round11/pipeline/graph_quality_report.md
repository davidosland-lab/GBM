# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round11\pipeline\graph_records.jsonl`
- Valid records: 50
- Invalid records: 0
- Unique PMIDs: 50
- Unique NCT IDs: 0
- Paper-only records: 0
- Node mentions: 223
- Unique nodes: 19
- Relations: 21

## Labels
- Outcome: 87
- Disease: 49
- Drug: 28
- Gene: 19
- Biomarker: 17
- Treatment: 12
- DeliveryModifier: 7
- CellType: 4

## Relation Types
- ASSOCIATED_WITH: 8
- WORSENS: 4
- IMPROVES: 4
- PREDICTS: 3
- TARGETS: 1
- SYNERGIZES_WITH: 1

## Evidence Tiers
- tier 3: 15
- tier 4: 5
- tier 0: 1

## Top Entities
- Disease `glioblastoma`: 38
- Outcome `survival`: 35
- Drug `temozolomide`: 22
- Outcome `response`: 21
- Gene `MGMT`: 15
- Outcome `recurrence`: 13
- Disease `Glioblastoma`: 11
- Biomarker `IDH-wildtype`: 8
- Drug `Temozolomide`: 6
- Treatment `immunotherapy`: 6

## Top Relation Pairs
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 2
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 2
- `Drug:temozolomide` -[WORSENS]-> `Outcome:survival`: 2
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:Response`: 1
- `Gene:MGMT` -[PREDICTS]-> `Outcome:response`: 1
- `Drug:temozolomide` -[WORSENS]-> `Outcome:response`: 1
- `Biomarker:EGFR amplification` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Biomarker:MGMT methylation` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Gene:EGFR` -[PREDICTS]-> `Outcome:response`: 1
- `Gene:EGFR` -[PREDICTS]-> `Outcome:recurrence`: 1

## Warnings
- none
