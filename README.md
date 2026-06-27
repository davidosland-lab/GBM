# GBM-AI Platform

Glioblastoma research intelligence platform for literature ingestion, structured biomedical annotation, and downstream research workflows.

> Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This repository currently implements the Phase 1-3 research scaffold plus a local Knowledge Graph Explorer prototype:

- PubMed search and record ingestion through NCBI E-utilities.
- Curated PubMed query packs for original and expanded GBM literature backfills.
- Read-only ClinicalTrials.gov v2 registry ingestion.
- ClinicalTrials.gov-to-graph registry record export.
- Trial graph-record Neo4j loader support.
- Corpus manifest generation with SHA256 artifact hashes.
- Standardized local artifact directories and enriched artifact index reports with hashes, timestamps, and artifact types.
- JSONL persistence for literature records.
- Basic text cleaning utilities.
- Pydantic schemas for papers, entities, relations, and evidence claims.
- Baseline biomedical named entity extraction over PubMed JSONL.
- Configurable deterministic GBM lexicon extraction for offline smoke baselines.
- Transparent placeholder evidence-tier classification.
- Conservative rule-based relation extraction.
- End-to-end PubMed-to-graph pipeline CLI with dry-run graph-record validation.
- Pre-load PubMed, trial, and unified graph quality reports in Markdown and JSON.
- Evidence and relation review queue export for low-confidence items.
- Review queue summary reports for curation planning.
- Reviewed queue scaffold creation for manual curation without overwriting raw queue exports.
- Reviewed queue resolution summaries for pending, accepted, corrected, and rejected items.
- Curated graph export and curation diff reports from reviewed queue decisions.
- Annotation dataset export and dataset quality reports for future GBM-BERT training.
- GBM-BERT dataset splitting, label maps, dataset cards, baseline reports, experiment manifests, and checkpoint registry metadata.
- GBM-BERT gated training runner scaffold, Hugging Face dataset loaders, and task-aware tokenization preparation.
- GBM-BERT evidence-classifier training execution with evaluation metrics, run manifests, and registry integration.
- GBM-BERT research batch scoring, model-card generation, and no-download training smoke fixture.
- GBM-BERT prediction review queues, active learning candidate exports, reviewed CSV import, curation summaries, quality/audit reports, curated evidence exports, overlay diffs, load guards, and graph evidence-tier overlays.
- Local environment preflight checks.
- Neo4j-oriented knowledge graph schema, loader, query helpers, and read-only inspection.
- Dry-run graph load reports in Markdown and JSON.
- Graph-record provenance audit reports for PubMed PMID and ClinicalTrials.gov NCT traceability.
- Reproducible smoke baseline rebuild command for local handoff artifacts.
- Local Knowledge Graph Explorer prototype for sample JSONL, artifact-index-selected JSONL, or Neo4j-backed graph review.
- GBM-BERT fine-tuning scaffold with dry-run training plans and dataset adapters.
- Streamlit dashboard shell with the required research-use warning on every page.

The project must not be used to recommend treatment for a real patient, generate clinical instructions, present itself as a medical device, or claim predictive clinical accuracy.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set `NCBI_EMAIL`. An NCBI API key is optional but recommended for higher rate limits.

Run a local preflight check:

```powershell
gbmbert-preflight --markdown-output reports/preflight.md --json-output reports/preflight.json
```

## PubMed Ingestion

```python
from gbmbert.ingest.pubmed import fetch_pubmed_records, save_jsonl, search_pubmed

pmids = search_pubmed("glioblastoma MGMT methylation temozolomide", retmax=10)
records = fetch_pubmed_records(pmids)
save_jsonl(records, "data/raw/pubmed_gbm.jsonl")
```

Run a curated PubMed query pack:

```powershell
gbmbert-search-pubmed --query-pack pubmed_gbm_v1 --retmax-per-query 10 --output data/raw/pubmed_gbm_v1.jsonl
gbmbert-search-pubmed --query-pack pubmed_gbm_v2 --retmax-per-query 10 --output data/raw/pubmed_gbm_v2.jsonl
```

Query pack JSON files live under `data/query_packs/`.

The first small real corpus snapshot lives at `reports/corpus/pubmed_small_snapshot_2026-06-23.md`, with raw PubMed JSONL under `data/raw/`.

## Clinical Trial Registry Ingestion

ClinicalTrials.gov ingestion is read-only and descriptive. It records registry metadata such as NCT ID, title, status, phase, conditions, interventions, sponsor, update date, and source URL; it does not interpret trial suitability or recommend enrollment.

