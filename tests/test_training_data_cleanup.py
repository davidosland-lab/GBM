import json
from pathlib import Path

from gbmbert.training.gold_pack import build_gold_training_pack, format_gold_training_pack_markdown
from gbmbert.training.preparation import (
    format_evidence_label_repair_markdown,
    format_pmid_split_markdown,
    repair_evidence_labels,
    split_annotation_dataset_by_pmid,
)
from gbmbert.training.readiness import build_training_readiness_report


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_split_annotation_dataset_by_pmid_prevents_cross_split_leakage(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    rows = [
        {"source_pmid": "1", "text": "MGMT", "label": "BIOMARKER", "start": 0, "end": 4},
        {"source_pmid": "1", "text": "MGMT predicts response", "label": "PREDICTS"},
        {"source_pmid": "2", "text": "EGFR", "label": "GENE", "start": 0, "end": 4},
        {"source_pmid": "3", "text": "TMZ", "label": "DRUG", "start": 0, "end": 3},
    ]
    _write_jsonl(dataset / "ner.jsonl", rows[:1] + rows[2:])
    _write_jsonl(dataset / "relations.jsonl", [rows[1]])
    _write_jsonl(dataset / "evidence.jsonl", [{"source_pmid": "2", "text": "phase II", "label": 4}])

    manifest = split_annotation_dataset_by_pmid(dataset, tmp_path / "splits", seed=3, train_ratio=0.34, validation_ratio=0.33, test_ratio=0.33)
    markdown = format_pmid_split_markdown(manifest)

    assert manifest.leakage_warnings == []
    assert sum(manifest.pmid_counts.values()) == 3
    assert "PMID-Safe Split" in markdown


def test_repair_evidence_labels_uses_tier_fields(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_jsonl(dataset / "evidence.jsonl", [{"source_pmid": "1", "text": "trial", "evidence_tier": 4}])
    _write_jsonl(dataset / "ner.jsonl", [{"source_pmid": "1", "text": "MGMT", "label": "GENE", "start": 0, "end": 4}])
    _write_jsonl(dataset / "relations.jsonl", [])

    report = repair_evidence_labels(dataset, tmp_path / "repaired")
    markdown = format_evidence_label_repair_markdown(report)
    repaired = json.loads((tmp_path / "repaired" / "evidence.jsonl").read_text(encoding="utf-8").strip())

    assert report.changed_count == 1
    assert report.skipped_count == 0
    assert repaired["label"] == 4
    assert "Evidence Label Repair" in markdown


def test_training_readiness_flags_ner_quality_issues(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "ner_train.jsonl",
        [
            {"source_pmid": "1", "text": "MGMT", "label": "GENE", "start": 5, "end": 4},
            {"source_pmid": "1", "text": "MGMT", "label": "GENE", "start": 5, "end": 4},
            {"source_pmid": "2", "text": "EGFR", "label": "BIOMARKER", "start": 0, "end": 4},
        ],
    )
    _write_jsonl(tmp_path / "evidence_train.jsonl", [{"source_pmid": "3", "text": "trial", "label": 4}])
    _write_jsonl(tmp_path / "relation_train.jsonl", [{"source_pmid": "4", "text": "predicts", "label": "PREDICTS"}])

    report = build_training_readiness_report(tmp_path, min_examples_per_task=1, min_examples_per_label=1, max_label_fraction=0.6)
    ner = next(task for task in report.task_reports if task.task == "ner")

    assert ner.ready is False
    assert ner.duplicate_count == 1
    assert ner.invalid_ner_span_count == 2
    assert any("dominant label fraction" in warning for warning in ner.warnings)


def test_build_gold_training_pack_runs_local_workflow(tmp_path: Path) -> None:
    reviewed = tmp_path / "prediction_reviewed.jsonl"
    _write_jsonl(
        reviewed,
        [
            {
                "item_id": "prediction:1:1",
                "item_type": "evidence_prediction",
                "source_pmid": "1",
                "text": "phase II trial",
                "predicted_evidence_tier": 4,
                "prediction_label": "4",
                "confidence": 0.9,
                "review_status": "accepted",
            }
        ],
    )

    report = build_gold_training_pack(
        output_dir=tmp_path / "gold_pack",
        reports_dir=tmp_path / "reports",
        prediction_reviewed_queue_jsonl=reviewed,
        min_examples_per_task=1,
        min_examples_per_label=1,
    )
    markdown = format_gold_training_pack_markdown(report)

    assert (tmp_path / "gold_pack" / "annotation_splits" / "evidence_train.jsonl").exists()
    assert (tmp_path / "reports" / "gold_training_pack.json").exists()
    assert report.ready is False
    assert "Gold Training Pack" in markdown
