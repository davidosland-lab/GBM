import json
from pathlib import Path

from gbmbert.annotation.schema import EntityType
from gbmbert.datasets import (
    analyze_annotation_dataset,
    export_annotation_datasets,
    format_dataset_quality_markdown,
    save_dataset_quality_json,
    save_dataset_quality_markdown,
)
from gbmbert.extraction.entities import EntityExtractionResult, ExtractedEntity


def test_export_annotation_datasets_writes_task_jsonl_files(tmp_path: Path) -> None:
    reviewed_path = tmp_path / "reviewed_queue.jsonl"
    entity_path = tmp_path / "entities.jsonl"
    dataset_dir = tmp_path / "datasets"
    reviewed_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "item_id": "evidence:12345678",
                        "item_type": "evidence_claim",
                        "source_pmid": "12345678",
                        "evidence_tier": 0,
                        "confidence": 0.5,
                        "text": "Hypothesis claim",
                        "reasons": [],
                        "review_status": "accepted",
                    }
                ),
                json.dumps(
                    {
                        "item_id": "relation:12345678:1",
                        "item_type": "graph_relation",
                        "source_pmid": "12345678",
                        "evidence_tier": 0,
                        "confidence": 0.6,
                        "text": "MGMT methylation predicts response.",
                        "relation_type": "PREDICTS",
                        "head": "Biomarker:MGMT methylation",
                        "tail": "Outcome:response",
                        "reasons": [],
                        "review_status": "corrected",
                        "review_notes": "Corrected evidence tier.",
                        "corrected_evidence_tier": 3,
                    }
                ),
                json.dumps(
                    {
                        "item_id": "evidence:23456789",
                        "item_type": "evidence_claim",
                        "source_pmid": "23456789",
                        "evidence_tier": 0,
                        "confidence": 0.5,
                        "text": "Pending claim",
                        "reasons": [],
                        "review_status": "pending",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    entity_path.write_text(
        EntityExtractionResult(
            pmid="12345678",
            entities=[
                ExtractedEntity(
                    text="MGMT",
                    label=EntityType.GENE,
                    start=0,
                    end=4,
                    confidence=0.9,
                    normalized_text="MGMT",
                )
            ],
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    summary = export_annotation_datasets(
        reviewed_queue_jsonl=reviewed_path,
        output_dir=dataset_dir,
        entity_jsonl=entity_path,
    )

    evidence_rows = [json.loads(line) for line in (dataset_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()]
    relation_rows = [json.loads(line) for line in (dataset_dir / "relations.jsonl").read_text(encoding="utf-8").splitlines()]
    ner_rows = [json.loads(line) for line in (dataset_dir / "ner.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = json.loads((dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))

    assert summary.evidence_count == 1
    assert summary.relation_count == 1
    assert summary.ner_count == 1
    assert evidence_rows[0]["label"] == 0
    assert relation_rows[0]["evidence_tier"] == 3
    assert ner_rows[0]["label"] == "GENE"
    assert manifest["included_statuses"] == ["accepted", "corrected"]


def test_analyze_annotation_dataset_reports_warnings_and_labels(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    (dataset_dir / "ner.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"text": "MGMT", "label": "GENE", "source_pmid": "1", "start": 0, "end": 4}),
                json.dumps({"text": "MGMT", "label": "GENE", "source_pmid": "1", "start": 0, "end": 4}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "evidence.jsonl").write_text(json.dumps({"text": "", "label": 0, "source_pmid": "1"}) + "\n", encoding="utf-8")
    (dataset_dir / "relations.jsonl").write_text("", encoding="utf-8")
    json_path = tmp_path / "quality.json"
    markdown_path = tmp_path / "quality.md"

    report = analyze_annotation_dataset(dataset_dir)
    save_dataset_quality_json(report, json_path)
    save_dataset_quality_markdown(report, markdown_path)
    markdown = format_dataset_quality_markdown(report)

    assert report.total_examples == 3
    assert report.task_reports[0].duplicate_count == 1
    assert report.warning_count >= 3
    assert json.loads(json_path.read_text(encoding="utf-8"))["total_examples"] == 3
    assert "Annotation Dataset Quality Report" in markdown_path.read_text(encoding="utf-8")
    assert "fewer than two labels present" in markdown
