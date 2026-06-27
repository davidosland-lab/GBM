import csv
import json
from pathlib import Path

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    NodeLabel,
    RelationType,
)
from gbmbert.training.prediction_curation import (
    PredictionReviewItem,
    audit_curated_evidence,
    analyze_prediction_quality,
    apply_evidence_overlay_to_graph,
    browse_curation_runs,
    build_curation_handoff_bundle,
    build_overlay_diff_report,
    build_prediction_review_queue,
    export_active_learning_batch_csv,
    export_active_learning_candidates,
    export_curated_evidence,
    format_active_learning_batch_roundtrip_markdown,
    format_active_learning_report_markdown,
    format_active_learning_batch_report_markdown,
    format_active_learning_batch_status_markdown,
    format_curation_run_browser_markdown,
    format_curation_handoff_bundle_markdown,
    format_curation_handoff_validation_markdown,
    format_curation_regression_pack_markdown,
    format_curated_evidence_search_markdown,
    format_curated_evidence_audit_markdown,
    format_overlay_diff_markdown,
    format_overlay_report_markdown,
    format_overlay_revert_report_markdown,
    format_prediction_review_summary_markdown,
    format_prediction_quality_markdown,
    import_prediction_review_csv,
    import_active_learning_batch_csv,
    initialize_prediction_reviewed_queue,
    plan_active_learning_batches,
    revert_evidence_overlay_graph,
    run_curation_regression_pack,
    run_curation_smoke_workflow,
    search_curated_evidence,
    save_prediction_review_queue_jsonl,
    summarize_active_learning_batch_status,
    summarize_prediction_review_queue,
    update_curation_run_registry,
    validate_curation_handoff_bundle,
)


