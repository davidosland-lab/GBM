import json
from pathlib import Path

from gbmbert.ingest.clinicaltrials import ClinicalTrialRecord
from gbmbert.smoke_baseline import (
    SmokeBaselinePaths,
    format_smoke_baseline_report_markdown,
    run_smoke_baseline,
)


def test_run_smoke_baseline_offline_rebuilds_artifact_bundle(tmp_path: Path) -> None:
    pubmed_raw = tmp_path / "data" / "raw" / "pubmed_smoke.jsonl"
    trial_raw = tmp_path / "data" / "raw" / "clinicaltrials_smoke.jsonl"
    lexicon_path = tmp_path / "configs" / "lexicon.json"
    pubmed_raw.parent.mkdir(parents=True)
    trial_raw.parent.mkdir(parents=True, exist_ok=True)
    lexicon_path.parent.mkdir(parents=True)
    pubmed_raw.write_text(
        json.dumps(
            {
                "pmid": "12345678",
                "title": "MGMT methylation predicts temozolomide response in glioblastoma",
                "abstract": "A retrospective patient cohort found MGMT methylation predicts temozolomide response.",
                "journal": "Test",
                "publication_date": "2026",
                "mesh_terms": ["Glioblastoma"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    trial_raw.write_text(
        ClinicalTrialRecord(
            nct_id="NCT12345678",
            brief_title="Glioblastoma trial",
            conditions=["Glioblastoma"],
            interventions=["temozolomide"],
            source_url="https://clinicaltrials.gov/study/NCT12345678",
            query="glioblastoma",
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )
    lexicon_path.write_text(
        json.dumps(
            {
                "entries": [
                    {"term": "MGMT methylation", "label": "BIOMARKER"},
                    {"term": "temozolomide response", "label": "OUTCOME"},
                    {"term": "glioblastoma", "label": "DISEASE"},
                    {"term": "temozolomide", "label": "DRUG"},
                ]
            }
        ),
        encoding="utf-8",
    )
    paths = SmokeBaselinePaths(
        pubmed_raw=pubmed_raw,
        pubmed_pipeline_dir=tmp_path / "data" / "processed" / "pubmed_pipeline",
        trial_raw=trial_raw,
        trial_pipeline_dir=tmp_path / "data" / "processed" / "trial_pipeline",
        review_queue_jsonl=tmp_path / "data" / "review" / "review_queue.jsonl",
        review_queue_csv=tmp_path / "data" / "review" / "review_queue.csv",
        reviewed_queue_jsonl=tmp_path / "data" / "review" / "reviewed_queue.jsonl",
        reviewed_queue_csv=tmp_path / "data" / "review" / "reviewed_queue.csv",
        reports_dir=tmp_path / "reports",
        lexicon_path=lexicon_path,
    )

    report = run_smoke_baseline(paths=paths, offline=True)
    markdown = format_smoke_baseline_report_markdown(report)

    assert report.offline is True
    assert Path(report.paths["pubmed_graph"]).exists()
    assert Path(report.paths["trial_graph"]).exists()
    assert Path(report.paths["artifact_index"]).exists()
    assert (tmp_path / "reports" / "graph" / "ncbi_env_smoke_provenance_audit.json").exists()
    assert "Smoke Baseline Report" in markdown