```powershell
gbmbert-search-trials --condition glioblastoma --max-records 50 --output data/raw/clinicaltrials_gbm.jsonl
```

Convert normalized registry records into trial graph-record JSONL:

```powershell
gbmbert-build-trial-graph-records data/raw/clinicaltrials_gbm.jsonl data/processed/trial_graph_records.jsonl
```

The trial graph-record format preserves NCT ID provenance and creates descriptive `Trial`, `Disease`, and `Treatment` nodes with `ASSOCIATED_WITH` registry relations. It does not turn trial metadata into patient-specific recommendations.

The first tiny real ClinicalTrials.gov smoke snapshot lives at:

- `data/raw/clinicaltrials_gbm_smoke_2026-06-23.jsonl`
- `data/processed/clinicaltrials_gbm_smoke_2026-06-23/trial_graph_records.jsonl`
- `reports/graph/clinicaltrials_gbm_smoke_quality.md`
- `reports/graph/clinicaltrials_gbm_smoke_load_report.md`
- `reports/corpus/clinicaltrials_gbm_smoke_manifest.md`

## Corpus Manifests

Generate a reproducibility manifest for one or more corpus artifacts:

```powershell
gbmbert-build-corpus-manifest data/raw/pubmed_gbm_v1.jsonl --name pubmed_gbm_v1 --query-pack pubmed_gbm_v1 --source PubMed --output reports/corpus/pubmed_gbm_v1_manifest.json --markdown-output reports/corpus/pubmed_gbm_v1_manifest.md
```

Manifests include exact paths, line counts, SHA256 hashes, generation time, command metadata, and whether NCBI credentials are configured. They never write the email address or API key.

Build an index of local artifacts:

```powershell
gbmbert-artifact-index --markdown-output reports/artifact_index.md --json-output reports/artifact_index.json
```

The artifact index classifies local outputs such as raw PubMed JSONL, ClinicalTrials.gov JSONL, entity/evidence files, graph records, review queues, manifests, quality reports, and load reports. It includes SHA256 hashes and modified timestamps for handoff review.

## Testing

```powershell
pytest
```

## Scope Addenda

- `docs/RESEARCH_SCOPE_V2.md` extends the project vocabulary and graph schema with focused-ultrasound delivery modifiers, IDH-mutant therapy vocabulary, oncolytic virotherapy, CSF1R/myeloid biology, Neftel cell states, and related safety guardrails.
- `docs/PROJECT_SCOPE.json` is the current scope lockfile. It records active phases, future phases, required safety language, prohibited product behavior, and implemented modules.

## Entity Extraction

The baseline NER pipeline uses Hugging Face `pipeline("ner", aggregation_strategy="simple")` with `d4data/biomedical-ner-all` by default.

```powershell
gbmbert-extract-entities data/raw/pubmed_gbm.jsonl data/processed/entities.jsonl
```

For deterministic offline smoke runs, use the checked-in GBM lexicon config:

```powershell
gbmbert-run-pipeline data/raw/pubmed_gbm.jsonl --output-dir data/processed/pubmed_gbm_pipeline --entity-mode lexicon --lexicon configs/extraction/lexicon_gbm_v1.json
```

The output JSONL contains one record per PMID:

```json
{"pmid":"12345678","entities":[{"text":"MGMT","label":"GENE","start":0,"end":4,"confidence":0.92,"normalized_text":"MGMT"}]}
```

## Evidence Classification

The current evidence classifier is a transparent rule-based placeholder. It provides the interface and JSONL shape that future GBM-BERT evidence classification can replace.

```powershell
gbmbert-classify-evidence data/raw/pubmed_gbm.jsonl data/processed/evidence_claims.jsonl
```

Export low-confidence evidence claims and uncertain graph relations for human review:

```powershell
gbmbert-export-review-queue --evidence-jsonl data/processed/evidence_claims.jsonl --graph-jsonl data/processed/graph_records.jsonl --output data/review/evidence_review_queue.jsonl --csv-output data/review/evidence_review_queue.csv
```

The review queue is an audit artifact for research curation. It does not modify source records.

Summarize a review queue for curation planning:

```powershell
gbmbert-review-queue-summary data/review/evidence_review_queue.jsonl --markdown-output reports/review/evidence_review_summary.md --json-output reports/review/evidence_review_summary.json
```

Initialize a separate reviewed queue scaffold for manual curation. This preserves the raw queue and adds review fields such as status, reviewer, notes, and corrected relation/evidence fields:

```powershell
gbmbert-init-reviewed-queue data/review/evidence_review_queue.jsonl data/review/evidence_reviewed_queue.jsonl --csv-output data/review/evidence_reviewed_queue.csv --reviewer curator
```

Summarize a reviewed queue after manual curation:

```powershell
gbmbert-reviewed-queue-summary data/review/evidence_reviewed_queue.jsonl --markdown-output reports/review/evidence_reviewed_summary.md --json-output reports/review/evidence_reviewed_summary.json
```

Export a separate curated graph artifact from reviewed graph-relation decisions. Raw graph records are not modified:

```powershell
gbmbert-export-curated-graph data/processed/graph_records.jsonl data/review/evidence_reviewed_queue.jsonl data/processed/curated_graph_records.jsonl --report-markdown-output reports/review/curation_diff.md --report-json-output reports/review/curation_diff.json
```

Build or refresh a curation diff report:

```powershell
gbmbert-curation-diff data/processed/graph_records.jsonl data/processed/curated_graph_records.jsonl data/review/evidence_reviewed_queue.jsonl --markdown-output reports/review/curation_diff.md --json-output reports/review/curation_diff.json
```

## GBM-BERT Training Scaffold

Training configs live under `configs/training/`. The current CLI validates a config and builds a dry-run plan without downloading model weights or running optimization.

```powershell
gbmbert-training-plan configs/training/gbmbert_ner_pubmedbert.json --json
```

The scaffold only supports approved pretrained biomedical base models such as PubMedBERT and BioBERT. It does not train from scratch.

Export reviewed annotations into simple JSONL datasets for future GBM-BERT tasks:

```powershell
gbmbert-export-annotation-dataset data/review/evidence_reviewed_queue.jsonl data/training/annotation_dataset --entity-jsonl data/processed/entities.jsonl --summary-json-output reports/training/annotation_dataset_manifest.json
```

Audit exported dataset quality before training:

```powershell
gbmbert-annotation-dataset-quality data/training/annotation_dataset --markdown-output reports/training/annotation_dataset_quality.md --json-output reports/training/annotation_dataset_quality.json
```

Build a conservative gold seed dataset from accepted/corrected reviewed queues:

```powershell
gbmbert-build-gold-seed-dataset data/training/gold_seed --reviewed-queue-jsonl data/review/evidence_reviewed_queue.jsonl --prediction-reviewed-queue-jsonl data/review/evidence_prediction_reviewed_queue.jsonl --entity-jsonl data/processed/entities.jsonl --json-output reports/training/gold_seed_manifest.json --markdown-output reports/training/gold_seed_manifest.md
```

Compare multiple reviewed annotation passes for adjudication conflicts:

```powershell
gbmbert-adjudication-report data/review/reviewer_a_reviewed_queue.jsonl data/review/reviewer_b_reviewed_queue.jsonl --markdown-output reports/review/adjudication_report.md --json-output reports/review/adjudication_report.json
```

Prepare deterministic train/validation/test splits:

```powershell
gbmbert-split-annotation-dataset data/training/annotation_dataset data/training/annotation_splits
```

Prepare source-PMID-safe splits so no PMID appears in more than one train/validation/test split:

```powershell
gbmbert-split-by-pmid data/training/annotation_dataset data/training/annotation_splits_pmid --markdown-output reports/training/pmid_split_manifest.md --json-output reports/training/pmid_split_manifest.json
```

Repair evidence rows whose label can be recovered from evidence-tier fields:

```powershell
gbmbert-repair-evidence-labels data/training/annotation_dataset data/training/annotation_dataset_repaired --markdown-output reports/training/evidence_label_repair.md --json-output reports/training/evidence_label_repair.json
```

Build label maps for NER, evidence classification, and relation extraction:

```powershell
gbmbert-build-label-maps data/training/annotation_splits data/training/label_maps
```

Build a dataset card and majority-label baseline report:

```powershell
gbmbert-build-dataset-card data/training/annotation_splits --markdown-output reports/training/dataset_card.md --json-output reports/training/dataset_card.json
gbmbert-baseline-report data/training/annotation_splits --markdown-output reports/training/baseline_report.md --json-output reports/training/baseline_report.json
```

Gate datasets for real GBM-BERT training readiness:

```powershell
gbmbert-training-readiness-report data/training/annotation_splits --markdown-output reports/training/training_readiness.md --json-output reports/training/training_readiness.json
```

