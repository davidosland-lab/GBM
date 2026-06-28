# GBM-AI Platform Handoff

Project root:

`C:\Users\david\GBM`

Use this as the canonical project folder. The local virtual environment is:

`C:\Users\david\GBM\.venv`

Do not install dependencies globally. Use the project `.venv`.

## Persistent Safety Boundary

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

The platform is a research-use-only glioblastoma literature intelligence system for literature mining, structured biomedical annotation, knowledge graph construction, curation workflows, and in-silico hypothesis generation scaffolding.

Current non-goals:

- Patient-specific treatment recommendations
- Clinical decision support
- Predictive clinical accuracy claims
- Production clinical dashboard
- Claiming that a validated trained GBM-BERT model exists
- Tumour simulator
- Treatment optimizer

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
- Streamlit dashboard shell
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

- Tests: `238 passed`
- `pip check`: no broken requirements
- Scope drift monitor: safe, 0 findings
- Platform regression: passed
- Canonical local verification: passed, 8/8 steps
- Curated round rebuild orchestrator: passed, 7 rounds, 20/20 steps, 0 warnings
- Artifact policy: safe, 0 findings
- Artifact index refreshed: 502 artifacts
- Default training governance suite: passed, 10/10, no blocking warnings
- Strict training governance audit: ran with `--allow-findings`; scaffold findings remain visible for unpromoted full-label evidence coverage
- Label drift: 0 warnings, using config-specific governance datasets
- Launcher menu check: safe, 0 findings
- CI report summary: tracked at `reports\platform_regression\ci_report_summary.md`; includes the Governance detail contract row; CI summary contract valid
- Curated fixture import: safe, 48 evidence rows, 96 entity rows, 96 reviewed queue rows, 42 source PMIDs
- Curated provenance diff: safe across seven rounds, 240 observations, 42 source PMIDs, 0 duplicate/changed/withdrawn findings
- Governance detail export: required rows visible; missing report rows visible for review
- Governance detail contract: valid, all required rows visible
- Gold-pack promotion review: not promotable; current fixture has 48 evidence, 96 NER, 48 relation examples and 42 source PMIDs, below promotion thresholds
- Promotion planning report: scaffold-only, 13 suggested future curation batches from the current deltas, with per-task label-balance/task-volume relationship and delta-coverage view (overall label-floor coverage 14.8%)
- Training config suite: 5 configs, 3 current passed, 0 current failed, 2 scaffold configs
- Model registry audit: passed, 1 checkpoint, 0 findings

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
- `src\gbmbert\training\curated_round_rebuild.py`
- `src\gbmbert\training\governance_detail_export.py`
- `src\gbmbert\knowledge_graph\explorer.py`
- `src\gbmbert\knowledge_graph\inspect.py`
- `src\gbmbert\knowledge_graph\loader.py`
- `src\gbmbert\knowledge_graph\queries.py`

## Recommended Next PR Series

PR161 Eighth Curated Expansion Round:

- Add an eighth reviewed fixture batch (six new source PMIDs) toward promotion thresholds (target 54 evidence / 108 NER / 54 relation, 48 source PMIDs).
- Add the round-eight trio under `data\training\curated_expansion`, then regenerate everything with `gbmbert-rebuild-curated-rounds` (PR158) followed by `gbmbert-verify-local` and the CI summary. No multi-step chain or launcher edits needed for the orchestrator path.

PR160 Rebuild Orchestrator In Verify-Local / CI:

- Optional: surface the `curated_round_rebuild` report state in the CI summary or wire an opt-in rebuild step ahead of verification, keeping platform verification and the curated-data rebuild cleanly separated.
- Keep everything observe-only; it must not promote a dataset or claim a validated GBM-BERT model exists.

## Suggested Prompt For New Chat

Use this exact starter:

```text
Project root is C:\Users\david\GBM. Use the local .venv only.

This is the GBM-AI Platform, a research-use-only glioblastoma literature intelligence platform. Persistent boundary: Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Read PROJECT_HANDOFF.md, README.md, docs\PROJECT_SCOPE.json, docs\ARTIFACT_POLICY.md, docs\LAUNCHER_MENU.md, CHANGELOG.md, and the latest reports\artifact_index.md. Then continue from PR157. First verify the current state with gbmbert-verify-local unless the handoff says it was just run. To regenerate the curated-round reports use the one-command orchestrator gbmbert-rebuild-curated-rounds (PR158). Preserve all safety guardrails and do not claim a validated trained GBM-BERT model exists.
```
