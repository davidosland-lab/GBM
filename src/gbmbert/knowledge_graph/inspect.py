"""Read-only inspection helpers for the GBM-AI Neo4j knowledge graph."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Protocol

LOGGER = logging.getLogger(__name__)


class InspectSession(Protocol):
    def run(self, query: str, **parameters: Any) -> Any: ...


class InspectSessionContext(Protocol):
    def __enter__(self) -> InspectSession: ...
    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None: ...


class InspectDriver(Protocol):
    def session(self) -> InspectSessionContext: ...


@dataclass(frozen=True)
class GraphCounts:
    nodes: int
    relationships: int
    labels: dict[str, int]
    relation_types: dict[str, int]


@dataclass(frozen=True)
class EvidenceTierCount:
    tier: int
    count: int


@dataclass(frozen=True)
class RecentPaper:
    pmid: str
    title: str
    publication_date: str


@dataclass(frozen=True)
class GraphInspection:
    counts: GraphCounts
    evidence_tiers: list[EvidenceTierCount]
    recent_papers: list[RecentPaper]

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": asdict(self.counts),
            "evidence_tiers": [asdict(item) for item in self.evidence_tiers],
            "recent_papers": [asdict(item) for item in self.recent_papers],
        }


def inspect_graph(driver: InspectDriver, recent_limit: int = 5) -> GraphInspection:
    """Run read-only summary queries against a Neo4j graph."""

    with driver.session() as session:
        return GraphInspection(
            counts=fetch_graph_counts(session),
            evidence_tiers=fetch_evidence_tier_counts(session),
            recent_papers=fetch_recent_papers(session, limit=recent_limit),
        )


def fetch_graph_counts(session: InspectSession) -> GraphCounts:
    """Fetch total nodes, relationships, labels, and relationship-type counts."""

    total_nodes = _single_value(session.run("MATCH (n) RETURN count(n) AS count"), "count")
    total_relationships = _single_value(session.run("MATCH ()-[r]->() RETURN count(r) AS count"), "count")
    labels = {
        str(row["label"]): int(row["count"])
        for row in session.run(
            """
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN label, count(*) AS count
            ORDER BY label
            """
        )
    }
    relation_types = {
        str(row["type"]): int(row["count"])
        for row in session.run(
            """
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(*) AS count
            ORDER BY type
            """
        )
    }
    return GraphCounts(
        nodes=int(total_nodes or 0),
        relationships=int(total_relationships or 0),
        labels=labels,
        relation_types=relation_types,
    )


def fetch_evidence_tier_counts(session: InspectSession) -> list[EvidenceTierCount]:
    """Fetch relationship counts grouped by evidence tier."""

    rows = session.run(
        """
        MATCH ()-[r]->()
        WHERE r.evidence_tier IS NOT NULL
        RETURN r.evidence_tier AS tier, count(*) AS count
        ORDER BY tier
        """
    )
    return [
        EvidenceTierCount(tier=int(row["tier"]), count=int(row["count"]))
        for row in rows
    ]


def fetch_recent_papers(session: InspectSession, limit: int = 5) -> list[RecentPaper]:
    """Fetch recent paper nodes for a quick provenance sanity check."""

    rows = session.run(
        """
        MATCH (p:Paper)
        RETURN
            p.pmid AS pmid,
            coalesce(p.title, '') AS title,
            coalesce(p.publication_date, '') AS publication_date
        ORDER BY publication_date DESC, pmid DESC
        LIMIT $limit
        """,
        limit=limit,
    )
    return [
        RecentPaper(
            pmid=str(row["pmid"]),
            title=str(row["title"]),
            publication_date=str(row["publication_date"]),
        )
        for row in rows
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a GBM-AI Neo4j knowledge graph.")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument("--recent-limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    if args.recent_limit < 1:
        parser.error("--recent-limit must be at least 1")
    if not args.password:
        parser.error("NEO4J_PASSWORD is required")
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise RuntimeError("Install neo4j to inspect a live database") from exc

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        inspection = inspect_graph(driver, recent_limit=args.recent_limit)
    finally:
        driver.close()

    if args.json:
        print(json.dumps(inspection.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_inspection(inspection))
    return 0


def format_inspection(inspection: GraphInspection) -> str:
    """Format inspection results for terminal display."""

    lines = [
        "GBM-AI Knowledge Graph Inspection",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"Nodes: {inspection.counts.nodes}",
        f"Relationships: {inspection.counts.relationships}",
        "",
        "Labels:",
    ]
    lines.extend(f"  {label}: {count}" for label, count in inspection.counts.labels.items())
    lines.append("")
    lines.append("Relation Types:")
    lines.extend(f"  {rel_type}: {count}" for rel_type, count in inspection.counts.relation_types.items())
    lines.append("")
    lines.append("Evidence Tiers:")
    if inspection.evidence_tiers:
        lines.extend(f"  tier {item.tier}: {item.count}" for item in inspection.evidence_tiers)
    else:
        lines.append("  none")
    lines.append("")
    lines.append("Recent Papers:")
    if inspection.recent_papers:
        lines.extend(
            f"  PMID {paper.pmid} ({paper.publication_date}): {paper.title}"
            for paper in inspection.recent_papers
        )
    else:
        lines.append("  none")
    return "\n".join(lines)


def _single_value(rows: Any, key: str) -> Any:
    for row in rows:
        return row[key]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
