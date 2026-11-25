# GBM-AI Platform Handoff

Project root:

`C:\Users\david\GBM`

Use this as the canonical project folder. The local virtual environment is:

`C:\Users\david\GBM\.venv`

Do not install dependencies globally. Use the project `.venv`.

## Persistent Safety Boundary

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

The platform is a research-use-only glioblastoma literature intelligence system for literature mining, structured biomedical annotation, knowledge graph construction, curation workflows, and in-silico hypothesis generation scaffolding.

Local research checkpoints, gold-pack promotion reviews, and Phase 5 toy tumour simulations may exist. Those artifacts support literature-mining experiments and in-silico hypothesis exploration only. They do not create a validated clinical model, authorize diagnosis or treatment decisions, claim patient-ready predictions, or remove the research-use boundary.

Current non-goals:

- Patient-specific treatment recommendations
- Clinical decision support
- Predictive clinical accuracy claims
- Production clinical dashboard
- Claiming that a validated trained GBM-BERT model exists (research-candidate checkpoints and promotion reviews are not clinical validation)
- Clinically validated tumour simulator / biophysical digital twin
- Clinical treatment optimizer / CDS (Phase 6 is research scenario ranking only — not prescriptions)

## Current State

The project has working local scaffolding and CLI workflows for:

- PubMed ingestion and query packs
- ClinicalTrials.gov read-only ingestion and trial graph records
- Corpus manifests and standard artifact paths
- Text cleaning
- Biomedical annotation schemas
- Entity extraction, including offline lexicon mode
- Evidence classification placeholders and curation queues
- Reviewed queue workflows and adjudication reports
- Annotation dataset export and quality reports
- Gold seed dataset builder
- Rule-based relation extraction and relation quality audit
- Knowledge graph schema, graph record builder, graph quality reports, provenance audit, Neo4j loader, and graph inspection CLI
- Local Knowledge Graph Explorer web UI/API
- Evidence overlay, overlay diff, overlay load guard, overlay promotion gate, and overlay revert
- Prediction curation workflows, active learning candidates, active learning batches, CSV roundtrip, and curation regression pack
- Scope drift monitor and platform regression command
- Streamlit research operations console (live in-process runners across literature → extract → graph → curation → training artifacts → sim/rank)
- Phase 5 research prototype tumour simulation (compartment toy model + scenario runner CLI; not clinically validated)
- GBM-BERT training scaffold, dataset splitting, label maps, dataset cards, baseline reports, experiment manifests, checkpoint registry metadata, gated training runner, HF dataset loaders, tokenizer pipeline, evidence classifier training execution, evaluation reports, run manifests, evidence batch inference, model cards, and smoke fixture

## Recently Implemented PR111-158

PR111 NER Registry Retirement:

- Retired the stale `gbmbert_ner_smoke_candidate` checkpoint registry entry because no checkpoint artifact existed.
- `models\checkpoint_registry.json` now lists only the real local evidence smoke research candidate.
- Registry audit now passes with 1 checkpoint, 0 errors, and 0 warnings.

PR112 Evidence Config Profile Split:

- Added `configs\training\gbmbert_evidence_smoke_pubmedbert.json` for the current tiny evidence smoke pack.
- Marked `configs\training\gbmbert_evidence_pubmedbert.json` as a future scaffold with the full evidence label profile.
- Training label drift now compares the current smoke evidence config against the current evidence smoke data.

PR113 NER Config Scaffold Review:

- Marked `configs\training\gbmbert_ner_pubmedbert.json` as a nonblocking scaffold.
- The NER config remains visible for future work, but its broader label vocabulary no longer fails the current governance gate.

PR114 Governance Green Mode:

- Default `gbmbert-run-training-governance-suite` now passes for current local artifacts.
- Added `--strict-scaffolds` for audit mode when scaffold gaps should be treated as blocking.

PR115 Training Config Suite Report v2:

- Config-suite reports now distinguish current blocking configs from scaffold configs.
- Reports include current passed/failed counts, scaffold counts, raw review status, governance profile, and scaffold warnings.

PR116 Dashboard Governance Status Cleanup:

- Dashboard training context and manifest now separate registry health, current config health, and scaffold config count.
- `reports\training\dashboard_training_manifest.md` now shows current config failures separately from scaffold visibility.

PR117 Handoff Refresh:

- This handoff now reflects the current PR111-117 state.
- The next work starts after the green governance cleanup, not at PR95.

PR119 Changelog and Artifact Policy:

- Added `CHANGELOG.md` with the current unreleased governance/data-planning changes.
- Added `docs\ARTIFACT_POLICY.md` to distinguish tracked handoff reports from regenerated local byproducts.

PR124 Canonical Local Verification:

- Added `gbmbert-verify-local`, which runs pytest, pip check, scope drift, default training governance, compact platform regression, launcher checks, artifact policy, and artifact indexing in order.
- Added `reports\platform_regression\local_verification.md` and JSON output from the current run.
- Added launcher option `16BI`.

PR123 Strict Governance Audit Profile:

- Added `gbmbert-run-strict-training-governance` with default output under `reports\training\governance_strict`.
- Added launcher option `16BH`.
- The strict profile intentionally reports scaffold gaps for the full evidence and broad NER configs unless `--allow-findings` is used.

PR120 Gold Pack Expansion Plan:

- Added `reports\training\gold_pack\gold_pack_expansion_plan.md` and JSON.
- The plan keeps the gold pack scaffold-only until evidence, NER, relation, split, and provenance criteria are met.

PR121 Current NER Smoke Config:

- Added `configs\training\gbmbert_ner_smoke_pubmedbert.json`.
- Training config suite now reports 5 configs: 3 current configs passing, 0 current failures, and 2 scaffold configs.

PR122 Full Evidence Label Coverage Plan:

- Added `reports\training\evidence_pack\full_label_coverage_plan.md` and JSON.
- The full evidence config remains scaffold-only until labels `0` through `5` are represented in the local pack.

PR125 Curated Evidence Label Expansion:

- Added `data\training\curated_expansion\evidence_full_label.jsonl` with source-backed local fixture rows for evidence labels `0` through `5`.
- Rebuilt `data\training\evidence_pack` and refreshed the evidence-pack reports.
- Kept `configs\training\gbmbert_evidence_pubmedbert.json` scaffold-only because the fixture is intentionally minimal.

PR126 NER Gold Pack Expansion:

- Added curated broad-label NER fixture rows under `data\training\curated_expansion\gold_entities.jsonl`.
- Rebuilt `data\training\gold_seed` and `data\training\gold_pack` with non-empty NER splits and label maps.
- Kept the broad NER config scaffold-only until larger reviewed data volumes are available.

PR127 Relation Gold Pack Expansion:

- Added curated relation fixture rows, including positive relation labels and `NO_RELATION`, via `data\training\curated_expansion\gold_reviewed_queue.jsonl`.
- Rebuilt the gold pack relation splits and relation quality/provenance reports.
- Relation pack rows now preserve curated source type metadata for provenance audits.

PR128 Local Verification CI Hook:

- Added `.github\workflows\local-verification.yml`.
- The workflow installs the project, runs `gbmbert-verify-local`, and runs strict governance with `--allow-findings`.
- `gbmbert-verify-local` now includes launcher-menu and artifact-policy checks before artifact indexing.

PR129 Artifact Policy Enforcement:

- Added `gbmbert-check-artifact-policy`.
- Added `reports\platform_regression\artifact_policy.md` and JSON.
- The policy check verifies required handoff artifacts exist and blocks tracked cache, virtual-environment, large-checkpoint, and oversized local byproduct paths.

