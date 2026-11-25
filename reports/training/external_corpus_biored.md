# External Corpus Import

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Corpus: `biored` (reader `biored_bioc`)
- License: BioRED (Luo et al., Brief Bioinform 2022); NCBI / NLM research corpus. PubMed-derived abstracts. Research-use only.
- Source type: `external_corpus`
- Input: `data\research\biored\extracted\BioRED\Dev.BioC.JSON`
- Output: `data\training\external_corpus\biored\gold_entities.jsonl`
- Relations output: `data\training\external_corpus\biored\gold_relations.jsonl`
- Documents: 100
- Entities mapped: 3163
- Relations mapped: 1114

## Project Entity Label Counts
- BIOMARKER: 250
- CELL_TYPE: 22
- DISEASE: 982
- DRUG: 822
- GENE: 1087

## Project Relation Label Counts
- ASSOCIATED_WITH: 750
- PREDICTS: 344
- SYNERGIZES_WITH: 10
- TARGETS: 10

## Dropped Unmapped Entity Labels
- OrganismTaxon: 370

## Dropped Unmapped/Unresolved Relations
- Association: 22
- Bind: 9
- Negative_Correlation: 9
- Positive_Correlation: 8

## Warnings
- dropped unmapped source entity labels (add them to the crosswalk to keep them): OrganismTaxon=370
- dropped unmapped or unresolved source relations: Association=22, Bind=9, Negative_Correlation=9, Positive_Correlation=8
