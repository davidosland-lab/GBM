import json
from pathlib import Path

from gbmbert.annotation.schema import EvidenceClaim, EvidenceLevel
from gbmbert.extraction.review_queue import (
    ReviewQueueItem,
    build_review_queue,
    export_review_queue,
    format_review_queue_summary_markdown,
    format_reviewed_queue_summary_markdown,
    initialize_reviewed_queue,
    load_review_queue_jsonl,
    save_review_queue_csv,
    save_review_queue_summary_json,
    save_review_queue_summary_markdown,
    save_reviewed_queue_summary_json,
    save_reviewed_queue_summary_markdown,
    summarize_review_queue,
    summarize_reviewed_queue,
)
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    NodeLabel,
    RelationType,
)


def test_build_review_queue_includes_low_confidence_evidence_claims(tmp_path: Path) -> None:
    evidence_path = tmp_path / "evidence.jsonl"
    low = EvidenceClaim(
        claim="Uncertain claim",
        source_pmid="12345678",
        evidence_level=EvidenceLevel.HYPOTHESIS,
        confidence=0.5,
    )
    high = EvidenceClaim(
        claim="Higher confidence claim",
        source_pmid="23456789",
        evidence_level=EvidenceLevel.RETROSPECTIVE_HUMAN,
        confidence=0.9,
    )
    evidence_path.write_text(low.model_dump_json() + "\n" + high.model_dump_json() + "\n", encoding="utf-8")

    items = build_review_queue(evidence_jsonl=evidence_path, max_confidence=0.65)

    assert len(items) == 1
    assert items[0].item_id == "evidence:12345678"
    assert items[0].text == "Uncertain claim"
    assert "confidence <= 0.65" in items[0].reasons
    assert "hypothesis-tier evidence" in items[0].reasons


def test_build_review_queue_includes_uncertain_graph_relations(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph.jsonl"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="temozolomide response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.HYPOTHESIS,
                confidence=0.54,
                properties={"sentence": "MGMT methylation predicts response."},
            )
        ],
    )
    graph_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    items = build_review_queue(graph_jsonl=graph_path, max_confidence=0.65)

    assert len(items) == 1
    assert items[0].item_type == "graph_relation"
    assert items[0].relation_type == "PREDICTS"
    assert items[0].head == "Biomarker:MGMT methylation"
    assert items[0].tail == "Outcome:temozolomide response"


