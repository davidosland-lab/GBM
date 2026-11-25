# Phase 4 Definition of Done (Research)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This checklist reconciles `docs/PROJECT_SCOPE.json` (Phase 4 scaffold + future training execution), `PROJECT_HANDOFF.md`, gold-pack promotion governance, and current experiment reports. It is a **research** definition of done — not clinical validation.

## Out of scope (explicit)

- Phases 5–6 (tumour simulator / treatment strategy engine)
- Clinical validation, CDS, diagnosis/treatment claims
- Claiming a validated clinical GBM-BERT model exists
- Production clinical dashboard

## Must-have (Phase 4 research scaffold + real local training loops)

| # | Criterion | Target | Status |
|---|-----------|--------|--------|
| M1 | Training scaffold: configs, adapters, PMID-safe splits, label maps, gates, HF loaders, tokenization | Present and wired | PASS |
| M2 | Real local evidence training loop with eval reports + checkpoint | Evidence experiment run (prefer latest weighted) | PASS (v9) |
| M3 | Real local relation training loop with eval reports + checkpoint | Relation experiment run | PASS (v3) |
| M4 | Real local document BIO NER training loop with exact-span metrics | BIO NER experiment run | PASS (v3 preferred; v4/v5 weaker) |
| M5 | Gold-pack promotion floors met (research-governance only) | 200/task, 20/label, 100 PMIDs | PASS (promotable) |
| M6 | Default training governance green; scaffolds visible nonblocking | Suite pass; scaffolds marked | PASS |
| M7 | Preferred checkpoints recorded; `training_enabled=false` after runs | Governance notes + disabled flags | PASS |
| M8 | Research-use warning preserved; no clinical-readiness claims | Boundary language | PASS |

## Quality stretch (research-reasonable; not scope numeric bars)

Scope does not set numeric F1 bars. Proposed research targets for literature-mining experiments:

| # | Criterion | Proposed target | Status |
|---|-----------|-----------------|--------|
| Q1 | Evidence macro-F1 on held-out PMID split | ≥ 0.50 with all tiers represented on test | PASS (v9 macro-F1 ≈ 0.59; tier-4 F1 ≈ 0.71) |
| Q2 | Relation macro-F1 on held-out PMID split | ≥ 0.50 with IMPROVES/WORSENS/NO_RELATION present | PASS (v3 macro-F1 ≈ 0.59) |
| Q3 | BIO NER span accuracy | ≥ 0.90 | PASS (v6 ≈ 0.987) |
| Q4 | BIO NER **type macro-F1** | ≥ 0.40 while keeping span ≥ 0.90 | PASS (v6 ≈ 0.691 on cleaned 11-type pack) |

### Why type macro-F1 ≥ 0.40?

With 11–12 entity types and severe imbalance (DISEASE/OUTCOME dominate; CELL_STATE/PATHWAY/TRIAL_PHASE sparse), 0.40 is a research-reasonable bar that requires sparse types to contribute without collapsing precision via class-weight over-prediction. It is **not** a clinical performance claim.

## Evidence snapshot (post-v6)

- Gold pack: **809 evidence / 8020 NER / 294 relation / 909 PMIDs**, promotable
- Evidence v9: accuracy 0.64 / macro-F1 **0.59**
- Relation v3: accuracy 0.65 / macro-F1 **0.59**
- BIO NER **v6 preferred**: span **0.987** / type macro-F1 **0.691** (cleaned pack: UNKNOWN dropped, PATHWAY gene-symbols→GENE, stratified split, tempered weights)
- BIO NER v3 historical: span 0.96 / type macro-F1 0.30 on noisier pack (not freeze-split comparable)
- Soft residual: CELL_STATE/PATHWAY F1 still ~0 on tiny test supports (n=1–2)

## Phase 4 verdict

**Satisfied** for research Phase 4: all must-haves and quality stretch Q1–Q4 PASS. Soft residual remains on sparse-type F1 stability. Phases 5–6 still deferred. Not clinical validation.
