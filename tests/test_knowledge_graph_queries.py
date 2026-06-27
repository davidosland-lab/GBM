import pytest

from gbmbert.knowledge_graph.queries import neighborhood_query, node_summary_query
from gbmbert.knowledge_graph.schema import EvidenceTier, NodeLabel, RelationType


def test_neighborhood_query_builds_parameterized_cypher() -> None:
    query = neighborhood_query(
        search="MGMT",
        node_labels=[NodeLabel.BIOMARKER, NodeLabel.OUTCOME],
        relation_types=[RelationType.PREDICTS],
        min_evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
        depth=2,
        min_citations=3,
        limit=50,
    )

    assert "MATCH path = (start)-[*1..2]-(neighbor)" in query.cypher
    assert "$search" in query.cypher
    assert query.parameters["search"] == "MGMT"
    assert query.parameters["node_labels"] == ["Biomarker", "Outcome"]
    assert query.parameters["relation_types"] == ["PREDICTS"]
    assert query.parameters["min_evidence_tier"] == 3
    assert query.parameters["min_citations"] == 3


def test_neighborhood_query_rejects_unsafe_depth() -> None:
    with pytest.raises(ValueError):
        neighborhood_query(search="MGMT", depth=4)


def test_node_summary_query_uses_label_specific_key() -> None:
    query = node_summary_query(NodeLabel.GENE, "EGFR")

    assert "MATCH (n:Gene {symbol: $key_value})" in query.cypher
    assert query.parameters == {"key_value": "EGFR", "limit": 25}


def test_node_summary_query_supports_scope_v2_node_labels() -> None:
    cell_state = node_summary_query(NodeLabel.CELL_STATE, "MES-like")
    delivery_modifier = node_summary_query(NodeLabel.DELIVERY_MODIFIER, "FUS-BBBO")

    assert "MATCH (n:CellState {name: $key_value})" in cell_state.cypher
    assert "MATCH (n:DeliveryModifier {name: $key_value})" in delivery_modifier.cypher
