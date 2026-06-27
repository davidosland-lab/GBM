"""Neo4j loader for GBM-AI knowledge graph records."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    GraphNode,
    GraphRelation,
    KnowledgeGraphRecord,
    NODE_KEY,
    NodeLabel,
)
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord, TrialGraphRelation

LOGGER = logging.getLogger(__name__)


class GraphSession(Protocol):
    def run(self, query: str, **parameters: Any) -> Any: ...


class GraphSessionContext(Protocol):
    def __enter__(self) -> GraphSession: ...
    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None: ...


class GraphDriver(Protocol):
    def session(self) -> GraphSessionContext: ...


@dataclass(frozen=True)
class LoaderConfig:
    apply_constraints: bool = True
    dry_run: bool = False
    skip_invalid_records: bool = False


@dataclass
class LoaderStats:
    records_seen: int = 0
    records_loaded: int = 0
    records_skipped: int = 0
    nodes_merged: int = 0
    mentions_merged: int = 0
    relations_merged: int = 0


class GraphLoader:
    """Write validated knowledge graph records using idempotent Cypher MERGE."""

    def __init__(self, driver: GraphDriver, config: LoaderConfig | None = None) -> None:
        self.driver = driver
        self.config = config or LoaderConfig()

    def initialize(self) -> None:
        if not self.config.apply_constraints:
            return
        with self.driver.session() as session:
            for label, key in NODE_KEY.items():
                constraint_name = f"{label.value.lower()}_{key}_unique"
                self._run(
                    session,
                    (
                        f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                        f"FOR (n:{label.value}) REQUIRE n.{key} IS UNIQUE"
                    ),
                )
            for tier in EvidenceTier:
                self._run(
                    session,
                    """
                    MERGE (e:EvidenceLevel {tier: $tier})
                    SET e.name = $name
                    """,
                    tier=int(tier),
                    name=tier.name.lower(),
                )

    def load_records(self, records: Iterable[KnowledgeGraphRecord]) -> LoaderStats:
        stats = LoaderStats()
        self.initialize()
        with self.driver.session() as session:
            for record in records:
                stats.records_seen += 1
                self._write_record(session, record, stats)
                stats.records_loaded += 1
        return stats

    def load_jsonl(self, path: str | Path) -> LoaderStats:
        return self.load_pubmed_jsonl(path)

    def load_pubmed_jsonl(self, path: str | Path) -> LoaderStats:
        stats = LoaderStats()
        self.initialize()
        input_path = Path(path)
        with self.driver.session() as session:
            with input_path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    stats.records_seen += 1
                    try:
                        record = KnowledgeGraphRecord.model_validate(json.loads(line))
                    except (json.JSONDecodeError, ValidationError) as exc:
                        if not self.config.skip_invalid_records:
                            raise ValueError(f"Invalid graph record on line {line_number}") from exc
                        LOGGER.warning("Skipping invalid graph record on line %d: %s", line_number, exc)
                        stats.records_skipped += 1
                        continue
                    self._write_record(session, record, stats)
                    stats.records_loaded += 1
        return stats

    def load_trial_records(self, records: Iterable[ClinicalTrialGraphRecord]) -> LoaderStats:
        stats = LoaderStats()
        self.initialize()
        with self.driver.session() as session:
            for record in records:
                stats.records_seen += 1
                self._write_trial_record(session, record, stats)
                stats.records_loaded += 1
        return stats

    def load_trial_jsonl(self, path: str | Path) -> LoaderStats:
        stats = LoaderStats()
        self.initialize()
        input_path = Path(path)
        with self.driver.session() as session:
            with input_path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    stats.records_seen += 1
                    try:
                        record = ClinicalTrialGraphRecord.model_validate(json.loads(line))
                    except (json.JSONDecodeError, ValidationError) as exc:
                        if not self.config.skip_invalid_records:
                            raise ValueError(f"Invalid trial graph record on line {line_number}") from exc
                        LOGGER.warning("Skipping invalid trial graph record on line %d: %s", line_number, exc)
                        stats.records_skipped += 1
                        continue
                    self._write_trial_record(session, record, stats)
                    stats.records_loaded += 1
        return stats

    def _write_record(
        self,
        session: GraphSession,
        record: KnowledgeGraphRecord,
        stats: LoaderStats,
    ) -> None:
        paper = GraphNode(
            label=NodeLabel.PAPER,
            key_value=record.pmid,
            properties=record.paper_properties,
        )
        self._merge_node(session, paper)
        stats.nodes_merged += 1

        node_index = self._dedupe_nodes(record.nodes)
        for node in node_index.values():
            self._merge_node(session, node)
            self._merge_mention(session, paper, node)
            stats.nodes_merged += 1
            stats.mentions_merged += 1

        for relation in record.relations:
            self._merge_node(session, relation.head)
            self._merge_node(session, relation.tail)
            self._merge_relation(session, relation)
            stats.relations_merged += 1

    def _write_trial_record(
        self,
        session: GraphSession,
        record: ClinicalTrialGraphRecord,
        stats: LoaderStats,
    ) -> None:
        trial = GraphNode(
            label=NodeLabel.TRIAL,
            key_value=record.nct_id,
            properties=record.trial_properties,
        )
        self._merge_node(session, trial)
        stats.nodes_merged += 1

        node_index = self._dedupe_nodes(record.nodes)
        for node in node_index.values():
            self._merge_node(session, node)
            stats.nodes_merged += 1

        for relation in record.relations:
            self._merge_node(session, relation.head)
            self._merge_node(session, relation.tail)
            self._merge_trial_relation(session, relation)
            stats.relations_merged += 1

    def _merge_node(self, session: GraphSession, node: GraphNode) -> None:
        label = node.label.value
        key = NODE_KEY[node.label]
        properties = node.keyed_properties()
        self._run(
            session,
            f"""
            MERGE (n:{label} {{{key}: $key_value}})
            SET n += $properties
            """,
            key_value=node.key_value,
            properties=properties,
        )

    def _merge_mention(self, session: GraphSession, paper: GraphNode, node: GraphNode) -> None:
        key = NODE_KEY[node.label]
        self._run(
            session,
            f"""
            MATCH (p:Paper {{pmid: $pmid}})
            MATCH (n:{node.label.value} {{{key}: $node_key}})
            MERGE (p)-[r:MENTIONS]->(n)
            ON CREATE SET
                r.source_pmids = [$pmid],
                r.evidence_tier = 0
            ON MATCH SET
                r.source_pmids =
                    CASE
                        WHEN $pmid IN coalesce(r.source_pmids, [])
                        THEN r.source_pmids
                        ELSE coalesce(r.source_pmids, []) + $pmid
                    END,
                r.evidence_tier = coalesce(r.evidence_tier, 0)
            """,
            pmid=paper.key_value,
            node_key=node.key_value,
        )

    def _merge_relation(self, session: GraphSession, relation: GraphRelation) -> None:
        head_key = NODE_KEY[relation.head.label]
        tail_key = NODE_KEY[relation.tail.label]
        rel_type = relation.relation.value
        self._run(
            session,
            f"""
            MATCH (head:{relation.head.label.value} {{{head_key}: $head_key}})
            MATCH (tail:{relation.tail.label.value} {{{tail_key}: $tail_key}})
            MERGE (head)-[r:{rel_type}]->(tail)
            ON CREATE SET
                r.source_pmids = [$source_pmid],
                r.evidence_tier = $evidence_tier,
                r.confidence = $confidence,
                r.created_from = $source_pmid
            ON MATCH SET
                r.source_pmids =
                    CASE
                        WHEN $source_pmid IN coalesce(r.source_pmids, [])
                        THEN r.source_pmids
                        ELSE coalesce(r.source_pmids, []) + $source_pmid
                    END,
                r.evidence_tier =
                    CASE
                        WHEN coalesce(r.evidence_tier, 0) < $evidence_tier
                        THEN $evidence_tier
                        ELSE r.evidence_tier
                    END,
                r.confidence =
                    CASE
                        WHEN coalesce(r.confidence, 0.0) < $confidence
                        THEN $confidence
                        ELSE r.confidence
                    END
            SET r += $properties
            WITH r, tail
            MATCH (e:EvidenceLevel {{tier: $evidence_tier}})
            MERGE (tail)-[:HAS_EVIDENCE]->(e)
            """,
            head_key=relation.head.key_value,
            tail_key=relation.tail.key_value,
            source_pmid=relation.source_pmid,
            evidence_tier=int(relation.evidence_tier),
            confidence=relation.confidence,
            properties=relation.graph_properties(),
        )

    def _merge_trial_relation(self, session: GraphSession, relation: TrialGraphRelation) -> None:
        head_key = NODE_KEY[relation.head.label]
        tail_key = NODE_KEY[relation.tail.label]
        rel_type = relation.relation.value
        self._run(
            session,
            f"""
            MATCH (head:{relation.head.label.value} {{{head_key}: $head_key}})
            MATCH (tail:{relation.tail.label.value} {{{tail_key}: $tail_key}})
            MERGE (head)-[r:{rel_type}]->(tail)
            ON CREATE SET
                r.source_ids = [$source_id],
                r.confidence = $confidence,
                r.created_from = $source_id
            ON MATCH SET
                r.source_ids =
                    CASE
                        WHEN $source_id IN coalesce(r.source_ids, [])
                        THEN r.source_ids
                        ELSE coalesce(r.source_ids, []) + $source_id
                    END,
                r.confidence =
                    CASE
                        WHEN coalesce(r.confidence, 0.0) < $confidence
                        THEN $confidence
                        ELSE r.confidence
                    END
            SET r += $properties
            """,
            head_key=relation.head.key_value,
            tail_key=relation.tail.key_value,
            source_id=relation.source_id,
            confidence=relation.confidence,
            properties=relation.properties,
        )

    def _run(self, session: GraphSession, query: str, **parameters: Any) -> None:
        normalized_query = "\n".join(line.rstrip() for line in query.strip().splitlines())
        if self.config.dry_run:
            LOGGER.info("DRY RUN Cypher:\n%s\nparams=%s", normalized_query, parameters)
            return
        session.run(normalized_query, **parameters)

    @staticmethod
    def _dedupe_nodes(nodes: Iterable[GraphNode]) -> dict[tuple[NodeLabel, str | int], GraphNode]:
        deduped: dict[tuple[NodeLabel, str | int], GraphNode] = {}
        for node in nodes:
            deduped[(node.label, node.key_value)] = node
        return deduped
