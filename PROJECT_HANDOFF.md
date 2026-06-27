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

## Recently Implemented PR111-134

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

## Latest Verification

Last verified from `C:\Users\david\GBM` using the project `.venv`:

```powershell
.\.venv\Scripts\gbmbert-review-training-config-suite.exe --markdown-output reports\training\training_config_suite_review.md --json-output reports\training\training_config_suite_review.json
.\.venv\Scripts\gbmbert-run-training-governance-suite.exe --output-dir reports\training\governance
.\.venv\Scripts\gbmbert-run-strict-training-governance.exe --output-dir reports\training\governance_strict --allow-findings
.\.venv\Scripts\gbmbert-verify-local.exe
.\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports\artifact_index.md --json-output reports\artifact_index.json
```

Results:

- Tests: `212 passed`
- `pip check`: no broken requirements
- Scope drift monitor: safe, 0 findings
- Platform regression: passed
- Artifact policy: safe, 0 findings
- Artifact index refreshed: 467 artifacts
- Default training governance suite: passed, 10/10, no blocking warnings
- Strict training governance audit: ran with `--allow-findings`; scaffold findings remain visible for unpromoted full-label evidence coverage
- Label drift: 0 warnings, using config-specific governance datasets
- Launcher menu check: safe, 0 findings
- Gold-pack promotion review: not promotable; current fixture is below promotion thresholds
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
.\.venv\Scripts\gbmbert-import-curated-training-fixture.exe --evidence-jsonl data\training\curated_expansion\evidence_full_label.jsonl --entity-jsonl data\training\curated_expansion\gold_entities.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue.jsonl --output-dir data\training\curated_import --no-copy --markdown-output reports\training\curated_fixture_import.md --json-output reports\training\curated_fixture_import.json
```

Review gold-pack promotion thresholds:

```powershell
.\.venv\Scripts\gbmbert-review-gold-pack-promotion.exe --markdown-output reports\training\gold_pack\gold_pack_promotion_review.md --json-output reports\training\gold_pack\gold_pack_promotion_review.json --allow-blockers
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
- `src\gbmbert\launcher_check.py`
- `src\gbmbert\verification.py`
- `src\gbmbert\training\curated_fixture_import.py`
- `src\gbmbert\training\promotion_review.py`
- `src\gbmbert\knowledge_graph\explorer.py`
- `src\gbmbert\knowledge_graph\inspect.py`
- `src\gbmbert\knowledge_graph\loader.py`
- `src\gbmbert\knowledge_graph\queries.py`

## Recommended Next PR Series

PR135 Curated Import Batch Scaling:

- Add support for validating multiple curated fixture files in one import manifest.
- Keep source PMID and review metadata mandatory.

PR136 Promotion Threshold Configuration:

- Move gold-pack promotion thresholds into a config file so thresholds are reviewable without code edits.

PR137 CI Report Summary:

- Add a compact Markdown summary to GitHub Actions output in addition to uploaded artifacts.

PR138 Governance Dashboard Refresh:

- Surface label drift, launcher check, curated import, and promotion-review state in the dashboard training context.

PR139 Larger Gold-Pack Curation Round:

- Use the curated fixture importer for the next reviewed batch and rebuild evidence, NER, and relation packs.

## Suggested Prompt For New Chat

Use this exact starter:

```text
Project root is C:\Users\david\GBM. Use the local .venv only.

This is the GBM-AI Platform, a research-use-only glioblastoma literature intelligence platform. Persistent boundary: Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Read PROJECT_HANDOFF.md, README.md, docs\PROJECT_SCOPE.json, docs\ARTIFACT_POLICY.md, docs\LAUNCHER_MENU.md, CHANGELOG.md, and the latest reports\artifact_index.md. Then continue from PR135. First verify the current state with gbmbert-verify-local unless the handoff says it was just run. Preserve all safety guardrails and do not claim a validated trained GBM-BERT model exists.
```