Build a full local gold training pack from reviewed curation artifacts. The pack runs gold-seed export, evidence-label repair, PMID-safe splitting, label maps, dataset card, baseline report, and readiness checks; it still does not claim clinical or model readiness:

```powershell
gbmbert-build-gold-training-pack --prediction-reviewed-queue-jsonl data/review/sample_graph_prediction_reviewed_queue.jsonl --output-dir data/training/gold_pack --reports-dir reports/training/gold_pack --allow-not-ready
```

Build synthetic relation negatives and audit relation dataset quality:

```powershell
gbmbert-build-relation-negatives data/training/annotation_dataset data/training/relation_negatives.jsonl --markdown-output reports/training/relation_negatives.md --json-output reports/training/relation_negatives.json
gbmbert-merge-relation-pack data/training/annotation_dataset data/training/relation_negatives.jsonl data/training/relation_training_pack.jsonl --markdown-output reports/training/relation_training_pack.md --json-output reports/training/relation_training_pack.json
gbmbert-relation-dataset-quality data/training/relation_training_pack.jsonl --markdown-output reports/training/relation_dataset_quality.md --json-output reports/training/relation_dataset_quality.json
```

Build a relation-only training pack, review its relation config, compare packs, and audit registry metadata:

```powershell
gbmbert-build-relation-training-pack data/training/relation_training_pack.jsonl --output-dir data/training/relation_pack --reports-dir reports/training/relation_pack --allow-not-ready
gbmbert-review-training-config configs/training/gbmbert_relation_biobert.json data/training/relation_pack/annotation_splits --label-map-dir data/training/relation_pack/label_maps --markdown-output reports/training/relation_training_config_review.md --json-output reports/training/relation_training_config_review.json
gbmbert-compare-training-packs --markdown-output reports/training/training_pack_comparison.md --json-output reports/training/training_pack_comparison.json
gbmbert-audit-model-registry models/checkpoint_registry.json --markdown-output reports/training/model_registry_audit.md --json-output reports/training/model_registry_audit.json --allow-findings
```

Run the training artifact governance reports. These commands remain read-only/report-only and do not execute model training:

```powershell
gbmbert-build-training-artifact-bundle --output-dir data/processed/training_artifact_bundle
gbmbert-search-training-artifacts relation_pack --markdown-output reports/training/training_artifact_search.md --json-output reports/training/training_artifact_search.json
gbmbert-audit-training-pack-leakage --markdown-output reports/training/training_pack_leakage_audit.md --json-output reports/training/training_pack_leakage_audit.json --allow-warnings
gbmbert-review-training-config-suite --markdown-output reports/training/training_config_suite_review.md --json-output reports/training/training_config_suite_review.json --allow-failed
gbmbert-plan-registry-remediation --markdown-output reports/training/model_registry_remediation_plan.md --json-output reports/training/model_registry_remediation_plan.json
gbmbert-training-label-drift --markdown-output reports/training/training_label_drift.md --json-output reports/training/training_label_drift.json --allow-warnings
gbmbert-audit-training-provenance data/training/relation_training_pack.jsonl --markdown-output reports/training/training_provenance_audit.md --json-output reports/training/training_provenance_audit.json
gbmbert-training-readiness-snapshot --markdown-output reports/training/training_readiness_snapshot.md --json-output reports/training/training_readiness_snapshot.json
gbmbert-dashboard-training-manifest --output reports/training/dashboard_training_manifest.json --markdown-output reports/training/dashboard_training_manifest.md
gbmbert-run-training-governance-suite --output-dir reports/training/governance --allow-findings
```

Build an evidence-only training pack for evidence classification experiments:

```powershell
gbmbert-build-evidence-training-pack data/training/annotation_dataset --output-dir data/training/evidence_pack --reports-dir reports/training/evidence_pack --allow-not-ready
```

Review an evidence training config against prepared splits and label maps before any execution:

```powershell
gbmbert-review-training-config configs/training/gbmbert_evidence_pubmedbert.json data/training/evidence_pack/annotation_splits --label-map-dir data/training/evidence_pack/label_maps --markdown-output reports/training/training_config_review.md --json-output reports/training/training_config_review.json
```

Build a no-training experiment manifest that ties a config, prepared data, and label maps together:

```powershell
gbmbert-build-experiment-manifest configs/training/gbmbert_ner_pubmedbert.json data/training/annotation_splits reports/training/experiment_manifest.json --label-map-dir data/training/label_maps
```

Register checkpoint metadata when a future local training run produces a checkpoint:

```powershell
gbmbert-register-checkpoint models/checkpoint_registry.json --name gbmbert_ner_v1 --checkpoint-dir models/checkpoints/gbmbert_ner_v1 --task ner --base-model microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext --status candidate
```

These commands prepare and audit GBM-BERT training artifacts. They do not claim that a trained GBM-BERT model exists.

Validate the training gate without running optimization:

```powershell
gbmbert-train configs/training/gbmbert_ner_pubmedbert.json data/training/annotation_splits data/training/label_maps --experiment-manifest reports/training/train_gate_experiment_manifest.json --json-output reports/training/train_gate.json --json
```

The `gbmbert-train` command is dry-run by default. `--execute-training` is intentionally gated and will refuse to run unless the required prepared dataset, label map, config, manifest, metrics output, and run-manifest output checks pass. At present, executable training is limited to evidence classification.

Run the evidence-classifier training path only after setting `training_enabled` to `true` in a reviewed evidence-classification config:

```powershell
gbmbert-train configs/training/gbmbert_evidence_pubmedbert.json data/training/annotation_splits data/training/label_maps --experiment-manifest reports/training/evidence_experiment_manifest.json --execute-training --metrics-output reports/training/evidence_metrics.json --evaluation-markdown-output reports/training/evidence_metrics.md --run-manifest-output reports/training/evidence_run_manifest.json --registry models/checkpoint_registry.json --checkpoint-name gbmbert_evidence_pubmedbert
```

This executable path is currently limited to evidence classification. It writes local metrics and metadata for research review; it does not validate clinical performance.

Score research evidence rows with a registered evidence-classifier checkpoint:

```powershell
gbmbert-score-evidence data/training/evidence_rows.jsonl reports/training/evidence_predictions.jsonl models/checkpoint_registry.json --checkpoint-name gbmbert_evidence_pubmedbert
```

Export prediction rows for human review. This writes a separate review artifact and does not modify raw predictions:

```powershell
gbmbert-export-prediction-review-queue reports/training/evidence_predictions.jsonl data/review/evidence_prediction_review_queue.jsonl --csv-output data/review/evidence_prediction_review_queue.csv --queue-all
```

Export active learning candidates for priority review:

```powershell
gbmbert-export-active-learning-candidates reports/training/evidence_predictions.jsonl data/review/active_learning_candidates.jsonl --csv-output data/review/active_learning_candidates.csv --graph-jsonl data/processed/graph_records.jsonl --report-markdown-output reports/review/active_learning_candidates.md --report-json-output reports/review/active_learning_candidates.json
```

Initialize a reviewed prediction queue scaffold for curator decisions:

```powershell
gbmbert-init-reviewed-prediction-queue data/review/evidence_prediction_review_queue.jsonl data/review/evidence_prediction_reviewed_queue.jsonl --csv-output data/review/evidence_prediction_reviewed_queue.csv --reviewer curator
```

Summarize reviewed prediction decisions and tier shifts:

```powershell
gbmbert-prediction-review-summary data/review/evidence_prediction_reviewed_queue.jsonl --markdown-output reports/review/evidence_prediction_review_summary.md --json-output reports/review/evidence_prediction_review_summary.json
```

Import a manually edited reviewed prediction CSV back into validated JSONL:

```powershell
gbmbert-import-prediction-review-csv data/review/evidence_prediction_reviewed_queue.csv data/review/evidence_prediction_reviewed_queue.jsonl --overwrite
```

Build a prediction quality report before using model outputs downstream:

```powershell
gbmbert-prediction-quality-report reports/training/evidence_predictions.jsonl --markdown-output reports/training/evidence_prediction_quality.md --json-output reports/training/evidence_prediction_quality.json
```

Export curated evidence predictions from reviewed decisions. Rejected rows are omitted; pending rows are carried forward as pending unless `--fail-on-pending` is used:

```powershell
gbmbert-export-curated-evidence reports/training/evidence_predictions.jsonl data/review/evidence_prediction_reviewed_queue.jsonl data/processed/curated_evidence_predictions.jsonl --report-markdown-output reports/review/curated_evidence_export.md --report-json-output reports/review/curated_evidence_export.json
```

Audit curated evidence rows for PMID linkage, warning text, checkpoint metadata, reviewer fields, and valid evidence tiers:

```powershell
gbmbert-audit-curated-evidence data/processed/curated_evidence_predictions.jsonl --markdown-output reports/review/curated_evidence_audit.md --json-output reports/review/curated_evidence_audit.json
```

