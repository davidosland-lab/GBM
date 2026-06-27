import json
from pathlib import Path

from gbmbert.artifacts import build_artifact_index, save_artifact_index_json
from gbmbert.training.governance import (
    audit_training_pack_leakage,
    audit_training_provenance,
    build_dashboard_training_manifest,
    build_registry_remediation_plan,
    build_training_artifact_bundle,
    build_training_label_drift_report,
    build_training_readiness_snapshot,
    review_training_config_suite,
    run_training_governance_suite,
    search_training_artifacts,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_training_artifact_bundle_and_search_use_artifact_index(tmp_path: Path) -> None:
    training_dir = tmp_path / "reports" / "training"
    training_dir.mkdir(parents=True)
    (training_dir / "relation_training_pack.md").write_text("# Relation Pack\n", encoding="utf-8")
    index = build_artifact_index([tmp_path / "reports"])
    index_path = tmp_path / "artifact_index.json"
    save_artifact_index_json(index, index_path)

    bundle = build_training_artifact_bundle(output_dir=tmp_path / "bundle", index_json=index_path)
    search = search_training_artifacts("relation_training_pack", index_json=index_path)

    assert bundle.artifact_count == 1
    assert "relation_training_pack.md" in bundle.entries[0].source_path
    assert search.match_count == 1
    assert search.artifacts[0]["artifact_type"] == "relation_training_pack_report"


def test_training_pack_leakage_detects_cross_pack_overlap(tmp_path: Path) -> None:
    evidence_split = tmp_path / "evidence" / "splits"
    relation_split = tmp_path / "relation" / "splits"
    _write_jsonl(evidence_split / "evidence_train.jsonl", [{"source_pmid": "1", "label": "1"}])
    _write_jsonl(relation_split / "relation_train.jsonl", [{"source_pmid": "1", "label": "NO_RELATION"}])
    evidence_report = tmp_path / "evidence.json"
    relation_report = tmp_path / "relation.json"
    evidence_report.write_text(json.dumps({"split_dataset_dir": str(evidence_split), "ready": True}), encoding="utf-8")
    relation_report.write_text(json.dumps({"split_dataset_dir": str(relation_split), "ready": True}), encoding="utf-8")

    report = audit_training_pack_leakage(evidence_pack_report=evidence_report, relation_pack_report=relation_report, gold_pack_report=None)

    assert report.safe is True
    assert report.cross_pack_warnings
    assert "shared PMID" in report.cross_pack_warnings[0]


def test_registry_remediation_plan_maps_audit_findings(tmp_path: Path) -> None:
    audit = tmp_path / "model_registry_audit.json"
    audit.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "name": "x",
                        "errors": ["x: checkpoint_dir does not exist"],
                        "warnings": ["x: no matching model card found"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    plan = build_registry_remediation_plan(audit)

    assert plan.action_count == 2
    assert "checkpoint directory" in plan.actions[0].suggested_action
    assert "model card" in plan.actions[1].suggested_action


def test_training_provenance_audit_checks_warning_pmid_and_source_type(tmp_path: Path) -> None:
    dataset = tmp_path / "relation_training_pack.jsonl"
    _write_jsonl(
        dataset,
        [
            {
                "source_pmid": "1",
                "label": "NO_RELATION",
                "relation_pack_source_type": "synthetic_no_relation",
                "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
            }
        ],
    )

    report = audit_training_provenance(dataset)

    assert report.safe is True
    assert report.source_type_counts == {"synthetic_no_relation": 1}


def test_dashboard_manifest_and_snapshot_read_local_context(tmp_path: Path) -> None:
    reports = tmp_path / "reports" / "training"
    relation = reports / "relation_pack"
    relation.mkdir(parents=True)
    (relation / "relation_training_pack.md").write_text("# Relation\n", encoding="utf-8")
    (relation / "relation_training_pack.json").write_text('{"ready":true}\n', encoding="utf-8")
    (reports / "relation_training_config_review.json").write_text('{"status":"passed"}\n', encoding="utf-8")
    (reports / "model_registry_audit.json").write_text('{"passed":true}\n', encoding="utf-8")
    models = tmp_path / "models"
    models.mkdir()
    (models / "checkpoint_registry.json").write_text('{"checkpoints":[{"name":"x"}]}\n', encoding="utf-8")

    manifest = build_dashboard_training_manifest(tmp_path / "dashboard_training_manifest.json", root=tmp_path)
    snapshot = build_training_readiness_snapshot(tmp_path)

    assert manifest.ready_pack_count == 1
    assert manifest.registry_entry_count == 1
    assert snapshot.relation_config_status == "passed"


def test_config_suite_and_label_drift_return_reports() -> None:
    suite = review_training_config_suite([])
    drift = build_training_label_drift_report(evidence_pack_report=None, relation_pack_report=None, gold_pack_report=None)

    assert suite.config_count == 0
    assert suite.passed_count == 0
    assert drift.warning_count == 0


def test_training_governance_suite_writes_report(tmp_path: Path) -> None:
    report = run_training_governance_suite(tmp_path / "governance")

    assert report.step_count == 10
    assert (tmp_path / "governance" / "training_governance_suite.json").exists()
    assert "bundle" in report.artifacts
