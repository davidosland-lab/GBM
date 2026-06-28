import json
from pathlib import Path

from gbmbert.ci_report_summary import build_ci_report_summary, validate_ci_report_summary_contract
from gbmbert.launcher_check import check_launcher_menu
from gbmbert.training.promotion_planning import build_gold_pack_promotion_planning_report

CURATED_DIR = Path("data/training/curated_expansion")
ROUND6_PMIDS = {"28967586", "29380516", "31562462", "33417753", "35020937", "37314262"}


def test_round6_curated_fixtures_extend_pmid_coverage() -> None:
    evidence = _read_jsonl(CURATED_DIR / "evidence_round6.jsonl")
    entities = _read_jsonl(CURATED_DIR / "gold_entities_round6.jsonl")
    reviewed = _read_jsonl(CURATED_DIR / "gold_reviewed_queue_round6.jsonl")

    assert len(evidence) == 6
    assert len(entities) == 6
    assert len(reviewed) == 12  # 6 evidence_claim + 6 graph_relation
    assert {str(row["source_pmid"]) for row in evidence} == ROUND6_PMIDS
    assert {row["item_type"] for row in reviewed} == {"evidence_claim", "graph_relation"}
    # Round 6 must introduce brand-new PMIDs (not reuse rounds 1-5) so the gold
    # pack source-PMID count keeps moving toward the promotion threshold.
    prior_pmids: set[str] = set()
    for prior in ("evidence_full_label", "evidence_round2", "evidence_round3", "evidence_round4", "evidence_round5"):
        prior_pmids |= {str(row["source_pmid"]) for row in _read_jsonl(CURATED_DIR / f"{prior}.jsonl")}
    assert ROUND6_PMIDS.isdisjoint(prior_pmids)


def test_promotion_planning_reports_label_balance_to_task_volume_relationship(tmp_path: Path) -> None:
    review_path = tmp_path / "promotion.json"
    _write_json(
        review_path,
        {
            "promotable": False,
            "source_pmid_delta": 4,
            "task_example_deltas": {"evidence": 20, "ner": 8, "relation": 0},
            "label_example_deltas": {
                "evidence": {"0": 3, "1": 2},
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

    # The new relationship view ties label-floor deltas to the task-volume delta.
    assert report.label_balance_relationship["evidence"] == {
        "task_example_delta": 20,
        "label_delta_total": 5,
        "remaining_task_volume_after_labels": 15,
    }
    assert report.label_balance_relationship["ner"]["remaining_task_volume_after_labels"] == 4
    label_batches = [b for b in report.batches if b.batch_type == "label_balance"]
    assert label_batches
    assert all(b.counts_toward_task_volume for b in label_batches)
    assert all(b.task_volume_delta == report.task_remaining_examples[b.task] for b in report.batches if b.task != "all")


def test_ci_summary_surfaces_governance_detail_contract(tmp_path: Path) -> None:
    _write_required_ci_reports(tmp_path)
    _write_json(
        tmp_path / "reports/training/governance_detail_contract.json",
        {"valid": True, "missing_required_rows": []},
    )

    summary = build_ci_report_summary(tmp_path)

    assert "| Governance detail contract | pass | 0 missing row(s) |" in summary
    assert "governance detail contract is a visibility signal" in summary


def test_ci_summary_keeps_missing_governance_detail_contract_visible(tmp_path: Path) -> None:
    _write_required_ci_reports(tmp_path)

    summary = build_ci_report_summary(tmp_path)

    # Optional report absent -> still listed as a review signal, never an error.
    assert "| Governance detail contract | review | report missing |" in summary


def test_ci_contract_now_requires_governance_detail_contract_family(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.md"
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
                "Strict governance and gold-pack promotion are audit signals.",
            ]
        ),
        encoding="utf-8",
    )

    contract = validate_ci_report_summary_contract(summary_path)

    assert contract.valid is False
    assert "Governance detail contract" in contract.missing_families


def test_launcher_menu_includes_multibatch_import_shortcut() -> None:
    report = check_launcher_menu("launcher_menu.bat")

    assert report.safe is True
    assert "16BR" not in report.missing_shortcuts
    text = Path("launcher_menu.bat").read_text(encoding="utf-8")
    assert ":curated_fixture_import_multibatch" in text
    assert "evidence_round6.jsonl" in text


def _write_required_ci_reports(root: Path) -> None:
    _write_json(root / "reports/platform_regression/local_verification.json", {"passed": True, "passed_step_count": 8, "step_count": 8})
    _write_json(root / "reports/platform_regression/artifact_policy.json", {"safe": True, "finding_count": 0})
    _write_json(root / "reports/platform_regression/launcher_menu_check.json", {"safe": True, "warning_count": 0})
    _write_json(root / "reports/training/governance/training_governance_suite.json", {"passed": True, "warnings": []})
    _write_json(root / "reports/training/governance_strict/training_governance_suite.json", {"passed": False, "warnings": ["scaffold"]})
    _write_json(root / "reports/training/gold_pack/gold_pack_promotion_review.json", {"promotable": False, "blockers": ["small"]})


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
