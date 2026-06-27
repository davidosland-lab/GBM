import json
from pathlib import Path

from gbmbert.adjudication import build_adjudication_report, format_adjudication_markdown
from gbmbert.extraction.review_queue import ReviewQueueItem, save_review_queue_jsonl
from gbmbert.knowledge_graph.qualifiers import enrich_graph_relation_qualifiers
from gbmbert.knowledge_graph.schema import EvidenceTier, GraphNode, GraphRelation, KnowledgeGraphRecord, NodeLabel, RelationType, SpeciesModel
from gbmbert.normalization import normalize_graph_records
from gbmbert.training.gold_seed import build_gold_seed_dataset, format_gold_seed_markdown
from gbmbert.training.readiness import build_training_readiness_report, format_training_readiness_markdown


def test_gold_seed_builder_keeps_reviewed_items_only(tmp_path: Path) -> None:
    reviewed = tmp_path / "reviewed.jsonl"
    save_review_queue_jsonl(
        [
            ReviewQueueItem(
                item_id="relation:12345678:1",
                item_type="graph_relation",
                source_pmid="12345678",
                evidence_tier=3,
                confidence=0.8,
                text="MGMT methylation predicts response.",
                relation_type="PREDICTS",
                head="Biomarker:MGMT methylation",
                tail="Outcome:response",
                review_status="accepted",
                reviewer="curator",
            ),
            ReviewQueueItem(
                item_id="evidence:12345678",
                item_type="evidence_claim",
                source_pmid="12345678",
                evidence_tier=0,
                confidence=0.5,
                text="Hypothesis only.",
                review_status="pending",
            ),
        ],
        reviewed,
    )

    report = build_gold_seed_dataset(output_dir=tmp_path / "gold", reviewed_queue_jsonl=reviewed)
    markdown = format_gold_seed_markdown(report)

    assert report.relation_count == 1
    assert report.evidence_count == 0
    assert report.skipped_pending_count == 1
    assert "Gold Seed Dataset" in markdown
    assert (tmp_path / "gold" / "gold_relations.jsonl").read_text(encoding="utf-8")


def test_adjudication_report_flags_conflicting_review_decisions(tmp_path: Path) -> None:
    left = tmp_path / "left.jsonl"
    right = tmp_path / "right.jsonl"
    left.write_text(json.dumps({"item_id": "x1", "review_status": "accepted", "evidence_tier": 3}) + "\n", encoding="utf-8")
    right.write_text(json.dumps({"item_id": "x1", "review_status": "corrected", "evidence_tier": 4}) + "\n", encoding="utf-8")

    report = build_adjudication_report([left, right])
    markdown = format_adjudication_markdown(report)

    assert report.conflict_count == 2
    assert {conflict.field for conflict in report.conflicts} == {"review_status", "evidence_tier"}
    assert "Annotation Adjudication Report" in markdown


def test_entity_normalization_adds_canonical_properties_to_nodes_and_relation_endpoints(tmp_path: Path) -> None:
    graph = tmp_path / "graph.jsonl"
    output = tmp_path / "normalized_graph_records.jsonl"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
                properties={"sentence": "MGMT methylation predicts response."},
            )
        ],
    )
    graph.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = normalize_graph_records(graph, output)
    normalized = KnowledgeGraphRecord.model_validate(json.loads(output.read_text(encoding="utf-8").splitlines()[0]))

    assert report.normalized_node_count == 1
    assert normalized.nodes[0].properties["canonical_id"] == "gene:MGMT"
    assert normalized.relations[0].head.properties["canonical_name"] == "MGMT"


def test_relation_qualifier_enrichment_fills_missing_context(tmp_path: Path) -> None:
    graph = tmp_path / "graph.jsonl"
    output = tmp_path / "qualifier_enriched_graph_records.jsonl"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="temozolomide response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
                properties={
                    "sentence": "In a retrospective human cohort, MGMT methylation predicts temozolomide response."
                },
            )
        ],
    )
    graph.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = enrich_graph_relation_qualifiers(graph, output)
    enriched = KnowledgeGraphRecord.model_validate(json.loads(output.read_text(encoding="utf-8").splitlines()[0]))

    assert report.enriched_relation_count == 1
    assert enriched.relations[0].qualifiers.species_model is SpeciesModel.HUMAN
    assert enriched.relations[0].qualifiers.evidence_context == "retrospective"


def test_training_readiness_report_checks_counts_and_leakage(tmp_path: Path) -> None:
    rows = {
        "ner_train.jsonl": [{"source_pmid": "1", "text": "MGMT", "label": "BIOMARKER", "start": 0, "end": 4}],
        "evidence_validation.jsonl": [{"source_pmid": "2", "text": "phase II", "label": 4}],
        "relations_test.jsonl": [{"source_pmid": "3", "text": "predicts", "label": "PREDICTS"}],
    }
    for name, payload in rows.items():
        (tmp_path / name).write_text("\n".join(json.dumps(row) for row in payload) + "\n", encoding="utf-8")

    report = build_training_readiness_report(tmp_path, min_examples_per_task=1, min_examples_per_label=1)
    markdown = format_training_readiness_markdown(report)

    assert report.ready is True
    assert report.warning_count == 0
    assert "Training Readiness Report" in markdown
