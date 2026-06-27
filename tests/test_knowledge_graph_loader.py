import json
from pathlib import Path
from typing import Any

from gbmbert.knowledge_graph.loader import GraphLoader, LoaderConfig
from gbmbert.knowledge_graph.overlay_guard import (
    build_overlay_load_guard_report,
    format_overlay_load_guard_markdown,
)
from gbmbert.knowledge_graph.cli import (
    GraphLoadReport,
    detect_record_type,
    format_load_report_markdown,
    save_load_report_json,
)
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    MutationStatus,
    NodeLabel,
    RelationQualifiers,
    RelationType,
)
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord, TrialGraphRelation


class StubSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "StubSession":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def run(self, query: str, **parameters: Any) -> None:
        self.calls.append((query, parameters))


class StubDriver:
    def __init__(self) -> None:
        self.session_obj = StubSession()

    def session(self) -> StubSession:
        return self.session_obj


def canonical_record() -> KnowledgeGraphRecord:
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="Temozolomide Response")
    return KnowledgeGraphRecord(
        pmid="29097493",
        paper_properties={"title": "MGMT methylation in GBM", "year": 2018},
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="29097493",
                evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
                confidence=0.91,
                qualifiers=RelationQualifiers(mutation_status=MutationStatus.MGMT_METHYLATED),
            )
        ],
    )


def test_loader_applies_constraints_and_seeds_evidence_levels() -> None:
    driver = StubDriver()
    loader = GraphLoader(driver)

    loader.initialize()

    queries = [query for query, _ in driver.session_obj.calls]
    assert any("CREATE CONSTRAINT paper_pmid_unique" in query for query in queries)
    assert sum("MERGE (e:EvidenceLevel" in query for query in queries) == 6


def test_loader_merges_canonical_record() -> None:
    driver = StubDriver()
    loader = GraphLoader(driver, LoaderConfig(apply_constraints=False))

    stats = loader.load_records([canonical_record()])

    assert stats.records_seen == 1
    assert stats.records_loaded == 1
    assert stats.nodes_merged == 3
    assert stats.mentions_merged == 2
    assert stats.relations_merged == 1
    mention_queries = [
        query
        for query, _ in driver.session_obj.calls
        if "MERGE (p)-[r:MENTIONS]->(n)" in query
    ]
    assert len(mention_queries) == 2
    assert "r.source_pmids" in mention_queries[0]
    assert "r.evidence_tier = 0" in mention_queries[0]
    relation_calls = [
        params
        for query, params in driver.session_obj.calls
        if "MERGE (head)-[r:PREDICTS]->(tail)" in query
    ]
    assert relation_calls[0]["source_pmid"] == "29097493"
    assert relation_calls[0]["evidence_tier"] == 3
    assert relation_calls[0]["properties"]["mutation_status"] == "mgmt_methylated"


def test_loader_loads_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "graph.jsonl"
    path.write_text(canonical_record().model_dump_json() + "\n", encoding="utf-8")
    driver = StubDriver()
    loader = GraphLoader(driver, LoaderConfig(apply_constraints=False))

    stats = loader.load_jsonl(path)

    assert stats.records_seen == 1
    assert stats.records_loaded == 1
    assert stats.relations_merged == 1


def test_loader_can_skip_invalid_jsonl_records(tmp_path: Path) -> None:
    path = tmp_path / "graph.jsonl"
    invalid = {"pmid": "not-a-pmid"}
    path.write_text(json.dumps(invalid) + "\n", encoding="utf-8")
    driver = StubDriver()
    loader = GraphLoader(
        driver,
        LoaderConfig(apply_constraints=False, skip_invalid_records=True),
    )

    stats = loader.load_jsonl(path)

    assert stats.records_seen == 1
    assert stats.records_skipped == 1
    assert stats.records_loaded == 0


