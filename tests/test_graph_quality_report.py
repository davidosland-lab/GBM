import json
from pathlib import Path

from gbmbert.knowledge_graph.quality import (
    analyze_graph_records_jsonl,
    analyze_unified_graph_records,
    format_quality_report_markdown,
    save_quality_report_json,
    save_quality_report_markdown,
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


def test_analyze_graph_records_jsonl_counts_records_and_provenance(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph_records.jsonl"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="temozolomide response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        paper_properties={
            "title": "MGMT methylation predicts temozolomide response",
            "abstract": "Retrospective patient cohort.",
        },
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
                properties={
                    "sentence": "MGMT methylation predicts temozolomide response.",
                    "extraction_method": "rule_based_v1",
                },
            )
        ],
    )
    graph_path.write_text(record.model_dump_json() + "\nnot-json\n", encoding="utf-8")

    report = analyze_graph_records_jsonl(graph_path, top_n=3)

    assert report.record_count == 1
    assert report.invalid_record_count == 1
    assert report.unique_pmid_count == 1
    assert report.node_mention_count == 2
    assert report.unique_node_count == 2
    assert report.relation_count == 1
    assert [(item.key, item.count) for item in report.label_counts] == [
        ("Biomarker", 1),
        ("Outcome", 1),
    ]
    assert [(item.key, item.count) for item in report.relation_type_counts] == [("PREDICTS", 1)]
    assert [(item.key, item.count) for item in report.evidence_tier_counts] == [("3", 1)]
    assert report.top_entities[0].key_value == "MGMT methylation"
    assert any("invalid JSON" in warning for warning in report.warnings)


def test_quality_report_writes_json_and_markdown(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph_records.jsonl"
    record = KnowledgeGraphRecord(
        pmid="12345678",
        paper_properties={"title": "Paper without entities", "abstract": "Research-use record."},
    )
    graph_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")
    report = analyze_graph_records_jsonl(graph_path)
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    save_quality_report_json(report, json_path)
    save_quality_report_markdown(report, markdown_path)
    markdown = format_quality_report_markdown(report)

    assert json.loads(json_path.read_text(encoding="utf-8"))["record_count"] == 1
    assert "# GBM-AI Graph Quality Report" in markdown_path.read_text(encoding="utf-8")
    assert "Research-use only. Not medical advice." in markdown
    assert "Paper-only records: 1" in markdown


def test_analyze_trial_graph_records_jsonl_counts_nct_records(tmp_path: Path) -> None:
    trial_path = tmp_path / "trial_graph_records.jsonl"
    trial = GraphNode(
        label=NodeLabel.TRIAL,
        key_value="NCT12345678",
        properties={"display_name": "GBM trial", "source_url": "https://clinicaltrials.gov/study/NCT12345678"},
    )
    disease = GraphNode(label=NodeLabel.DISEASE, key_value="Glioblastoma", properties={"display_name": "Glioblastoma"})
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
                properties={"source_url": "https://clinicaltrials.gov/study/NCT12345678"},
            )
        ],
    )
    trial_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = analyze_graph_records_jsonl(trial_path, record_type="trial")

    assert report.record_count == 1
    assert report.unique_nct_count == 1
    assert report.unique_pmid_count == 0
    assert report.relation_count == 1
    assert [(item.key, item.count) for item in report.label_counts] == [
        ("Trial", 1),
        ("Disease", 1),
    ]


def test_analyze_unified_graph_records_combines_pubmed_and_trial(tmp_path: Path) -> None:
    pubmed_path = tmp_path / "pubmed_graph.jsonl"
    trial_path = tmp_path / "trial_graph.jsonl"
    pubmed_path.write_text(
        KnowledgeGraphRecord(
            pmid="12345678",
            paper_properties={"title": "Paper", "abstract": "Abstract"},
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )
    trial = GraphNode(label=NodeLabel.TRIAL, key_value="NCT12345678", properties={"display_name": "Trial"})
    trial_path.write_text(
        ClinicalTrialGraphRecord(
            nct_id="NCT12345678",
            trial_properties=trial.keyed_properties(),
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    report = analyze_unified_graph_records([pubmed_path, trial_path])

    assert report.record_count == 2
    assert report.unique_pmid_count == 1
    assert report.unique_nct_count == 1