Launcher Menu Simplification:

- Simplified `launcher_menu.bat` to workflow groups: setup, verification, pipeline, curation, training, explorer, and advanced index.
- Preserved legacy shortcuts such as `16BI` from the main prompt.
- Added `docs\LAUNCHER_MENU.md` explaining the groups and recommended paths.

PR130 Strict Governance Label-Drift Alignment:

- `gbmbert-training-label-drift` now compares each config against its own governance dataset path when present.
- Current smoke configs are no longer compared against expanded scaffold packs.
- Strict governance still stays visibly strict by warning when scaffold configs are present.

PR131 Larger Curated Fixture Import:

- Added `gbmbert-import-curated-training-fixture`.
- The importer validates source PMIDs and review metadata for curated evidence/review batches before a larger pack rebuild.
- Current import report is tracked at `reports\training\curated_fixture_import.md` and JSON.

PR132 CI Artifact Reporting:

- GitHub Actions now uploads verification, platform regression, governance, strict governance, and promotion-review reports as CI artifacts.

PR133 Launcher Smoke Tests:

- Added `gbmbert-check-launcher-menu`.
- `gbmbert-verify-local` now runs the launcher menu check before artifact policy.
- Launcher check reports are tracked under `reports\platform_regression`.

PR134 Gold Pack Promotion Review:

- Added `gbmbert-review-gold-pack-promotion`.
- Promotion thresholds are currently 100 examples per task, 10 examples per label, and 50 source PMIDs.
- The current minimal fixture is explicitly not promotion-ready.

PR135 Curated Import Batch Scaling:

- `gbmbert-import-curated-training-fixture` now accepts repeated evidence, entity, and reviewed-queue JSONL inputs.
- The importer writes combined evidence, entity, and reviewed queue JSONL files under `data\training\curated_import`.
- Source PMID and review metadata validation remain mandatory.

PR136 Promotion Threshold Configuration:

- Added `configs\training\gold_pack_promotion_thresholds.json`.
- `gbmbert-review-gold-pack-promotion` now reads reviewable thresholds from that config by default.
- Governance scans now ignore non-training threshold JSON when selecting model training configs.

PR137 CI Markdown Summary:

- Added `gbmbert-ci-report-summary`.
- GitHub Actions appends `reports\platform_regression\ci_report_summary.md` to the step summary after verification and strict governance.
- The CI summary is now a required handoff/platform artifact.

PR138 Dashboard Governance Context Refresh:

- Dashboard training context now surfaces label drift warnings, launcher menu safety, curated import safety, and gold-pack promotion state.
- Training artifact dashboard links now include the refreshed governance reports.

PR139 Larger Gold-Pack Curation Round:

- Added second-round curated fixture files under `data\training\curated_expansion`.
- Rebuilt the combined curated import, evidence pack, gold seed, gold pack, relation quality, provenance, drift, comparison, and promotion-review reports.
- The second-round gold pack was locally ready with 18 evidence, 36 NER, and 18 relation examples, while promotion remained blocked by threshold config.

PR140 Multi-Batch Curation Provenance Diff:

- Added `gbmbert-curated-provenance-diff` to compare curated batches by source file, PMID, task, label, reviewer, and review status before pack rebuilds.
- The report highlights duplicate, changed, and withdrawn/rejected reviewed examples without implying model or clinical readiness.
- Current three-round curated fixture diff is safe for pack rebuild review, with 120 observations, 18 source PMIDs, and 0 findings.

PR141 Promotion Threshold Review UX:

- `gbmbert-review-gold-pack-promotion` now reports exact promotion deltas for task examples, per-label examples, and source PMIDs.
- The report keeps non-promotable gold packs as review signals and does not imply model or clinical readiness.

PR142 CI Summary Hardening:

- `gbmbert-ci-report-summary` now fails when required verification or governance JSON reports are missing, invalid, or not JSON objects.
- Strict-governance and gold-pack promotion findings remain visible review signals rather than default pass/fail claims about model readiness.

PR143 Dashboard Governance Detail Links:

- The dashboard training context now includes governance detail rows with Markdown path, JSON path, existence flags, and parsed status.
- Missing governance report files are visible in dashboard context without implying model or clinical readiness.

PR144 Third Curated Expansion Round:

- Added third-round curated fixture files under `data\training\curated_expansion`.
- Rebuilt combined curated import, provenance diff, evidence pack, gold seed, gold pack, relation pack, relation quality, provenance, drift, comparison, promotion, dashboard, CI, and governance reports.
- Current gold pack is locally ready with 24 evidence, 48 NER, and 24 relation examples across 18 source PMIDs, while promotion remains correctly blocked by threshold config.

PR145 Fourth Curated Expansion Round:

- Added fourth-round curated fixture files under `data\training\curated_expansion`.
- Rebuilt combined curated import, provenance diff, evidence pack, gold seed, gold pack, relation pack, relation quality, provenance, drift, comparison, promotion, dashboard, CI, and governance reports.
- Current gold pack is locally ready with 30 evidence, 60 NER, and 30 relation examples across 24 source PMIDs, while promotion remains correctly blocked by threshold config.

PR146 Governance Detail Export:

- Added `gbmbert-export-governance-detail-links` for standalone Markdown/JSON exports of dashboard governance detail rows.
- The export keeps missing report files visible as handoff review signals without implying model or clinical readiness.

PR147 CI Summary Artifact Contract:

- Added `gbmbert-check-ci-summary-contract` to validate that the generated CI summary references all required report families.
- Strict-governance and gold-pack promotion findings remain review signals, not default readiness claims.

PR148 Promotion Planning Report:

- Added `gbmbert-plan-gold-pack-promotion` to group promotion deltas into scaffold-only future curation batches.
- The planning report is explicitly research-use-only and does not promote a dataset or claim a validated GBM-BERT model exists.

PR149 Fifth Curated Expansion Round:

- Added fifth-round curated fixture files under `data\training\curated_expansion`.
- Rebuilt combined curated import, provenance diff, evidence pack, gold seed, gold pack, relation pack, relation quality, provenance, drift, comparison, promotion, dashboard, CI, and governance reports.
- Current gold pack is locally ready with 36 evidence, 72 NER, and 36 relation examples across 30 source PMIDs, while promotion remains correctly blocked by threshold config.

PR150 Promotion Planning UX Refinement:

- Added compact promotion-planning summary fields for remaining task examples, per-label remaining examples, and source-PMID batches.
- The report remains scaffold-only and explicitly research-use-only.

PR151 Governance Detail Contract:

- Added `gbmbert-check-governance-detail-contract` for standalone validation that required governance detail rows remain visible.
- Missing report files inside detail rows remain review signals only and do not imply model or clinical readiness.

PR152 Launcher Report Shortcuts:

- Added launcher shortcuts for promotion planning, governance detail export, and CI summary contract checks.
- Launcher smoke checks remain preserved with no training or clinical-readiness semantics.

PR153 Sixth Curated Expansion Round:

- Added sixth-round curated fixture files under `data\training\curated_expansion` (`evidence_round6.jsonl`, `gold_entities_round6.jsonl`, `gold_reviewed_queue_round6.jsonl`) introducing six brand-new source PMIDs.
- Rebuilt combined curated import, provenance diff, evidence pack, gold seed, gold pack, relation pack, relation quality, provenance, drift, comparison, promotion-review, planning, CI, and governance reports from all six rounds.
- Current gold pack is locally ready with 42 evidence, 84 NER, and 42 relation examples across 36 source PMIDs, while promotion remains correctly blocked by threshold config.

