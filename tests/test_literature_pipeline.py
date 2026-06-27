import json
from pathlib import Path
from typing import Any

from gbmbert.extraction.pipeline import BiomedicalNERPipeline
from gbmbert.pipeline import create_lexicon_ner_pipeline, load_lexicon_entries, run_literature_pipeline


def test_run_literature_pipeline_creates_artifacts_with_fake_ner(tmp_path: Path) -> None:
    pubmed_path = tmp_path / "pubmed.jsonl"
    source_title = "MGMT methylation predicts temozolomide response"
    pubmed_path.write_text(
        json.dumps(
            {
                "pmid": "12345678",
                "title": source_title,
                "abstract": "A retrospective patient cohort found the same association.",
                "journal": "Neuro-Oncology",
                "publication_date": "2025",
                "mesh_terms": ["Glioblastoma"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_ner(text: str) -> list[dict[str, Any]]:
        biomarker = "MGMT methylation"
        outcome = "temozolomide response"
        return [
            {
                "word": biomarker,
                "entity_group": "BIOMARKER",
                "start": text.find(biomarker),
                "end": text.find(biomarker) + len(biomarker),
                "score": 0.95,
            },
            {
                "word": outcome,
                "entity_group": "OUTCOME",
                "start": text.find(outcome),
                "end": text.find(outcome) + len(outcome),
                "score": 0.93,
            },
        ]

    outputs = run_literature_pipeline(
        pubmed_path,
        output_dir=tmp_path / "pipeline",
        entity_extractor=BiomedicalNERPipeline(ner_pipeline=fake_ner),
    )

    assert outputs.entities_jsonl.exists()
    assert outputs.evidence_jsonl.exists()
    assert outputs.graph_jsonl.exists()
    assert outputs.quality_json.exists()
    assert outputs.quality_markdown.exists()
    assert outputs.manifest_json.exists()
    assert outputs.manifest_markdown.exists()
    assert outputs.quality_report.record_count == 1
    assert outputs.quality_report.invalid_record_count == 0
    assert outputs.quality_report.relation_count == 1

    graph_record = json.loads(outputs.graph_jsonl.read_text(encoding="utf-8").splitlines()[0])
    assert graph_record["relations"][0]["evidence_tier"] == 3
    assert graph_record["relations"][0]["properties"]["evidence_classification_method"]
    manifest = json.loads(outputs.manifest_json.read_text(encoding="utf-8"))
    assert manifest["name"] == "pipeline"
    assert any(item["path"].endswith("graph_records.jsonl") for item in manifest["files"])


def test_lexicon_ner_pipeline_extracts_offline_smoke_entities() -> None:
    ner = create_lexicon_ner_pipeline()

    outputs = ner("MGMT methylation predicts temozolomide response in glioblastoma.")

    assert [output["entity_group"] for output in outputs] == [
        "BIOMARKER",
        "OUTCOME",
        "DISEASE",
    ]


def test_lexicon_ner_pipeline_loads_configured_terms(tmp_path: Path) -> None:
    lexicon_path = tmp_path / "lexicon.json"
    lexicon_path.write_text(
        json.dumps(
            {
                "name": "test",
                "entries": [
                    {"term": "perampanel", "label": "DRUG"},
                    {"term": "radiographic response", "label": "OUTCOME"},
                ],
            }
        ),
        encoding="utf-8",
    )

    entries = load_lexicon_entries(lexicon_path)
    ner = create_lexicon_ner_pipeline(lexicon_path)
    outputs = ner("Perampanel was associated with radiographic response.")

    assert entries[0][0] == "perampanel"
    assert [output["entity_group"] for output in outputs] == ["DRUG", "OUTCOME"]
