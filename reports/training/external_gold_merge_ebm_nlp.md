# External Gold Pack Merge (GBM Filter)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Output directory: `data\training\gold_pack_combined_ebm_nlp`
- Keywords: `configs\extraction\gbm_relevance_keywords.json`
- External entities: `data\training\external_corpus\ebm_nlp\gold_entities.jsonl`
- External relations: `none`
- External documents: 4980 total, 10 kept, 4970 dropped
- Entity documents (combined): 851
- NER rows: 7864
- Relation rows: 294
- Evidence rows: 755

## Curated Inputs
- entities: `data\training\curated_import\combined_entities.jsonl`
- relations: `data\training\gold_seed\gold_relations.jsonl`
- evidence: `data\training\curated_import\combined_evidence.jsonl`

## Matched GBM Patterns
- `\bMGMT\b`: 1
- `\bTMZ\b`: 2
- `astrocytoma`: 3
- `blood-brain barrier`: 1
- `glioma`: 3
- `temozolomide`: 2

## Provenance
- curated_no_relation: 74
- external_corpus: 153
- human_or_curated_positive: 220
- human_reviewed: 9317

## Entity Labels
- BIOMARKER: 319
- CELL_STATE: 40
- CELL_TYPE: 202
- DELIVERY_MODIFIER: 248
- DISEASE: 3466
- DRUG: 886
- GENE: 654
- OUTCOME: 1356
- PATHWAY: 40
- TREATMENT: 585
- TRIAL_PHASE: 45
- UNKNOWN: 23

## Relation Labels
- ASSOCIATED_WITH: 78
- IMPROVES: 40
- NO_RELATION: 74
- PREDICTS: 46
- WORSENS: 56

## Files
- entities: `data\training\gold_pack_combined_ebm_nlp\gold_entities.jsonl`
- evidence: `data\training\gold_pack_combined_ebm_nlp\gold_evidence.jsonl`
- manifest: `data\training\gold_pack_combined_ebm_nlp\external_gold_merge_manifest.json`
- markdown: `data\training\gold_pack_combined_ebm_nlp\external_gold_merge_manifest.md`
- ner: `data\training\gold_pack_combined_ebm_nlp\gold_ner.jsonl`
- relations: `data\training\gold_pack_combined_ebm_nlp\gold_relations.jsonl`

## Warnings
- none