def test_prediction_review_queue_flags_low_confidence_and_smoke_rows(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.jsonl"
    predictions_path.write_text(
        "\n".join(
            [
                json.dumps(_prediction_row("12345678", "3", 0.94, status="candidate")),
                json.dumps(_prediction_row("23456789", "LABEL_2", 0.61, status="candidate")),
                json.dumps(_prediction_row("34567890", "1", 0.99, status="smoke_fixture")),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    items = build_prediction_review_queue(predictions_path, min_confidence=0.75)

    assert [item.item_id for item in items] == [
        "prediction:23456789:2",
        "prediction:34567890:3",
    ]
    assert items[0].predicted_evidence_tier == 2
    assert "confidence < 0.75" in items[0].reasons
    assert "checkpoint status: smoke_fixture" in items[1].reasons


def test_initialize_prediction_reviewed_queue_preserves_raw_queue(tmp_path: Path) -> None:
    queue_path = tmp_path / "prediction_review_queue.jsonl"
    reviewed_path = tmp_path / "prediction_reviewed_queue.jsonl"
    csv_path = tmp_path / "prediction_reviewed_queue.csv"
    item = PredictionReviewItem(
        item_id="prediction:12345678:1",
        source_pmid="12345678",
        text="MGMT methylation predicts response.",
        predicted_evidence_tier=3,
        prediction_label="3",
        confidence=0.91,
    )
    save_prediction_review_queue_jsonl([item], queue_path)

    reviewed = initialize_prediction_reviewed_queue(
        queue_path,
        reviewed_path,
        reviewer="curator",
        csv_output=csv_path,
    )

    assert reviewed[0].reviewer == "curator"
    assert reviewed[0].reviewer_id == "curator"
    assert len(reviewed[0].source_queue_sha256) == 64
    assert reviewed[0].review_status == "pending"
    assert queue_path.read_text(encoding="utf-8") != reviewed_path.read_text(encoding="utf-8")
    assert csv_path.exists()


def test_export_active_learning_candidates_prioritizes_review_value(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.jsonl"
    graph_path = tmp_path / "graph.jsonl"
    candidates_path = tmp_path / "active_learning_candidates.jsonl"
    report_path = tmp_path / "active_learning_report.md"
    predictions_path.write_text(
        "\n".join(
            [
                json.dumps(_prediction_row("12345678", "3", 0.94, status="candidate")),
                json.dumps(_prediction_row("23456789", "LABEL_9", 0.61, status="smoke_fixture", warning="")),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    graph_path.write_text(_graph_record("12345678", EvidenceTier.IN_VITRO).model_dump_json() + "\n", encoding="utf-8")

    report = export_active_learning_candidates(
        predictions_jsonl=predictions_path,
        output_jsonl=candidates_path,
        graph_jsonl=graph_path,
        min_confidence=0.8,
    )
    markdown = format_active_learning_report_markdown(report)
    report_path.write_text(markdown, encoding="utf-8")
    rows = [json.loads(line) for line in candidates_path.read_text(encoding="utf-8").splitlines()]

    assert report.candidate_count == 2
    assert rows[0]["source_pmid"] == "23456789"
    assert "invalid evidence prediction label" in rows[0]["reasons"]
    assert "tier-change-sensitive evidence" in rows[1]["reasons"]
    assert "Active Learning Candidate Report" in report_path.read_text(encoding="utf-8")


def test_prediction_quality_report_counts_labels_and_warnings(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.jsonl"
    predictions_path.write_text(
        "\n".join(
            [
                json.dumps(_prediction_row("12345678", "3", 0.94, status="candidate")),
                json.dumps(_prediction_row("", "LABEL_9", 0.4, status="smoke_fixture", warning="")),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = analyze_prediction_quality(predictions_path, low_confidence_threshold=0.75)
    markdown = format_prediction_quality_markdown(report)

    assert report.prediction_count == 2
    assert report.low_confidence_count == 1
    assert report.invalid_prediction_count == 1
    assert report.missing_pmid_count == 1
    assert report.missing_warning_count == 1
    assert "Prediction Quality Report" in markdown
    assert RESEARCH_WARNING in markdown


def test_prediction_review_summary_counts_status_and_tier_shifts(tmp_path: Path) -> None:
    reviewed_path = tmp_path / "reviewed_predictions.jsonl"
    reviewed_path.write_text(
        "\n".join(
            [
                PredictionReviewItem(
                    item_id="prediction:12345678:1",
                    source_pmid="12345678",
                    text="First claim.",
                    predicted_evidence_tier=1,
                    prediction_label="1",
                    confidence=0.9,
                    checkpoint_name="gbmbert_evidence_v1",
                    checkpoint_status="candidate",
                    review_status="accepted",
                    reviewer="curator",
                ).model_dump_json(),
                PredictionReviewItem(
                    item_id="prediction:23456789:2",
                    source_pmid="23456789",
                    text="Second claim.",
                    predicted_evidence_tier=1,
                    prediction_label="1",
                    confidence=0.8,
                    checkpoint_name="gbmbert_evidence_v1",
                    checkpoint_status="candidate",
                    review_status="corrected",
                    reviewer="curator",
                    review_notes="Upgrade after review.",
                    corrected_evidence_tier=3,
                ).model_dump_json(),
                PredictionReviewItem(
                    item_id="prediction:34567890:3",
                    source_pmid="34567890",
                    text="Third claim.",
                    predicted_evidence_tier=2,
                    prediction_label="2",
                    confidence=0.7,
                    checkpoint_name="gbmbert_evidence_v1",
                    checkpoint_status="candidate",
                    review_status="pending",
                    reviewer="curator",
                ).model_dump_json(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = summarize_prediction_review_queue(reviewed_path)
    markdown = format_prediction_review_summary_markdown(summary)

    assert summary.item_count == 3
    assert summary.pending_count == 1
    assert any(item.key == "corrected" and item.count == 1 for item in summary.status_counts)
    assert any(item.key == "1 -> 3" and item.count == 1 for item in summary.tier_shift_counts)
    assert any(item.key == "increased" and item.count == 1 for item in summary.tier_shift_counts)
    assert "Prediction Review Summary" in markdown
    assert "still pending review" in markdown


def test_import_prediction_review_csv_round_trips_manual_edits(tmp_path: Path) -> None:
    csv_path = tmp_path / "reviewed_predictions.csv"
    jsonl_path = tmp_path / "reviewed_predictions.jsonl"
    csv_path.write_text(
        "\n".join(
            [
                "item_id,item_type,source_pmid,text,predicted_evidence_tier,prediction_label,confidence,checkpoint_name,checkpoint_status,checkpoint_dir,reasons,source_file,warning,review_status,reviewer,review_notes,corrected_evidence_tier",
                '"prediction:12345678:1",evidence_prediction,12345678,"Claim text",1,1,0.8,gbmbert_evidence_v1,candidate,models/checkpoint,"confidence < 0.75;manual check",predictions.jsonl,"Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",corrected,curator,"Upgrade tier",3',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    items = import_prediction_review_csv(csv_path, jsonl_path)

    assert len(items) == 1
    assert items[0].review_status == "corrected"
    assert items[0].decision_timestamp_utc
    assert len(items[0].imported_csv_sha256) == 64
    assert items[0].reviewer_id == "curator"
    assert items[0].corrected_evidence_tier == 3
    assert items[0].reasons == ["confidence < 0.75", "manual check"]
    assert jsonl_path.exists()


def test_export_curated_evidence_applies_decisions_without_mutating_predictions(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.jsonl"
    reviewed_path = tmp_path / "reviewed_predictions.jsonl"
    curated_path = tmp_path / "curated_evidence.jsonl"
    predictions_text = (
        "\n".join(
            [
                json.dumps(_prediction_row("12345678", "1", 0.9, text="First claim.")),
                json.dumps(_prediction_row("23456789", "2", 0.8, text="Second claim.")),
                json.dumps(_prediction_row("34567890", "3", 0.7, text="Third claim.")),
            ]
        )
        + "\n"
    )
    predictions_path.write_text(predictions_text, encoding="utf-8")
    reviewed_path.write_text(
        "\n".join(
            [
                PredictionReviewItem(
                    item_id="prediction:12345678:1",
                    source_pmid="12345678",
                    text="First claim.",
                    predicted_evidence_tier=1,
                    prediction_label="1",
                    confidence=0.9,
                    review_status="accepted",
                    reviewer="curator",
                ).model_dump_json(),
                PredictionReviewItem(
                    item_id="prediction:23456789:2",
                    source_pmid="23456789",
                    text="Second claim.",
                    predicted_evidence_tier=2,
                    prediction_label="2",
                    confidence=0.8,
                    review_status="corrected",
                    reviewer="curator",
                    review_notes="Human clinical retrospective evidence.",
                    corrected_evidence_tier=3,
                ).model_dump_json(),
                PredictionReviewItem(
                    item_id="prediction:34567890:3",
                    source_pmid="34567890",
                    text="Third claim.",
                    predicted_evidence_tier=3,
                    prediction_label="3",
                    confidence=0.7,
                    review_status="rejected",
                    reviewer="curator",
                    review_notes="Not supported.",
                ).model_dump_json(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = export_curated_evidence(
        predictions_jsonl=predictions_path,
        reviewed_queue_jsonl=reviewed_path,
        output_jsonl=curated_path,
    )
    curated_rows = [json.loads(line) for line in curated_path.read_text(encoding="utf-8").splitlines()]

    assert predictions_path.read_text(encoding="utf-8") == predictions_text
    assert report.accepted_count == 1
    assert report.corrected_count == 1
    assert report.rejected_count == 1
    assert len(curated_rows) == 2
    assert curated_rows[0]["curated_evidence_tier"] == 1
    assert curated_rows[1]["curated_evidence_tier"] == 3
    assert curated_rows[1]["original_predicted_evidence_tier"] == 2


def test_audit_curated_evidence_flags_missing_provenance(tmp_path: Path) -> None:
    curated_path = tmp_path / "curated_evidence.jsonl"
    curated_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "item_id": "prediction:12345678:1",
                        "source_pmid": "12345678",
                        "curated_evidence_tier": 3,
                        "original_prediction": "3",
                        "original_predicted_evidence_tier": 3,
                        "checkpoint_name": "gbmbert_evidence_v1",
                        "checkpoint_status": "candidate",
                        "review_status": "accepted",
                        "reviewer": "curator",
                        "warning": RESEARCH_WARNING,
                    }
                ),
                json.dumps(
                    {
                        "item_id": "prediction:99999999:2",
                        "source_pmid": "23456789",
                        "curated_evidence_tier": 9,
                        "review_status": "accepted",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit_curated_evidence(curated_path)
    markdown = format_curated_evidence_audit_markdown(report)

    assert report.row_count == 2
    assert report.missing_warning_count == 1
    assert report.missing_checkpoint_count == 1
    assert report.missing_reviewer_count == 1
    assert report.invalid_tier_count == 1
    assert report.linkage_warning_count == 2
    assert "Curated Evidence Audit" in markdown


def test_apply_evidence_overlay_to_graph_updates_new_graph_artifact(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph_records.jsonl"
    curated_path = tmp_path / "curated_evidence.jsonl"
    overlay_path = tmp_path / "evidence_overlay_graph_records.jsonl"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="temozolomide response")
    raw_record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.HYPOTHESIS,
                confidence=0.7,
            )
        ],
    )
    graph_path.write_text(raw_record.model_dump_json() + "\n", encoding="utf-8")
    curated_path.write_text(
        json.dumps(
            {
                "item_id": "prediction:12345678:1",
                "source_pmid": "12345678",
                "curated_evidence_tier": 3,
                "checkpoint_name": "gbmbert_evidence_v1",
                "review_status": "accepted",
                "warning": RESEARCH_WARNING,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = apply_evidence_overlay_to_graph(
        graph_jsonl=graph_path,
        curated_evidence_jsonl=curated_path,
        output_jsonl=overlay_path,
    )
    overlay = KnowledgeGraphRecord.model_validate(json.loads(overlay_path.read_text(encoding="utf-8")))
    markdown = format_overlay_report_markdown(report)

    assert report.changed_relation_count == 1
    assert overlay.relations[0].evidence_tier == EvidenceTier.RETROSPECTIVE_HUMAN
    assert overlay.relations[0].properties["evidence_overlay_original_tier"] == 0
    assert overlay.relations[0].properties["evidence_overlay_checkpoint"] == "gbmbert_evidence_v1"
    assert KnowledgeGraphRecord.model_validate(json.loads(graph_path.read_text(encoding="utf-8"))).relations[
        0
    ].evidence_tier == EvidenceTier.HYPOTHESIS
    assert "Evidence Overlay Report" in markdown


def test_revert_evidence_overlay_graph_restores_original_tier(tmp_path: Path) -> None:
    overlay_path = tmp_path / "overlay.jsonl"
    reverted_path = tmp_path / "reverted.jsonl"
    record = _graph_record("12345678", EvidenceTier.RETROSPECTIVE_HUMAN)
    relation = record.relations[0]
    record.relations[0] = relation.model_copy(
        update={
            "properties": {
                "evidence_overlay_original_tier": 1,
                "evidence_overlay_tier": 3,
                "evidence_overlay_checkpoint": "gbmbert",
            }
        }
    )
    overlay_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = revert_evidence_overlay_graph(overlay_path, reverted_path)
    markdown = format_overlay_revert_report_markdown(report)
    reverted = KnowledgeGraphRecord.model_validate(json.loads(reverted_path.read_text(encoding="utf-8")))

    assert report.reverted_relation_count == 1
    assert reverted.relations[0].evidence_tier == EvidenceTier.IN_VITRO
    assert "evidence_overlay_tier" not in reverted.relations[0].properties
    assert "Evidence Overlay Revert" in markdown


def test_overlay_diff_report_compares_raw_and_overlay_graphs(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw_graph.jsonl"
    overlay_path = tmp_path / "overlay_graph.jsonl"
    raw_path.write_text(_graph_record("12345678", EvidenceTier.IN_VITRO).model_dump_json() + "\n", encoding="utf-8")
    overlay_record = _graph_record("12345678", EvidenceTier.RETROSPECTIVE_HUMAN)
    relation = overlay_record.relations[0]
    overlay_record.relations[0] = relation.model_copy(
        update={
            "properties": {
                **relation.properties,
                "evidence_overlay_original_tier": 1,
                "evidence_overlay_tier": 3,
            }
        }
    )
    overlay_path.write_text(overlay_record.model_dump_json() + "\n", encoding="utf-8")

    report = build_overlay_diff_report(raw_graph_jsonl=raw_path, overlay_graph_jsonl=overlay_path)
    markdown = format_overlay_diff_markdown(report)

    assert report.changed_relation_count == 1
    assert report.increased_tier_count == 1
    assert report.overlay_metadata_count == 1
    assert report.changes[0].detail == "Evidence tier 1 -> 3"
    assert "Evidence Overlay Diff Report" in markdown


def test_curation_smoke_workflow_runs_existing_artifacts(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.jsonl"
    graph_path = tmp_path / "graph.jsonl"
    reviewed_path = tmp_path / "reviewed.jsonl"
    output_dir = tmp_path / "outputs"
    reports_dir = tmp_path / "reports"
    predictions_path.write_text(json.dumps(_prediction_row("12345678", "3", 0.98)) + "\n", encoding="utf-8")
    graph_path.write_text(_graph_record("12345678", EvidenceTier.IN_VITRO).model_dump_json() + "\n", encoding="utf-8")
    reviewed_path.write_text(
        PredictionReviewItem(
            item_id="prediction:12345678:1",
            source_pmid="12345678",
            text="MGMT methylation predicts response.",
            predicted_evidence_tier=3,
            prediction_label="3",
            confidence=0.98,
            checkpoint_name="gbmbert_evidence_v1",
            checkpoint_status="candidate",
            review_status="accepted",
            reviewer="curator",
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    report = run_curation_smoke_workflow(
        predictions_jsonl=predictions_path,
        graph_jsonl=graph_path,
        reviewed_queue_jsonl=reviewed_path,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )

    assert Path(report.candidate_path).exists()
    assert Path(report.curated_evidence_path).exists()
    assert Path(report.overlay_graph_path).exists()
    assert Path(report.overlay_diff_path).exists()
    assert (reports_dir / "curated_evidence_audit.md").exists()


def test_curation_handoff_bundle_copies_artifacts_with_manifest(tmp_path: Path) -> None:
    artifact_one = tmp_path / "prediction_quality.md"
    artifact_two = tmp_path / "curated_evidence_predictions.jsonl"
    missing_artifact = tmp_path / "missing.jsonl"
    artifact_one.write_text("# Quality\n", encoding="utf-8")
    artifact_two.write_text('{"source_pmid":"1"}\n', encoding="utf-8")

    report = build_curation_handoff_bundle(
        artifact_paths=[artifact_one, artifact_two, missing_artifact],
        output_dir=tmp_path / "handoff",
    )
    markdown = format_curation_handoff_bundle_markdown(report)

    assert report.artifact_count == 2
    assert report.copied_artifact_count == 2
    assert report.artifacts[0].artifact_role == "prediction_quality_report"
    assert report.artifacts[0].line_count == 1
    assert len(report.artifacts[0].sha256) == 64
    assert Path(report.artifacts[0].bundled_path).exists()
    assert any("Missing artifact" in warning for warning in report.warnings)
    assert "Curation Handoff Bundle" in markdown
    assert "Research-use only" in markdown


def test_active_learning_batch_planner_groups_candidates(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    batches_path = tmp_path / "batches.jsonl"
    csv_path = tmp_path / "batches.csv"
    items = [
        PredictionReviewItem(
            item_id=f"prediction:123:{index}",
            source_pmid="123",
            text="Claim",
            predicted_evidence_tier=3,
            prediction_label="3",
            confidence=0.9,
            checkpoint_name="ckpt",
            reasons=["tier-change-sensitive evidence"],
        )
        for index in range(1, 4)
    ]
    save_prediction_review_queue_jsonl(items, candidates_path)

    report = plan_active_learning_batches(candidates_path, batches_path, csv_output=csv_path, batch_size=2)
    markdown = format_active_learning_batch_report_markdown(report)
    rows = [json.loads(line) for line in batches_path.read_text(encoding="utf-8").splitlines()]

    assert report.batch_count == 2
    assert rows[0]["batch_id"] == "ALBATCH-001"
    assert rows[2]["batch_id"] == "ALBATCH-002"
    assert csv_path.exists()
    assert "Active Learning Batch Plan" in markdown


def test_active_learning_batch_status_and_csv_roundtrip(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    batches_path = tmp_path / "batches.jsonl"
    batch_csv = tmp_path / "batch.csv"
    imported_path = tmp_path / "reviewed_from_batch.jsonl"
    items = [
        PredictionReviewItem(
            item_id=f"prediction:123:{index}",
            source_pmid="123",
            text="Claim",
            predicted_evidence_tier=3,
            prediction_label="3",
            confidence=0.9,
            checkpoint_name="ckpt",
            reviewer="curator",
            reviewer_id="curator",
            reasons=["tier-change-sensitive evidence"],
        )
        for index in range(1, 3)
    ]
    save_prediction_review_queue_jsonl(items, candidates_path)
    plan_active_learning_batches(candidates_path, batches_path, batch_size=2)

    status = summarize_active_learning_batch_status(batches_path)
    status_markdown = format_active_learning_batch_status_markdown(status)
    export_report = export_active_learning_batch_csv(
        batches_path,
        "ALBATCH-001",
        batch_csv,
        assigned_reviewer="curator",
    )
    with batch_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    rows[0]["review_status"] = "accepted"
    rows[0]["reviewer"] = "curator"
    with batch_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    import_report = import_active_learning_batch_csv(batch_csv, imported_path)
    imported = [json.loads(line) for line in imported_path.read_text(encoding="utf-8").splitlines()]

    assert status.batch_count == 1
    assert status.pending_count == 2
    assert "Active Learning Batch Status" in status_markdown
    assert export_report.row_count == 2
    assert "Batch Roundtrip" in format_active_learning_batch_roundtrip_markdown(export_report)
    assert import_report.row_count == 2
    assert imported[0]["review_status"] == "accepted"
    assert imported[0]["decision_timestamp_utc"]
    assert len(imported[0]["imported_csv_sha256"]) == 64


def test_curation_handoff_validation_checks_hashes_and_required_roles(tmp_path: Path) -> None:
    artifact = tmp_path / "prediction_quality.md"
    artifact.write_text(f"# Quality\n\n{RESEARCH_WARNING}\n", encoding="utf-8")
    bundle = build_curation_handoff_bundle(artifact_paths=[artifact], output_dir=tmp_path / "handoff")
    manifest = tmp_path / "handoff" / "curation_handoff_bundle.json"
    manifest.write_text(json.dumps(bundle.to_dict(), indent=2), encoding="utf-8")

    report = validate_curation_handoff_bundle(manifest, required_roles={"prediction_quality_report"})
    markdown = format_curation_handoff_validation_markdown(report)

    assert report.valid is True
    assert report.checked_artifact_count == 1
    assert report.checksum_mismatch_count == 0
    assert "Curation Handoff Validation" in markdown


def test_curation_handoff_validation_allows_empty_required_roles(tmp_path: Path) -> None:
    artifact = tmp_path / "active_learning_batches.md"
    artifact.write_text(f"# Batch Plan\n\n{RESEARCH_WARNING}\n", encoding="utf-8")
    bundle = build_curation_handoff_bundle(artifact_paths=[artifact], output_dir=tmp_path / "handoff")
    manifest = tmp_path / "handoff" / "curation_handoff_bundle.json"
    manifest.write_text(json.dumps(bundle.to_dict(), indent=2), encoding="utf-8")

    report = validate_curation_handoff_bundle(manifest, required_roles=set())

    assert report.required_role_missing_count == 0
    assert not any("Missing required artifact role" in warning for warning in report.warnings)


def test_curation_run_registry_records_workflow_and_handoff_hashes(tmp_path: Path) -> None:
    workflow = {
        "predictions_path": "predictions.jsonl",
        "graph_path": "graph.jsonl",
        "reviewed_queue_path": "reviewed.jsonl",
        "overlay_graph_path": "overlay.jsonl",
        "warnings": ["review warning"],
    }
    workflow_path = tmp_path / "curation_smoke_workflow.json"
    handoff_path = tmp_path / "curation_handoff_bundle.json"
    registry_path = tmp_path / "curation_run_registry.json"
    workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
    handoff_path.write_text(
        json.dumps(
            {
                "warning": RESEARCH_WARNING,
                "artifact_count": 1,
                "artifacts": [{"artifact_role": "prediction_quality_report", "sha256": "A" * 64}],
            }
        ),
        encoding="utf-8",
    )

    report = update_curation_run_registry(
        registry_json=registry_path,
        workflow_report_json=workflow_path,
        handoff_manifest_json=handoff_path,
    )

    assert report.run_count == 1
    assert report.entries[0].warning_count == 1
    assert report.entries[0].artifact_hashes["prediction_quality_report"] == "A" * 64
    assert json.loads(registry_path.read_text(encoding="utf-8"))["warning"] == RESEARCH_WARNING


def test_browse_curation_runs_filters_registry_entries(tmp_path: Path) -> None:
    registry_path = tmp_path / "curation_run_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "warning": RESEARCH_WARNING,
                "run_count": 2,
                "latest_run_id": "curation-B",
                "entries": [
                    {
                        "run_id": "curation-A",
                        "created_at_utc": "2026-01-01T00:00:00+00:00",
                        "predictions_path": "predictions_a.jsonl",
                        "graph_path": "graph_a.jsonl",
                        "reviewed_queue_path": "reviewed_a.jsonl",
                        "overlay_graph_path": "overlay_a.jsonl",
                        "handoff_bundle_path": "handoff_a.json",
                        "warning_count": 1,
                        "artifact_hashes": {},
                    },
                    {
                        "run_id": "curation-B",
                        "created_at_utc": "2026-01-02T00:00:00+00:00",
                        "predictions_path": "predictions_b.jsonl",
                        "graph_path": "graph_b.jsonl",
                        "reviewed_queue_path": "reviewed_b.jsonl",
                        "overlay_graph_path": "overlay_b.jsonl",
                        "handoff_bundle_path": "handoff_b.json",
                        "warning_count": 0,
                        "artifact_hashes": {},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = browse_curation_runs(registry_path, warnings_only=True)
    markdown = format_curation_run_browser_markdown(report)

    assert report.run_count == 2
    assert report.match_count == 1
    assert report.runs[0].run_id == "curation-A"
    assert "Curation Run Browser" in markdown


def test_search_curated_evidence_filters_rows(tmp_path: Path) -> None:
    curated = tmp_path / "curated.jsonl"
    curated.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "item_id": "prediction:123:1",
                        "source_pmid": "123",
                        "text": "MGMT methylation predicts response.",
                        "curated_evidence_tier": 3,
                        "review_status": "accepted",
                        "reviewer": "curator",
                        "checkpoint_name": "gbmbert_evidence_v1",
                    }
                ),
                json.dumps(
                    {
                        "item_id": "prediction:456:1",
                        "source_pmid": "456",
                        "text": "Other claim.",
                        "curated_evidence_tier": 1,
                        "review_status": "pending",
                        "reviewer": "",
                        "checkpoint_name": "gbmbert_evidence_v1",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = search_curated_evidence(curated, evidence_tier=3, review_status="accepted", text="mgmt")
    markdown = format_curated_evidence_search_markdown(report)

    assert report.match_count == 1
    assert report.matches[0]["source_pmid"] == "123"
    assert "Curated Evidence Search" in markdown


def test_curation_regression_pack_runs_end_to_end(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.jsonl"
    graph_path = tmp_path / "graph.jsonl"
    reviewed_path = tmp_path / "reviewed.jsonl"
    predictions_path.write_text(json.dumps(_prediction_row("12345678", "3", 0.98)) + "\n", encoding="utf-8")
    graph_path.write_text(_graph_record("12345678", EvidenceTier.IN_VITRO).model_dump_json() + "\n", encoding="utf-8")
    reviewed_path.write_text(
        PredictionReviewItem(
            item_id="prediction:12345678:1",
            source_pmid="12345678",
            text="MGMT methylation predicts response.",
            predicted_evidence_tier=3,
            prediction_label="3",
            confidence=0.98,
            checkpoint_name="gbmbert_evidence_v1",
            checkpoint_status="candidate",
            review_status="accepted",
            reviewer="curator",
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    report = run_curation_regression_pack(
        predictions_jsonl=predictions_path,
        graph_jsonl=graph_path,
        reviewed_queue_jsonl=reviewed_path,
        output_dir=tmp_path / "outputs",
        reports_dir=tmp_path / "reports",
        registry_json=tmp_path / "registry.json",
    )
    markdown = format_curation_regression_pack_markdown(report)

    assert Path(report.handoff_manifest_path).exists()
    assert Path(report.validation_report_path).exists()
    assert Path(report.reverted_graph_path).exists()
    assert "Curation Regression Pack" in markdown


def _prediction_row(
    pmid: str,
    prediction: str,
    confidence: float,
    *,
    status: str = "candidate",
    text: str = "MGMT methylation predicts response.",
    warning: str = RESEARCH_WARNING,
) -> dict[str, object]:
    return {
        "source_pmid": pmid,
        "text": text,
        "prediction": prediction,
        "confidence": confidence,
        "checkpoint_name": "gbmbert_evidence_v1",
        "checkpoint_status": status,
        "checkpoint_dir": "models/checkpoints/gbmbert_evidence_v1",
        "warning": warning,
    }


def _graph_record(pmid: str, tier: EvidenceTier) -> KnowledgeGraphRecord:
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="temozolomide response")
    return KnowledgeGraphRecord(
        pmid=pmid,
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid=pmid,
                evidence_tier=tier,
                confidence=0.7,
            )
        ],
    )
