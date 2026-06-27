"""Local Knowledge Graph Explorer web service."""

from __future__ import annotations

import argparse
import json
import logging
import os
import webbrowser
from collections import Counter
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from gbmbert.knowledge_graph.inspect import (
    EvidenceTierCount,
    GraphCounts,
    GraphInspection,
    RecentPaper,
    inspect_graph,
)
from gbmbert.knowledge_graph.queries import neighborhood_query, node_summary_query
from gbmbert.knowledge_graph.schema import (
    EvidenceTier,
    KnowledgeGraphRecord,
    NODE_KEY,
    NodeLabel,
    RelationType,
)
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord

LOGGER = logging.getLogger(__name__)
DEFAULT_SAMPLE_DATA = Path("data/examples/graph_records_sample.jsonl")
DEFAULT_BASELINE_DATA = Path("data/processed/ncbi_env_smoke_pipeline/graph_records.jsonl")
RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)
SELECTABLE_NODE_LABELS = [label for label in NodeLabel if label != NodeLabel.EVIDENCE_LEVEL]
SELECTABLE_RELATION_TYPES = [
    relation for relation in RelationType if relation != RelationType.HAS_EVIDENCE
]
ExplorerRecord = KnowledgeGraphRecord | ClinicalTrialGraphRecord


class GraphExplorerService:
    """Serve graph explorer data from sample JSONL records or a live Neo4j driver."""

    def __init__(
        self,
        *,
        records: list[ExplorerRecord] | None = None,
        driver: Any | None = None,
        source_path: str = "",
        artifact_index_path: str = "",
    ) -> None:
        if records is None and driver is None:
            raise ValueError("records or driver is required")
        self.records = records
        self.driver = driver
        self.source_path = source_path
        self.artifact_index_path = artifact_index_path

    @classmethod
    def from_jsonl(
        cls,
        path: str | Path,
        *,
        artifact_index_path: str | Path | None = None,
    ) -> "GraphExplorerService":
        return cls(
            records=load_graph_records(path),
            source_path=str(path),
            artifact_index_path=str(artifact_index_path or ""),
        )

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()

    def inspection(self, recent_limit: int = 5) -> dict[str, Any]:
        if self.driver is not None:
            return inspect_graph(self.driver, recent_limit=recent_limit).to_dict()
        return sample_inspection(self.records or [], recent_limit=recent_limit).to_dict()

    def metadata(self) -> dict[str, Any]:
        if self.driver is not None:
            inspection = inspect_graph(self.driver, recent_limit=5)
        else:
            inspection = sample_inspection(self.records or [], recent_limit=5)
        metadata = explorer_metadata(inspection)
        metadata["source_path"] = self.source_path
        metadata["graph_artifacts"] = graph_artifacts_from_index(self.artifact_index_path)
        return metadata

    def neighborhood(
        self,
        *,
        search: str = "",
        node_labels: list[NodeLabel] | None = None,
        relation_types: list[RelationType] | None = None,
        min_evidence_tier: EvidenceTier = EvidenceTier.HYPOTHESIS,
        depth: int = 1,
        min_citations: int = 1,
        limit: int = 100,
        overlay_only: bool = False,
        tier_changed_only: bool = False,
    ) -> dict[str, Any]:
        query = neighborhood_query(
            search=search,
            node_labels=node_labels,
            relation_types=relation_types,
            min_evidence_tier=min_evidence_tier,
            depth=depth,
            min_citations=min_citations,
            limit=limit,
        )
        if self.driver is not None:
            return _filter_overlay_graph(
                live_neighborhood(self.driver, query.cypher, query.parameters),
                overlay_only=overlay_only,
                tier_changed_only=tier_changed_only,
            )
        return sample_neighborhood(
            self.records or [],
            search=query.parameters["search"],
            node_labels=node_labels or [],
            relation_types=relation_types or [],
            min_evidence_tier=min_evidence_tier,
            min_citations=min_citations,
            limit=limit,
            cypher=query.cypher,
            parameters=query.parameters,
            overlay_only=overlay_only,
            tier_changed_only=tier_changed_only,
        )

    def node_summary(self, label: NodeLabel, key_value: str, limit: int = 25) -> dict[str, Any]:
        query = node_summary_query(label, key_value, limit=limit)
        if self.driver is not None:
            return live_node_summary(self.driver, query.cypher, query.parameters)
        return sample_node_summary(self.records or [], label, key_value, limit=limit)


def load_graph_records(path: str | Path) -> list[ExplorerRecord]:
    input_path = Path(path)
    records: list[ExplorerRecord] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if "nct_id" in payload:
                    records.append(ClinicalTrialGraphRecord.model_validate(payload))
                else:
                    records.append(KnowledgeGraphRecord.model_validate(payload))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"Invalid graph record on line {line_number}") from exc
    return records


def explorer_metadata(inspection: GraphInspection) -> dict[str, Any]:
    """Build filter metadata from the schema plus active graph counts."""

    label_counts = inspection.counts.labels
    relation_counts = inspection.counts.relation_types
    evidence_counts = {item.tier: item.count for item in inspection.evidence_tiers}
    return {
        "node_labels": [
            {
                "value": label.value,
                "label": label.value,
                "count": int(label_counts.get(label.value, 0)),
            }
            for label in SELECTABLE_NODE_LABELS
        ],
        "relation_types": [
            {
                "value": relation.value,
                "label": relation.value,
                "count": int(relation_counts.get(relation.value, 0)),
            }
            for relation in SELECTABLE_RELATION_TYPES
        ],
        "evidence_tiers": [
            {
                "value": int(tier),
                "label": tier.name.lower().replace("_", " "),
                "count": int(evidence_counts.get(int(tier), 0)),
            }
            for tier in EvidenceTier
        ],
        "warning": RESEARCH_WARNING,
    }


