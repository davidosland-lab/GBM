# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\research\review_batches\round8\pipeline\graph_records.jsonl`
- Valid records: 30
- Invalid records: 0
- Unique PMIDs: 30
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 84
- Unique nodes: 11
- Relations: 3

## Labels
- Disease: 27
- Outcome: 24
- Gene: 10
- CellType: 10
- Biomarker: 7
- Drug: 6

## Relation Types
- ASSOCIATED_WITH: 2
- IMPROVES: 1

## Evidence Tiers
- tier 3: 2
- tier 5: 1

## Top Entities
- Disease `glioblastoma`: 23
- Outcome `survival`: 13
- CellType `stem cells`: 7
- Outcome `recurrence`: 6
- Drug `temozolomide`: 6
- Gene `EGFR`: 5
- Biomarker `EGFR amplification`: 5
- Outcome `response`: 5
- Gene `MGMT`: 5
- Disease `Glioblastoma`: 4

## Top Relation Pairs
- `Gene:EGFR` -[ASSOCIATED_WITH]-> `Disease:glioblastoma`: 1
- `Gene:MGMT` -[ASSOCIATED_WITH]-> `Outcome:survival`: 1
- `Drug:temozolomide` -[IMPROVES]-> `Outcome:survival`: 1

## Warnings
- none
