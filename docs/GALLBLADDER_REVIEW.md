# Gallbladder and Gallstone Research Review

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, surgical eligibility, post-operative care instruction, dietary advice, causation assessment for an individual case, or clinical decision-making.

## Purpose

This review extension uses the existing literature-search, review-queue, and visual graph workflow to map research on gallbladder disease, gallstones, gallbladder removal (cholecystectomy), and recovery after surgery. It is intended to help organize articles, entities, relationships, evidence levels, and uncertainty.

It covers four linked question areas:

- the gallbladder and gallstone disease itself (presentations, complications, natural history),
- management of patients with gallstones (conservative, medical, endoscopic, surgical),
- gallbladder removal (approach, timing, intraoperative safety, complications),
- recovery after gallbladder surgery (short-term recovery and longer-term persistent symptoms).

## Initial corpus path

- Query pack: `data/query_packs/pubmed_gallbladder_v1.json`
- Review schema: `configs/extraction/gallbladder_review_schema.json`
- Offline lexicon: `configs/extraction/lexicon_gallbladder_v1.json`

Suggested first pull:

```powershell
gbmbert-search-pubmed --query-pack pubmed_gallbladder_v1 --output data/raw/pubmed_gallbladder_v1_2026-09-08.jsonl --retmax-per-query 8 --sort relevance
```

Then create a manifest:

```powershell
gbmbert-build-corpus-manifest data/raw/pubmed_gallbladder_v1_2026-09-08.jsonl --name gallbladder_v1 --query-pack pubmed_gallbladder_v1 --source PubMed --command "gbmbert-search-pubmed --query-pack pubmed_gallbladder_v1 --retmax-per-query 8 --sort relevance" --output reports/corpus/pubmed_gallbladder_v1_2026-09-08_manifest.json --markdown-output reports/corpus/pubmed_gallbladder_v1_2026-09-08_manifest.md --note "Research-grade literature triage only; no patient-specific claims."
```

Then run the pipeline into the graph path the console reads by default:

```powershell
gbmbert-run-pipeline data/raw/pubmed_gallbladder_v1_2026-09-08.jsonl --output-dir data/processed/gallbladder_v1 --entity-mode lexicon --lexicon configs/extraction/lexicon_gallbladder_v1.json
```

## Review questions

- Which presentations are studied, and how are asymptomatic gallstones, biliary colic, acute cholecystitis, choledocholithiasis, and gallstone pancreatitis distinguished?
- What is reported for conservative management or watchful waiting compared with cholecystectomy, and in which populations?
- Where does medical dissolution therapy (for example ursodeoxycholic acid) or drainage (percutaneous cholecystostomy) appear, and with what reported effect?
- Which cholecystectomy approaches, timings, and intraoperative safety strategies are associated with which complication rates, including bile duct injury?
- What recovery trajectories are reported after gallbladder removal: pain, length of stay, conversion to open surgery, readmission, return to work, quality of life?
- What persistent or new symptoms are reported after surgery, such as post-cholecystectomy syndrome or bile-acid diarrhoea, and what mechanisms are proposed?
- Which patient, disease, and perioperative factors are reported as predictors of poorer outcomes, and at what level of evidence?

## Human review rules

- Accept only records that discuss the gallbladder, gallstone disease, biliary stones, or cholecystectomy and its aftermath.
- Mark records as excluded when they are about unrelated abdominal pain, other hepatobiliary disease without a gallbladder or gallstone component, general laparoscopy technique with no gallbladder focus, or patient anecdotes without research evidence.
- Keep indication, procedure, and outcome separate. For example, acute cholecystitis is a presentation; early laparoscopic cholecystectomy is a procedure plus timing; conversion to open surgery is an outcome.
- Keep post-operative symptoms separate from proposed mechanisms. Post-cholecystectomy diarrhoea is an outcome; bile acid malabsorption is a proposed mechanism.
- Record comparators explicitly. Much of this literature is comparative (early versus delayed, laparoscopic versus open, surgery versus observation), and an association is meaningless without its comparator.
- Record uncertainty explicitly. Do not infer an individual patient's expected recovery from population-level associations.
- Flag any language that reads as patient-specific surgical, dietary, or post-operative advice for removal or rewrite.

## Visual graph target

The visual dashboard should show articles connected to:

- presentation or indication,
- procedure or management strategy,
- approach and timing,
- comparator,
- complication,
- proposed mechanism,
- recovery outcome and time course.

Edges should retain PMID provenance and evidence tier. Conflicting or weak evidence should remain visible rather than being collapsed into a single answer.