Apply curated evidence tiers to a new graph artifact by PMID. The raw graph is not modified, and pending curated evidence is skipped by default:

```powershell
gbmbert-apply-evidence-overlay data/processed/graph_records.jsonl data/processed/curated_evidence_predictions.jsonl data/processed/evidence_overlay_graph_records.jsonl --report-markdown-output reports/graph/evidence_overlay.md --report-json-output reports/graph/evidence_overlay.json
```

Compare a raw graph with an evidence-overlay graph:

```powershell
gbmbert-overlay-diff data/processed/graph_records.jsonl data/processed/evidence_overlay_graph_records.jsonl --markdown-output reports/graph/evidence_overlay_diff.md --json-output reports/graph/evidence_overlay_diff.json
```

Inspect an overlay graph before any Neo4j load:

```powershell
gbmbert-overlay-load-guard data/processed/evidence_overlay_graph_records.jsonl --markdown-output reports/graph/overlay_load_guard.md --json-output reports/graph/overlay_load_guard.json
```

Run the no-download local curation smoke workflow:

```powershell
gbmbert-run-curation-smoke-workflow
```

Build a local curation handoff bundle from the smoke workflow artifacts:

```powershell
gbmbert-build-curation-handoff --output-dir data/processed/curation_handoff_bundle --markdown-output data/processed/curation_handoff_bundle/curation_handoff_bundle.md --json-output data/processed/curation_handoff_bundle/curation_handoff_bundle.json
```

Validate the handoff bundle and register a curation run:

```powershell
gbmbert-validate-curation-handoff data/processed/curation_handoff_bundle/curation_handoff_bundle.json --markdown-output reports/review/curation_handoff_validation.md --json-output reports/review/curation_handoff_validation.json
gbmbert-register-curation-run reports/review/curation_smoke_workflow/curation_smoke_workflow.json --handoff-manifest-json data/processed/curation_handoff_bundle/curation_handoff_bundle.json --registry-json reports/review/curation_run_registry.json --report-markdown-output reports/review/curation_run_registry.md
```

Search curated evidence rows by PMID, tier, reviewer, review status, checkpoint, or text:

```powershell
gbmbert-search-curated-evidence data/processed/curation_smoke_workflow/curated_evidence_predictions.jsonl --review-status accepted --text ultrasound --markdown-output reports/review/curated_evidence_search.md --json-output reports/review/curated_evidence_search.json
```

Reviewed prediction queues carry optional audit-trail fields, including `decision_timestamp_utc`, `reviewer_id`, `source_queue_sha256`, and `imported_csv_sha256`.

Plan reviewer-sized active learning batches, revert an evidence overlay, or run the full local curation regression pack:

```powershell
gbmbert-plan-active-learning-batches data/processed/curation_smoke_workflow/active_learning_candidates.jsonl data/processed/curation_regression_pack/active_learning_batches.jsonl --csv-output data/processed/curation_regression_pack/active_learning_batches.csv --report-markdown-output reports/review/curation_regression_pack/active_learning_batches.md --report-json-output reports/review/curation_regression_pack/active_learning_batches.json
gbmbert-revert-evidence-overlay data/processed/curation_smoke_workflow/evidence_overlay_graph_records.jsonl data/processed/curation_regression_pack/reverted_graph_records.jsonl --report-markdown-output reports/review/curation_regression_pack/overlay_revert.md --report-json-output reports/review/curation_regression_pack/overlay_revert.json
gbmbert-run-curation-regression-pack
```

Browse curation runs, inspect artifact details, track active learning batch progress, and roundtrip one active learning batch through CSV:

```powershell
gbmbert-browse-curation-runs --registry-json reports/review/curation_run_registry.json --report-markdown-output reports/review/curation_run_browser.md --report-json-output reports/review/curation_run_browser.json
gbmbert-artifact-detail active_learning_batches --index-json reports/artifact_index.json --markdown-output reports/artifact_detail.md --json-output reports/artifact_detail.json
gbmbert-active-learning-batch-status data/processed/curation_regression_pack/active_learning_batches.jsonl --reviewed-queue-jsonl data/processed/curation_regression_pack/prediction_reviewed_queue.jsonl --report-markdown-output reports/review/curation_regression_pack/active_learning_batch_status.md --report-json-output reports/review/curation_regression_pack/active_learning_batch_status.json
gbmbert-export-active-learning-batch-csv data/processed/curation_regression_pack/active_learning_batches.jsonl ALBATCH-001 data/review/active_learning_batch_ALBATCH-001.csv --assigned-reviewer curator --report-markdown-output reports/review/active_learning_batch_roundtrip_export.md
gbmbert-import-active-learning-batch-csv data/review/active_learning_batch_ALBATCH-001.csv data/review/active_learning_batch_reviewed_queue.jsonl --reviewed-queue-jsonl data/processed/curation_regression_pack/prediction_reviewed_queue.jsonl --overwrite --report-markdown-output reports/review/active_learning_batch_roundtrip_import.md
```