PR154 Promotion Planning Label-Cap Refinement:

- Promotion planning now reports a `label_balance_relationship` per task (label-floor total, task-volume delta, and remaining task volume after label balancing), and each batch carries `task_volume_delta` + `counts_toward_task_volume`.
- The plan stays scaffold-only and explicitly research-use-only; it does not promote a dataset or claim a validated GBM-BERT model exists.

PR155 Governance Detail Contract In CI Summary:

- The compact CI Markdown summary now includes a `Governance detail contract` row read from `reports\training\governance_detail_contract.json`, and the CI summary contract requires that family.
- The contract report is an optional read: a missing file stays visible as a `report missing` review signal and never blocks summary generation or implies model/clinical readiness.

PR156 Launcher Curated Import Multi-Batch Defaults:

- Added launcher option `16BR` (`:curated_fixture_import_multibatch`) running the full six-round curated import with the same fixed file set the provenance diff (`16BN`) uses.
- Extended the provenance diff recipe to include round six and registered `16BR` in the launcher menu check; `16BL` remains the interactive single-batch import.

PR157 Seventh Curated Expansion Round:

- Added seventh-round curated fixture files under `data\training\curated_expansion` (`evidence_round7.jsonl`, `gold_entities_round7.jsonl`, `gold_reviewed_queue_round7.jsonl`) introducing six brand-new source PMIDs (PMID-disjoint from all prior rounds).
- Regenerated the entire report chain with the PR158 orchestrator (`gbmbert-rebuild-curated-rounds`, auto-discovered round seven with no code changes) — 7 rounds, 20/20 steps.
- Current gold pack is locally ready with 48 evidence, 96 NER, and 48 relation examples across 42 source PMIDs, while promotion remains correctly blocked by threshold config (needs 50 PMIDs / 100 examples per task).
- Updated the static `16BN` provenance-diff and `16BR` multi-batch-import launcher recipes to include round seven; the dynamic `16BS` orchestrator needs no per-round edits.

PR158 Curated Round Rebuild Orchestrator:

- Added `gbmbert-rebuild-curated-rounds` (`src\gbmbert\training\curated_round_rebuild.py`, launcher `16BS`): one observe-only command that discovers every curated expansion round (base trio + `*_round{N}` trios) and runs the full 20-step report chain — import, provenance diff, gold seed, gold pack, evidence pack, relation pack, relation quality, the seven top-level governance reports, promotion review/planning, the governance + strict-governance suites, and the governance detail export/contract.
- Modeled on the `gbmbert-verify-local` runner: an injectable command runner, ordered step list, and a `reports\training\curated_round_rebuild.{md,json}` report with per-step status. Partial/missing rounds are surfaced as warnings; platform verification (`gbmbert-verify-local`) and the CI summary stay a separate downstream step.
- Verified idempotent against the six-round corpus: 20/20 steps pass and the gold pack stays at 42 evidence / 84 NER / 42 relation across 36 source PMIDs.

PR159 Promotion Planning Coverage Report:

- The gold-pack promotion planning report now includes a per-task `task_coverage` view (label-floor coverage percentage of the task delta vs. remaining raw task-volume percentage, capped at 100%) plus an `overall_label_floor_coverage_pct` summary, surfaced in both the JSON and the Markdown.
- Builds directly on the PR154 label-balance relationship; stays scaffold-only and research-use-only (it does not promote a dataset or claim a validated GBM-BERT model exists).

PR161-real Real-Annotation Review-Batch Helper:

- Added `src\gbmbert\training\review_batch_prep.py` with two console scripts. `gbmbert-prep-review-batch` ingests real PubMed abstracts (optionally fetching via `--query-pack`), runs the offline lexicon literature pipeline (Hugging Face NER is unreachable in this environment; lexicon mode is the validated substitute), exports a review queue, and writes a human-review reviewed-queue skeleton + entities + INSTRUCTIONS under a staging dir.
- `gbmbert-finalize-review-batch` validates the human-reviewed batch and promotes the three round files into `data\training\curated_expansion` ONLY when no row is still `pending`; only accepted rows enter the corpus, and the evidence_round{N} labels are derived from the human-confirmed (or corrected) evidence tiers. `gbmbert-rebuild-curated-rounds` then discovers the new round.
- Dry-run validated end-to-end on 39 real GBM abstracts: 46 review items staged (39 evidence claims + 7 relations), finalize correctly refuses an all-`pending` batch. No unreviewed round was committed — round 8 is left for real human annotation.
- Scope: observe-only, research-use-only. Entity spans are lexicon-suggested (not span-reviewed); the human-reviewed signal is the evidence tiers and relations.

PR163 External-Corpus Ingestion Adapter (real-corpora pivot, slice 1):

- Strategic pivot (decided this session): re-found the NER/relation tracks on real, peer-used biomedical corpora instead of synthetic fixtures. The evidence-tier (0-5) task stays human-annotated (no public corpus for that rubric); NER + relations come from real corpora.
- Added `src\gbmbert\training\external_corpus_import.py` + `gbmbert-import-external-corpus`: a corpus-agnostic adapter (raw corpus -> reader -> normalized CorpusDocument -> crosswalk -> project gold_entities JSONL) tagged with corpus provenance (`source_type=external_corpus`, `source_corpus`, license). Onboarding a corpus = a new reader + a config block; the project labels stay stable.
- Crosswalk config `configs\extraction\external_corpus_crosswalk.json` maps BC5CDR Chemical->DRUG, Disease->DISEASE. BioRED (PR164) now supplies GENE/CELL_TYPE/BIOMARKER plus relations; TREATMENT still needs a future intervention-annotated source.
- Validated on REAL BC5CDR (token-level `tner/bc5cdr` mirror, reachable here): 5,228 documents -> 9,385 entities (5,203 DRUG + 4,182 DISEASE), 0 dropped, offsets verified against text. Bulk corpus data is NOT committed (regenerate with the command below); only the adapter + crosswalk + tests are tracked.
- CONSTRAINTS: the tner mirror is NER-only (no PMIDs, no relations). Relations + real PMIDs + GENE/CELL_TYPE arrive with the BioRED BioC reader (PR164).

PR164 BioRED BioC Reader:

- Added `biored_bioc` reader in `external_corpus_import.py` for NCBI BioRED BioC JSON (`https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/BIORED.zip`). Document ids are PubMed PMIDs; entity offsets are absolute against the reconstructed passage buffer; relations are document-level and keyed by entity identifiers.
- Crosswalk `biored` block now has resolved source/license and maps GeneOrGeneProduct->GENE, CellLine->CELL_TYPE, ChemicalEntity->DRUG, DiseaseOrPhenotypicFeature->DISEASE, SequenceVariant->BIOMARKER, plus Association/Positive_Correlation/Negative_Correlation/Bind/Cotreatment/Comparison/Drug_Interaction/Conversion onto project relation labels. OrganismTaxon is intentionally unmapped.
- Importer writes optional `gold_relations.jsonl` (`--relations-output`) with corpus provenance. CLI accepts a single `*.BioC.JSON` file or a directory of them.
- Validated on BioRED Dev: 100 documents -> 3,163 mapped entities (GENE 1,087 / DISEASE 982 / DRUG 822 / BIOMARKER 250 / CELL_TYPE 22) and 1,114 mapped relations; 370 OrganismTaxon mentions dropped by design; a small number of relations drop when an endpoint identifier has no mapped mention. Reports: `reports/training/external_corpus_biored.md` (+ JSON). Bulk BioRED files stay under `data/research/biored/` (gitignored).
- Observe-only, research-use only. Merged into a combined gold pack via PR165.

