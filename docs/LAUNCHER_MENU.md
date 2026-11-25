# Launcher Menu Guide

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

`launcher_menu.bat` is a local convenience wrapper for common GBM-AI commands. The first screen is intentionally short: choose the workflow family first, then pick the specific command. Existing legacy shortcuts, such as `16BI`, still work from the main prompt.

## Main Groups

| Group | Use it for | Typical commands |
| --- | --- | --- |
| Setup and environment | Creating `.venv`, installing dependencies, opening an activated shell, and checking installed packages. | `1`, `1R`, `2`, `3`, `5`, `6` |
| Verify, reports, and handoff checks | Running tests, preflight, scope drift, platform regression, artifact index, local verification, artifact policy checks, and launcher structure checks. | `4`, `15`, `16`, `16AO`, `16AP`, `16BI`, `16BJ`, `16BK` |
| Literature and graph pipeline | Building source-derived PubMed, ClinicalTrials.gov, corpus, entity, and graph artifacts. | `7`, `8`, `9`, `12`, `13`, `14`, `14A`, `16B` |
| Review and curation workflow | Creating review queues, reviewed queues, curated graph outputs, curation bundles, overlays, regression packs, real PubMed review-batch prep/finalize, and entity-span review export/apply. | `10`, `11`, `11R`, `11S`, `11C`, `11D`, `16O`, `16P`, `16R`, `16S`, `16Z`, `16BT`, `16BU`, `16BV`, `16BW` |
| Training data and governance | Building annotation packs, gold/evidence/relation training packs, readiness reports, import checks, provenance diffs, promotion review, planning, ops status, detail exports, and governance audits. | `16C`, `16D`, `16AQ`, `16AX`, `16BA`, `16AZ`, `16BE`, `16BB`, `16BG`, `16BH`, `16BL`, `16BM`, `16BN`, `16BO`, `16CC`, `16BP`, `16BQ`, `16BR`, `16BS` |
| Knowledge Graph Explorer | Starting the local browser explorer with sample, baseline, artifact-index-selected, or Neo4j-backed data. | `17`, `17A`, `17B`, `18` |
| Tumour simulation (research) | Phase 5 toy simulation, Monte Carlo sweeps, Phase 6 scenario ranking, and Phase 7 dashboard launch (research prototypes only; not clinically validated; not CDS). | `16BX`, `16BY`, `16BZ`, `16CA` |
| Advanced command index | A compact map of the legacy flat menu for people who already know the old shortcut. | All legacy shortcuts |

## Recommended Paths

For a fresh checkout:

```powershell
launcher_menu.bat
# A -> 1
# A -> 3
# B -> 16BI
```

For a normal handoff check:

```powershell
launcher_menu.bat
# B -> 16BI
```

For training-data governance work:

```powershell
launcher_menu.bat
# E -> 16AX
# E -> 16BA
# E -> 16BE
# E -> 16BG
# E -> 16BH
# E -> 16BS
# E -> 16BR
# E -> 16BO
# E -> 16CC
# E -> 16BP
# E -> 16BQ
```

`16CC` runs `gbmbert-gold-pack-ops-status` (pack counts, soft densify gaps, dual-review/AL backlog, next actions). See `docs\GOLD_PACK_OPS_RUNBOOK.md`.

`16BR` runs the full multi-batch curated import across every expansion round (rounds 1-6) with the same fixed file set the provenance diff (`16BN`) uses, writing the combined import under `data\training\curated_import`. `16BL` remains the interactive single-batch import.

`16BS` runs `gbmbert-rebuild-curated-rounds`, which discovers every curated round and regenerates the entire downstream report chain in one command (import, provenance diff, gold seed/pack, evidence/relation packs, the top-level governance reports, promotion review/planning, the governance suites, and the governance detail export/contract). It is observe-only; run `16BI` (local verification) afterward for platform checks and the CI summary. The CI summary surfaces curated-round rebuild as an opt-in visibility row only (not a hard verification gate).

`16BT` / `16BU` prep and finalize a real PubMed review batch (`gbmbert-prep-review-batch` / `gbmbert-finalize-review-batch`). Lexicon entity spans from prep alone are not span-reviewed; use `16BV` / `16BW` (`gbmbert-export-entity-span-review` / `gbmbert-apply-entity-span-review`) to make offsets/labels a reviewed signal before promoting NER gold.

For local graph inspection:

```powershell
launcher_menu.bat
# F -> 17B
```

For Phase 5/6 research tumour simulation and scenario ranking (toy models only):

```powershell
launcher_menu.bat
# H -> 16BX   # deterministic Phase 5 simulation
# H -> 16BY   # Monte Carlo sweeps
# H -> 16BZ   # Phase 6 treatment-scenario ranking (not CDS)
# H -> 16CA   # Phase 7 research operations console
```

`16BX` runs `gbmbert-run-tumour-simulation` against `configs\simulation\compartment_toy_v1.json` (optional graph modulation prompt) and writes reports under `reports\simulation\`. `16BY` runs `gbmbert-run-simulation-monte-carlo`. `16BZ` runs `gbmbert-rank-treatment-scenarios` (research scenario comparison only — not prescriptions or CDS; supports toy toxicity trade-offs and intensity/schedule simulation knobs). `16CA` launches `gbmbert-dashboard` with live in-process runners for literature search, entity extraction, knowledge-graph explore, prediction curation, training-artifact browse/audit, simulation, Monte Carlo, and treatment ranking. For a double-click / desktop shortcut with the same defaults (`http://127.0.0.1:8501`), use `start_dashboard.bat`. Offline defaults prefer local JSONL/lexicon fixtures; NCBI/model modes surface clear errors when network or models are unavailable. `16CB` runs `gbmbert-fit-simulation-parameters` (toy posterior-style sampling against synthetic targets — explicitly not PK/PD). These are research prototypes, not biophysical digital twins, and not for clinical decision-making.

## What Changed

The previous launcher showed every command on the first screen, which made normal use harder as the project grew. The simplified launcher keeps all commands available but groups them by the question a user is usually asking:

- "Is my environment ready?"
- "Is the project safe to hand off?"
- "Do I need to build literature or graph artifacts?"
- "Do I need review or curation tools?"
- "Do I need training data/governance tools?"
- "Do I want to inspect a graph in the browser?"
- "Do I want to run the Phase 5/6 research simulation or scenario-ranking prototypes, or open the Phase 7 dashboard?"
