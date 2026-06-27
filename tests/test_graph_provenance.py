import json
from pathlib import Path

from gbmbert.knowledge_graph.provenance import (
    audit_graph_provenance,
    format_provenance_audit_markdown,
    save_provenance_audit_json,
)
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    NodeLabel,
    RelationType,
)
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord, TrialGraphRelation


def test_audit_pubmed_graph_records_flags_missing_relation_provenance(tmp_path: Path) -> None:
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
                evidence_tier=EvidenceTier.HYPOTHESIS,
                confidence=0.6,
                properties={},
            )
        ],
    )
    path = tmp_path / "graph_records.jsonl"
    path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = audit_graph_provenance(path)
    markdown = format_provenance_audit_markdown(report)

    assert report.records_seen == 1
    assert report.relations_seen == 1
    assert report.issue_type_counts["missing_source_sentence"] == 1
    assert report.issue_type_counts["missing_evidence_method"] == 1
    assert "Graph Provenance Audit" in markdown


def test_audit_trial_graph_records_accepts_registry_provenance(tmp_path: Path) -> None:
    trial = GraphNode(
        label=NodeLabel.TRIAL,
        key_value="NCT12345678",
        properties={"source_url": "https://clinicaltrials.gov/study/NCT12345678"},
    )
    disease = GraphNode(label=NodeLabel.DISEASE, key_value="Glioblastoma")
    record = ClinicalTrialGraphRecord(
        nct_id="NCT12345678",
        trial_properties=trial.keyed_properties(),
        nodes=[disease],
        relations=[
            TrialGraphRelation(
                head=trial,
                relation=RelationType.ASSOCIATED_WITH,
                tail=disease,
                source_id="NCT12345678",
                properties={
                    "source_url": "https://clinicaltrials.gov/study/NCT12345678",
                    "registry_field": "condition",
                },
            )
        ],
    )
    path = tmp_path / "trial_graph_records.jsonl"
    json_path = tmp_path / "audit.json"
    path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = audit_graph_provenance(path, record_type="trial")
    save_provenance_audit_json(report, json_path)

    assert report.records_seen == 1
    assert report.relations_seen == 1
    assert report.issue_count == 0
    assert json.loads(json_path.read_text(encoding="utf-8"))["record_type"] == "trial"


def test_audit_trial_graph_records_flags_missing_source_url(tmp_path: Path) -> None:
    trial = GraphNode(label=NodeLabel.TRIAL, key_value="NCT12345678")
    disease = GraphNode(label=NodeLabel.DISEASE, key_value="Glioblastoma")
    record = ClinicalTrialGraphRecord(
        nct_id="NCT12345678",
        trial_properties=trial.keyed_properties(),
        nodes=[disease],
        relations=[
            TrialGraphRelation(
                head=trial,
                relation=RelationType.ASSOCIATED_WITH,
                tail=disease,
                source_id="NCT12345678",
                properties={"registry_field": "condition"},
            )
        ],
    )
    path = tmp_path / "trial_graph_records.jsonl"
    path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = audit_graph_provenance(path)

    assert report.record_type == "trial"
    assert report.issue_type_counts["missing_source_url"] == 1
