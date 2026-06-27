# GBM-AI Smoke Baseline Report

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Offline mode: True

## Paths
- pubmed_raw: `data\raw\ncbi_env_smoke_2026-06-23.jsonl`
- pubmed_graph: `data\processed\ncbi_env_smoke_pipeline\graph_records.jsonl`
- trial_raw: `data\raw\clinicaltrials_gbm_smoke_2026-06-23.jsonl`
- trial_graph: `data\processed\clinicaltrials_gbm_smoke_2026-06-23\trial_graph_records.jsonl`
- artifact_index: `reports\artifact_index.json`

## Steps
- Built PubMed pipeline graph records: data\processed\ncbi_env_smoke_pipeline\graph_records.jsonl
- Exported review queue: data\review\ncbi_env_smoke_review_queue.jsonl
- Initialized reviewed queue: data\review\ncbi_env_smoke_reviewed_queue.jsonl
- Built trial graph records: data\processed\clinicaltrials_gbm_smoke_2026-06-23\trial_graph_records.jsonl
- Generated graph quality reports
- Generated dry-run graph load reports
- Generated provenance audit reports
- Generated corpus manifests
- Generated artifact index

## Warnings
- 7 item(s) still pending review