def sample_inspection(records: list[ExplorerRecord], recent_limit: int = 5) -> GraphInspection:
    nodes = _sample_nodes(records)
    label_counts = Counter(node["labels"][0] for node in nodes.values())
    relation_counts: Counter[str] = Counter()
    evidence_counts: Counter[int] = Counter()
    relationship_total = 0

    for record in records:
        if _is_pubmed_record(record):
            relation_counts[RelationType.MENTIONS.value] += len(record.nodes)
            evidence_counts[int(EvidenceTier.HYPOTHESIS)] += len(record.nodes)
            relationship_total += len(record.nodes)
        for relation in record.relations:
            relation_counts[relation.relation.value] += 1
            evidence_counts[_relation_evidence_tier(relation)] += 1
            relationship_total += 1

    recent_papers = sorted(
        (
            RecentPaper(
                pmid=_source_id(record),
                title=_source_title(record),
                publication_date=_source_date(record),
            )
            for record in records
        ),
        key=lambda paper: (paper.publication_date, paper.pmid),
        reverse=True,
    )[:recent_limit]

    return GraphInspection(
        counts=GraphCounts(
            nodes=len(nodes),
            relationships=relationship_total,
            labels=dict(sorted(label_counts.items())),
            relation_types=dict(sorted(relation_counts.items())),
        ),
        evidence_tiers=[
            EvidenceTierCount(tier=tier, count=count)
            for tier, count in sorted(evidence_counts.items())
        ],
        recent_papers=recent_papers,
    )


def sample_neighborhood(
    records: list[ExplorerRecord],
    *,
    search: str,
    node_labels: list[NodeLabel],
    relation_types: list[RelationType],
    min_evidence_tier: EvidenceTier,
    min_citations: int,
    limit: int,
    cypher: str,
    parameters: dict[str, Any],
    overlay_only: bool = False,
    tier_changed_only: bool = False,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    search_text = search.casefold()
    allowed_labels = {label.value for label in node_labels}
    allowed_relations = {relation.value for relation in relation_types}

    for record in records:
        if _is_pubmed_record(record) and (not allowed_relations or RelationType.MENTIONS.value in allowed_relations):
            paper = _source_node_payload(record)
            for node in record.nodes:
                if int(EvidenceTier.HYPOTHESIS) < int(min_evidence_tier):
                    continue
                source_pmids = [_source_id(record)]
                if len(source_pmids) < min_citations:
                    continue
                if allowed_labels and not (
                    NodeLabel.PAPER.value in allowed_labels
                    or node.label.value in allowed_labels
                ):
                    continue
                if search_text and not _mention_matches_search(record, node, search_text):
                    continue

                target = _sample_node_payload(node.label, node.key_value, node.properties)
                nodes[paper["id"]] = paper
                nodes[target["id"]] = target
                edge_id = f"{paper['id']}|{RelationType.MENTIONS.value}|{target['id']}"
                edges[edge_id] = {
                    "id": edge_id,
                    "source": paper["id"],
                    "target": target["id"],
                    "type": RelationType.MENTIONS.value,
                    "evidence_tier": int(EvidenceTier.HYPOTHESIS),
                    "confidence": 1.0,
                    "source_pmids": source_pmids,
                    "properties": {"source": "record.nodes"},
                    "evidence_overlay": {},
                    "curation_links": _curation_links_for_properties({"source_pmids": source_pmids}, source_pmids),
                }
                if len(edges) >= limit:
                    break
        if len(edges) >= limit:
            break

        for relation in record.relations:
            overlay_metadata = _relation_overlay_metadata(relation)
            if overlay_only and not overlay_metadata:
                continue
            if tier_changed_only and not _overlay_tier_changed(overlay_metadata):
                continue
            source_ids = _relation_source_ids(relation)
            source_pmids = source_ids if _is_pubmed_relation(relation) else []
            if _relation_evidence_tier(relation) < int(min_evidence_tier):
                continue
            if len(source_ids) < min_citations:
                continue
            if allowed_relations and relation.relation.value not in allowed_relations:
                continue
            if allowed_labels and not (
                relation.head.label.value in allowed_labels
                or relation.tail.label.value in allowed_labels
            ):
                continue
            if search_text and not _relation_matches_search(record, relation, search_text):
                continue

            head = _sample_node_payload(relation.head.label, relation.head.key_value, relation.head.properties)
            tail = _sample_node_payload(relation.tail.label, relation.tail.key_value, relation.tail.properties)
            nodes[head["id"]] = head
            nodes[tail["id"]] = tail
            edge_id = f"{head['id']}|{relation.relation.value}|{tail['id']}"
            edges[edge_id] = {
                "id": edge_id,
                "source": head["id"],
                "target": tail["id"],
                "type": relation.relation.value,
                "evidence_tier": _relation_evidence_tier(relation),
                "confidence": relation.confidence,
                "source_pmids": source_pmids if _is_pubmed_relation(relation) else [],
                "source_ids": source_ids,
                "properties": _relation_properties(relation),
                "evidence_overlay": overlay_metadata,
                "curation_links": _curation_links_for_relation(relation, source_pmids),
            }
            if len(edges) >= limit:
                break
        if len(edges) >= limit:
            break

    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "cypher": cypher,
        "parameters": parameters,
        "warning": RESEARCH_WARNING,
        "mode": "sample",
    }


def sample_node_summary(
    records: list[ExplorerRecord],
    label: NodeLabel,
    key_value: str,
    limit: int = 25,
) -> dict[str, Any]:
    selected = _find_sample_node(records, label, key_value)
    if selected is None:
        return {"node": None, "labels": [label.value], "relations": [], "warning": RESEARCH_WARNING}

    relations: list[dict[str, Any]] = []
    for record in records:
        for relation in record.relations:
            if relation.head.label == label and str(relation.head.key_value) == str(key_value):
                relations.append(_sample_relation_summary(relation, relation.tail, reverse=False))
            elif relation.tail.label == label and str(relation.tail.key_value) == str(key_value):
                relations.append(_sample_relation_summary(relation, relation.head, reverse=True))

    relations.sort(
        key=lambda item: (int(item["evidence_tier"]), len(item["source_ids"])),
        reverse=True,
    )
    return {
        "node": _sample_node_payload(label, key_value, selected.properties)["properties"],
        "labels": [label.value],
        "relations": relations[:limit],
        "warning": RESEARCH_WARNING,
    }


