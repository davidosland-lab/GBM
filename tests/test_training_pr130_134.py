import json
from pathlib import Path

from gbmbert.launcher_check import check_launcher_menu
from gbmbert.ci_report_summary import CIReportInputError, build_ci_report_summary, validate_ci_report_summary_contract
from gbmbert.training.governance_detail_export import build_governance_detail_export, validate_governance_detail_contract
from gbmbert.training.curated_fixture_import import import_curated_training_fixture
from gbmbert.training.curated_provenance_diff import build_curated_provenance_diff, format_curated_provenance_diff_markdown
from gbmbert.training.governance import build_training_label_drift_report, review_training_config_suite
from gbmbert.training.promotion_planning import build_gold_pack_promotion_planning_report
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


def test_curated_provenance_diff_flags_changed_and_withdrawn_reviewed_rows(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.jsonl"
    entities = tmp_path / "entities.jsonl"
    reviewed_a = tmp_path / "reviewed_a.jsonl"
    reviewed_b = tmp_path / "reviewed_b.jsonl"
    _write_jsonl(evidence, [{"source_pmid": "1", "label": 0, "review_status": "accepted", "reviewer": "a", "review_notes": "ok"}])
    _write_jsonl(entities, [{"pmid": "1", "entities": [{"label": "GENE", "text": "IDH1", "start": 0, "end": 4}]}])
    _write_jsonl(
        reviewed_a,
        [
            {
                "item_id": "item-1",
                "source_pmid": "1",
                "item_type": "evidence_claim",
                "evidence_tier": 0,
                "review_status": "accepted",
                "reviewer": "a",
                "text": "same text",
            }
        ],
    )
    _write_jsonl(
        reviewed_b,
        [
            {
                "item_id": "item-1",
                "source_pmid": "1",
                "item_type": "evidence_claim",
                "evidence_tier": 1,
                "review_status": "withdrawn",
                "reviewer": "b",
                "text": "same text",
            }
        ],
    )

    report = build_curated_provenance_diff(
        evidence_jsonl=[evidence],
        entity_jsonl=[entities],
        reviewed_queue_jsonl=[reviewed_a, reviewed_b],
    )
    markdown = format_curated_provenance_diff_markdown(report)

    assert report.safe is False
    assert report.changed_count == 1
    assert report.withdrawn_count == 1
    assert report.task_counts["evidence"] == 3
    assert "Changed reviewed examples: 1" in markdown
    assert "Withdrawn/rejected reviewed examples: 1" in markdown


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
    assert report.task_example_deltas["evidence"] == 7
    assert report.label_example_deltas["evidence"]["0"] == 4
    assert report.source_pmid_delta == 7
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


def test_ci_report_summary_requires_verification_inputs(tmp_path: Path) -> None:
    _write_json(tmp_path / "reports/platform_regression/local_verification.json", {"passed": True, "passed_step_count": 8, "step_count": 8})

    try:
        build_ci_report_summary(tmp_path)
    except CIReportInputError as exc:
        assert "required report not found" in str(exc)
    else:
        raise AssertionError("Expected missing CI summary inputs to fail")


def test_ci_report_summary_contract_requires_all_report_families(tmp_path: Path) -> None:
    summary_path = tmp_path / "reports/platform_regression/ci_report_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "\n".join(
            [
                "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
                "| Local verification | pass | 8/8 steps |",
                "| Artifact policy | pass | 0 findings |",
                "| Launcher menu | pass | 0 warnings |",
                "| Default governance | pass | 0 warnings |",
                "| Strict governance audit | review | 1 expected audit warning(s) |",
                "| Gold-pack promotion | review | 1 blocker(s) |",
                "| Governance detail contract | pass | 0 missing row(s) |",
                "Strict governance and gold-pack promotion are audit signals.",
            ]
        ),
        encoding="utf-8",
    )

    contract = validate_ci_report_summary_contract(summary_path)

    assert contract.valid is True
    assert contract.missing_families == []
    assert contract.audit_signal_note_present is True


def test_governance_detail_export_keeps_missing_reports_visible(tmp_path: Path) -> None:
    _write_json(tmp_path / "reports/training/curated_fixture_import.json", {"safe": True})
    (tmp_path / "reports/training/curated_fixture_import.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports/training/curated_fixture_import.md").write_text("# Import\n", encoding="utf-8")

    report = build_governance_detail_export(tmp_path)
    rows = {str(row["title"]): row for row in report.rows}

    assert report.row_count > 0
    assert rows["Curated fixture import"]["status"] == "safe"
    assert rows["Gold-pack promotion review"]["status"] == "missing"
    assert report.missing_count >= 1


def test_promotion_planning_report_groups_deltas_without_promoting(tmp_path: Path) -> None:
    review_path = tmp_path / "promotion.json"
    _write_json(
        review_path,
        {
            "promotable": False,
            "source_pmid_delta": 7,
            "task_example_deltas": {"evidence": 20, "ner": 8, "relation": 0},
            "label_example_deltas": {
                "evidence": {"0": 3, "1": 2, "2": 1},
                "ner": {"GENE": 4},
                "relation": {},
            },
        },
    )

    report = build_gold_pack_promotion_planning_report(
        promotion_review=review_path,
        examples_per_batch=10,
        labels_per_batch=2,
        pmids_per_batch=5,
    )

    assert report.scaffold_only is True
    assert report.promotable_now is False
    assert report.source_pmid_delta == 7
    assert report.task_remaining_examples["evidence"] == 20
    assert report.label_remaining_examples["ner"]["GENE"] == 4
    assert report.source_pmid_batches == [
        {"batch_id": "source-pmid-expansion-001", "suggested_new_pmids": 5},
        {"batch_id": "source-pmid-expansion-002", "suggested_new_pmids": 2},
    ]
    assert report.batch_count >= 4
    assert any(batch.batch_type == "label_balance" for batch in report.batches)
    assert any(batch.batch_type == "source_pmid_expansion" for batch in report.batches)


def test_governance_detail_contract_requires_expected_rows(tmp_path: Path) -> None:
    rows = []
    for title in (
        "Curated fixture import",
        "Curated provenance diff",
        "Evidence pack",
        "Gold pack",
        "Gold-pack promotion review",
        "Launcher menu check",
        "Model registry audit",
        "Relation pack",
        "Training config suite",
        "Training label drift",
        "Training pack comparison",
    ):
        rows.append(
            {
                "title": title,
                "status": "missing",
                "markdown_path": "",
                "markdown_exists": False,
                "json_path": "",
                "json_exists": False,
            }
        )
    detail = tmp_path / "governance_detail_links.json"
    _write_json(
        detail,
        {
            "row_count": len(rows),
            "rows": rows,
            "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        },
    )

    contract = validate_governance_detail_contract(detail)

    assert contract.valid is True
    assert contract.missing_required_rows == []
    assert contract.row_count == len(rows)


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
