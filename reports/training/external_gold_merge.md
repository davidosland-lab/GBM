# External Gold Pack Merge (GBM Filter)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Output directory: `data\training\gold_pack_combined`
- Keywords: `configs\extraction\gbm_relevance_keywords.json`
- External entities: `data\training\external_corpus\biored_all\gold_entities.jsonl`
- External relations: `data\training\external_corpus\biored_all\gold_relations.jsonl`
- External documents: 500 total, 6 kept, 494 dropped
- Entity documents (combined): 563
- NER rows: 6072
- Relation rows: 288
- Evidence rows: 498

## Curated Inputs
- entities: `data\training\curated_import\combined_entities.jsonl`
- relations: `data\training\gold_pack\gold_seed\gold_relations.jsonl`
- evidence: `data\training\gold_pack\gold_seed\gold_evidence.jsonl`

## Matched GBM Patterns
- `U87MG`: 1
- `\bT98G\b`: 1
- `blood-brain barrier`: 2
- `glioblastoma`: 1
- `glioma`: 3

## Provenance
- curated_no_relation: 74
- external_corpus: 286
- human_or_curated_positive: 137
- human_reviewed: 6924

## Entity Labels
- BIOMARKER: 261
- CELL_STATE: 20
- CELL_TYPE: 162
- DELIVERY_MODIFIER: 154
- DISEASE: 2576
- DRUG: 791
- GENE: 609
- OUTCOME: 1052
- PATHWAY: 20
- TREATMENT: 387
- TRIAL_PHASE: 20
- UNKNOWN: 20

## Relation Labels
- ASSOCIATED_WITH: 138
- IMPROVES: 20
- NO_RELATION: 74
- PREDICTS: 36
- WORSENS: 20

## Files
- entities: `data\training\gold_pack_combined\gold_entities.jsonl`
- evidence: `data\training\gold_pack_combined\gold_evidence.jsonl`
- manifest: `data\training\gold_pack_combined\external_gold_merge_manifest.json`
- markdown: `data\training\gold_pack_combined\external_gold_merge_manifest.md`
- ner: `data\training\gold_pack_combined\gold_ner.jsonl`
- relations: `data\training\gold_pack_combined\gold_relations.jsonl`

## Warnings
- none
