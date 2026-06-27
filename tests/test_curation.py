import json
from pathlib import Path

from gbmbert.curation import (
    build_curation_diff_report,
    export_curated_graph_records,
    format_curation_report_markdown,
    save_curation_report_json,
)
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    NodeLabel,
    RelationType,
)


def test_export_curated_graph_records_applies_corrections_and_rejections(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph_records.jsonl"
    reviewed_path = tmp_path / "reviewed_queue.jsonl"
    curated_path = tmp_path / "curated_graph_records.jsonl"
    report_path = tmp_path / "curation_report.json"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="temozolomide response")
    drug = GraphNode(label=NodeLabel.DRUG, key_value="temozolomide")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[biomarker, outcome, drug],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.HYPOTHESIS,
                confidence=0.6,
                properties={"sentence": "MGMT methylation predicts response."},
            ),
            GraphRelation(
                head=drug,
                relation=RelationType.IMPROVES,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.HYPOTHESIS,
                confidence=0.4,
                properties={"sentence": "Weak claim."},
            ),
        ],
    )
    graph_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")
    reviewed_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "item_id": "relation:12345678:1",
                        "item_type": "graph_relation",
                        "source_pmid": "12345678",
                        "evidence_tier": 0,
                        "confidence": 0.6,
                        "text": "MGMT methylation predicts response.",
                        "relation_type": "PREDICTS",
                        "head": "Biomarker:MGMT methylation",
                        "tail": "Outcome:temozolomide response",
                        "reasons": [],
                        "review_status": "corrected",
                        "review_notes": "Upgrade evidence after review.",
                        "corrected_relation_type": "ASSOCIATED_WITH",
                        "corrected_evidence_tier": 3,
                    }
                ),
                json.dumps(
                    {
                        "item_id": "relation:12345678:2",
                        "item_type": "graph_relation",
                        "source_pmid": "12345678",
                        "evidence_tier": 0,
                        "confidence": 0.4,
                        "text": "Weak claim.",
                        "relation_type": "IMPROVES",
                        "head": "Drug:temozolomide",
                        "tail": "Outcome:temozolomide response",
                        "reasons": [],
                        "review_status": "rejected",
                        "review_notes": "Not supported by the source sentence.",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = export_curated_graph_records(
        graph_jsonl=graph_path,
        reviewed_queue_jsonl=reviewed_path,
        output_jsonl=curated_path,
    )
    save_curation_report_json(report, report_path)
    curated = KnowledgeGraphRecord.model_validate(json.loads(curated_path.read_text(encoding="utf-8")))
    diff = build_curation_diff_report(
        graph_jsonl=graph_path,
        curated_graph_jsonl=curated_path,
        reviewed_queue_jsonl=reviewed_path,
    )
    markdown = format_curation_report_markdown(diff)

    assert report.corrected_count == 1
    assert report.rejected_count == 1
    assert report.raw_relation_count == 2
    assert report.curated_relation_count == 1
    assert curated.relations[0].relation == RelationType.ASSOCIATED_WITH
    assert curated.relations[0].evidence_tier == EvidenceTier.RETROSPECTIVE_HUMAN
    assert curated.relations[0].properties["curation_status"] == "corrected"
    assert json.loads(report_path.read_text(encoding="utf-8"))["rejected_count"] == 1
    assert "Curation Diff Report" in markdown


def test_export_curated_graph_records_can_fail_on_pending(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph_records.jsonl"
    reviewed_path = tmp_path / "reviewed_queue.jsonl"
    node = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[node, outcome],
        relations=[
            GraphRelation(
                head=node,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
            )
        ],
    )
    graph_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")
    reviewed_path.write_text(
        json.dumps(
            {
                "item_id": "relation:12345678:1",
                "item_type": "graph_relation",
                "source_pmid": "12345678",
                "evidence_tier": 0,
                "confidence": 0.5,
                "text": "",
                "relation_type": "PREDICTS",
                "head": "Biomarker:MGMT",
                "tail": "Outcome:response",
                "reasons": [],
                "review_status": "pending",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        export_curated_graph_records(
            graph_jsonl=graph_path,
            reviewed_queue_jsonl=reviewed_path,
            output_jsonl=tmp_path / "curated.jsonl",
            fail_on_pending=True,
        )
    except ValueError as exc:
        assert "pending review" in str(exc)
    else:
        raise AssertionError("Expected pending review failure")
