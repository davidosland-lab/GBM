"""Knowledge graph schema, loading, and query helpers."""

from gbmbert.knowledge_graph.loader import GraphLoader, LoaderConfig, LoaderStats
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    MutationStatus,
    NodeLabel,
    RelationQualifiers,
    RelationType,
    SpeciesModel,
)
__all__ = [
    "EvidenceTier",
    "GraphLoader",
    "GraphNode",
    "GraphRelation",
    "KnowledgeGraphRecord",
    "LoaderConfig",
    "LoaderStats",
    "MutationStatus",
    "NodeLabel",
    "RelationQualifiers",
    "RelationType",
    "SpeciesModel",
    "build_graph_records",
]


def __getattr__(name: str) -> object:
    if name == "build_graph_records":
        from gbmbert.knowledge_graph.build_records import build_graph_records

        return build_graph_records
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