Gate an evidence-overlay graph before treating it as load-ready, audit relation extraction provenance, monitor project-scope drift, or run the compact platform regression command:

```powershell
gbmbert-graph-quality-report data/processed/curation_regression_pack/evidence_overlay_graph_records.jsonl --markdown-output reports/review/curation_regression_pack/overlay_graph_quality.md --json-output reports/review/curation_regression_pack/overlay_graph_quality.json
gbmbert-promote-evidence-overlay --overlay-graph-jsonl data/processed/curation_regression_pack/evidence_overlay_graph_records.jsonl --json-output reports/review/curation_regression_pack/evidence_overlay_promotion_gate.json --markdown-output reports/review/curation_regression_pack/evidence_overlay_promotion_gate.md
gbmbert-relation-extraction-audit data/processed/curation_regression_pack/evidence_overlay_graph_records.jsonl --markdown-output reports/graph/relation_extraction_audit.md --json-output reports/graph/relation_extraction_audit.json
gbmbert-scope-drift-monitor --markdown-output reports/platform_regression/scope_drift.md --json-output reports/platform_regression/scope_drift.json
gbmbert-platform-regression
```

Normalize graph entities with the scaffold synonym table and enrich missing relation qualifiers:

```powershell
gbmbert-normalize-graph-entities data/processed/curation_regression_pack/evidence_overlay_graph_records.jsonl data/processed/curation_regression_pack/normalized_graph_records.jsonl --synonym-table data/examples/entity_synonyms.json --markdown-output reports/graph/entity_normalization.md --json-output reports/graph/entity_normalization.json
gbmbert-enrich-relation-qualifiers data/processed/curation_regression_pack/normalized_graph_records.jsonl data/processed/curation_regression_pack/qualifier_enriched_graph_records.jsonl --markdown-output reports/graph/qualifier_enrichment.md --json-output reports/graph/qualifier_enrichment.json
```

Generate a local model card from registry, metrics, and run-manifest metadata:

```powershell
gbmbert-build-model-card models/checkpoint_registry.json --checkpoint-name gbmbert_evidence_pubmedbert --dataset-card-json reports/training/dataset_card.json --markdown-output reports/training/evidence_model_card.md --json-output reports/training/evidence_model_card.json
```

Run a no-download training smoke fixture that uses tiny synthetic evidence rows and fake model components:

```powershell
gbmbert-run-training-smoke --output-dir data/training/evidence_smoke_fixture --reports-dir reports/training/evidence_smoke_fixture --registry models/checkpoint_registry.json --checkpoint-name gbmbert_evidence_smoke --json
```

## Knowledge Graph

The graph layer is implemented under `gbmbert.knowledge_graph`. It defines graph node labels, allowed relation topologies, relation qualifiers, idempotent Neo4j `MERGE` writes, and parameterized query builders for graph review.

Build graph-ready JSONL from PubMed and entity extraction outputs:

```powershell
gbmbert-build-graph-records data/raw/pubmed_gbm.jsonl data/processed/entities.jsonl data/processed/graph_records.jsonl
```

Include evidence classification output when available:

```powershell
gbmbert-build-graph-records data/raw/pubmed_gbm.jsonl data/processed/entities.jsonl data/processed/graph_records.jsonl --evidence-jsonl data/processed/evidence_claims.jsonl
```

This step creates paper/entity nodes and conservative rule-based relation candidates when schema-valid entity pairs appear in the same sentence with trigger phrases such as `predicts`, `associated with`, `targets`, `inhibits`, `enhances delivery of`, or `synergizes with`. Relation qualifiers preserve explicit context such as mutation status, species/model, trial phase, cohort, and evidence context when available. When evidence claims are provided, relation records carry the paper-level evidence tier and classifier provenance.

Run the complete local literature pipeline:

```powershell
gbmbert-run-pipeline data/raw/pubmed_gbm.jsonl --output-dir data/processed/pubmed_gbm_pipeline
```

