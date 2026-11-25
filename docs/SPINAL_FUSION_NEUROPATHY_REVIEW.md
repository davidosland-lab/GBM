# Spinal Fusion Neuropathy Research Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, surgical eligibility, causation assessment for an individual case, or clinical decision-making.

## Purpose

This review extension uses the existing literature-search, review-queue, and visual graph workflow to map research on spinal fusion surgery and associated neuropathy or neurologic symptoms. It is intended to help organize articles, entities, relationships, evidence levels, and uncertainty.

## Initial corpus path

- Query pack: `data/query_packs/pubmed_spinal_fusion_neuropathy_v1.json`
- Review schema: `configs/extraction/spinal_fusion_neuropathy_review_schema.json`
- Offline lexicon: `configs/extraction/lexicon_spinal_fusion_neuropathy_v1.json`

Suggested first pull:

```powershell
gbmbert-search-pubmed --query-pack pubmed_spinal_fusion_neuropathy_v1 --output data/raw/pubmed_spinal_fusion_neuropathy_v1_2026-07-24.jsonl --retmax-per-query 8 --sort relevance
```

Then create a manifest:

```powershell
gbmbert-build-corpus-manifest data/raw/pubmed_spinal_fusion_neuropathy_v1_2026-07-24.jsonl --name spinal_fusion_neuropathy_v1 --query-pack pubmed_spinal_fusion_neuropathy_v1 --source PubMed --command "gbmbert-search-pubmed --query-pack pubmed_spinal_fusion_neuropathy_v1 --retmax-per-query 8 --sort relevance" --output reports/corpus/pubmed_spinal_fusion_neuropathy_v1_2026-07-24_manifest.json --markdown-output reports/corpus/pubmed_spinal_fusion_neuropathy_v1_2026-07-24_manifest.md --note "Research-grade literature triage only; no patient-specific claims."
```

## Review questions

- What neuropathic symptoms or neurologic complications are reported after spinal fusion?
- Which fusion approaches, spinal levels, or perioperative factors are associated with neuropathy or radiculopathy?
- What mechanisms are proposed, such as compression, traction, inflammation, scarring, hardware irritation, or adjacent segment disease?
- What time course and outcomes are reported?
- Which treatments or follow-up interventions are discussed, and how strong is the evidence?

## Human review rules

- Accept only records that discuss spinal fusion, spinal arthrodesis, or named fusion approaches.
- Mark records as excluded when they are about general back pain, non-fusion spine surgery only, unrelated neuropathy, or patient anecdotes without research evidence.
- Record uncertainty explicitly. Do not infer causation for an individual patient from population-level associations.
- Keep outcome terms separate from mechanisms. For example, leg numbness is an outcome/symptom; nerve root compression is a mechanism or imaging-related finding.
- Flag any language that sounds like patient-specific advice for removal or rewrite.

## Visual graph target

The visual dashboard should show articles connected to:

- surgery type or approach,
- spinal region or level,
- symptom or complication,
- proposed mechanism,
- treatment or follow-up intervention,
- outcome and time course.

Edges should retain PMID provenance and evidence tier. Conflicting or weak evidence should remain visible rather than being collapsed into a single answer.