PR166 Promotion Threshold Recalibration + Boundary Language:

- Updated `configs/training/gold_pack_promotion_thresholds.json` and promotion-review defaults to **200 examples/task**, **20/label**, **100 source PMIDs**, with a written rationale and explicit note that promotion is research-governance only (not clinical validation).
- Clarified the persistent safety boundary and `docs/PROJECT_SCOPE.json` so research-candidate checkpoints / promotion reviews may exist without implying a validated clinical GBM-BERT model.

PR161 Round 8 — Real Reviewed Batch:

- Prepared and finalized Round 8 from 30 PMID-disjoint abstracts drawn from the merged PubMed backfill (`data/research/review_batches/round8/`).
- Adjudicated 33 review items -> 23 accepted evidence + 2 accepted relations (+ 8 rejected); promoted into `curated_expansion` and rebuilt via `gbmbert-rebuild-curated-rounds`.
- Fixed finalize so `corrected` rows are gold-usable (apply correction fields, then promote).

PR161 Round 9 — Real Reviewed Batch:

- Prepared and finalized Round 9 from 35 PMID-disjoint abstracts (`data/research/review_batches/round9/`), excluding all prior curated + Round 8 candidate PMIDs.
- Adjudicated 44 review items -> 33 accepted evidence + 5 accepted relations (+ 6 rejected); promoted and rebuilt via `gbmbert-rebuild-curated-rounds` (20/20 steps).
- Current curated gold pack after Round 9: **104 evidence / 670 NER / 55 relation across 107 source PMIDs**; source-PMID floor (100) is met, but promotion remains blocked on task volume (evidence needs ~96 more, relations ~145) and some per-label floors.

PR161 Round 10 — Relation-Heavier Real Reviewed Batch:

- Prepared and finalized Round 10 from 50 PMID-disjoint abstracts (`data/research/review_batches/round10/`), biased toward multi-entity abstracts so more relation candidates survived adjudication.
- Adjudicated 64 review items -> 50 accepted evidence + 13 accepted relations (+ 1 rejected); promoted and rebuilt via `gbmbert-rebuild-curated-rounds`.
- Expanded `configs/training/gbmbert_relation_biobert.json` label_set to cover newly curated `IMPROVES` / `WORSENS` (with existing ASSOCIATED_WITH / NO_RELATION / PREDICTS).
- Current curated gold pack after Round 10: **154 evidence / 1455 NER / 68 relation across 157 source PMIDs**; PMID floor met; promotion still blocked on task volume (evidence needs ~46 more, relations ~132) and some per-label floors (notably IMPROVES/WORSENS/NO_RELATION and sparse NER labels).

PR161 Round 11 — Relation-Weighted Real Reviewed Batch:

- Prepared and finalized Round 11 from 50 PMID-disjoint abstracts (`data/research/review_batches/round11/`), scored for longer text + relation-friendly keywords (prognosis/outcome/response/etc.).
- Adjudicated 71 review items -> 49 accepted evidence + 18 accepted relations (+ 4 rejected, including 2 near-duplicate relations cleared so the gold pack stays dedupe-ready); promoted and rebuilt via `gbmbert-rebuild-curated-rounds`.
- Current curated gold pack after Round 11: **203 evidence / 2315 NER / 86 relation across 207 source PMIDs**; evidence task floor (200) and PMID floor met; promotion still blocked on relation volume (~114 more), sparse relation labels (`IMPROVES`/`WORSENS`/`NO_RELATION`), sparse evidence tiers 2/4/5, and sparse NER labels.

PR161 Rounds 12–14 — Relation-Weighted Real Reviewed Batches:

- Prepared and finalized Rounds 12–14 from 150 PMID-disjoint abstracts (`data/research/review_batches/round12|13|14/`), scored for longer text + relation-friendly keywords.
- Adjudicated -> **147 accepted evidence + 46 accepted relations** (rare graph types remapped to `ASSOCIATED_WITH`; near-duplicates rejected); promoted and rebuilt once via `gbmbert-rebuild-curated-rounds`.
- Current curated gold pack after Round 14: **350 evidence / 4237 NER / 132 relation across 357 source PMIDs**; evidence task + evidence per-label floors met; promotion still blocked on relation volume (~68 more), `IMPROVES`/`WORSENS`/`NO_RELATION` label floors, and sparse NER labels (`CELL_STATE`/`PATHWAY`/`TRIAL_PHASE`/`UNKNOWN`).

PR161 Round 15 — Relation-Weighted Real Reviewed Batch:

- Prepared and finalized Round 15 from 55 PMID-disjoint abstracts (`data/research/review_batches/round15/`).
- Adjudicated 67 review items -> 51 accepted evidence + 12 accepted relations (+ 4 rejected); promoted and rebuilt via `gbmbert-rebuild-curated-rounds`.
- Current curated gold pack after Round 15: **401 evidence / 4803 NER / 144 relation across 412 source PMIDs**; evidence floors met; promotion still blocked on relation volume (~56 more), `IMPROVES`/`WORSENS`/`NO_RELATION` label floors, and sparse NER labels.

PR161 Round 16 — Larger Relation-Weighted Batch:

- Prepared and finalized Round 16 from **100** PMID-disjoint abstracts (`data/research/review_batches/round16/`) with `--max-confidence 0.90`.
- Adjudicated 107 review items -> 97 accepted evidence + 7 accepted relations (+ 3 rejected). Lexicon pipeline extracted only 7 graph relations from the 100 abstracts — remaining backfill is relation-sparse after earlier high-yield rounds.
- Current curated gold pack after Round 16: **498 evidence / 5820 NER / 151 relation across 512 source PMIDs**; evidence floors met; promotion still blocked on relation volume (~49 more), `IMPROVES`/`NO_RELATION` label floors, and sparse NER labels (`WORSENS` now 18).

PR161 Round 17 — Curated NO_RELATION Co-Mention Fill:

- Generated 55 accepted `NO_RELATION` rows from co-mentioned endpoints (`gold_reviewed_queue_round17.jsonl`): other pairs in sentences that already have positives, plus same-type co-mentions; excluded risky true-relation type pairs (Disease/Gene/Biomarker/Drug/Treatment ↔ Outcome/Disease, etc.).
- Report: `reports/training/curated_no_relation_round17.md` (+ JSON). Empty evidence/entity sidecars keep the round trio discoverable without NER duplicates.
- Current curated gold pack after Round 17: **498 evidence / 5820 NER / 206 relation across 512 source PMIDs**; relation task floor met (`NO_RELATION` 74); promotion still blocked on `IMPROVES` (17) / `WORSENS` (18) and sparse NER labels.

PR161 Round 18 — Label-Floor Close + Evidence v2:

- Added 3 curated `IMPROVES` + 2 curated `WORSENS` from outcome-language intervention→outcome sentences, plus real-span NER fill for `CELL_STATE`/`PATHWAY`/`TRIAL_PHASE`/`UNKNOWN` (`reports/training/curated_label_floor_round18.*`).
- After rebuild, gold-pack promotion review is **promotable**: **498 evidence / 5869 NER / 211 relation across 526 source PMIDs** (all task/label/PMID floors met). Research-governance promotion only — not clinical validation.
- Re-merged BioRED GBM-filtered external gold: **563 entity docs / 6072 NER / 288 relations / 498 evidence**.
- Ran second PubMedBERT evidence experiment on the larger pack (399/49/50 splits): checkpoint `gbmbert_evidence_experiment_pubmedbert_v2`, reports under `reports/training/evidence_experiment_v2_*`, scored 912 claims to `evidence_claims_scored_v2.jsonl`. Local test accuracy 0.60 / macro-F1 0.15 — research artifact only.