The pipeline runs entity extraction, evidence classification, graph-record construction, and pre-load validation. Use `--reuse-existing` to skip stages whose outputs already exist in the output directory. Use `--entity-mode lexicon` for deterministic offline smoke baselines when the Hugging Face NER model is not cached locally.

Each pipeline run also writes `pipeline_manifest.json` and `pipeline_manifest.md` in the output directory.

Generate a quality report for graph records without loading Neo4j:

```powershell
gbmbert-graph-quality-report data/processed/graph_records.jsonl --markdown-output reports/graph_quality.md --json-output reports/graph_quality.json
```

Generate a unified report that includes PubMed and trial graph records:

```powershell
gbmbert-graph-quality-report data/processed/graph_records.jsonl --trial-jsonl data/processed/trial_graph_records.jsonl --markdown-output reports/graph/unified_quality.md --json-output reports/graph/unified_quality.json
```

The report summarizes node and relation counts, evidence-tier distribution, top entities, top relation pairs, paper-only records, NCT counts, invalid records, and provenance warnings.

Dry-run a graph load without a live Neo4j instance:

```powershell
gbmbert-load-graph data/processed/graph_records.jsonl --dry-run
```

Write a dry-run load report for handoff or audit:

```powershell
gbmbert-load-graph data/processed/graph_records.jsonl --dry-run --report-markdown-output reports/graph/load_report.md --report-json-output reports/graph/load_report.json
```

Audit graph-record provenance without loading Neo4j:

```powershell
gbmbert-audit-graph-provenance data/processed/graph_records.jsonl --record-type pubmed --markdown-output reports/graph/provenance_audit.md --json-output reports/graph/provenance_audit.json
gbmbert-audit-graph-provenance data/processed/clinicaltrials_gbm_smoke_2026-06-23/trial_graph_records.jsonl --record-type trial --markdown-output reports/graph/trial_provenance_audit.md --json-output reports/graph/trial_provenance_audit.json
```

Trial graph records can be dry-run or loaded through the same command:

```powershell
gbmbert-load-graph data/processed/trial_graph_records.jsonl --record-type trial --dry-run
```

Try the included sample graph fixture:

```powershell
gbmbert-load-graph data/examples/graph_records_sample.jsonl --dry-run
```

For a live Neo4j load, set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`, then run:

```powershell
gbmbert-load-graph data/examples/graph_records_sample.jsonl
gbmbert-inspect-graph
```

Use `gbmbert-inspect-graph --json` when the local Explorer, future dashboard, or another tool needs machine-readable graph counts, evidence-tier counts, and recent paper provenance.

Run the local Knowledge Graph Explorer with the sample graph records:

```powershell
gbmbert-explorer --sample-data data/examples/graph_records_sample.jsonl --open
```

Run the Explorer against the local real PubMed smoke baseline graph records, when present:

```powershell
gbmbert-explorer --baseline-data --open
```

Run the Explorer against a graph JSONL selected from the artifact index:

```powershell
gbmbert-artifact-index --markdown-output reports/artifact_index.md --json-output reports/artifact_index.json
gbmbert-explorer --artifact-index reports/artifact_index.json --artifact trial_graph_records --open
```

For a live Neo4j-backed Explorer, set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`, then run:

```powershell
gbmbert-explorer --neo4j --open
```

The Explorer exposes `/api/metadata` for schema-derived filter options with active graph counts and available graph artifacts when an artifact index is supplied. Loaded PubMed `MENTIONS` edges carry `source_pmids` and tier-0 evidence metadata; ClinicalTrials.gov sample-mode edges carry NCT `source_ids`. This Explorer is a local prototype for graph review; the original Streamlit dashboard remains a later Phase 7 deliverable.

The Knowledge Graph Explorer wireframe note lives at `reports/wireframes/kg_explorer.md`.

## Smoke Baseline

Rebuild the local smoke baseline from existing raw PubMed and ClinicalTrials.gov JSONL files:

```powershell
gbmbert-run-smoke-baseline --offline --markdown-output reports/smoke_baseline.md --json-output reports/smoke_baseline.json
```

Without `--offline`, the command refreshes the small PubMed query-pack and ClinicalTrials.gov snapshots before rebuilding pipeline outputs, review queues, quality reports, dry-run load reports, provenance audits, manifests, and the artifact index.

## Dashboard Shell

The Streamlit dashboard shell provides the required page structure and persistent research-use warning. Install the optional dashboard extra before launching it:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dashboard]"
gbmbert-dashboard --host 127.0.0.1 --port 8501
```

The dashboard shell does not implement simulator or treatment-explorer logic yet.
