import json
from pathlib import Path

from gbmbert.training.config_review import format_training_config_review_markdown, review_training_config
from gbmbert.training.evidence_pack import build_evidence_training_pack, format_evidence_training_pack_markdown
from gbmbert.training.relation_negatives import build_relation_negatives, format_relation_negative_markdown
from gbmbert.training.relation_pack import format_relation_pack_markdown, merge_relation_training_pack
from gbmbert.training.relation_quality import analyze_relation_dataset_quality, format_relation_quality_markdown


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_relation_negative_sampler_builds_no_relation_examples(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_jsonl(
        dataset / "relations.jsonl",
        [
            {
                "source_pmid": "1",
                "sentence": "MGMT predicts TMZ response.",
                "head": "MGMT",
                "tail": "TMZ",
                "label": "PREDICTS_RESPONSE",
            }
        ],
    )

    report = build_relation_negatives(dataset, tmp_path / "relation_negatives.jsonl", negative_ratio=1.0)
    rows = [json.loads(line) for line in (tmp_path / "relation_negatives.jsonl").read_text(encoding="utf-8").splitlines()]
    markdown = format_relation_negative_markdown(report)

    assert report.positive_count == 1
    assert report.negative_count == 1
    assert rows[0]["label"] == "NO_RELATION"
    assert rows[0]["head"] == "TMZ"
    assert rows[0]["tail"] == "MGMT"
    assert "Relation Negative Sampler" in markdown


def test_relation_dataset_quality_reports_counts_and_warnings(tmp_path: Path) -> None:
    relation_file = tmp_path / "relations.jsonl"
    _write_jsonl(
        relation_file,
        [
            {"source_pmid": "1", "sentence": "A activates B.", "head": "A", "tail": "B", "label": "ACTIVATES"},
            {"source_pmid": "1", "sentence": "A activates B.", "head": "B", "tail": "A", "label": "NO_RELATION"},
            {"source_pmid": "2", "sentence": "", "head": "C", "tail": "C", "label": "ASSOCIATED_WITH"},
        ],
    )

    report = analyze_relation_dataset_quality(relation_file)
    markdown = format_relation_quality_markdown(report)

    assert report.relation_count == 3
    assert report.positive_count == 2
    assert report.negative_count == 1
    assert report.missing_sentence_count == 1
    assert report.invalid_endpoint_count == 1
    assert "Relation Dataset Quality Report" in markdown


def test_relation_pack_merger_combines_positive_and_negative_rows(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_jsonl(
        dataset / "relations.jsonl",
        [
            {
                "source_pmid": "1",
                "sentence": "MGMT predicts TMZ response.",
                "head": "MGMT",
                "tail": "TMZ",
                "label": "PREDICTS_RESPONSE",
            }
        ],
    )
    negatives = tmp_path / "relation_negatives.jsonl"
    _write_jsonl(
        negatives,
        [
            {
                "source_pmid": "1",
                "sentence": "MGMT predicts TMZ response.",
                "head": "TMZ",
                "tail": "MGMT",
                "label": "NO_RELATION",
                "negative_source": "synthetic_entity_pair_v1",
            }
        ],
    )

    report = merge_relation_training_pack(dataset, negatives, tmp_path / "relation_training_pack.jsonl")
    rows = [
        json.loads(line)
        for line in (tmp_path / "relation_training_pack.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    markdown = format_relation_pack_markdown(report)

    assert report.ready is True
    assert report.positive_count == 1
    assert report.negative_count == 1
    assert report.label_counts == {"NO_RELATION": 1, "PREDICTS_RESPONSE": 1}
    assert rows[0]["relation_pack_source_type"] == "human_or_curated_positive"
    assert rows[0]["relation_pack_synthetic"] is False
    assert rows[1]["relation_pack_source_type"] == "synthetic_no_relation"
    assert rows[1]["relation_pack_synthetic"] is True
    assert "Relation Pack Merger" in markdown


def test_evidence_training_pack_builds_evidence_only_readiness(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_jsonl(
        dataset / "evidence.jsonl",
        [
            {"source_pmid": "1", "text": "phase II evidence", "label": 1},
            {"source_pmid": "2", "text": "preclinical evidence", "label": 0},
        ],
    )
    _write_jsonl(dataset / "ner.jsonl", [{"source_pmid": "1", "text": "MGMT", "label": "GENE", "start": 0, "end": 4}])
    _write_jsonl(dataset / "relations.jsonl", [{"source_pmid": "1", "sentence": "MGMT predicts TMZ", "head": "MGMT", "tail": "TMZ", "label": "PREDICTS"}])

    report = build_evidence_training_pack(
        dataset,
        output_dir=tmp_path / "evidence_pack",
        reports_dir=tmp_path / "reports",
        min_examples_per_task=1,
        min_examples_per_label=1,
    )
    markdown = format_evidence_training_pack_markdown(report)

    assert report.evidence_rows == 2
    assert report.ready is True
    assert (tmp_path / "evidence_pack" / "annotation_splits" / "evidence_train.jsonl").exists()
    assert (tmp_path / "evidence_pack" / "label_maps" / "evidence_label_map.json").exists()
    assert "Evidence Training Pack" in markdown


def test_training_config_review_gate_passes_reviewed_evidence_pack(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_jsonl(
        dataset / "evidence.jsonl",
        [
            {"source_pmid": "1", "text": "phase II evidence", "label": "1"},
            {"source_pmid": "2", "text": "preclinical evidence", "label": "0"},
        ],
    )
    _write_jsonl(dataset / "ner.jsonl", [])
    _write_jsonl(dataset / "relations.jsonl", [])
    pack = build_evidence_training_pack(
        dataset,
        output_dir=tmp_path / "pack",
        reports_dir=tmp_path / "reports",
        min_examples_per_task=1,
        min_examples_per_label=1,
    )
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "name": "evidence_review",
                "task": "evidence_classification",
                "base_model": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                "train_path": "unused/evidence_train.jsonl",
                "validation_path": "unused/evidence_validation.jsonl",
                "output_dir": "models/evidence_review",
                "label_set": ["0", "1"],
                "hyperparameters": {"epochs": 3, "learning_rate": 0.00002, "batch_size": 8, "max_length": 256},
            }
        ),
        encoding="utf-8",
    )

    report = review_training_config(config, pack.split_dataset_dir, label_map_dir=pack.label_map_dir)
    markdown = format_training_config_review_markdown(report)

    assert report.status == "passed"
    assert report.prepared_task == "evidence"
    assert report.checks["dataset_labels_covered_by_config"] is True
    assert report.checks["dataset_labels_covered_by_label_map"] is True
    assert any("training_enabled is false" in warning for warning in report.warnings)
    assert "Training Config Review Gate" in markdown
