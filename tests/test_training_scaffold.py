import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from gbmbert.training.cli import build_training_plan
from gbmbert.training.config import TrainingConfig, TrainingTask, load_training_config
from gbmbert.training.datasets import (
    adapt_evidence_record,
    adapt_ner_record,
    adapt_relation_record,
    summarize_dataset,
)
from gbmbert.training.evaluation import evaluate_predictions
from gbmbert.training.execution import execute_evidence_training
from gbmbert.training.hf_datasets import dataset_split_counts, load_label_map, load_prepared_dataset
from gbmbert.training.inference import score_evidence_jsonl
from gbmbert.training.model_card import build_model_card, format_model_card_markdown
from gbmbert.training.preparation import (
    build_baseline_report,
    build_dataset_card,
    build_experiment_manifest,
    build_label_maps,
    split_annotation_dataset,
)
from gbmbert.training.registry import load_registry, register_checkpoint
from gbmbert.training.runner import build_training_gate_report
from gbmbert.training.smoke_training import run_training_smoke
from gbmbert.training.tokenization import summarize_tokenized_dataset, tokenize_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_load_training_config_uses_approved_pubmedbert_base_model() -> None:
    config = load_training_config(ROOT / "configs" / "training" / "gbmbert_ner_pubmedbert.json")

    assert config.task is TrainingTask.NER
    assert config.base_model.startswith("microsoft/BiomedNLP-PubMedBERT")
    assert config.is_training_enabled is False


def test_training_config_rejects_training_from_scratch_style_model() -> None:
    with pytest.raises(ValidationError):
        TrainingConfig(
            name="bad",
            task=TrainingTask.NER,
            base_model="scratch",
            train_path=Path("train.jsonl"),
            output_dir=Path("out"),
            label_set=["GENE"],
        )


def test_dataset_adapters_extract_task_labels() -> None:
    assert adapt_ner_record({"pmid": "1", "entities": [{"label": "GENE"}]})["labels"] == ["GENE"]
    assert adapt_relation_record({"pmid": "1", "relations": [{"relation": "PREDICTS"}]})["labels"] == ["PREDICTS"]
    assert adapt_evidence_record({"source_pmid": "1", "evidence_level": 3})["labels"] == ["3"]
    assert adapt_ner_record({"task": "ner", "source_pmid": "2", "text": "MGMT", "label": "GENE"})["labels"] == ["GENE"]
    assert adapt_relation_record({"task": "relation", "source_pmid": "2", "label": "ASSOCIATED_WITH"})["labels"] == [
        "ASSOCIATED_WITH"
    ]
    assert adapt_evidence_record({"task": "evidence", "source_pmid": "2", "text": "Phase II", "label": 4})[
        "labels"
    ] == ["4"]


def test_summarize_dataset_counts_labels(tmp_path: Path) -> None:
    path = tmp_path / "evidence.jsonl"
    path.write_text(
        json.dumps({"source_pmid": "1", "claim": "Phase II study", "evidence_level": 4}) + "\n",
        encoding="utf-8",
    )

    summary = summarize_dataset(path, TrainingTask.EVIDENCE_CLASSIFICATION, ["0", "4"])

    assert summary.records == 1
    assert summary.labels == {"4": 1}
    assert summary.missing_labels == ["0"]


def test_build_training_plan_is_dry_run_when_data_missing() -> None:
    plan = build_training_plan(ROOT / "configs" / "training" / "gbmbert_evidence_pubmedbert.json")

    assert plan["training_enabled"] is False
    assert plan["status"] == "dry_run_only"
    assert "does not train from scratch" in " ".join(plan["notes"])
    assert plan["datasets"]["train"]["status"] == "missing"