def trial_record() -> ClinicalTrialGraphRecord:
    trial = GraphNode(
        label=NodeLabel.TRIAL,
        key_value="NCT12345678",
        properties={"display_name": "GBM trial", "source_url": "https://clinicaltrials.gov/study/NCT12345678"},
    )
    disease = GraphNode(label=NodeLabel.DISEASE, key_value="Glioblastoma")
    treatment = GraphNode(label=NodeLabel.TREATMENT, key_value="Temozolomide")
    return ClinicalTrialGraphRecord(
        nct_id="NCT12345678",
        trial_properties=trial.keyed_properties(),
        nodes=[disease, treatment],
        relations=[
            TrialGraphRelation(
                head=trial,
                relation=RelationType.ASSOCIATED_WITH,
                tail=disease,
                source_id="NCT12345678",
                properties={"source_url": "https://clinicaltrials.gov/study/NCT12345678"},
            ),
            TrialGraphRelation(
                head=trial,
                relation=RelationType.ASSOCIATED_WITH,
                tail=treatment,
                source_id="NCT12345678",
                properties={"source_url": "https://clinicaltrials.gov/study/NCT12345678"},
            ),
        ],
    )


def test_loader_merges_trial_graph_record() -> None:
    driver = StubDriver()
    loader = GraphLoader(driver, LoaderConfig(apply_constraints=False))

    stats = loader.load_trial_records([trial_record()])

    assert stats.records_seen == 1
    assert stats.records_loaded == 1
    assert stats.nodes_merged == 3
    assert stats.relations_merged == 2
    relation_calls = [
        params
        for query, params in driver.session_obj.calls
        if "MERGE (head)-[r:ASSOCIATED_WITH]->(tail)" in query
    ]
    assert relation_calls[0]["source_id"] == "NCT12345678"
    assert relation_calls[0]["properties"]["source_url"] == "https://clinicaltrials.gov/study/NCT12345678"


def test_loader_loads_trial_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "trial_graph.jsonl"
    path.write_text(trial_record().model_dump_json() + "\n", encoding="utf-8")
    driver = StubDriver()
    loader = GraphLoader(driver, LoaderConfig(apply_constraints=False))

    stats = loader.load_trial_jsonl(path)

    assert stats.records_seen == 1
    assert stats.records_loaded == 1
    assert stats.relations_merged == 2


def test_detect_record_type_distinguishes_trial_jsonl(tmp_path: Path) -> None:
    pubmed_path = tmp_path / "pubmed_graph.jsonl"
    trial_path = tmp_path / "trial_graph.jsonl"
    pubmed_path.write_text(canonical_record().model_dump_json() + "\n", encoding="utf-8")
    trial_path.write_text(trial_record().model_dump_json() + "\n", encoding="utf-8")

    assert detect_record_type(pubmed_path) == "pubmed"
    assert detect_record_type(trial_path) == "trial"


def test_graph_load_report_formats_and_saves_json(tmp_path: Path) -> None:
    driver = StubDriver()
    loader = GraphLoader(driver, LoaderConfig(apply_constraints=False, dry_run=True))
    stats = loader.load_records([canonical_record()])
    report = GraphLoadReport(
        source_path="graph.jsonl",
        record_type="pubmed",
        dry_run=True,
        apply_constraints=False,
        skip_invalid_records=False,
        stats=stats,
    )

    output = save_load_report_json(report, tmp_path / "load_report.json")
    markdown = format_load_report_markdown(report)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["stats"]["records_loaded"] == 1
    assert payload["dry_run"] is True
    assert "GBM-AI Graph Load Report" in markdown
    assert "Research-use only" in markdown


def test_overlay_load_guard_reports_safe_overlay_graph(tmp_path: Path) -> None:
    path = tmp_path / "overlay_graph.jsonl"
    record = canonical_record()
    relation = record.relations[0]
    record.relations[0] = relation.model_copy(
        update={
            "properties": {
                "evidence_overlay_original_tier": 1,
                "evidence_overlay_tier": 3,
                "evidence_overlay_review_status": "accepted",
            }
        }
    )
    path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = build_overlay_load_guard_report(path)
    markdown = format_overlay_load_guard_markdown(report)

    assert report.overlay_relation_count == 1
    assert report.safe_to_load is True
    assert "Neo4j Overlay Load Guard" in markdown


def test_overlay_load_guard_warns_for_raw_graph(tmp_path: Path) -> None:
    path = tmp_path / "raw_graph.jsonl"
    path.write_text(canonical_record().model_dump_json() + "\n", encoding="utf-8")

    report = build_overlay_load_guard_report(path)

    assert report.overlay_relation_count == 0
    assert report.safe_to_load is False
    assert "no evidence overlay metadata" in report.warnings[0]
