# External Gold Pack Merge (GBM Filter)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Output directory: `data\training\gold_pack_combined`
- Keywords: `configs\extraction\gbm_relevance_keywords.json`
- External entities: `data\training\external_corpus\biored_all\gold_entities.jsonl`
- External relations: `data\training\external_corpus\biored_all\gold_relations.jsonl`
- External documents: 500 total, 118 kept, 382 dropped
- Entity documents (combined): 1256
- NER rows: 13543
- Relation rows: 1723
- Evidence rows: 1016

## Curated Inputs
- entities: `data\training\curated_import\combined_entities.jsonl`
- relations: `data\training\gold_pack\gold_seed\gold_relations.jsonl`
- evidence: `data\training\gold_pack\gold_seed\gold_evidence.jsonl`

## Matched GBM Patterns
- `U87MG`: 1
- `\bT98G\b`: 1
- `blood-brain barrier`: 2
- `brain (?:tumou?rs?|cancers?|neoplasms?|metastas[ie]s)`: 3
- `cancers?\b`: 75
- `carcinomas?\b`: 19
- `chemotherap`: 19
- `glioblastoma`: 1
- `glioma`: 3
- `leuka?emi`: 8
- `lymphomas?\b`: 12
- `malignan`: 18
- `melanomas?\b`: 3
- `metasta`: 13
- `myelomas?\b`: 1
- `neoplas(?:m|ms|tic|ia)\b`: 3
- `oncogen`: 9
- `oncolog`: 3
- `sarcomas?\b`: 3
- `tumou?r(?!\s*necrosis)`: 63

## Provenance
- curated_no_relation: 74
- external_corpus: 5669
- human_or_curated_positive: 239
- human_reviewed: 11556

## Entity Labels
- BIOMARKER: 524
- CELL_STATE: 131
- CELL_TYPE: 327
- DELIVERY_MODIFIER: 347
- DISEASE: 5439
- DRUG: 1681
- GENE: 2602
- OUTCOME: 1574
- PATHWAY: 93
- TREATMENT: 695
- TRIAL_PHASE: 71
- UNKNOWN: 59

## Relation Labels
- ASSOCIATED_WITH: 1140
- ENHANCES_DELIVERY_OF: 2
- IMPROVES: 44
- NO_RELATION: 74
- PREDICTS: 364
- SYNERGIZES_WITH: 16
- TARGETS: 25
- WORSENS: 58

## Files
- entities: `data\training\gold_pack_combined\gold_entities.jsonl`
- evidence: `data\training\gold_pack_combined\gold_evidence.jsonl`
- manifest: `data\training\gold_pack_combined\external_gold_merge_manifest.json`
- markdown: `data\training\gold_pack_combined\external_gold_merge_manifest.md`
- ner: `data\training\gold_pack_combined\gold_ner.jsonl`
- relations: `data\training\gold_pack_combined\gold_relations.jsonl`

## Warnings
- none
