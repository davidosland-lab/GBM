import json
from pathlib import Path
from typing import Any

from gbmbert.knowledge_graph.inspect import (
    GraphCounts,
    GraphInspection,
    RecentPaper,
    EvidenceTierCount,
    fetch_recent_papers,
    format_inspection,
    inspect_graph,
)
from gbmbert.knowledge_graph.schema import KnowledgeGraphRecord


class StubSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "StubSession":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def run(self, query: str, **parameters: Any) -> list[dict[str, Any]]:
        self.calls.append((query, parameters))
        if "MATCH (n) RETURN count(n) AS count" in query:
            return [{"count": 4}]
        if "MATCH ()-[r]->() RETURN count(r) AS count" in query:
            return [{"count": 3}]
        if "UNWIND labels(n)" in query:
            return [{"label": "Paper", "count": 2}, {"label": "Biomarker", "count": 1}]
        if "RETURN type(r) AS type" in query:
            return [{"type": "MENTIONS", "count": 2}, {"type": "PREDICTS", "count": 1}]
        if "r.evidence_tier" in query:
            return [{"tier": 3, "count": 1}]
        if "MATCH (p:Paper)" in query:
            return [
                {
                    "pmid": "29097493",
                    "title": "MGMT methylation predicts temozolomide response",
                    "publication_date": "2018",
                }
            ]
        raise AssertionError(f"Unexpected query: {query}")


class StubDriver:
    def __init__(self) -> None:
        self.session_obj = StubSession()

    def session(self) -> StubSession:
        return self.session_obj


def test_inspect_graph_returns_counts_and_provenance() -> None:
    driver = StubDriver()

    inspection = inspect_graph(driver, recent_limit=1)

    assert inspection.counts.nodes == 4
    assert inspection.counts.relationships == 3
    assert inspection.counts.labels == {"Paper": 2, "Biomarker": 1}
    assert inspection.counts.relation_types == {"MENTIONS": 2, "PREDICTS": 1}
    assert inspection.evidence_tiers == [EvidenceTierCount(tier=3, count=1)]
    assert inspection.recent_papers == [
        RecentPaper(
            pmid="29097493",
            title="MGMT methylation predicts temozolomide response",
            publication_date="2018",
        )
    ]


def test_fetch_recent_papers_passes_limit_parameter() -> None:
    session = StubSession()

    fetch_recent_papers(session, limit=7)

    assert session.calls[-1][1] == {"limit": 7}


def test_format_inspection_includes_research_warning_and_counts() -> None:
    inspection = GraphInspection(
        counts=GraphCounts(
            nodes=4,
            relationships=3,
            labels={"Paper": 2},
            relation_types={"PREDICTS": 1},
        ),
        evidence_tiers=[EvidenceTierCount(tier=3, count=1)],
        recent_papers=[
            RecentPaper(
                pmid="29097493",
                title="MGMT methylation predicts temozolomide response",
                publication_date="2018",
            )
        ],
    )

    text = format_inspection(inspection)

    assert "Research-use only. Not medical advice." in text
    assert "Nodes: 4" in text
    assert "Relationships: 3" in text
    assert "tier 3: 1" in text
    assert "PMID 29097493" in text


def test_graph_inspection_to_dict_is_json_serializable() -> None:
    inspection = GraphInspection(
        counts=GraphCounts(nodes=1, relationships=0, labels={"Paper": 1}, relation_types={}),
        evidence_tiers=[],
        recent_papers=[],
    )

    assert json.loads(json.dumps(inspection.to_dict())) == {
        "counts": {
            "nodes": 1,
            "relationships": 0,
            "labels": {"Paper": 1},
            "relation_types": {},
        },
        "evidence_tiers": [],
        "recent_papers": [],
    }


def test_sample_graph_records_fixture_is_schema_valid() -> None:
    path = Path("data/examples/graph_records_sample.jsonl")

    records = [
        KnowledgeGraphRecord.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]

    assert len(records) == 2
    assert {record.pmid for record in records} == {"29097493", "40000001"}
