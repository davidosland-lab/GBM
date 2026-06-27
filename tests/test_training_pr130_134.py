import json
from pathlib import Path

from gbmbert.launcher_check import check_launcher_menu
from gbmbert.ci_report_summary import build_ci_report_summary
from gbmbert.training.curated_fixture_import import import_curated_training_fixture
from gbmbert.training.governance import build_training_label_drift_report, review_training_config_suite
from gbmbert.training.promotion_review import review_gold_pack_promotion


def test_label_drift_uses_config_specific_governance_dataset(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    full_dir = tmp_path / "full"
    _write_jsonl(smoke_dir / "evidence_train.jsonl", [{"source_pmid": "1", "label": "0"}])
    _write_jsonl(smoke_dir / "evidence_validation.jsonl", [{"source_pmid": "2", "label": "1"}])
    _write_jsonl(smoke_dir / "evidence_test.jsonl", [{"source_pmid": "3", "label": "0"}])
    _write_jsonl(full_dir / "evidence_train.jsonl", [{"source_pmid": "4", "label": str(label)} for label in range(6)])
    _write_jsonl(full_dir / "evidence_validation.jsonl", [{"source_pmid": "5", "label": "0"}])
    _write_jsonl(full_dir / "evidence_test.jsonl", [{"source_pmid": "6", "label": "1"}])
    current = _config(tmp_path / "current.json", "current", smoke_dir, ["0", "1"], "current")
    scaffold = _config(tmp_path / "scaffold.json", "scaffold", full_dir, ["0", "1", "2", "3", "4", "5"], "scaffold")

    report = build_training_label_drift_report(config_paths=[current, scaffold])

    assert report.warning_count == 0
    assert [row.governance_profile for row in report.rows] == ["current", "scaffold"]
    assert report.rows[0].dataset_dir == str(smoke_dir)
    assert report.rows[1].dataset_dir == str(full_dir)


def test_default_training_config_scan_skips_threshold_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "configs" / "training"
    split_dir = tmp_path / "splits"
    config_dir.mkdir(parents=True)
    _write_jsonl(split_dir / "evidence_train.jsonl", [{"source_pmid": "1", "label": "0"}])
    _write_jsonl(split_dir / "evidence_validation.jsonl", [{"source_pmid": "2", "label": "1"}])
    _write_jsonl(split_dir / "evidence_test.jsonl", [{"source_pmid": "3", "label": "0"}])
    _config(config_dir / "gbmbert_evidence_smoke_pubmedbert.json", "current", split_dir, ["0", "1"], "current")
    _write_json(
        config_dir / "gold_pack_promotion_thresholds.json",
        {"min_examples_per_task": 100, "min_examples_per_label": 10, "min_source_pmids": 50},
    )

    suite = review_training_config_suite()
    drift = build_training_label_drift_report()

    assert suite.config_count == 1
    assert [row.name for row in drift.rows] == ["current"]
    assert drift.warning_count == 0


def test_curated_fixture_import_requires_pmids_and_review_metadata(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.jsonl"
    entities = tmp_path / "entities.jsonl"
    reviewed = tmp_path / "reviewed.jsonl"
    _write_jsonl(
        evidence,
        [{"source_pmid": "1", "label": 0, "review_status": "accepted", "reviewer": "curator", "review_notes": "ok"}],
    )
    _write_jsonl(entities, [{"pmid": "1", "entities": [{"label": "GENE", "text": "IDH1"}]}])
    _write_jsonl(
        reviewed,
        [{"source_pmid": "1", "item_type": "evidence_claim", "review_status": "accepted", "reviewer": "curator", "review_notes": "ok"}],
    )

    report = import_curated_training_fixture(
        evidence_jsonl=evidence,
        entity_jsonl=entities,
        reviewed_queue_jsonl=reviewed,
        output_dir=tmp_path / "imported",
    )

    assert report.safe is True
    assert report.evidence_rows == 1
    assert report.entity_rows == 1
    assert report.reviewed_item_types == {"evidence_claim": 1}
    assert (tmp_path / "imported" / "evidence.jsonl").exists()
    assert (tmp_path / "imported" / "combined_evidence.jsonl").exists()


def test_curated_fixture_import_combines_multiple_files(tmp_path: Path) -> None:
    evidence_a = tmp_path / "evidence_a.jsonl"
    evidence_b = tmp_path / "evidence_b.jsonl"
    entities = tmp_path / "entities.jsonl"
    reviewed = tmp_path / "reviewed.jsonl"
    _write_jsonl(evidence_a, [{"source_pmid": "1", "label": 0, "review_status": "accepted", "reviewer": "a", "review_notes": "ok"}])
    _write_jsonl(evidence_b, [{"source_pmid": "2", "label": 1, "review_status": "accepted", "reviewer": "b", "review_notes": "ok"}])
    _write_jsonl(entities, [{"pmid": "1", "entities": []}, {"pmid": "2", "entities": []}])
    _write_jsonl(
        reviewed,
        [
            {"source_pmid": "1", "item_type": "evidence_claim", "review_status": "accepted", "reviewer": "a", "review_notes": "ok"},
            {"source_pmid": "2", "item_type": "graph_relation", "review_status": "accepted", "reviewer": "b", "review_notes": "ok"},
        ],
    )

    report = import_curated_training_fixture(
        evidence_jsonl=[evidence_a, evidence_b],
        entity_jsonl=[entities],
        reviewed_queue_jsonl=[reviewed],
        output_dir=tmp_path / "imported",
        copy_files=False,
    )

    assert report.safe is True
    assert report.evidence_rows == 2
    assert report.pmid_count == 2
    assert len((tmp_path / "imported" / "combined_evidence.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_launcher_menu_check_parses_grouped_menu() -> None:
    report = check_launcher_menu("launcher_menu.bat")

    assert report.safe is True
    assert report.missing_shortcuts == []
    assert report.missing_goto_targets == []


def test_gold_pack_promotion_review_blocks_minimal_fixture(tmp_path: Path) -> None:
    split_dir = tmp_path / "splits"
    for task in ("evidence", "ner", "relation"):
        _write_jsonl(split_dir / f"{task}_train.jsonl", [{"source_pmid": "1", "label": 0 if task == "evidence" else "A"}])
        _write_jsonl(split_dir / f"{task}_validation.jsonl", [{"source_pmid": "2", "label": "A"}])
        _write_jsonl(split_dir / f"{task}_test.jsonl", [{"source_pmid": "3", "label": "A"}])
    pack = tmp_path / "gold_training_pack.json"
    pack.write_text(json.dumps({"ready": True, "split_dir": str(split_dir)}), encoding="utf-8")

    thresholds = tmp_path / "thresholds.json"
    thresholds.write_text(json.dumps({"min_examples_per_task": 10, "min_examples_per_label": 5, "min_source_pmids": 10}), encoding="utf-8")

    report = review_gold_pack_promotion(gold_pack_report=pack, threshold_config=thresholds)

    assert report.promotable is False
    assert report.pack_ready is True
    assert report.label_counts["evidence"]["0"] == 1
    assert report.blockers


def test_ci_report_summary_compacts_report_status(tmp_path: Path) -> None:
    _write_json(tmp_path / "reports/platform_regression/local_verification.json", {"passed": True, "passed_step_count": 8, "step_count": 8})
    _write_json(tmp_path / "reports/platform_regression/artifact_policy.json", {"safe": True, "finding_count": 0})
    _write_json(tmp_path / "reports/platform_regression/launcher_menu_check.json", {"safe": True, "warning_count": 0})
    _write_json(tmp_path / "reports/training/governance/training_governance_suite.json", {"passed": True, "warnings": []})
    _write_json(tmp_path / "reports/training/governance_strict/training_governance_suite.json", {"passed": False, "warnings": ["scaffold"]})
    _write_json(tmp_path / "reports/training/gold_pack/gold_pack_promotion_review.json", {"promotable": False, "blockers": ["small"]})

    summary = build_ci_report_summary(tmp_path)

    assert "GBM-AI CI Verification Summary" in summary
    assert "| Local verification | pass | 8/8 steps |" in summary
    assert "| Gold-pack promotion | review | 1 blocker(s) |" in summary


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _config(path: Path, name: str, dataset_dir: Path, labels: list[str], profile: str) -> Path:
    path.write_text(
        json.dumps(
            {
                "name": name,
                "governance_profile": profile,
                "governance_dataset_dir": str(dataset_dir),
                "task": "evidence_classification",
                "base_model": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                "train_path": str(dataset_dir / "evidence_train.jsonl"),
                "validation_path": str(dataset_dir / "evidence_validation.jsonl"),
                "output_dir": f"models/{name}",
                "label_set": labels,
                "hyperparameters": {"epochs": 3, "learning_rate": 0.00002, "batch_size": 8, "max_length": 256},
            }
        ),
        encoding="utf-8",
    )
    return path
