# GBM-AI Graph Quality Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Source: `data\processed\gallbladder_v1\graph_records.jsonl`
- Valid records: 158
- Invalid records: 0
- Unique PMIDs: 158
- Unique NCT IDs: 0
- Paper-only records: 1
- Node mentions: 703
- Unique nodes: 63
- Relations: 5

## Labels
- Treatment: 263
- Disease: 253
- Outcome: 108
- DeliveryModifier: 57
- Drug: 15
- Biomarker: 7

## Relation Types
- SYNERGIZES_WITH: 5

## Evidence Tiers
- tier 5: 4
- tier 3: 1

## Top Entities
- Treatment `cholecystectomy`: 78
- Treatment `laparoscopic cholecystectomy`: 54
- Disease `gallstones`: 32
- Outcome `mortality`: 30
- Disease `gallstone`: 29
- DeliveryModifier `laparoscopic`: 24
- Disease `acute cholecystitis`: 22
- Disease `cholecystitis`: 18
- Disease `bile duct injury`: 18
- Outcome `quality of life`: 17

## Top Relation Pairs
- `Treatment:Subtotal cholecystectomy` -[SYNERGIZES_WITH]-> `Treatment:intraoperative cholangiography`: 1
- `Treatment:ERCP` -[SYNERGIZES_WITH]-> `Treatment:Laparoscopic Cholecystectomy`: 1
- `Treatment:ERCP` -[SYNERGIZES_WITH]-> `Treatment:ERCP`: 1
- `Treatment:Laparoscopic Cholecystectomy` -[SYNERGIZES_WITH]-> `Treatment:ERCP`: 1
- `Treatment:Laparoscopic Cholecystectomy` -[SYNERGIZES_WITH]-> `Treatment:Laparoscopic Cholecystectomy`: 1

## Warnings
- PMID 40960586: missing paper abstract
