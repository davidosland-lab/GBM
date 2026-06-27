"""Parameterized Cypher helpers for the Knowledge Graph Explorer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from gbmbert.knowledge_graph.schema import EvidenceTier, NodeLabel, RelationType


class GraphQuery(BaseModel):
    cypher: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class NodeSummaryQuery(BaseModel):
    cypher: str
    parameters: dict[str, Any] = Field(default_factory=dict)


def neighborhood_query(
    search: str,
    node_labels: list[NodeLabel] | None = None,
    relation_types: list[RelationType] | None = None,
    min_evidence_tier: EvidenceTier = EvidenceTier.HYPOTHESIS,
    depth: int = 1,
    min_citations: int = 1,
    limit: int = 100,
) -> GraphQuery:
    """Build a safe neighborhood query for the KG Explorer graph canvas."""

    if depth not in {1, 2, 3}:
        raise ValueError("depth must be 1, 2, or 3")
    if min_citations < 1:
        raise ValueError("min_citations must be at least 1")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    labels = [label.value for label in node_labels] if node_labels else []
    rels = [relation.value for relation in relation_types] if relation_types else []
    cypher = f"""
    MATCH (start)
    WHERE $search = ''
       OR any(value IN [start.name, start.symbol, start.pmid, start.nct_id]
              WHERE value IS NOT NULL AND toLower(toString(value)) CONTAINS toLower($search))
    MATCH path = (start)-[*1..{depth}]-(neighbor)
    WITH path, relationships(path) AS rels, nodes(path) AS ns
    WHERE ($node_labels = [] OR any(n IN ns WHERE any(label IN labels(n) WHERE label IN $node_labels)))
      AND ($relation_types = [] OR all(r IN rels WHERE type(r) IN $relation_types))
      AND all(r IN rels WHERE coalesce(r.evidence_tier, 0) >= $min_evidence_tier)
      AND all(r IN rels WHERE size(coalesce(r.source_pmids, [])) >= $min_citations)
    RETURN path
    LIMIT $limit
    """
    return GraphQuery(
        cypher=_clean_cypher(cypher),
        parameters={
            "search": search.strip(),
            "node_labels": labels,
            "relation_types": rels,
            "min_evidence_tier": int(min_evidence_tier),
            "min_citations": min_citations,
            "limit": limit,
        },
    )


def node_summary_query(label: NodeLabel, key_value: str | int, limit: int = 25) -> NodeSummaryQuery:
    """Build a query for the KG Explorer selected-node side panel."""

    if limit < 1:
        raise ValueError("limit must be at least 1")
    key_name = {
        NodeLabel.PAPER: "pmid",
        NodeLabel.GENE: "symbol",
        NodeLabel.DRUG: "name",
        NodeLabel.PATHWAY: "name",
        NodeLabel.BIOMARKER: "name",
        NodeLabel.TREATMENT: "name",
        NodeLabel.OUTCOME: "name",
        NodeLabel.CELL_TYPE: "name",
        NodeLabel.CELL_STATE: "name",
        NodeLabel.DELIVERY_MODIFIER: "name",
        NodeLabel.TRIAL: "nct_id",
        NodeLabel.DISEASE: "name",
        NodeLabel.EVIDENCE_LEVEL: "tier",
    }[label]
    cypher = f"""
    MATCH (n:{label.value} {{{key_name}: $key_value}})
    OPTIONAL MATCH (n)-[r]-(neighbor)
    WHERE type(r) <> 'HAS_EVIDENCE'
    WITH n, r, neighbor
    ORDER BY coalesce(r.evidence_tier, 0) DESC, size(coalesce(r.source_pmids, [])) DESC
    RETURN
        properties(n) AS node,
        labels(n) AS labels,
        collect({{
            relation: type(r),
            neighbor: properties(neighbor),
            neighbor_labels: labels(neighbor),
            evidence_tier: coalesce(r.evidence_tier, 0),
            source_pmids: coalesce(r.source_pmids, [])
        }})[..$limit] AS relations
    """
    return NodeSummaryQuery(
        cypher=_clean_cypher(cypher),
        parameters={"key_value": key_value, "limit": limit},
    )


def _clean_cypher(cypher: str) -> str:
    return "\n".join(line.rstrip() for line in cypher.strip().splitlines())