def test_export_review_queue_writes_jsonl_and_csv(tmp_path: Path) -> None:
    evidence_path = tmp_path / "evidence.jsonl"
    evidence_path.write_text(
        EvidenceClaim(
            claim="Hypothesis",
            source_pmid="12345678",
            evidence_level=EvidenceLevel.HYPOTHESIS,
            confidence=0.5,
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "queue.jsonl"
    csv_path = tmp_path / "queue.csv"

    items = export_review_queue(
        evidence_jsonl=evidence_path,
        output_jsonl=jsonl_path,
        csv_output=csv_path,
    )

    assert len(items) == 1
    assert json.loads(jsonl_path.read_text(encoding="utf-8"))["source_pmid"] == "12345678"
    assert "hypothesis-tier evidence" in csv_path.read_text(encoding="utf-8")


def test_summarize_review_queue_counts_reasons_and_writes_reports(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "item_id": "evidence:12345678",
                        "item_type": "evidence_claim",
                        "source_pmid": "12345678",
                        "evidence_tier": 0,
                        "confidence": 0.5,
                        "text": "Hypothesis",
                        "reasons": ["confidence <= 0.65", "hypothesis-tier evidence"],
                    }
                ),
                json.dumps(
                    {
                        "item_id": "relation:12345678:1",
                        "item_type": "graph_relation",
                        "source_pmid": "12345678",
                        "evidence_tier": 1,
                        "confidence": 0.6,
                        "text": "Sentence",
                        "relation_type": "PREDICTS",
                        "head": "Biomarker:MGMT",
                        "tail": "Outcome:response",
                        "reasons": ["confidence <= 0.65"],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    json_path = tmp_path / "summary.json"
    markdown_path = tmp_path / "summary.md"

    summary = summarize_review_queue(queue_path)
    save_review_queue_summary_json(summary, json_path)
    save_review_queue_summary_markdown(summary, markdown_path)
    markdown = format_review_queue_summary_markdown(summary)

    assert summary.item_count == 2
    assert [(item.key, item.count) for item in summary.item_type_counts] == [
        ("evidence_claim", 1),
        ("graph_relation", 1),
    ]
    assert summary.reason_counts[0].key == "confidence <= 0.65"
    assert json.loads(json_path.read_text(encoding="utf-8"))["item_count"] == 2
    assert "# GBM-AI Review Queue Summary" in markdown_path.read_text(encoding="utf-8")
    assert "Relation Types" in markdown


def test_initialize_reviewed_queue_scaffolds_status_without_modifying_raw_queue(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.jsonl"
    reviewed_path = tmp_path / "reviewed_queue.jsonl"
    csv_path = tmp_path / "reviewed_queue.csv"
    raw_item = {
        "item_id": "evidence:12345678",
        "item_type": "evidence_claim",
        "source_pmid": "12345678",
        "evidence_tier": 0,
        "confidence": 0.5,
        "text": "Hypothesis",
        "reasons": ["hypothesis-tier evidence"],
    }
    queue_path.write_text(json.dumps(raw_item) + "\n", encoding="utf-8")

    items = initialize_reviewed_queue(
        queue_path,
        reviewed_path,
        reviewer="curator-a",
        csv_output=csv_path,
    )

    assert items[0].review_status == "pending"
    assert items[0].reviewer == "curator-a"
    assert "review_status" not in json.loads(queue_path.read_text(encoding="utf-8"))
    assert load_review_queue_jsonl(reviewed_path)[0].review_status == "pending"
    assert "curator-a" in csv_path.read_text(encoding="utf-8")


def test_initialize_reviewed_queue_refuses_to_overwrite_by_default(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.jsonl"
    reviewed_path = tmp_path / "reviewed_queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "item_id": "evidence:12345678",
                "item_type": "evidence_claim",
                "source_pmid": "12345678",
                "evidence_tier": 0,
                "confidence": 0.5,
                "text": "Hypothesis",
                "reasons": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    reviewed_path.write_text("", encoding="utf-8")

    try:
        initialize_reviewed_queue(queue_path, reviewed_path)
    except FileExistsError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Expected FileExistsError")


def test_review_queue_item_requires_notes_for_rejected_and_corrected_items() -> None:
    base = {
        "item_id": "relation:12345678:1",
        "item_type": "graph_relation",
        "source_pmid": "12345678",
        "evidence_tier": 0,
        "confidence": 0.5,
        "text": "Sentence",
        "relation_type": "PREDICTS",
        "head": "Biomarker:MGMT",
        "tail": "Outcome:response",
        "reasons": [],
    }

    try:
        ReviewQueueItem.model_validate({**base, "review_status": "rejected"})
    except ValueError as exc:
        assert "rejected items require review_notes" in str(exc)
    else:
        raise AssertionError("Expected rejected item validation failure")

    try:
        ReviewQueueItem.model_validate(
            {
                **base,
                "review_status": "corrected",
                "review_notes": "Correct relation",
                "corrected_relation_type": "NOT_A_RELATION",
            }
        )
    except ValueError as exc:
        assert "corrected_relation_type" in str(exc)
    else:
        raise AssertionError("Expected corrected relation validation failure")


def test_summarize_reviewed_queue_counts_statuses_and_corrections(tmp_path: Path) -> None:
    reviewed_path = tmp_path / "reviewed_queue.jsonl"
    items = [
        {
            "item_id": "evidence:1",
            "item_type": "evidence_claim",
            "source_pmid": "12345678",
            "evidence_tier": 0,
            "confidence": 0.5,
            "text": "Hypothesis",
            "reasons": [],
            "review_status": "pending",
        },
        {
            "item_id": "relation:2:1",
            "item_type": "graph_relation",
            "source_pmid": "23456789",
            "evidence_tier": 0,
            "confidence": 0.6,
            "text": "Corrected",
            "reasons": [],
            "review_status": "corrected",
            "review_notes": "Relation type curated by reviewer.",
            "corrected_relation_type": "ASSOCIATED_WITH",
            "corrected_evidence_tier": 3,
        },
        {
            "item_id": "relation:3:1",
            "item_type": "graph_relation",
            "source_pmid": "34567890",
            "evidence_tier": 0,
            "confidence": 0.4,
            "text": "Rejected",
            "reasons": [],
            "review_status": "rejected",
            "review_notes": "Evidence is not relevant to GBM curation.",
        },
    ]
    reviewed_path.write_text("\n".join(json.dumps(item) for item in items) + "\n", encoding="utf-8")
    json_path = tmp_path / "reviewed_summary.json"
    markdown_path = tmp_path / "reviewed_summary.md"

    summary = summarize_reviewed_queue(reviewed_path)
    save_reviewed_queue_summary_json(summary, json_path)
    save_reviewed_queue_summary_markdown(summary, markdown_path)
    markdown = format_reviewed_queue_summary_markdown(summary)

    assert summary.pending_count == 1
    assert summary.warning_count == 1
    assert [(item.key, item.count) for item in summary.status_counts] == [
        ("pending", 1),
        ("corrected", 1),
        ("rejected", 1),
    ]
    assert summary.corrected_relation_type_counts[0].key == "ASSOCIATED_WITH"
    assert summary.corrected_evidence_tier_counts[0].key == "3"
    assert json.loads(json_path.read_text(encoding="utf-8"))["pending_count"] == 1
    assert "GBM-AI Reviewed Queue Summary" in markdown_path.read_text(encoding="utf-8")
    assert "1 item(s) still pending review" in markdown
