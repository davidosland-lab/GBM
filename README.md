# GBM-AI Platform

Glioblastoma research intelligence platform for literature ingestion, structured biomedical annotation, and downstream research workflows.

> Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This repository currently implements the first scaffolded layer:

- PubMed search and record ingestion through NCBI E-utilities.
- JSONL persistence for literature records.
- Basic text cleaning utilities.
- Pydantic schemas for papers, entities, relations, and evidence claims.
- Baseline biomedical named entity extraction over PubMed JSONL.

The project must not be used to recommend treatment for a real patient, generate clinical instructions, present itself as a medical device, or claim predictive clinical accuracy.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set `NCBI_EMAIL`. An NCBI API key is optional but recommended for higher rate limits.

## PubMed Ingestion

```python
from gbmbert.ingest.pubmed import fetch_pubmed_records, save_jsonl, search_pubmed

pmids = search_pubmed("glioblastoma MGMT methylation temozolomide", retmax=10)
records = fetch_pubmed_records(pmids)
save_jsonl(records, "data/raw/pubmed_gbm.jsonl")
```

## Testing

```powershell
pytest
```

## Entity Extraction

The baseline NER pipeline uses Hugging Face `pipeline("ner", aggregation_strategy="simple")` with `d4data/biomedical-ner-all` by default.

```powershell
gbmbert-extract-entities data/raw/pubmed_gbm.jsonl data/processed/entities.jsonl
```

The output JSONL contains one record per PMID:

```json
{"pmid":"12345678","entities":[{"text":"MGMT","label":"GENE","start":0,"end":4,"confidence":0.92,"normalized_text":"MGMT"}]}
```
