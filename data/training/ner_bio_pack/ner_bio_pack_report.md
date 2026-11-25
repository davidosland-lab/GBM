# NER BIO Pack Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Output dir: `data\training\ner_bio_pack`
- Documents: 754
- Entity spans: 6906
- Splits: {'train': 712, 'validation': 75, 'test': 76}
- Label map: `data\training\ner_bio_pack\label_maps\ner_label_map.json`

## Entity types
- BIOMARKER: 264
- CELL_STATE: 95
- CELL_TYPE: 182
- DELIVERY_MODIFIER: 221
- DISEASE: 3013
- DRUG: 717
- GENE: 616
- OUTCOME: 1190
- PATHWAY: 46
- TREATMENT: 520
- TRIAL_PHASE: 42

## Warnings
- skipped 38 entity doc(s) with no matching PubMed text
- skipped 22 entity span(s) with invalid/unaligned offsets
- dropped 46 all UNKNOWN span(s) (keyword-dump cleanup)
- remapped 31 gene-symbol PATHWAY span(s) to GENE
- used stratified PMID split preserving sparse entity types in train+test
- oversampled sparse-type train docs x2 (603 -> 712)
