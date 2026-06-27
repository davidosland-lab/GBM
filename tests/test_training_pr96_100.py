import json
from pathlib import Path

from gbmbert.training.config_review import review_training_config
from gbmbert.training.pack_comparison import compare_training_packs, format_training_pack_comparison_markdown
from gbmbert.training.registry_audit import audit_checkpoint_registry, format_registry_audit_markdown
from gbmbert.training.relation_training_pack import build_relation_training_pack, format_relation_training_pack_markdown


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_relation_training_pack_builds_relation_only_artifacts(tmp_path: Path) -> None:
    relation_file = tmp_path / "relation_training_pack.jsonl"
    _write_jsonl(
        relation_file,
        [
            {"source_pmid": "1", "sentence": "A predicts B.", "head": "A", "tail": "B", "label": "PREDICTS"},
            {"source_pmid": "2", "sentence": "B unrelated A.", "head": "B", "tail": "A", "label": "NO_RELATION"},
        ],
    )

    report = build_relation_training_pack(
        relation_file,
        output_dir=tmp_path / "relation_pack",
        reports_dir=tmp_path / "reports",
        min_examples_per_task=1,
        min_examples_per_label=1,
    )
    markdown = format_relation_training_pack_markdown(report)

    assert report.ready is True
    assert report.positive_rows == 1
    assert report.negative_rows == 1
    assert (tmp_path / "relation_pack" / "annotation_splits" / "relation_train.jsonl").exists()
    assert (tmp_path / "relation_pack" / "label_maps" / "relation_label_map.json").exists()
    assert (tmp_path / "reports" / "relation_training_pack_quality.json").exists()
    assert "Relation Training Pack" in markdown


def test_relation_config_review_requires_no_relation_and_label_alignment(tmp_path: Path) -> None:
    split_dir = tmp_path / "splits"
    _write_jsonl(split_dir / "relation_train.jsonl", [{"source_pmid": "1", "label": "PREDICTS", "head": "A", "tail": "B"}])
    _write_jsonl(split_dir / "relation_validation.jsonl", [{"source_pmid": "2", "label": "NO_RELATION", "head": "B", "tail": "A"}])
    _write_jsonl(split_dir / "relation_test.jsonl", [])
    label_dir = tmp_path / "label_maps"
    label_dir.mkdir()
    (label_dir / "relation_label_map.json").write_text(
        json.dumps({"label_to_id": {"NO_RELATION": 0, "PREDICTS": 1}, "id_to_label": {"0": "NO_RELATION", "1": "PREDICTS"}}),
        encoding="utf-8",
    )
    config = tmp_path / "relation_config.json"
    config.write_text(
        json.dumps(
            {
                "name": "relation_review",
                "task": "relation_extraction",
                "base_model": "dmis-lab/biobert-base-cased-v1.2",
                "train_path": "unused/relation_train.jsonl",
                "validation_path": "unused/relation_validation.jsonl",
                "output_dir": "models/relation_review",
                "label_set": ["NO_RELATION", "PREDICTS"],
                "hyperparameters": {"epochs": 3, "learning_rate": 0.00002, "batch_size": 8, "max_length": 256},
            }
        ),
        encoding="utf-8",
    )

    report = review_training_config(config, split_dir, label_map_dir=label_dir)

    assert report.status == "passed"
    assert report.prepared_task == "relation"
    assert report.checks["relation_config_includes_no_relation"] is True
    assert report.checks["label_map_labels_match_config"] is True


def test_training_pack_comparison_reports_pack_health(tmp_path: Path) -> None:
    evidence_split = tmp_path / "evidence_pack" / "splits"
    relation_split = tmp_path / "relation_pack" / "splits"
    _write_jsonl(evidence_split / "evidence_train.jsonl", [{"source_pmid": "1", "label": "1"}])
    _write_jsonl(relation_split / "relation_train.jsonl", [{"source_pmid": "1", "label": "NO_RELATION"}])
    evidence_report = tmp_path / "evidence.json"
    relation_report = tmp_path / "relation.json"
    evidence_report.write_text(json.dumps({"split_dataset_dir": str(evidence_split), "ready": True, "warnings": []}), encoding="utf-8")
    relation_report.write_text(json.dumps({"split_dataset_dir": str(relation_split), "ready": True, "warnings": []}), encoding="utf-8")

    report = compare_training_packs(evidence_pack_report=evidence_report, relation_pack_report=relation_report)
    markdown = format_training_pack_comparison_markdown(report)

    assert report.ready_count == 2
    assert report.packs[0].row_counts["evidence"] == 1
    assert report.packs[1].row_counts["relation"] == 1
    assert "Training Pack Comparison" in markdown


def test_model_registry_audit_flags_missing_cards_and_paths(tmp_path: Path) -> None:
    registry = tmp_path / "checkpoint_registry.json"
    registry.write_text(
        json.dumps(
            {
                "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
                "checkpoints": [
                    {
                        "name": "missing_card",
                        "checkpoint_dir": str(tmp_path / "missing"),
                        "task": "evidence_classification",
                        "base_model": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                        "status": "candidate",
                        "registered_at": "2026-01-01T00:00:00+00:00",
                        "metrics_path": None,
                        "manifest_path": None,
                        "notes": "Metadata-only smoke registration.",
                        "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = audit_checkpoint_registry(registry, reports_dir=tmp_path / "reports")
    markdown = format_registry_audit_markdown(report)

    assert report.passed is False
    assert "checkpoint_dir does not exist" in report.errors[0]
    assert "no matching model card found" in report.warnings[0]
    assert "Model Registry Audit" in markdown
