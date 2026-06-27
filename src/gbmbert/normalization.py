"""Lightweight entity normalization scaffold for GBM-AI graph records."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.knowledge_graph.schema import GraphNode, GraphRelation, KnowledgeGraphRecord, NodeLabel


@dataclass(frozen=True)
class NormalizationMatch:
    source_pmid: str
    label: str
    original_value: str
    canonical_id: str
    canonical_name: str


@dataclass(frozen=True)
class NormalizationReport:
    input_graph_path: str
    output_graph_path: str
    synonym_table_path: str
    record_count: int
    node_count: int
    normalized_node_count: int
    matches: list[NormalizationMatch]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_graph_records(
    graph_jsonl: str | Path,
    output_jsonl: str | Path,
    *,
    synonym_table: str | Path = Path("data/examples/entity_synonyms.json"),
) -> NormalizationReport:
    """Add canonical normalization properties to graph nodes when synonym matches exist."""

    records = _load_graph_records(graph_jsonl)
    normalizer = EntityNormalizer.from_json(synonym_table)
    output_records: list[KnowledgeGraphRecord] = []
    matches: list[NormalizationMatch] = []
    node_count = 0
    for record in records:
        new_nodes: list[GraphNode] = []
        for node in record.nodes:
            node_count += 1
            match = normalizer.match(node.label, str(node.key_value))
            if match is None:
                new_nodes.append(node)
                continue
            properties = {
                **node.properties,
                "canonical_id": match["canonical_id"],
                "canonical_name": match["canonical_name"],
                "normalization_source": str(synonym_table),
                "original_key_value": str(node.key_value),
            }
            new_nodes.append(node.model_copy(update={"properties": properties}))
            matches.append(
                NormalizationMatch(
                    source_pmid=record.pmid,
                    label=node.label.value,
                    original_value=str(node.key_value),
                    canonical_id=match["canonical_id"],
                    canonical_name=match["canonical_name"],
                )
            )
        new_relations = [
            _normalize_relation_endpoints(relation, normalizer, synonym_table)
            for relation in record.relations
        ]
        output_records.append(record.model_copy(update={"nodes": new_nodes, "relations": new_relations}))
    _write_graph_records(output_records, output_jsonl)
    return NormalizationReport(
        input_graph_path=str(graph_jsonl),
        output_graph_path=str(output_jsonl),
        synonym_table_path=str(synonym_table),
        record_count=len(records),
        node_count=node_count,
        normalized_node_count=len(matches),
        matches=matches,
        warnings=[],
    )


class EntityNormalizer:
    def __init__(self, entries: list[dict[str, Any]]) -> None:
        self._index: dict[tuple[str, str], dict[str, str]] = {}
        for entry in entries:
            canonical_id = str(entry.get("canonical_id") or "")
            canonical_name = str(entry.get("canonical_name") or "")
            labels = [str(label) for label in entry.get("labels", [])]
            synonyms = [canonical_name, *[str(value) for value in entry.get("synonyms", [])]]
            for label in labels:
                for synonym in synonyms:
                    key = (_normalize_label(label), _normalize_text(synonym))
                    if key[1]:
                        self._index[key] = {"canonical_id": canonical_id, "canonical_name": canonical_name}

    @classmethod
    def from_json(cls, path: str | Path) -> "EntityNormalizer":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(list(payload.get("entities", [])))

    def match(self, label: NodeLabel, text: str) -> dict[str, str] | None:
        return self._index.get((_normalize_label(label.value), _normalize_text(text)))


def _normalize_relation_endpoints(
    relation: GraphRelation,
    normalizer: EntityNormalizer,
    synonym_table: str | Path,
) -> GraphRelation:
    head = _normalized_node_copy(relation.head, normalizer, synonym_table)
    tail = _normalized_node_copy(relation.tail, normalizer, synonym_table)
    return relation.model_copy(update={"head": head, "tail": tail})


def _normalized_node_copy(
    node: GraphNode,
    normalizer: EntityNormalizer,
    synonym_table: str | Path,
) -> GraphNode:
    match = normalizer.match(node.label, str(node.key_value))
    if match is None:
        return node
    properties = {
        **node.properties,
        "canonical_id": match["canonical_id"],
        "canonical_name": match["canonical_name"],
        "normalization_source": str(synonym_table),
        "original_key_value": str(node.key_value),
    }
    return node.model_copy(update={"properties": properties})


def save_normalization_json(report: NormalizationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_normalization_markdown(report: NormalizationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_normalization_markdown(report), encoding="utf-8")
    return output


def format_normalization_markdown(report: NormalizationReport) -> str:
    match_lines = [
        f"- PMID {match.source_pmid} {match.label} `{match.original_value}` -> `{match.canonical_id}`"
        for match in report.matches[:100]
    ] or ["- none"]
    return "\n".join(
        [
            "# GBM-AI Entity Normalization Report",
            "",
            RESEARCH_WARNING,
            "",
            f"- Input graph: `{report.input_graph_path}`",
            f"- Output graph: `{report.output_graph_path}`",
            f"- Synonym table: `{report.synonym_table_path}`",
            f"- Records: {report.record_count}",
            f"- Nodes: {report.node_count}",
            f"- Normalized nodes: {report.normalized_node_count}",
            "",
            "## Matches",
            *match_lines,
            "",
            "## Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
        ]
    ).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize GBM-AI graph node properties using a synonym table.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--synonym-table", type=Path, default=Path("data/examples/entity_synonyms.json"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = normalize_graph_records(args.graph_jsonl, args.output_jsonl, synonym_table=args.synonym_table)
    if args.json_output:
        save_normalization_json(report, args.json_output)
    if args.markdown_output:
        save_normalization_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_normalization_markdown(report))
    return 0


def _load_graph_records(path: str | Path) -> list[KnowledgeGraphRecord]:
    records: list[KnowledgeGraphRecord] = []
    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(KnowledgeGraphRecord.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return records


def _write_graph_records(records: list[KnowledgeGraphRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json())
            handle.write("\n")


def _normalize_label(value: str) -> str:
    return value.casefold().replace("_", "")


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


if __name__ == "__main__":
    raise SystemExit(main())
