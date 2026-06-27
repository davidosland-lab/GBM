# GBM-AI Entity Normalization Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Input graph: `data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl`
- Output graph: `data\processed\curation_regression_pack\normalized_graph_records.jsonl`
- Synonym table: `data\examples\entity_synonyms.json`
- Records: 2
- Nodes: 4
- Normalized nodes: 3

## Matches
- PMID 29097493 Biomarker `MGMT methylation` -> `gene:MGMT`
- PMID 40000001 DeliveryModifier `focused ultrasound` -> `delivery:focused_ultrasound`
- PMID 40000001 Drug `temozolomide` -> `drug:temozolomide`

## Warnings
- none
