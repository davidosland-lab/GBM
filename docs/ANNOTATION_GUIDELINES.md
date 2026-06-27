# GBM-AI Annotation Guidelines

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

These guidelines define the first gold-standard annotation policy for GBM-AI literature curation. They are intended for research dataset construction, model evaluation, and knowledge graph quality control.

## Scope

Annotate glioblastoma research claims from abstracts, titles, and curated source passages when the source text explicitly supports the label. Prefer conservative labels over speculative inference.

Do not annotate patient-specific instructions, treatment recommendations, or clinical decision support content.

## Entity Labels

- `GENE`: gene symbols and named genomic alterations, such as EGFR, TERT, IDH1, PTEN.
- `DRUG`: specific drugs or compounds, such as temozolomide, bevacizumab, lomustine.
- `DISEASE`: GBM, glioblastoma, glioma, recurrent glioblastoma.
- `PATHWAY`: pathways and mechanisms, such as PI3K/AKT, MGMT repair, immune checkpoint signaling.
- `BIOMARKER`: biomarker states, assays, or molecular features, such as MGMT promoter methylation.
- `CELL_TYPE`: immune or tumor cell types, such as macrophages, T cells, glioma stem-like cells.
- `CELL_STATE`: state transitions or phenotypes, such as mesenchymal state, proneural state.
- `TREATMENT`: treatment classes, radiation, surgery, tumor treating fields, immunotherapy.
- `DELIVERY_MODIFIER`: delivery mechanisms, such as focused ultrasound, nanoparticles, BBB opening.
- `OUTCOME`: response, survival, progression, toxicity, resistance, prognosis.
- `TRIAL_PHASE`: phase I, phase II, randomized phase III.

## Relation Labels

- `PREDICTS`: a biomarker, gene, or disease feature predicts an outcome.
- `ASSOCIATED_WITH`: a source entity is associated or correlated with a disease, outcome, pathway, or treatment context.
- `TARGETS`: a treatment or drug targets a gene or pathway.
- `ACTIVATES` / `INHIBITS`: mechanistic activation or inhibition of a pathway.
- `IMPROVES` / `WORSENS`: a treatment, drug, gene, or biomarker improves or worsens an outcome.
- `ENHANCES_DELIVERY_OF`: a delivery modifier increases delivery of a drug or treatment.
- `SYNERGIZES_WITH`: a drug or treatment combination has explicitly stated synergy.
- `TRANSITIONS_TO`: a cell state shifts to another state.
- `MODULATES_POLARIZATION_OF`: a drug or treatment modulates polarization of a cell type.

## Evidence Tiers

- `0 HYPOTHESIS`: review, rationale, speculation, proposed mechanism.
- `1 IN_VITRO`: cell line or organoid evidence.
- `2 ANIMAL`: mouse, rat, xenograft, or other in vivo non-human model.
- `3 RETROSPECTIVE_HUMAN`: retrospective patient cohort or observational human study.
- `4 PHASE_I_II`: early phase clinical trial.
- `5 RANDOMIZED_EVIDENCE`: randomized or phase III evidence.

## Qualifiers

Add relation qualifiers only when directly supported by the source sentence or source passage.

- `species_model`: human, mouse, rat, cell_line, organoid, xenograft.
- `mutation_status`: idh_wildtype, idh_mutant, mgmt_methylated, mgmt_unmethylated, egfr_amplified.
- `trial_phase`: phase_i, phase_ii, phase_i_ii, phase_iii.
- `evidence_context`: retrospective, prospective, randomized, preclinical, case_report.
- `cohort`: named cohort or study group when explicitly stated.

## Review Status Rules

- `accepted`: extracted item is correct as written.
- `corrected`: item is usable after changing relation type, evidence tier, or another supported field. Add review notes.
- `rejected`: item is unsupported, unsafe, out of scope, duplicated in a harmful way, or too ambiguous. Add review notes.
- `pending`: not reviewed yet and must not enter gold training data.

## Adjudication

When reviewers disagree, prefer the most source-grounded interpretation. Escalate conflicts that change evidence tier, relation type, or rejection status.

Every gold item must retain source PMID, original text or sentence, reviewer decision, and research-use warning provenance.