def live_neighborhood(driver: Any, cypher: str, parameters: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    with driver.session() as session:
        for row in session.run(cypher, **parameters):
            path = row["path"]
            for node in path.nodes:
                payload = _neo4j_node_payload(node)
                nodes[payload["id"]] = payload
            for relationship in path.relationships:
                source = _neo4j_node_payload(relationship.start_node)
                target = _neo4j_node_payload(relationship.end_node)
                nodes[source["id"]] = source
                nodes[target["id"]] = target
                edge_id = getattr(relationship, "element_id", str(id(relationship)))
                edges[edge_id] = {
                    "id": edge_id,
                    "source": source["id"],
                    "target": target["id"],
                    "type": relationship.type,
                    "evidence_tier": int(relationship.get("evidence_tier", 0) or 0),
                    "confidence": float(relationship.get("confidence", 0.0) or 0.0),
                    "source_pmids": list(relationship.get("source_pmids", []) or []),
                    "properties": dict(relationship),
                    "evidence_overlay": _property_overlay_metadata(dict(relationship)),
                    "curation_links": _curation_links_for_properties(
                        dict(relationship),
                        list(relationship.get("source_pmids", []) or []),
                    ),
                }
    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "cypher": cypher,
        "parameters": parameters,
        "warning": RESEARCH_WARNING,
        "mode": "neo4j",
    }