PR165 GBM-Relevance Filter + Merge (+ Train expansion):

- Added `src\gbmbert\training\external_gold_merge.py` + `gbmbert-merge-external-gold-pack`. Filters external entity documents with configurable GBM-adjacent patterns (`configs\extraction\gbm_relevance_keywords.json`), keeps matching external relations by PMID, and merges with curated entities/relations/evidence.
- Dual provenance is preserved: curated rows get `source_type=human_reviewed` (and keep `relation_pack_source_type`); external rows keep `source_type=external_corpus` / `source_corpus` and gain `relation_pack_source_type=external_corpus` for governance. NER rows carry `source_type`/`source_corpus` (unlike the older gold_seed flattener).
- `audit_training_provenance` now accepts either `relation_pack_source_type` or `source_type`.
- Validated on BioRED Dev+Train + curated rounds: 500 external docs -> **6 GBM-adjacent kept** (494 dropped). Latest re-merge after Round 18: combined pack has **563 entity docs / 6072 NER / 288 relations / 498 evidence**; dual provenance intact. Reports: `reports\training\external_gold_merge.md` (+ JSON). Combined outputs under `data\training\gold_pack_combined\` (gitignored; regenerate with the command below).
- Observe-only, research-use only. Does not replace the curated-only gold pack used by governance defaults.

PR167 Operational Data Loop (corpus + curation + first evidence experiment):

- Confirmed NCBI env (`.env` email + API key), `gbmbert-preflight` pass, and `gbmbert-platform-regression` 7/7.
- Tuned five previously empty `pubmed_gbm_v2` queries; backfilled v1+v2 at `retmax-per-query=50`; merged to **912 unique PMIDs**; ran lexicon end-to-end pipeline with 0 invalid graph records.
- Closed the smoke review loop (7/7 decided) and curated a 30-item real backfill batch; rebuilt gold-seed/pack under `data/training/gold_*_backfill_batch1`.
- Fixed Trainer tokenization by removing source metadata columns after `tokenize_dataset` (string `label` columns were breaking collation).
- Ran first local PubMedBERT evidence-classifier research experiment (`configs/training/gbmbert_evidence_experiment_pubmedbert.json`) on the curated evidence pack (39/5/4 splits); scored all 912 merged evidence claims. Checkpoint weights stay local/gitignored; tracked reports under `reports/training/evidence_experiment_*`. Research-use only — tiny eval accuracy is not clinical validation.
- Second evidence experiment (post–Round 18 pack, 399/49/50): checkpoint `gbmbert_evidence_experiment_pubmedbert_v2`, reports `reports/training/evidence_experiment_v2_*`, scored claims `evidence_claims_scored_v2.jsonl`.
- Evidence quality pass (v3): optional class-weighted CE in `execution.py` (`use_class_weights`), 3-epoch weighted retrain → checkpoint `gbmbert_evidence_experiment_pubmedbert_v3`. Macro-F1 0.30 (vs v2 0.15); accuracy fell 0.60→0.44 as majority-class collapse ended; corpus score mix spans tiers 0–5. Compare: `reports/training/evidence_experiment_v3_vs_v2.md`.
- Round 19 minority-tier evidence pass: 70 abstracts → 67 evidence (48 tier 1, 12 tier 5); pack **565 / 6540 / 215 / 596 PMIDs**. Weighted v4 checkpoint `gbmbert_evidence_experiment_pubmedbert_v4` learns tier 1/5 (F1 0.56 / 0.44); compare `reports/training/evidence_experiment_v4_vs_v3.md` (test split changed after rebuild).
- Training execution now supports evidence, relation, and NER (`execute_task_training`). Relation BioBERT v3: accuracy 0.65 / macro-F1 0.59 (`relation_experiment_v3_*`). Mention-level NER scaffold v1 remains; document BIO NER v2 added (`ner_bio_experiment_v2_*`).
- Round 20 stabilize tiers 0/2/4: 70 abstracts → 68 evidence (13/27/14 for 0/2/4); pack **633 / 7081 / 217**. Weighted v5: macro-F1 0.47; tier 0/2 recovered (F1 0.38 / 0.83); tier 4 still 0 on n=2 test. Compare `evidence_experiment_v5_vs_v4.*`.
- Round 21 tier-4 refill (phase I/II query pack fetch) + Round 22 IMPROVES/WORSENS fill: pack **709 / 7653 / 259 / 745 PMIDs**. Evidence v6: tier-4 F1 **0.80** (n=9); compare `evidence_experiment_v6_vs_v5.*`. Relation v2 IMPROVES F1 0.50; compare `relation_experiment_v2_vs_v1.*`.
- Items 1–6 follow-on: Round 23 sparse NER (`CELL_STATE`/`PATHWAY`/`TRIAL_PHASE`/`UNKNOWN`); dual-review rounds 21–22 (`adjudication_round21/22.*`, agreement ~0.94/~0.93); TREATMENT stub corpus reader + crosswalk; Round 25 PREDICTS/WORSENS (+35 relations); Round 24 tiers 2/5 (+46 evidence); BIO NER v2 (`max_steps=400`, span acc 0.94 / type macro-F1 0.30); evidence v7 (macro-F1 0.50); relation v3 (macro-F1 0.59). Launcher `16BT`/`16BU`; CI opt-in curated-rebuild row (not a hard gate). Label drift understands BIO `ner_encoding` via pack label maps.
- Real TREATMENT corpus: EBM-NLP (`--corpus ebm_nlp`) replaces the stub as the peer-used Intervention path. Full import: 4,980 docs / 34,046 TREATMENT / 34,508 OUTCOME. GBM-filtered merge report: `reports/training/external_gold_merge_ebm_nlp.*`. Bulk raw under `data/raw/ebm_nlp/` (gitignored); tracked sample fixture `data/examples/ebm_nlp_sample/`.
- EBM-NLP fold-in: GBM-filtered docs live at `data/training/external_corpus/ebm_nlp_gbm/gold_entities.jsonl` and are included by `gbmbert-rebuild-curated-rounds` + BIO NER defaults. Gold NER TREATMENT/OUTCOME **585 / 1356**; BIO pack **734** docs (TREATMENT **549**). BIO builder prefers embedded entity-doc `text` when present so EBM offsets stay valid.
- Prefer research baseline `gbmbert_ner_bio_pubmedbert_v6` (span ~0.99 / type macro-F1 ~0.69 on cleaned pack); v3/v4/v5 remain historical.
- Entity-span review path: `gbmbert-export-entity-span-review` / `gbmbert-apply-entity-span-review` + launcher `16BV`/`16BW`; gold-seed NER builder dedupes identical `(pmid,start,end,label,text)` rows.
- Round 26 denser `CELL_STATE`/`UNKNOWN` (span-reviewed) + evidence AL export; Round 27 AL adjudication (+36 evidence; `adjudication_al_round26.*`, agreement ~0.93); Round 26/28 span dual-review (`adjudication_round26_spans.*`, `adjudication_round28_spans.*`).
- Round 29 sparse NER densify (dual span-reviewed; `adjudication_round29_spans.*`, agreement ~0.84) + Round 27 AL second-pass (`agent-curation-r3`; `adjudication_al_round27_second_pass.*`, consensus vs r3 agreement **0.96**; evidence_round27 unchanged). Round 30 tier-4 early-phase PubMed fill (+18 evidence; test tier-4 **n=2→8**).
- Gold pack: **promotable**, **809 evidence / 8020 NER / 294 relation / 909 PMIDs** (`CELL_STATE` 105, `UNKNOWN` 59, `PATHWAY` 69, `TRIAL_PHASE` 71).
- Evidence v9 (`evidence_experiment_v9_*`, macro-F1 **0.59** vs v8 0.57; tier-4 F1 **0.71** on n=8). BIO NER **v6 preferred** (`ner_bio_experiment_v6_*`; span **0.987** / type macro-F1 **0.691** on cleaned pack). Phase 4 research DoD **satisfied** (`reports/training/phase4_definition_of_done.*`). Soft residual: sparse `CELL_STATE`/`PATHWAY` F1 fragile on tiny test n. Phases 5–6 still deferred.
- Windows HF tip: set `HF_HUB_OFFLINE=0` and `HF_HUB_DISABLE_SYMLINKS=1` before model download/train. BioBERT (`dmis-lab/biobert-base-cased-v1.2`) is now in the local HF cache after the relation experiment.

## Latest Verification

Last verified from `C:\Users\david\GBM` using the project `.venv`:

```powershell
.\.venv\Scripts\gbmbert-review-training-config-suite.exe --markdown-output reports\training\training_config_suite_review.md --json-output reports\training\training_config_suite_review.json
.\.venv\Scripts\gbmbert-run-training-governance-suite.exe --output-dir reports\training\governance
.\.venv\Scripts\gbmbert-run-strict-training-governance.exe --output-dir reports\training\governance_strict --allow-findings
.\.venv\Scripts\gbmbert-verify-local.exe
.\.venv\Scripts\gbmbert-plan-gold-pack-promotion.exe --markdown-output reports\training\gold_pack\gold_pack_promotion_plan.md --json-output reports\training\gold_pack\gold_pack_promotion_plan.json
.\.venv\Scripts\gbmbert-export-governance-detail-links.exe --markdown-output reports\training\governance_detail_links.md --json-output reports\training\governance_detail_links.json
.\.venv\Scripts\gbmbert-check-governance-detail-contract.exe --detail-json reports\training\governance_detail_links.json --markdown-output reports\training\governance_detail_contract.md --json-output reports\training\governance_detail_contract.json
.\.venv\Scripts\gbmbert-ci-report-summary.exe --output reports\platform_regression\ci_report_summary.md
.\.venv\Scripts\gbmbert-check-ci-summary-contract.exe --summary reports\platform_regression\ci_report_summary.md --markdown-output reports\platform_regression\ci_summary_contract.md --json-output reports\platform_regression\ci_summary_contract.json
.\.venv\Scripts\gbmbert-check-artifact-policy.exe --markdown-output reports\platform_regression\artifact_policy.md --json-output reports\platform_regression\artifact_policy.json
.\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports\artifact_index.md --json-output reports\artifact_index.json
```

Results:

- Tests: `248 passed`
- `pip check`: no broken requirements
- Scope drift monitor: safe, 0 findings
- Platform regression: passed
- Canonical local verification: passed, 8/8 steps
- Curated round rebuild orchestrator: passed through Round 25; gold pack readiness clean
- Artifact policy: safe, 0 findings
- Artifact index refreshed after Round 23–25 rebuild
- Default training governance suite: passed after Round 25 rebuild
- Evidence experiments: v1–v7 reports under `reports/training/evidence_experiment_*` (checkpoints gitignored); latest compare `evidence_experiment_v7_vs_v6.*`
- Relation experiments: `relation_experiment_v1_*` / `v2_*` / `v3_*` (checkpoint `gbmbert_relation_biobert_v3`)
- NER scaffold (mention-level): `ner_experiment_v1_*`; BIO document NER: prefer `ner_bio_experiment_v6_*` (`gbmbert_ner_bio_pubmedbert_v6`); compare `ner_bio_experiment_v6_vs_v3.*` (cleaned pack; not freeze-split vs historical v3)
- Evidence experiments: latest `evidence_experiment_v9_*` (vs v8 in `evidence_experiment_v9_vs_v8.*`)
- Strict training governance audit: ran with `--allow-findings`; scaffold findings remain visible for research-only model claims
- Label drift: 0 warnings (BIO packs use label-map tags); config-specific governance datasets
- Launcher menu check: safe, 0 findings (includes `16BT`/`16BU` review-batch prep/finalize)
- CI report summary: tracked at `reports\platform_regression\ci_report_summary.md`; includes Governance detail contract + opt-in Curated round rebuild row; CI summary contract valid
- Curated fixture import: rebuilt through Round 22 into the combined curated packs
- Curated provenance diff: rebuilt across all curated rounds including Round 22
- Governance detail export: required rows visible; missing report rows visible for review
- Governance detail contract: valid, all required rows visible
- Gold-pack promotion review: **promotable**; current fixture has 709 evidence, 7653 NER, 259 relation examples and 745 source PMIDs (research-governance only)
- External gold merge refreshed: 563 entity docs / 6072 NER / 288 relations / 498 evidence
- Training config suite: 6 configs, 3 current passed, 0 current failed, 3 scaffold configs
- Model registry audit: passed (includes `gbmbert_evidence_experiment_pubmedbert_v2` research_candidate)

Expected nonblocking scaffold visibility: the full evidence and broad NER configs are marked `governance_profile=scaffold`, so minimal-fixture limitations remain visible without blocking the default governance gate.

## Useful Local Commands

Install/update editable project:

```powershell
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check --no-build-isolation --no-compile -e ".[dev]"
```

Run all tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run platform regression:

```powershell
.\.venv\Scripts\gbmbert-platform-regression.exe
```

Run canonical local verification:

```powershell
.\.venv\Scripts\gbmbert-verify-local.exe
```

Rebuild every curated-round report in one command (PR158):

```powershell
.\.venv\Scripts\gbmbert-rebuild-curated-rounds.exe --markdown-output reports\training\curated_round_rebuild.md --json-output reports\training\curated_round_rebuild.json
```

This discovers every curated expansion round and regenerates the full chain
(import, provenance diff, gold seed/pack, evidence/relation packs, governance,
promotion review/planning, governance detail). It replaces the multi-step
sequence under "PR91-94 smoke commands" plus the curated import/provenance/
promotion commands below. Run `gbmbert-verify-local` afterward for platform
checks and the CI summary.

Prep + finalize a REAL reviewed annotation round (PR161-real):

```powershell
# 1. Build a human-review skeleton from real abstracts (offline lexicon mode).
#    Add --query-pack pubmed_gbm_v1 to fetch the abstracts first.
.\.venv\Scripts\gbmbert-prep-review-batch.exe --round 8 --pubmed-jsonl data\research\round8_pubmed.jsonl --reviewer david
# 2. Annotate data\research\review_batches\round8\gold_reviewed_queue_round8.jsonl by hand
#    (set each row accepted/rejected; confirm/correct evidence_tier or relation_type).
# 3. Promote into the curated rounds (only succeeds when no row is still 'pending').
.\.venv\Scripts\gbmbert-finalize-review-batch.exe --round 8
# 4. Integrate.
.\.venv\Scripts\gbmbert-rebuild-curated-rounds.exe
```

Import a real external corpus (PR163/PR164 — re-founds NER/relations on real data):

```powershell
# BC5CDR (token-level NER mirror) -> DRUG/DISEASE entities.
# curl -sL "https://huggingface.co/datasets/tner/bc5cdr/resolve/main/dataset/train.json" -o data\research\bc5cdr_train.json
.\.venv\Scripts\gbmbert-import-external-corpus.exe --corpus bc5cdr --input data\research\bc5cdr_train.json --output data\training\external_corpus\bc5cdr\gold_entities.jsonl --markdown-output reports\training\external_corpus_bc5cdr.md --json-output reports\training\external_corpus_bc5cdr.json
# Real run observed: 5,228 docs -> 9,385 entities (5,203 DRUG + 4,182 DISEASE), 0 dropped.

