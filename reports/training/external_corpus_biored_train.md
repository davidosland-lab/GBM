# External Corpus Import

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Corpus: `biored` (reader `biored_bioc`)
- License: BioRED (Luo et al., Brief Bioinform 2022); NCBI / NLM research corpus. PubMed-derived abstracts. Research-use only.
- Source type: `external_corpus`
- Input: `data\research\biored\extracted\BioRED\Train.BioC.JSON`
- Output: `data\training\external_corpus\biored_train\gold_entities.jsonl`
- Relations output: `data\training\external_corpus\biored_train\gold_relations.jsonl`
- Documents: 400
- Entities mapped: 11922
- Relations mapped: 3831

## Project Entity Label Counts
- BIOMARKER: 890
- CELL_TYPE: 103
- DISEASE: 3646
- DRUG: 2853
- GENE: 4430

## Project Relation Label Counts
- ASSOCIATED_WITH: 2712
- PREDICTS: 1024
- SYNERGIZES_WITH: 42
- TARGETS: 53

## Dropped Unmapped Entity Labels
- OrganismTaxon: 1429

## Dropped Unmapped/Unresolved Relations
- Association: 200
- Bind: 8
- Negative_Correlation: 74
- Positive_Correlation: 65

## Warnings
- dropped unmapped source entity labels (add them to the crosswalk to keep them): OrganismTaxon=1429
- dropped unmapped or unresolved source relations: Association=200, Bind=8, Negative_Correlation=74, Positive_Correlation=65