def test_training_preparation_builds_splits_labels_cards_baselines_and_manifest(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    _write_jsonl(
        dataset_dir / "ner.jsonl",
        [
            {"task": "ner", "source_pmid": str(index), "text": "MGMT", "label": "GENE", "start": index, "end": index + 4}
            for index in range(6)
        ]
        + [
            {"task": "ner", "source_pmid": str(index), "text": "TMZ", "label": "DRUG", "start": index, "end": index + 3}
            for index in range(6, 12)
        ],
    )
    _write_jsonl(
        dataset_dir / "evidence.jsonl",
        [{"task": "evidence", "source_pmid": str(index), "text": "Phase II trial", "label": index % 2} for index in range(8)],
    )
    _write_jsonl(
        dataset_dir / "relations.jsonl",
        [
            {
                "task": "relation",
                "source_pmid": str(index),
                "text": "MGMT predicts response",
                "label": "PREDICTS" if index % 2 else "ASSOCIATED_WITH",
            }
            for index in range(8)
        ],
    )

    split_dir = tmp_path / "splits"
    manifest = split_annotation_dataset(dataset_dir, split_dir, seed=7)

    assert (split_dir / "split_manifest.json").exists()
    assert manifest.tasks[0].split_counts["train"] > 0
    assert (split_dir / "ner_test.jsonl").exists()

    label_summary = build_label_maps(split_dir, tmp_path / "labels")

    assert json.loads(Path(label_summary.files["ner"]).read_text(encoding="utf-8"))["label_to_id"] == {
        "DRUG": 0,
        "GENE": 1,
    }

    card = build_dataset_card(split_dir)
    baseline = build_baseline_report(split_dir)

    assert card.total_examples == 28
    assert baseline.tasks[0].majority_accuracy is not None

    experiment = build_experiment_manifest(
        ROOT / "configs" / "training" / "gbmbert_ner_pubmedbert.json",
        split_dir,
        label_map_dir=tmp_path / "labels",
    )

    assert experiment.training_enabled is False
    assert experiment.checks["evaluation_file_exists"] is True
    assert experiment.checks["label_map_exists"] is True


def test_checkpoint_registry_replaces_existing_entry(tmp_path: Path) -> None:
    registry_path = tmp_path / "checkpoint_registry.json"

    register_checkpoint(
        registry_path,
        name="gbmbert_ner_v1",
        checkpoint_dir=tmp_path / "checkpoints" / "ner",
        task="ner",
        base_model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
        notes="initial registration",
    )
    register_checkpoint(
        registry_path,
        name="gbmbert_ner_v1",
        checkpoint_dir=tmp_path / "checkpoints" / "ner",
        task="ner",
        base_model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
        status="evaluated",
        notes="updated registration",
    )

    registry = load_registry(registry_path)

    assert len(registry["checkpoints"]) == 1
    assert registry["checkpoints"][0]["status"] == "evaluated"
    assert "Research-use only" in registry["warning"]


def test_split_annotation_dataset_rebalances_tiny_tasks(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    _write_jsonl(dataset_dir / "ner.jsonl", [])
    _write_jsonl(dataset_dir / "evidence.jsonl", [])
    _write_jsonl(
        dataset_dir / "relations.jsonl",
        [
            {"task": "relation", "source_pmid": "1", "text": "a", "label": "ASSOCIATED_WITH"},
            {"task": "relation", "source_pmid": "2", "text": "b", "label": "ASSOCIATED_WITH"},
            {"task": "relation", "source_pmid": "3", "text": "c", "label": "PREDICTS"},
        ],
    )

    manifest = split_annotation_dataset(dataset_dir, tmp_path / "splits")
    relation_summary = next(task for task in manifest.tasks if task.task == "relation")

    assert relation_summary.split_counts == {"train": 1, "validation": 1, "test": 1}


def test_load_prepared_dataset_and_label_map(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "splits"
    dataset_dir.mkdir()
    _write_jsonl(dataset_dir / "evidence_train.jsonl", [{"task": "evidence", "source_pmid": "1", "text": "A", "label": 0}])
    _write_jsonl(
        dataset_dir / "evidence_validation.jsonl",
        [{"task": "evidence", "source_pmid": "2", "text": "B", "label": 1}],
    )
    _write_jsonl(dataset_dir / "evidence_test.jsonl", [{"task": "evidence", "source_pmid": "3", "text": "C", "label": 1}])
    label_dir = tmp_path / "labels"
    label_dir.mkdir()
    (label_dir / "evidence_label_map.json").write_text(
        json.dumps({"task": "evidence", "label_to_id": {"0": 0, "1": 1}}),
        encoding="utf-8",
    )

    dataset = load_prepared_dataset(dataset_dir, "evidence")

    assert dataset_split_counts(dataset) == {"train": 1, "validation": 1, "test": 1}
    assert dataset["train"][0]["label"] == "0"
    assert load_label_map(label_dir, "evidence") == {"0": 0, "1": 1}


def test_tokenize_dataset_handles_classification_and_ner_labels(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "splits"
    dataset_dir.mkdir()
    for split, label in [("train", "0"), ("validation", "1"), ("test", "1")]:
        _write_jsonl(
            dataset_dir / f"evidence_{split}.jsonl",
            [{"task": "evidence", "source_pmid": split, "text": "MGMT response", "label": label}],
        )
    dataset = load_prepared_dataset(dataset_dir, "evidence")

    tokenized = tokenize_dataset(
        dataset,
        task="evidence",
        tokenizer=FakeTokenizer(),
        label_to_id={"0": 0, "1": 1},
        max_length=5,
    )
    summary = summarize_tokenized_dataset(tokenized, task="evidence", max_length=5)

    assert tokenized["train"][0]["labels"] == 0
    assert summary.splits == {"train": 1, "validation": 1, "test": 1}
    assert "input_ids" in summary.columns

    ner_dir = tmp_path / "ner_splits"
    ner_dir.mkdir()
    for split in ["train", "validation", "test"]:
        _write_jsonl(
            ner_dir / f"ner_{split}.jsonl",
            [{"task": "ner", "source_pmid": split, "text": "MGMT", "label": "GENE", "start": 0, "end": 4}],
        )
    ner_dataset = load_prepared_dataset(ner_dir, "ner")
    ner_tokenized = tokenize_dataset(
        ner_dataset,
        task="ner",
        tokenizer=FakeTokenizer(),
        label_to_id={"GENE": 0},
        max_length=4,
    )

    assert ner_tokenized["train"][0]["labels"] == [0, -100, -100, -100]


def test_training_gate_report_blocks_execute_but_allows_dry_run(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "splits"
    dataset_dir.mkdir()
    for split, label in [("train", "GENE"), ("validation", "DRUG"), ("test", "GENE")]:
        _write_jsonl(
            dataset_dir / f"ner_{split}.jsonl",
            [{"task": "ner", "source_pmid": split, "text": label, "label": label, "start": 0, "end": len(label)}],
        )
    label_dir = tmp_path / "labels"
    label_dir.mkdir()
    (label_dir / "ner_label_map.json").write_text(
        json.dumps({"task": "ner", "label_to_id": {"DRUG": 0, "GENE": 1}}),
        encoding="utf-8",
    )

    dry_run = build_training_gate_report(
        config_path=ROOT / "configs" / "training" / "gbmbert_ner_pubmedbert.json",
        dataset_dir=dataset_dir,
        label_map_dir=label_dir,
        experiment_manifest_path=tmp_path / "experiment_manifest.json",
    )
    execute = build_training_gate_report(
        config_path=ROOT / "configs" / "training" / "gbmbert_ner_pubmedbert.json",
        dataset_dir=dataset_dir,
        label_map_dir=label_dir,
        execute_training=True,
    )

    assert dry_run.status == "dry_run_ready"
    assert dry_run.checks["experiment_manifest_exists"] is True
    assert dry_run.dataset_splits == {"train": 1, "validation": 1, "test": 1}
    assert execute.status == "blocked"
    assert "refused" in " ".join(execute.warnings)


def test_evaluation_report_computes_macro_metrics() -> None:
    report = evaluate_predictions(
        task="evidence_classification",
        true_labels=["0", "1", "1"],
        predicted_labels=["0", "0", "1"],
        label_set=["0", "1"],
    )

    assert report.examples == 3
    assert report.accuracy == pytest.approx(2 / 3)
    assert report.confusion_matrix["1"]["0"] == 1
    assert report.macro_f1 == pytest.approx((2 / 3 + 2 / 3) / 2)


def test_execute_evidence_training_writes_metrics_manifest_and_registry(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "splits"
    dataset_dir.mkdir()
    for split, rows in {
        "train": [{"task": "evidence", "source_pmid": "1", "text": "low evidence", "label": "0"}],
        "validation": [{"task": "evidence", "source_pmid": "2", "text": "high evidence", "label": "1"}],
        "test": [
            {"task": "evidence", "source_pmid": "3", "text": "low evidence", "label": "0"},
            {"task": "evidence", "source_pmid": "4", "text": "high evidence", "label": "1"},
        ],
    }.items():
        _write_jsonl(dataset_dir / f"evidence_{split}.jsonl", rows)
    label_dir = tmp_path / "labels"
    label_dir.mkdir()
    (label_dir / "evidence_label_map.json").write_text(
        json.dumps({"task": "evidence", "label_to_id": {"0": 0, "1": 1}}),
        encoding="utf-8",
    )
    config_path = tmp_path / "training_config.json"
    config = TrainingConfig(
        name="gbmbert_evidence_test",
        task=TrainingTask.EVIDENCE_CLASSIFICATION,
        base_model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
        train_path=dataset_dir / "evidence_train.jsonl",
        validation_path=dataset_dir / "evidence_validation.jsonl",
        output_dir=tmp_path / "checkpoint",
        label_set=["0", "1"],
        hyperparameters={"max_length": 4},
        training_enabled=True,
    )
    config_path.write_text(json.dumps(config.model_dump(mode="json")), encoding="utf-8")

    result = execute_evidence_training(
        config=config,
        config_path=config_path,
        dataset_dir=dataset_dir,
        label_map_dir=label_dir,
        metrics_output=tmp_path / "metrics.json",
        evaluation_markdown_output=tmp_path / "metrics.md",
        run_manifest_output=tmp_path / "run_manifest.json",
        registry_path=tmp_path / "checkpoint_registry.json",
        checkpoint_name="gbmbert_evidence_test",
        tokenizer_loader=lambda base_model, local_files_only: FakeTokenizer(),
        trainer_factory=lambda **kwargs: FakeTrainer(kwargs["tokenized"]),
    )

    registry = load_registry(tmp_path / "checkpoint_registry.json")

    assert result.status == "completed"
    assert Path(result.metrics_path).exists()
    assert Path(result.run_manifest_path).exists()
    assert (tmp_path / "metrics.md").exists()
    assert registry["checkpoints"][0]["status"] == "research_candidate"
    assert registry["checkpoints"][0]["metrics_path"] == str(tmp_path / "metrics.json")
    assert json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))["task"] == "evidence_classification"
    assert result.evaluation.accuracy == 1.0


def test_score_evidence_jsonl_writes_research_predictions(tmp_path: Path) -> None:
    registry_path = tmp_path / "checkpoint_registry.json"
    register_checkpoint(
        registry_path,
        name="gbmbert_evidence_test",
        checkpoint_dir=tmp_path / "checkpoint",
        task="evidence_classification",
        base_model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
        status="research_candidate",
    )
    input_path = tmp_path / "evidence_rows.jsonl"
    _write_jsonl(input_path, [{"source_pmid": "1", "text": "Phase II study"}])

    count = score_evidence_jsonl(
        input_jsonl=input_path,
        output_jsonl=tmp_path / "predictions.jsonl",
        registry_path=registry_path,
        checkpoint_name="gbmbert_evidence_test",
        predictor=lambda texts, checkpoint: [{"label": "1", "confidence": 0.91} for _ in texts],
    )
    prediction = json.loads((tmp_path / "predictions.jsonl").read_text(encoding="utf-8").strip())

    assert count == 1
    assert prediction["source_pmid"] == "1"
    assert prediction["prediction"] == "1"
    assert prediction["checkpoint_status"] == "research_candidate"
    assert "Research-use only" in prediction["warning"]


def test_build_model_card_summarizes_registry_metrics_and_manifest(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"examples": 2, "accuracy": 1.0, "macro_f1": 1.0}), encoding="utf-8")
    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(
        json.dumps({"metrics_path": str(metrics_path), "dataset_dir": "data/training/splits", "label_map_dir": "labels"}),
        encoding="utf-8",
    )
    registry_path = tmp_path / "checkpoint_registry.json"
    register_checkpoint(
        registry_path,
        name="gbmbert_evidence_test",
        checkpoint_dir=tmp_path / "checkpoint",
        task="evidence_classification",
        base_model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
        status="research_candidate",
        metrics_path=metrics_path,
        manifest_path=manifest_path,
    )

    card = build_model_card(registry_path=registry_path, checkpoint_name="gbmbert_evidence_test")
    markdown = format_model_card_markdown(card)

    assert card.metrics["accuracy"] == 1.0
    assert card.run_manifest["dataset_dir"] == "data/training/splits"
    assert "not medical advice" in markdown
    assert "research_candidate" in markdown


def test_run_training_smoke_creates_fixture_outputs(tmp_path: Path) -> None:
    summary = run_training_smoke(
        output_dir=tmp_path / "smoke_data",
        reports_dir=tmp_path / "smoke_reports",
        registry_path=tmp_path / "checkpoint_registry.json",
        checkpoint_name="gbmbert_evidence_smoke_test",
    )
    registry = load_registry(tmp_path / "checkpoint_registry.json")

    assert summary["status"] == "completed"
    assert Path(summary["metrics_path"]).exists()
    assert Path(summary["run_manifest_path"]).exists()
    assert registry["checkpoints"][0]["name"] == "gbmbert_evidence_smoke_test"
    assert registry["checkpoints"][0]["status"] == "research_candidate"


class FakeTokenizer:
    def __call__(
        self,
        texts: list[str],
        *,
        truncation: bool,
        padding: str,
        max_length: int,
    ) -> dict[str, list[list[int]]]:
        del truncation, padding
        input_ids: list[list[int]] = []
        attention_mask: list[list[int]] = []
        for text in texts:
            token_count = min(max(len(text.split()), 1), max_length)
            mask = [1] * token_count + [0] * (max_length - token_count)
            input_ids.append(list(range(1, max_length + 1)))
            attention_mask.append(mask)
        return {"input_ids": input_ids, "attention_mask": attention_mask}


class FakePredictionOutput:
    predictions = [[0.9, 0.1], [0.1, 0.9]]
    label_ids = [0, 1]


class FakeTrainer:
    def __init__(self, tokenized: object) -> None:
        self.tokenized = tokenized

    def train(self) -> None:
        return None

    def save_model(self, output_dir: str) -> None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        (Path(output_dir) / "fake-model.txt").write_text("fake", encoding="utf-8")

    def predict(self, dataset: object) -> FakePredictionOutput:
        del dataset
        return FakePredictionOutput()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")