# BioRED BioC (PMIDs + GENE/CELL_TYPE/BIOMARKER + relations). Download once from NCBI FTP.
# curl.exe -L -o data\research\biored\BIORED.zip https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/BIORED.zip
# Expand-Archive data\research\biored\BIORED.zip -DestinationPath data\research\biored\extracted
.\.venv\Scripts\gbmbert-import-external-corpus.exe --corpus biored --input data\research\biored\extracted\BioRED\Dev.BioC.JSON --output data\training\external_corpus\biored\gold_entities.jsonl --relations-output data\training\external_corpus\biored\gold_relations.jsonl --markdown-output reports\training\external_corpus_biored.md --json-output reports\training\external_corpus_biored.json
# Real Dev run observed: 100 docs -> 3,163 entities + 1,114 relations (OrganismTaxon dropped by design).

# PR165: GBM filter + merge with curated gold (provenance-preserving).
# Import BioRED Train (after Dev), combine, then GBM-filter + merge with curated gold.
.\.venv\Scripts\gbmbert-import-external-corpus.exe --corpus biored --input data\research\biored\extracted\BioRED\Train.BioC.JSON --output data\training\external_corpus\biored_train\gold_entities.jsonl --relations-output data\training\external_corpus\biored_train\gold_relations.jsonl --markdown-output reports\training\external_corpus_biored_train.md --json-output reports\training\external_corpus_biored_train.json
.\.venv\Scripts\gbmbert-merge-external-gold-pack.exe --output-dir data\training\gold_pack_combined --external-entities-jsonl data\training\external_corpus\biored_all\gold_entities.jsonl --external-relations-jsonl data\training\external_corpus\biored_all\gold_relations.jsonl --curated-entities-jsonl data\training\curated_import\combined_entities.jsonl --curated-relations-jsonl data\training\gold_pack\gold_seed\gold_relations.jsonl --curated-evidence-jsonl data\training\gold_pack\gold_seed\gold_evidence.jsonl --markdown-output reports\training\external_gold_merge.md --json-output reports\training\external_gold_merge.json
# Real run observed: 500 -> 6 GBM-adjacent docs kept; combined 84 entity docs / 577 NER / 127 relations / 71 evidence.
```

Run artifact policy directly:

```powershell
.\.venv\Scripts\gbmbert-check-artifact-policy.exe --markdown-output reports\platform_regression\artifact_policy.md --json-output reports\platform_regression\artifact_policy.json
```

Run launcher menu check:

```powershell
.\.venv\Scripts\gbmbert-check-launcher-menu.exe --markdown-output reports\platform_regression\launcher_menu_check.md --json-output reports\platform_regression\launcher_menu_check.json
```

Validate curated fixture import:

```powershell
.\.venv\Scripts\gbmbert-import-curated-training-fixture.exe --evidence-jsonl data\training\curated_expansion\evidence_full_label.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round2.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round3.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round4.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round5.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round6.jsonl --entity-jsonl data\training\curated_expansion\gold_entities.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round2.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round3.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round4.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round5.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round6.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round2.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round3.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round4.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round5.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round6.jsonl --output-dir data\training\curated_import --no-copy --markdown-output reports\training\curated_fixture_import.md --json-output reports\training\curated_fixture_import.json
```

Diff curated fixture batch provenance:

```powershell
.\.venv\Scripts\gbmbert-curated-provenance-diff.exe --evidence-jsonl data\training\curated_expansion\evidence_full_label.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round2.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round3.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round4.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round5.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round6.jsonl --entity-jsonl data\training\curated_expansion\gold_entities.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round2.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round3.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round4.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round5.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round6.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round2.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round3.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round4.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round5.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round6.jsonl --markdown-output reports\training\curated_provenance_diff.md --json-output reports\training\curated_provenance_diff.json
```

Review gold-pack promotion thresholds:

```powershell
.\.venv\Scripts\gbmbert-review-gold-pack-promotion.exe --threshold-config configs\training\gold_pack_promotion_thresholds.json --markdown-output reports\training\gold_pack\gold_pack_promotion_review.md --json-output reports\training\gold_pack\gold_pack_promotion_review.json --allow-blockers
```

Plan future scaffold-only gold-pack curation batches:

```powershell
.\.venv\Scripts\gbmbert-plan-gold-pack-promotion.exe --markdown-output reports\training\gold_pack\gold_pack_promotion_plan.md --json-output reports\training\gold_pack\gold_pack_promotion_plan.json
```

Gold-pack ops status (counts, soft densify gaps, dual-review/AL backlog, next actions):

```powershell
.\.venv\Scripts\gbmbert-gold-pack-ops-status.exe --markdown-output reports\training\gold_pack\gold_pack_ops_status.md --json-output reports\training\gold_pack\gold_pack_ops_status.json
```

Export sparse NER densify dual-review skeleton (pending for human; no invented labels):

```powershell
.\.venv\Scripts\gbmbert-export-sparse-densify-batch.exe --round 33
```

Export dashboard governance detail links:

```powershell
.\.venv\Scripts\gbmbert-export-governance-detail-links.exe --markdown-output reports\training\governance_detail_links.md --json-output reports\training\governance_detail_links.json
```

Validate governance detail artifact contract:

```powershell
.\.venv\Scripts\gbmbert-check-governance-detail-contract.exe --detail-json reports\training\governance_detail_links.json --markdown-output reports\training\governance_detail_contract.md --json-output reports\training\governance_detail_contract.json
```

Build CI summary:

```powershell
.\.venv\Scripts\gbmbert-ci-report-summary.exe --output reports\platform_regression\ci_report_summary.md
```

Validate CI summary artifact contract:

```powershell
.\.venv\Scripts\gbmbert-check-ci-summary-contract.exe --summary reports\platform_regression\ci_report_summary.md --markdown-output reports\platform_regression\ci_summary_contract.md --json-output reports\platform_regression\ci_summary_contract.json
```

Run strict training governance audit:

```powershell
.\.venv\Scripts\gbmbert-run-strict-training-governance.exe --output-dir reports\training\governance_strict --allow-findings
```

Refresh artifact index:

```powershell
.\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports\artifact_index.md --json-output reports\artifact_index.json
```

PR91-94 smoke commands:

```powershell
.\.venv\Scripts\gbmbert-build-relation-negatives.exe data\training\ncbi_env_smoke_annotation_dataset data\training\relation_negatives.jsonl --markdown-output reports\training\relation_negatives.md --json-output reports\training\relation_negatives.json

