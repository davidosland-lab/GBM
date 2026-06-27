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

## Recently Implemented PR91-94

PR91 Relation Negative Sampler:

- Added `gbmbert-build-relation-negatives`
- Module: `src\gbmbert\training\relation_negatives.py`
- Builds deterministic synthetic `NO_RELATION` examples from observed relation endpoints in the same source sentence.
- Smoke output:
  - `data\training\relation_negatives.jsonl`
  - `reports\training\relation_negatives.md`
  - `reports\training\relation_negatives.json`

PR92 Relation Dataset Quality v2:

- Added `gbmbert-relation-dataset-quality`
- Module: `src\gbmbert\training\relation_quality.py`
- Reports positive/negative counts, missing sentence/text, missing endpoints, identical endpoint pairs, duplicate examples, label counts, and warnings.
- Smoke output:
  - `reports\training\relation_dataset_quality.md`
  - `reports\training\relation_dataset_quality.json`

PR93 Evidence-Only Training Pack:

- Added `gbmbert-build-evidence-training-pack`
- Module: `src\gbmbert\training\evidence_pack.py`
- Builds an evidence-only pack with annotation dataset, repaired dataset, PMID-safe splits, label maps, dataset card, baseline report, and evidence-only readiness report.
- Extended `gbmbert-training-readiness-report` with repeatable `--task` filtering while preserving default all-task behavior.
- Smoke output:
  - `data\training\evidence_pack\annotation_dataset`
  - `data\training\evidence_pack\annotation_dataset_repaired`
  - `data\training\evidence_pack\annotation_splits`
  - `data\training\evidence_pack\label_maps`
  - `reports\training\evidence_pack\*`

PR94 Training Config Review Gate:

- Added `gbmbert-review-training-config`
- Module: `src\gbmbert\training\config_review.py`
- Checks training config validity, prepared splits, label coverage, optional label map coverage, hyperparameter review bounds, training-enabled confirmation, and research boundary warnings.
- Smoke output:
  - `reports\training\training_config_review.md`
  - `reports\training\training_config_review.json`

Also updated:

- `pyproject.toml` console scripts
- `README.md` command documentation
- `launcher_menu.bat` options `16AY` through `16BB`
- `docs\PROJECT_SCOPE.json`
- `src\gbmbert\artifacts.py`
- Tests for PR91-94, launcher wiring, scope lockfile, and artifact taxonomy

## Latest Verification

Last verified from `C:\Users\david\GBM` using the project `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\gbmbert-scope-drift-monitor.exe --markdown-output reports\platform_regression\scope_drift.md --json-output reports\platform_regression\scope_drift.json
.\.venv\Scripts\gbmbert-platform-regression.exe --skip-tests --skip-pip-check
.\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports\artifact_index.md --json-output reports\artifact_index.json
```

Results:

- Tests: `186 passed`
- `pip check`: no broken requirements
- Scope drift monitor: safe, 0 findings
- Platform regression: passed, 7/7
- Artifact index refreshed: 348 artifacts

One expected warning: `gbmbert-relation-dataset-quality` was smoke-tested on the generated negatives-only file, so it correctly warned that no positive relation examples were present in that specific file.

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

Refresh artifact index:

```powershell
.\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports\artifact_index.md --json-output reports\artifact_index.json
```

PR91-94 smoke commands:

```powershell
.\.venv\Scripts\gbmbert-build-relation-negatives.exe data\training\ncbi_env_smoke_annotation_dataset data\training\relation_negatives.jsonl --markdown-output reports\training\relation_negatives.md --json-output reports\training\relation_negatives.json

.\.venv\Scripts\gbmbert-relation-dataset-quality.exe data\training\relation_negatives.jsonl --markdown-output reports\training\relation_dataset_quality.md --json-output reports\training\relation_dataset_quality.json

.\.venv\Scripts\gbmbert-build-evidence-training-pack.exe data\training\ncbi_env_smoke_annotation_dataset --output-dir data\training\evidence_pack --reports-dir reports\training\evidence_pack --min-examples-per-task 1 --min-examples-per-label 1 --allow-not-ready

.\.venv\Scripts\gbmbert-review-training-config.exe configs\training\gbmbert_evidence_pubmedbert.json data\training\evidence_pack\annotation_splits --label-map-dir data\training\evidence_pack\label_maps --markdown-output reports\training\training_config_review.md --json-output reports\training\training_config_review.json
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
- `docs\PROJECT_SCOPE.json`
- `docs\RESEARCH_SCOPE_V2.md`
- `reports\artifact_index.md`
- `reports\artifact_index.json`
- `src\gbmbert\training\relation_negatives.py`
- `src\gbmbert\training\relation_quality.py`
- `src\gbmbert\training\evidence_pack.py`
- `src\gbmbert\training\config_review.py`
- `src\gbmbert\training\readiness.py`
- `src\gbmbert\training\preparation.py`
- `src\gbmbert\knowledge_graph\explorer.py`
- `src\gbmbert\knowledge_graph\inspect.py`
- `src\gbmbert\knowledge_graph\loader.py`
- `src\gbmbert\knowledge_graph\queries.py`

## Recommended Next PR Series

PR95 Relation Pack Merger:

- Merge positive relation examples and synthetic `NO_RELATION` examples into a single relation training dataset.
- Preserve provenance fields showing which rows are human/curated versus synthetic.
- Add quality checks that relation training packs include both positives and negatives.

PR96 Relation Training Pack Builder:

- Build a relation-only training pack with PMID-safe splits, label maps, dataset card, baseline report, readiness report, and relation-specific quality report.
- Should mirror the evidence-only pack pattern.

PR97 Relation Config Review Gate:

- Extend config review smoke coverage for `relation_extraction` configs.
- Confirm relation split files and relation label maps align with config labels.
- Keep execution gated; no claim of validated relation model.

PR98 Training Pack Comparison Report:

- Compare evidence, relation, and gold packs side by side.
- Report row counts, label coverage, warnings, leakage, and readiness status.
- Useful before any real fine-tuning.

PR99 Model Registry Audit:

- Audit checkpoint registry records for missing model cards, missing dataset cards, stale paths, unsafe statuses, or missing research warnings.
- Should help prevent accidental overclaiming.

PR100 Dashboard Training Artifacts Page:

- Add a Streamlit dashboard page for training artifacts: packs, readiness reports, config reviews, model cards, and checkpoint registry status.
- Keep it read-only and research-scaffold oriented.

## Suggested Prompt For New Chat

Use this exact starter:

```text
Project root is C:\Users\david\GBM. Use the local .venv only.

This is the GBM-AI Platform, a research-use-only glioblastoma literature intelligence platform. Persistent boundary: Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Read PROJECT_HANDOFF.md, README.md, docs\PROJECT_SCOPE.json, and the latest reports\artifact_index.md. Then continue from PR95. First verify the current state with pytest, pip check, scope drift monitor, and platform regression unless the handoff says they were just run. Preserve all safety guardrails and do not claim a validated trained GBM-BERT model exists.
```