def live_node_summary(driver: Any, cypher: str, parameters: dict[str, Any]) -> dict[str, Any]:
    with driver.session() as session:
        rows = session.run(cypher, **parameters)
        for row in rows:
            return {
                "node": row["node"],
                "labels": row["labels"],
                "relations": row["relations"],
                "warning": RESEARCH_WARNING,
            }
    return {"node": None, "labels": [], "relations": [], "warning": RESEARCH_WARNING}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local GBM-AI Knowledge Graph Explorer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--sample-data", default=str(DEFAULT_SAMPLE_DATA))
    parser.add_argument(
        "--baseline-data",
        action="store_true",
        help="Use the latest local real PubMed smoke baseline graph records if present.",
    )
    parser.add_argument("--neo4j", action="store_true", help="Use a live Neo4j database instead of sample JSONL.")
    parser.add_argument("--artifact-index", type=Path, help="Artifact index JSON used to list/select graph JSONL files.")
    parser.add_argument("--artifact", help="Graph artifact path, filename, or stem to load from --artifact-index.")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument("--open", action="store_true", help="Open the Explorer in the default browser.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    service = _build_service(args)
    url = f"http://{args.host}:{args.port}/"
    if args.open:
        webbrowser.open(url)
    LOGGER.info("Starting GBM-AI Knowledge Graph Explorer at %s", url)
    run_server(service, host=args.host, port=args.port)
    return 0


def run_server(service: GraphExplorerService, *, host: str, port: int) -> None:
    handler_class = make_handler(service)
    server = ThreadingHTTPServer((host, port), handler_class)
    try:
        server.serve_forever()
    finally:
        service.close()
        server.server_close()


def make_handler(service: GraphExplorerService) -> type[BaseHTTPRequestHandler]:
    class ExplorerHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            try:
                if parsed.path in {"/", "/index.html"}:
                    self._send_html(EXPLORER_HTML)
                elif parsed.path == "/api/metadata":
                    self._send_json(service.metadata())
                elif parsed.path == "/api/inspection":
                    limit = _int_param(params, "recent_limit", 5)
                    self._send_json(service.inspection(recent_limit=limit))
                elif parsed.path == "/api/neighborhood":
                    self._send_json(service.neighborhood(**_neighborhood_params(params)))
                elif parsed.path == "/api/node-summary":
                    label = NodeLabel(_required_param(params, "label"))
                    key_value = _required_param(params, "key_value")
                    limit = _int_param(params, "limit", 25)
                    self._send_json(service.node_summary(label, key_value, limit=limit))
                else:
                    self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            except Exception as exc:  # pragma: no cover - exercised through browser/runtime
                LOGGER.exception("Explorer request failed")
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            LOGGER.info("%s - %s", self.address_string(), format % args)

        def _send_html(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            data = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return ExplorerHandler


def _build_service(args: argparse.Namespace) -> GraphExplorerService:
    if args.neo4j:
        if not args.password:
            raise ValueError("NEO4J_PASSWORD is required for --neo4j mode")
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("Install neo4j to use live graph mode") from exc
        return GraphExplorerService(driver=GraphDatabase.driver(args.uri, auth=(args.user, args.password)))
    sample_data = _selected_graph_path(args)
    if args.baseline_data and not sample_data.exists():
        raise FileNotFoundError(
            f"Baseline graph records not found at {sample_data}; run the NCBI smoke pipeline first."
        )
    return GraphExplorerService.from_jsonl(sample_data, artifact_index_path=args.artifact_index)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = Path(".env")
    if not env_path.exists():
        return
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            load_dotenv(env_path, encoding=encoding)
            return
        except UnicodeDecodeError:
            continue
    LOGGER.warning("Could not read .env with utf-8 or utf-16 encodings")


def _neighborhood_params(params: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "search": _string_param(params, "search", ""),
        "node_labels": [NodeLabel(value) for value in _list_param(params, "node_label")],
        "relation_types": [RelationType(value) for value in _list_param(params, "relation_type")],
        "min_evidence_tier": EvidenceTier(_int_param(params, "min_evidence_tier", 0)),
        "depth": _int_param(params, "depth", 1),
        "min_citations": _int_param(params, "min_citations", 1),
        "limit": _int_param(params, "limit", 100),
        "overlay_only": _bool_param(params, "overlay_only", False),
        "tier_changed_only": _bool_param(params, "tier_changed_only", False),
    }


def _required_param(params: dict[str, list[str]], name: str) -> str:
    value = _string_param(params, name, "")
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _string_param(params: dict[str, list[str]], name: str, default: str) -> str:
    values = params.get(name)
    return values[0].strip() if values else default


def _int_param(params: dict[str, list[str]], name: str, default: int) -> int:
    values = params.get(name)
    return int(values[0]) if values else default


def _bool_param(params: dict[str, list[str]], name: str, default: bool) -> bool:
    values = params.get(name)
    if not values:
        return default
    return values[0].strip().casefold() in {"1", "true", "yes", "on"}


def _list_param(params: dict[str, list[str]], name: str) -> list[str]:
    values: list[str] = []
    for raw in params.get(name, []):
        values.extend(item.strip() for item in raw.split(",") if item.strip())
    return values


def graph_artifacts_from_index(index_path: str | Path | None) -> list[dict[str, str]]:
    if not index_path:
        return []
    path = Path(index_path)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    artifacts = []
    for item in payload.get("artifacts", []):
        artifact_type = str(item.get("artifact_type", ""))
        artifact_path = str(item.get("path", ""))
        if artifact_type in {"pubmed_graph_records", "trial_graph_records", "evidence_overlay_graph_records"} or artifact_path.endswith("graph_records.jsonl"):
            artifacts.append(
                {
                    "path": artifact_path,
                    "name": Path(artifact_path).name,
                    "stem": Path(artifact_path).stem,
                    "artifact_type": artifact_type or "graph_records",
                    "category": str(item.get("category", "")),
                }
            )
    return artifacts


def resolve_graph_artifact(index_path: str | Path | None, selector: str) -> Path:
    candidate = Path(selector)
    if candidate.exists():
        return candidate
    artifacts = graph_artifacts_from_index(index_path)
    for artifact in artifacts:
        path = Path(artifact["path"])
        if selector in {artifact["path"], artifact["name"], artifact["stem"], path.as_posix(), str(path)}:
            return path
    available = ", ".join(item["path"] for item in artifacts) or "none"
    raise FileNotFoundError(f"Graph artifact {selector!r} was not found; available artifacts: {available}")


def _selected_graph_path(args: argparse.Namespace) -> Path:
    if args.artifact:
        return resolve_graph_artifact(args.artifact_index, args.artifact)
    if args.baseline_data:
        return DEFAULT_BASELINE_DATA
    return Path(args.sample_data)


def _sample_nodes(records: list[ExplorerRecord]) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for record in records:
        source = _source_node_payload(record)
        nodes[source["id"]] = source
        for node in record.nodes:
            payload = _sample_node_payload(node.label, node.key_value, node.properties)
            nodes[payload["id"]] = payload
    return nodes


def _find_sample_node(
    records: list[ExplorerRecord],
    label: NodeLabel,
    key_value: str,
) -> Any | None:
    for record in records:
        if label == _source_label(record) and _source_id(record) == str(key_value):
            return type("SourceNode", (), {"properties": _source_properties(record)})()
        for node in record.nodes:
            if node.label == label and str(node.key_value) == str(key_value):
                return node
    return None


def _sample_node_payload(label: NodeLabel, key_value: str | int, properties: dict[str, Any]) -> dict[str, Any]:
    keyed = {NODE_KEY[label]: key_value, **properties}
    display = keyed.get("display_name") or keyed.get("title") or keyed.get(NODE_KEY[label]) or key_value
    return {
        "id": f"{label.value}:{key_value}",
        "label": str(display),
        "key_value": key_value,
        "labels": [label.value],
        "properties": keyed,
    }


def _sample_relation_summary(relation: Any, neighbor: Any, *, reverse: bool) -> dict[str, Any]:
    source_ids = _relation_source_ids(relation)
    source_pmids = source_ids if _is_pubmed_relation(relation) else []
    return {
        "relation": relation.relation.value,
        "neighbor": _sample_node_payload(neighbor.label, neighbor.key_value, neighbor.properties)["properties"],
        "neighbor_labels": [neighbor.label.value],
        "evidence_tier": _relation_evidence_tier(relation),
        "evidence_overlay": _relation_overlay_metadata(relation),
        "source_pmids": source_pmids,
        "source_ids": source_ids,
        "curation_links": _curation_links_for_relation(relation, source_pmids),
        "reverse": reverse,
    }


def _relation_matches_search(record: ExplorerRecord, relation: Any, search_text: str) -> bool:
    values = [
        _source_id(record),
        _source_title(record),
        str(relation.head.key_value),
        str(relation.tail.key_value),
        relation.head.label.value,
        relation.tail.label.value,
        relation.relation.value,
        str(relation.properties.get("sentence", "")),
        str(relation.properties.get("source_url", "")),
    ]
    return any(search_text in value.casefold() for value in values)


def _mention_matches_search(record: ExplorerRecord, node: Any, search_text: str) -> bool:
    values = [
        _source_id(record),
        _source_title(record),
        str(_source_properties(record).get("abstract", "")),
        str(node.key_value),
        node.label.value,
        str(node.properties.get("display_name", "")),
        " ".join(str(alias) for alias in node.properties.get("aliases", []) or []),
    ]
    return any(search_text in value.casefold() for value in values)


def _is_pubmed_record(record: ExplorerRecord) -> bool:
    return isinstance(record, KnowledgeGraphRecord)


def _is_pubmed_relation(relation: Any) -> bool:
    return hasattr(relation, "source_pmid")


def _source_label(record: ExplorerRecord) -> NodeLabel:
    return NodeLabel.PAPER if _is_pubmed_record(record) else NodeLabel.TRIAL


def _source_id(record: ExplorerRecord) -> str:
    return record.pmid if _is_pubmed_record(record) else record.nct_id


def _source_properties(record: ExplorerRecord) -> dict[str, Any]:
    return record.paper_properties if _is_pubmed_record(record) else record.trial_properties


def _source_title(record: ExplorerRecord) -> str:
    properties = _source_properties(record)
    return str(
        properties.get("title")
        or properties.get("display_name")
        or properties.get("brief_title")
        or _source_id(record)
    )


def _source_date(record: ExplorerRecord) -> str:
    properties = _source_properties(record)
    return str(
        properties.get("publication_date")
        or properties.get("last_update_posted")
        or properties.get("start_date")
        or ""
    )


def _source_node_payload(record: ExplorerRecord) -> dict[str, Any]:
    return _sample_node_payload(_source_label(record), _source_id(record), _source_properties(record))


def _relation_source_ids(relation: Any) -> list[str]:
    if _is_pubmed_relation(relation):
        return [relation.source_pmid]
    return [relation.source_id]


def _relation_evidence_tier(relation: Any) -> int:
    return int(getattr(relation, "evidence_tier", EvidenceTier.HYPOTHESIS))


def _relation_properties(relation: Any) -> dict[str, Any]:
    if hasattr(relation, "graph_properties"):
        return relation.graph_properties()
    return dict(relation.properties)


def _relation_overlay_metadata(relation: Any) -> dict[str, Any]:
    return _property_overlay_metadata(_relation_properties(relation))


def _property_overlay_metadata(properties: dict[str, Any]) -> dict[str, Any]:
    if "evidence_overlay_tier" not in properties:
        return {}
    return {
        "source": properties.get("evidence_overlay_source", ""),
        "original_tier": properties.get("evidence_overlay_original_tier"),
        "overlaid_tier": properties.get("evidence_overlay_tier"),
        "item_id": properties.get("evidence_overlay_item_id", ""),
        "checkpoint": properties.get("evidence_overlay_checkpoint", ""),
        "review_status": properties.get("evidence_overlay_review_status", ""),
        "tier_changed": properties.get("evidence_overlay_original_tier") != properties.get("evidence_overlay_tier"),
    }


def _curation_links_for_relation(relation: Any, source_pmids: list[str]) -> list[dict[str, str]]:
    return _curation_links_for_properties(_relation_properties(relation), source_pmids)


def _curation_links_for_properties(properties: dict[str, Any], source_pmids: list[str]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for pmid in source_pmids:
        if not pmid:
            continue
        links.append(
            {
                "label": f"PubMed {pmid}",
                "kind": "external",
                "value": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
        links.append(
            {
                "label": f"Curated evidence search PMID {pmid}",
                "kind": "command",
                "value": (
                    "gbmbert-search-curated-evidence "
                    "data/processed/curation_smoke_workflow/curated_evidence_predictions.jsonl "
                    f"--pmid {pmid}"
                ),
            }
        )
    item_id = str(properties.get("evidence_overlay_item_id") or "")
    if item_id:
        links.append(
            {
                "label": f"Curated item {item_id}",
                "kind": "curation_item",
                "value": item_id,
            }
        )
    return links


def _overlay_tier_changed(overlay: dict[str, Any]) -> bool:
    return bool(overlay) and overlay.get("original_tier") != overlay.get("overlaid_tier")


def _filter_overlay_graph(graph: dict[str, Any], *, overlay_only: bool, tier_changed_only: bool) -> dict[str, Any]:
    if not overlay_only and not tier_changed_only:
        return graph
    edges = []
    visible_node_ids: set[str] = set()
    for edge in graph.get("edges", []):
        overlay = edge.get("evidence_overlay") or {}
        if overlay_only and not overlay:
            continue
        if tier_changed_only and not _overlay_tier_changed(overlay):
            continue
        edges.append(edge)
        visible_node_ids.add(str(edge.get("source")))
        visible_node_ids.add(str(edge.get("target")))
    return {
        **graph,
        "nodes": [node for node in graph.get("nodes", []) if str(node.get("id")) in visible_node_ids],
        "edges": edges,
    }


def _neo4j_node_payload(node: Any) -> dict[str, Any]:
    labels = sorted(node.labels)
    properties = dict(node)
    label = labels[0] if labels else "Node"
    key_name = NODE_KEY.get(NodeLabel(label)) if label in NodeLabel._value2member_map_ else None
    key_value = properties.get(key_name) if key_name else getattr(node, "element_id", str(id(node)))
    display = properties.get("display_name") or properties.get("title") or properties.get("name")
    display = display or properties.get("symbol") or properties.get("pmid") or properties.get("nct_id") or key_value
    return {
        "id": getattr(node, "element_id", f"{label}:{key_value}"),
        "label": str(display),
        "key_value": key_value,
        "labels": labels,
        "properties": properties,
    }


EXPLORER_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GBM-AI Knowledge Graph Explorer</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #182026;
      --muted: #61717d;
      --line: #d7dde2;
      --panel: #f6f8f9;
      --paper: #ffffff;
      --accent: #0b6e69;
      --accent-2: #8a4d18;
      --danger: #8f2431;
      --node-paper: #5f6f82;
      --node-bio: #0b6e69;
      --node-treatment: #7b5fb2;
      --node-outcome: #8a4d18;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font: 14px/1.45 "Segoe UI", system-ui, sans-serif;
      letter-spacing: 0;
    }
    header {
      height: 58px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: var(--paper);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 650;
    }
    .warning {
      color: var(--danger);
      font-size: 12px;
      max-width: 760px;
      text-align: right;
    }
    main {
      display: grid;
      grid-template-columns: 280px minmax(360px, 1fr) 340px;
      min-height: calc(100vh - 58px);
    }
    aside, section {
      min-width: 0;
    }
    .filters, .details {
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 16px;
    }
    .details {
      border-right: 0;
      border-left: 1px solid var(--line);
      overflow: auto;
    }
    .graph-area {
      display: grid;
      grid-template-rows: 92px minmax(360px, 1fr) 170px;
      min-width: 0;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      border-bottom: 1px solid var(--line);
      background: #fbfcfc;
    }
    .metric {
      padding: 14px 16px;
      border-right: 1px solid var(--line);
    }
    .metric:last-child { border-right: 0; }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
    }
    .metric strong {
      display: block;
      margin-top: 4px;
      font-size: 20px;
    }
    label {
      display: block;
      margin: 14px 0 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }
    input, select {
      width: 100%;
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 6px 8px;
      color: var(--ink);
      background: var(--paper);
      font: inherit;
    }
    input[type="checkbox"] {
      width: auto;
      min-height: 0;
      margin-right: 6px;
    }
    select[multiple] { min-height: 110px; }
    button {
      height: 36px;
      border: 1px solid #095a56;
      border-radius: 4px;
      background: var(--accent);
      color: white;
      font-weight: 650;
      cursor: pointer;
    }
    .button-row {
      display: grid;
      grid-template-columns: 1fr 42px;
      gap: 8px;
      margin-top: 14px;
    }
    .icon-button { font-size: 18px; }
    .canvas {
      position: relative;
      min-height: 360px;
      overflow: hidden;
      background:
        linear-gradient(#eef2f3 1px, transparent 1px),
        linear-gradient(90deg, #eef2f3 1px, transparent 1px);
      background-size: 28px 28px;
    }
    svg {
      width: 100%;
      height: 100%;
      display: block;
    }
    .node { cursor: pointer; }
    .node circle { stroke: #fff; stroke-width: 2; filter: drop-shadow(0 1px 2px rgba(0,0,0,.18)); }
    .node text { fill: var(--ink); font-size: 12px; text-anchor: middle; pointer-events: none; }
    .edge {
      cursor: pointer;
      opacity: .86;
      vector-effect: non-scaling-stroke;
    }
    .edge.selected {
      opacity: 1;
      filter: drop-shadow(0 0 3px rgba(24,32,38,.35));
    }
    .edge-label {
      cursor: pointer;
      fill: var(--muted);
      font-size: 10px;
      text-anchor: middle;
      paint-order: stroke;
      stroke: var(--paper);
      stroke-width: 3px;
      stroke-linejoin: round;
    }
    .edge-label.selected { fill: var(--ink); font-weight: 650; }
    .legend {
      position: absolute;
      right: 12px;
      top: 12px;
      display: grid;
      grid-template-columns: repeat(2, minmax(104px, 1fr));
      gap: 4px 10px;
      max-width: min(360px, calc(100% - 24px));
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: rgba(255,255,255,.92);
      color: var(--muted);
      font-size: 11px;
      z-index: 2;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }
    .legend-line {
      width: 24px;
      height: 0;
      border-top-style: solid;
      flex: 0 0 auto;
    }
    .legend-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .query {
      border-top: 1px solid var(--line);
      padding: 12px 14px;
      overflow: auto;
      background: #20282f;
      color: #f4f7f8;
      font: 12px/1.45 Consolas, monospace;
      white-space: pre-wrap;
    }
    h2 {
      margin: 0 0 10px;
      font-size: 15px;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 8px 0 14px;
    }
    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 8px;
      background: var(--paper);
      color: var(--muted);
      font-size: 12px;
    }
    .relation {
      border-top: 1px solid var(--line);
      padding: 10px 0;
    }
    .relation strong {
      display: block;
      overflow-wrap: anywhere;
    }
    .mini-section {
      border-top: 1px solid var(--line);
      padding: 12px 0;
    }
    .mini-section h3 {
      margin: 0 0 8px;
      font-size: 12px;
      text-transform: uppercase;
      color: var(--muted);
    }
    .paper-list {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .paper-list li {
      overflow-wrap: anywhere;
      font-size: 12px;
    }
    .paper-list strong { display: block; }
    .kv {
      display: grid;
      grid-template-columns: 110px 1fr;
      gap: 6px 10px;
      margin-top: 10px;
      font-size: 12px;
    }
    .kv span:nth-child(odd) { color: var(--muted); }
    @media (max-width: 980px) {
      main { grid-template-columns: 1fr; }
      .filters, .details { border: 0; border-bottom: 1px solid var(--line); }
      .graph-area { min-height: 620px; }
      header { height: auto; min-height: 72px; align-items: flex-start; flex-direction: column; gap: 6px; padding: 12px; }
      .warning { text-align: left; }
    }
  </style>
</head>
<body>
  <header>
    <h1>GBM-AI Knowledge Graph Explorer</h1>
    <div class="warning">Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.</div>
  </header>
  <main>
    <aside class="filters">
      <h2>Filters</h2>
      <label for="search">Search</label>
      <input id="search" value="" autocomplete="off">
      <label for="node-label">Node Labels</label>
      <select id="node-label" multiple></select>
      <label for="relation-type">Relation Types</label>
      <select id="relation-type" multiple></select>
      <label for="evidence">Minimum Evidence Tier</label>
      <select id="evidence"></select>
      <label for="depth">Hop Depth</label>
      <select id="depth">
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
      </select>
      <label for="citations">Minimum PMIDs</label>
      <input id="citations" type="number" min="1" value="1">
      <label><input id="overlay-only" type="checkbox"> Overlaid relations only</label>
      <label><input id="tier-changed-only" type="checkbox"> Tier changed only</label>
      <div class="button-row">
        <button id="apply">Search</button>
        <button id="reset" class="icon-button" title="Reset filters">↺</button>
      </div>
    </aside>
    <section class="graph-area">
      <div class="stats">
        <div class="metric"><span>Nodes</span><strong id="nodes-count">0</strong></div>
        <div class="metric"><span>Relationships</span><strong id="relationships-count">0</strong></div>
        <div class="metric"><span>Visible Nodes</span><strong id="visible-nodes">0</strong></div>
        <div class="metric"><span>Visible Edges</span><strong id="visible-edges">0</strong></div>
      </div>
      <div class="canvas">
        <div id="evidence-legend" class="legend" aria-label="Evidence tier legend"></div>
        <svg id="graph" role="img" aria-label="Knowledge graph"></svg>
      </div>
      <pre id="query" class="query"></pre>
    </section>
    <aside class="details">
      <h2 id="detail-title">Graph</h2>
      <div id="detail-labels" class="pill-row"></div>
      <div id="detail-body"></div>
    </aside>
  </main>
  <script>
    const labelSelect = document.getElementById("node-label");
    const relationSelect = document.getElementById("relation-type");
    const evidenceSelect = document.getElementById("evidence");
    const state = { graph: { nodes: [], edges: [] }, inspection: null, metadata: null, selected: null };
    const evidenceTierStyles = {
      0: { color: "#8b98a3", width: 1.8, dash: "6 4" },
      1: { color: "#0b6e69", width: 2.2, dash: "" },
      2: { color: "#587728", width: 2.6, dash: "" },
      3: { color: "#b66a13", width: 3.0, dash: "" },
      4: { color: "#7b5fb2", width: 3.4, dash: "" },
      5: { color: "#8f2431", width: 4.0, dash: "" }
    };

    function selectedValues(select) {
      return Array.from(select.selectedOptions).map(option => option.value);
    }

    async function loadMetadata() {
      const response = await fetch("/api/metadata");
      state.metadata = await response.json();
      populateSelect(labelSelect, state.metadata.node_labels, false);
      populateSelect(relationSelect, state.metadata.relation_types, false);
      populateSelect(evidenceSelect, state.metadata.evidence_tiers, true);
      evidenceSelect.value = "0";
      renderEvidenceLegend();
    }

    function populateSelect(select, items, includeValuePrefix) {
      select.innerHTML = "";
      items.forEach(item => {
        const count = item.count ? ` (${item.count})` : "";
        const prefix = includeValuePrefix ? `${item.value} ` : "";
        select.add(new Option(`${prefix}${item.label}${count}`, item.value));
      });
    }

    async function loadInspection() {
      const response = await fetch("/api/inspection");
      const data = await response.json();
      state.inspection = data;
      document.getElementById("nodes-count").textContent = data.counts.nodes;
      document.getElementById("relationships-count").textContent = data.counts.relationships;
    }

    async function loadGraph() {
      const params = new URLSearchParams();
      params.set("search", document.getElementById("search").value);
      selectedValues(labelSelect).forEach(value => params.append("node_label", value));
      selectedValues(relationSelect).forEach(value => params.append("relation_type", value));
      params.set("min_evidence_tier", document.getElementById("evidence").value);
      params.set("depth", document.getElementById("depth").value);
      params.set("min_citations", document.getElementById("citations").value || "1");
      if (document.getElementById("overlay-only").checked) params.set("overlay_only", "true");
      if (document.getElementById("tier-changed-only").checked) params.set("tier_changed_only", "true");
      const response = await fetch(`/api/neighborhood?${params.toString()}`);
      state.graph = await response.json();
      state.selected = null;
      document.getElementById("query").textContent = `${state.graph.cypher}\n\nparams = ${JSON.stringify(state.graph.parameters, null, 2)}`;
      renderGraph();
      renderGraphDetails();
    }

    function renderEvidenceLegend() {
      const legend = document.getElementById("evidence-legend");
      const tiers = state.metadata?.evidence_tiers || [];
      legend.innerHTML = tiers.map(item => {
        const style = evidenceTierStyle(item.value);
        const borderStyle = style.dash ? "dashed" : "solid";
        const count = item.count ? ` (${item.count})` : "";
        return `<div class="legend-item"><span class="legend-line" style="border-color:${style.color};border-top-width:${style.width}px;border-top-style:${borderStyle}"></span><span class="legend-label">tier ${item.value} ${escapeHtml(item.label)}${count}</span></div>`;
      }).join("");
    }

    function renderGraph() {
      const svg = document.getElementById("graph");
      svg.innerHTML = "";
      const width = svg.clientWidth || 800;
      const height = svg.clientHeight || 480;
      const nodes = state.graph.nodes;
      const edges = state.graph.edges;
      document.getElementById("visible-nodes").textContent = nodes.length;
      document.getElementById("visible-edges").textContent = edges.length;
      if (!nodes.length) {
        svg.innerHTML = `<text x="${width / 2}" y="${height / 2}" text-anchor="middle" fill="#61717d">No graph records match the current filters</text>`;
        return;
      }
      const cx = width / 2;
      const cy = height / 2;
      const radius = Math.max(110, Math.min(width, height) * 0.34);
      const positions = {};
      nodes.forEach((node, index) => {
        const angle = (Math.PI * 2 * index) / Math.max(nodes.length, 1) - Math.PI / 2;
        positions[node.id] = {
          x: cx + Math.cos(angle) * (nodes.length === 1 ? 0 : radius),
          y: cy + Math.sin(angle) * (nodes.length === 1 ? 0 : radius)
        };
      });
      edges.forEach((edge, index) => {
        const source = positions[edge.source];
        const target = positions[edge.target];
        if (!source || !target) return;
        const style = evidenceTierStyle(edge.evidence_tier);
        const overlay = edge.evidence_overlay || {};
        const overlayTitle = overlay.overlaid_tier !== undefined ? ` overlay ${overlay.original_tier}->${overlay.overlaid_tier}` : "";
        const dash = style.dash ? ` stroke-dasharray="${style.dash}"` : "";
        svg.insertAdjacentHTML("beforeend", `<line class="edge" data-edge-index="${index}" x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="${style.color}" stroke-width="${style.width}"${dash}><title>${escapeHtml(edge.type)} tier ${edge.evidence_tier}${escapeHtml(overlayTitle)}</title></line>`);
        svg.insertAdjacentHTML("beforeend", `<text class="edge-label" data-edge-index="${index}" x="${(source.x + target.x)/2}" y="${(source.y + target.y)/2 - 6}">${escapeHtml(edge.type)}</text>`);
      });
      nodes.forEach(node => {
        const pos = positions[node.id];
        const color = nodeColor(node.labels[0]);
        const label = shortLabel(node.label);
        svg.insertAdjacentHTML("beforeend", `<g class="node" data-id="${node.id}" transform="translate(${pos.x},${pos.y})"><circle r="26" fill="${color}"></circle><text y="43">${label}</text></g>`);
      });
      svg.querySelectorAll(".node").forEach(el => {
        el.addEventListener("click", () => selectNode(el.dataset.id));
      });
      svg.querySelectorAll("[data-edge-index]").forEach(el => {
        el.addEventListener("click", () => selectEdge(Number(el.dataset.edgeIndex)));
      });
    }

    function evidenceTierStyle(tier) {
      return evidenceTierStyles[Number(tier)] || evidenceTierStyles[0];
    }

    function nodeColor(label) {
      if (label === "Paper") return "var(--node-paper)";
      if (["Drug","Treatment","DeliveryModifier"].includes(label)) return "var(--node-treatment)";
      if (["Outcome","Disease"].includes(label)) return "var(--node-outcome)";
      return "var(--node-bio)";
    }

    function shortLabel(value) {
      return String(value).length > 22 ? `${String(value).slice(0, 19)}...` : value;
    }

    async function selectNode(id) {
      const node = state.graph.nodes.find(item => item.id === id);
      if (!node) return;
      state.selected = node;
      clearSelectedEdges();
      const label = node.labels[0];
      const key = node.key_value;
      const response = await fetch(`/api/node-summary?label=${encodeURIComponent(label)}&key_value=${encodeURIComponent(key)}`);
      renderNodeDetails(await response.json(), node);
    }

    function selectEdge(index) {
      const edge = state.graph.edges[index];
      if (!edge) return;
      state.selected = edge;
      markSelectedEdge(index);
      renderEdgeDetails(edge);
    }

    function clearSelectedEdges() {
      document.querySelectorAll(".edge.selected,.edge-label.selected").forEach(el => el.classList.remove("selected"));
    }

    function markSelectedEdge(index) {
      clearSelectedEdges();
      document.querySelectorAll(`[data-edge-index="${index}"]`).forEach(el => el.classList.add("selected"));
    }

    function renderGraphDetails() {
      document.getElementById("detail-title").textContent = "Graph";
      document.getElementById("detail-labels").innerHTML = `<span class="pill">${state.graph.mode || "graph"}</span>`;
      const evidence = (state.inspection?.evidence_tiers || []).map(item => `<span>tier ${item.tier}</span><strong>${item.count}</strong>`).join("") || "<span>Evidence</span><strong>none</strong>";
      const papers = (state.inspection?.recent_papers || []).map(paper => {
        const title = paper.title || "Untitled";
        return `<li><strong>PMID ${escapeHtml(paper.pmid)} · ${escapeHtml(paper.publication_date || "n.d.")}</strong>${escapeHtml(title)}</li>`;
      }).join("") || "<li>none</li>";
      document.getElementById("detail-body").innerHTML = `
        <div class="kv"><span>Nodes</span><strong>${state.graph.nodes.length}</strong><span>Edges</span><strong>${state.graph.edges.length}</strong></div>
        <div class="mini-section"><h3>Evidence Tiers</h3><div class="kv">${evidence}</div></div>
        <div class="mini-section"><h3>Recent Papers</h3><ul class="paper-list">${papers}</ul></div>`;
    }

    function renderNodeDetails(summary, fallbackNode) {
      const title = fallbackNode.label;
      document.getElementById("detail-title").textContent = title;
      document.getElementById("detail-labels").innerHTML = (summary.labels || fallbackNode.labels).map(label => `<span class="pill">${escapeHtml(label)}</span>`).join("");
      const props = summary.node || fallbackNode.properties || {};
      const kv = Object.entries(props).slice(0, 10).map(([key, value]) => `<span>${key}</span><strong>${escapeHtml(JSON.stringify(value))}</strong>`).join("");
      const relations = (summary.relations || []).map(item => {
        const neighbor = item.neighbor || {};
        const overlay = item.evidence_overlay || {};
        const overlayText = overlay.overlaid_tier !== undefined ? ` · Overlay ${escapeHtml(overlay.original_tier)}->${escapeHtml(overlay.overlaid_tier)}` : "";
        const neighborName = neighbor.display_name || neighbor.name || neighbor.symbol || neighbor.pmid || neighbor.nct_id || "neighbor";
        const refs = (item.source_pmids && item.source_pmids.length ? item.source_pmids : item.source_ids || []).join(", ") || "none";
        return `<div class="relation"><strong>${item.relation} · ${escapeHtml(neighborName)}</strong><span>tier ${item.evidence_tier}${overlayText} · Source ${escapeHtml(refs)}</span></div>`;
      }).join("");
      document.getElementById("detail-body").innerHTML = `<div class="kv">${kv}</div>${relations}`;
    }

    function renderEdgeDetails(edge) {
      const source = state.graph.nodes.find(node => node.id === edge.source) || {};
      const target = state.graph.nodes.find(node => node.id === edge.target) || {};
      const props = edge.properties || {};
      const overlay = edge.evidence_overlay || {};
      const refs = (edge.source_pmids && edge.source_pmids.length ? edge.source_pmids : edge.source_ids || []).join(", ") || "none";
      const labels = [
        `<span class="pill">${escapeHtml(edge.type)}</span>`,
        `<span class="pill">tier ${escapeHtml(edge.evidence_tier)}</span>`,
        overlay.overlaid_tier !== undefined ? `<span class="pill">overlay ${escapeHtml(overlay.original_tier)}->${escapeHtml(overlay.overlaid_tier)}</span>` : ""
      ].join("");
      const kvItems = [
        ["Source", source.label || edge.source],
        ["Target", target.label || edge.target],
        ["Evidence", `tier ${edge.evidence_tier}`],
        ["Overlay", overlay.overlaid_tier !== undefined ? `tier ${overlay.original_tier} to ${overlay.overlaid_tier}` : "none"],
        ["Tier Changed", overlay.tier_changed === true ? "yes" : "no"],
        ["Overlay Review", overlay.review_status || "n/a"],
        ["Overlay Checkpoint", overlay.checkpoint || "n/a"],
        ["Confidence", edge.confidence ?? "n/a"],
        ["Sources", refs],
        ["Trigger", props.trigger || "n/a"],
        ["Method", props.extraction_method || props.source || "n/a"]
      ];
      const kv = kvItems.map(([key, value]) => `<span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong>`).join("");
      const sentence = props.sentence
        ? `<div class="mini-section"><h3>Source Sentence</h3><p>${escapeHtml(props.sentence)}</p></div>`
        : "";
      const curationLinks = (edge.curation_links || []).length
        ? `<div class="mini-section"><h3>Curation Links</h3><ul class="paper-list">${(edge.curation_links || []).map(link => {
            if (link.kind === "external") {
              return `<li><a href="${escapeHtml(link.value)}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a></li>`;
            }
            return `<li><strong>${escapeHtml(link.label)}</strong>${escapeHtml(link.value)}</li>`;
          }).join("")}</ul></div>`
        : "";
      const allProperties = Object.keys(props).length
        ? `<div class="mini-section"><h3>Properties</h3><pre class="query">${escapeHtml(JSON.stringify(props, null, 2))}</pre></div>`
        : "";
      document.getElementById("detail-title").textContent = "Edge Provenance";
      document.getElementById("detail-labels").innerHTML = labels;
      document.getElementById("detail-body").innerHTML = `<div class="kv">${kv}</div>${sentence}${curationLinks}${allProperties}`;
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
    }

    document.getElementById("apply").addEventListener("click", loadGraph);
    document.getElementById("reset").addEventListener("click", () => {
      document.getElementById("search").value = "";
      Array.from(labelSelect.options).forEach(option => option.selected = false);
      Array.from(relationSelect.options).forEach(option => option.selected = false);
      document.getElementById("evidence").value = "0";
      document.getElementById("depth").value = "1";
      document.getElementById("citations").value = "1";
      document.getElementById("overlay-only").checked = false;
      document.getElementById("tier-changed-only").checked = false;
      loadGraph();
    });
    window.addEventListener("resize", renderGraph);
    loadMetadata().then(loadInspection).then(loadGraph);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