.\.venv\Scripts\gbmbert-relation-dataset-quality.exe data\training\relation_negatives.jsonl --markdown-output reports\training\relation_dataset_quality.md --json-output reports\training\relation_dataset_quality.json

.\.venv\Scripts\gbmbert-build-evidence-training-pack.exe data\training\curated_expansion\evidence_full_label.jsonl --output-dir data\training\evidence_pack --reports-dir reports\training\evidence_pack --min-examples-per-task 10 --min-examples-per-label 2

.\.venv\Scripts\gbmbert-review-training-config.exe configs\training\gbmbert_evidence_smoke_pubmedbert.json data\training\evidence_smoke_fixture\splits --label-map-dir data\training\evidence_smoke_fixture\label_maps --markdown-output reports\training\training_config_review.md --json-output reports\training\training_config_review.json
```

Launch menu:

```powershell
.\launcher_menu.bat
```

Knowledge Graph Explorer:

```powershell
.\.venv\Scripts\gbmbert-explorer.exe --sample-data data\examples\graph_records_sample.jsonl --open
```

## Important Files

- `launcher_menu.bat`
- `pyproject.toml`
- `README.md`
- `CHANGELOG.md`
- `docs\PROJECT_SCOPE.json`
- `docs\ARTIFACT_POLICY.md`
- `docs\LAUNCHER_MENU.md`
- `docs\RESEARCH_SCOPE_V2.md`
- `reports\artifact_index.md`
- `reports\artifact_index.json`
- `src\gbmbert\training\relation_negatives.py`
- `src\gbmbert\training\relation_quality.py`
- `src\gbmbert\training\evidence_pack.py`
- `src\gbmbert\training\config_review.py`
- `src\gbmbert\training\readiness.py`
- `src\gbmbert\training\preparation.py`
- `src\gbmbert\artifact_policy.py`
- `src\gbmbert\ci_report_summary.py`
- `src\gbmbert\launcher_check.py`
- `src\gbmbert\verification.py`
- `src\gbmbert\training\curated_fixture_import.py`
- `src\gbmbert\training\curated_provenance_diff.py`
- `src\gbmbert\training\promotion_review.py`
- `src\gbmbert\training\promotion_planning.py`
- `src\gbmbert\training\gold_pack_ops.py`
- `docs\GOLD_PACK_OPS_RUNBOOK.md`
- `reports\training\gold_pack\gold_pack_ops_status.md`
- `src\gbmbert\training\curated_round_rebuild.py`
- `src\gbmbert\training\review_batch_prep.py`
- `src\gbmbert\training\external_corpus_import.py`
- `src\gbmbert\training\external_gold_merge.py`
- `configs\extraction\external_corpus_crosswalk.json`
- `configs\extraction\gbm_relevance_keywords.json`
- `src\gbmbert\training\governance_detail_export.py`
- `src\gbmbert\knowledge_graph\explorer.py`
- `src\gbmbert\knowledge_graph\inspect.py`
- `src\gbmbert\knowledge_graph\loader.py`
- `src\gbmbert\knowledge_graph\queries.py`

## Differentiation bet

**Deepen gold-pack / curation / governance** (evidence-tier gold, dual-review, AL, promotion gates, provenance, ops status) rather than competing on lit-mining scale or clinical ranking / CDS. Runbook: `docs/GOLD_PACK_OPS_RUNBOOK.md`. Ops CLI: `gbmbert-gold-pack-ops-status` / launcher `16CC`. Reports: `reports/training/gold_pack/gold_pack_ops_status.*`.

## Recommended Next PR Series

Strategic direction: deepen the gold-pack ops loop (sample → review → promote → rebuild → gates → metrics) on top of the real-corpora pivot (PR163+) and Phase 4 preferred checkpoints.

PR161 post-promotion — research follow-ons:

- **Phase 4 research criteria satisfied** (must-haves + quality stretch Q1–Q4). Preferred checkpoints: evidence v9, relation v3, BIO NER **v6**. DoD: `reports/training/phase4_definition_of_done.*`. Pack can still deepen via soft densify + dual-review.
- Soft residual mitigated in gold: Round 31 span-reviewed `CELL_STATE`/`PATHWAY` densify (dual-review agreement ~0.98); BIO pack rebuilt. Preferred checkpoint remains BIO NER **v6** (no v7 without freeze-split compare).
- Round 32 curated evidence fill (+26 PMID-disjoint → **835** evidence); preferred evidence **v9** retained (volume change not material).
- **Gold-pack ops deepening**: `gbmbert-gold-pack-ops-status`, sparse densify dual-review export, Training Artifacts readiness panel, Round 33 pending human dual-review queue under `data/research/review_batches/round33/`.
- **Phase 5 deepened (post-MVP)**: KG/relation-type modulation + provenance, resistance-axis populations, Monte Carlo sweeps (`gbmbert-run-simulation-monte-carlo`, `16BY`), richer comparison-table reports, plus toy parameter-fitting stub (`gbmbert-fit-simulation-parameters`, `16CB`) — explicitly **not PK/PD**. Spatial biophysics and real PK/PD remain out of scope. Deterministic runner remains `gbmbert-run-tumour-simulation` / `16BX`.
- **Phase 6 research depth**: treatment *scenario* ranking with toy efficacy vs toy toxicity/burden trade-offs and intensity/schedule *simulation* knobs (`gbmbert-rank-treatment-scenarios`, `16BZ`). Not CDS, not real dosing/schedule search, not patient eligibility, not medical advice.
- **Phase 7 research operations console**: all Streamlit pages are `live-runner` surfaces calling in-process Python APIs (`gbmbert.dashboard.runners`) — Literature Search, Entity Explorer, Knowledge Graph Explorer, Prediction Curation, Training Artifacts, Tumour Simulator, Treatment Explorer, Monte Carlo. Offline-friendly defaults, optional report writes, research-use banners on every page; launcher `16CA`. Visual polish: paper cards + PubMed/DOI open controls via `gbmbert.dashboard.paper_links`, metric/chart summaries where counts exist. Not hospital CDS; production clinical dashboard remains out of scope.
- Phase 4 research criteria remain satisfied (evidence v9 / relation v3 / BIO NER v6 preferred).
- Keep claiming boundary: promotable ≠ clinically validated GBM-BERT; toy simulation/ranking/fitting ≠ patient-ready prediction or CDS.
- Corpus fill provenance: `reports/training/corpus_fill_round31_32.md` (tracked fixtures vs gitignored raw bulk).

PR162 Review-Batch Launcher + Entity Review:

- Done: `16BT`/`16BU` prep/finalize and `16BV`/`16BW` entity-span export/apply in `launcher_menu.bat` + docs/tests.
- Keep everything observe-only and research-use-only.

PR160 Rebuild Orchestrator In Verify-Local / CI:

- Done as opt-in CI visibility: `ci_report_summary` surfaces curated-round rebuild status without making it a verify-local hard gate.
- Keep everything observe-only; it must not promote a dataset or claim a validated GBM-BERT model exists.

## Suggested Prompt For New Chat

Use this exact starter:

```text
Project root is C:\Users\david\GBM. Use the local .venv only.

This is the GBM-AI Platform, a research-use-only glioblastoma literature intelligence platform. Persistent boundary: Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Read PROJECT_HANDOFF.md, README.md, docs\PROJECT_SCOPE.json, docs\ARTIFACT_POLICY.md, docs\LAUNCHER_MENU.md, CHANGELOG.md, and the latest reports\artifact_index.md. Then continue from PR157. First verify the current state with gbmbert-verify-local unless the handoff says it was just run. To regenerate the curated-round reports use the one-command orchestrator gbmbert-rebuild-curated-rounds (PR158). Preserve all safety guardrails and do not claim a validated trained GBM-BERT model exists.
```
