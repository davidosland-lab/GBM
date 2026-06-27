"""Relation qualifier enrichment for existing GBM-AI graph records."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.extraction.relations import infer_relation_qualifiers
from gbmbert.knowledge_graph.schema import GraphRelation, KnowledgeGraphRecord, RelationQualifiers


@dataclass(frozen=True)
class QualifierEnrichmentChange:
    source_pmid: str
    relation_index: int
    relation: str
    added_fields: list[str]


@dataclass(frozen=True)
class QualifierEnrichmentReport:
    input_graph_path: str
    output_graph_path: str
    record_count: int
    relation_count: int
    enriched_relation_count: int
    changes: list[QualifierEnrichmentChange]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def enrich_graph_relation_qualifiers(graph_jsonl: str | Path, output_jsonl: str | Path) -> QualifierEnrichmentReport:
    """Infer missing relation qualifier fields from stored relation sentence text."""

    records = _load_graph_records(graph_jsonl)
    output_records: list[KnowledgeGraphRecord] = []
    changes: list[QualifierEnrichmentChange] = []
    relation_count = 0
    for record in records:
        enriched_relations: list[GraphRelation] = []
        for relation_index, relation in enumerate(record.relations, start=1):
            relation_count += 1
            sentence = _relation_context_text(record, relation)
            inferred = infer_relation_qualifiers(relation.relation, sentence)
            merged, added_fields = _merge_qualifiers(relation.qualifiers, inferred)
            if added_fields:
                relation = relation.model_copy(update={"qualifiers": merged})
                changes.append(
                    QualifierEnrichmentChange(
                        source_pmid=record.pmid,
                        relation_index=relation_index,
                        relation=relation.relation.value,
                        added_fields=added_fields,
                    )
                )
            enriched_relations.append(relation)
        output_records.append(record.model_copy(update={"relations": enriched_relations}))
    _write_graph_records(output_records, output_jsonl)
    return QualifierEnrichmentReport(
        input_graph_path=str(graph_jsonl),
        output_graph_path=str(output_jsonl),
        record_count=len(records),
        relation_count=relation_count,
        enriched_relation_count=len(changes),
        changes=changes,
        warnings=[],
    )


def save_qualifier_enrichment_json(report: QualifierEnrichmentReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_qualifier_enrichment_markdown(report: QualifierEnrichmentReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_qualifier_enrichment_markdown(report), encoding="utf-8")
    return output


def format_qualifier_enrichment_markdown(report: QualifierEnrichmentReport) -> str:
    change_lines = [
        f"- PMID {change.source_pmid} relation {change.relation_index} `{change.relation}`: {', '.join(change.added_fields)}"
        for change in report.changes[:100]
    ] or ["- none"]
    return "\n".join(
        [
            "# GBM-AI Relation Qualifier Enrichment Report",
            "",
            RESEARCH_WARNING,
            "",
            f"- Input graph: `{report.input_graph_path}`",
            f"- Output graph: `{report.output_graph_path}`",
            f"- Records: {report.record_count}",
            f"- Relations: {report.relation_count}",
            f"- Enriched relations: {report.enriched_relation_count}",
            "",
            "## Changes",
            *change_lines,
            "",
            "## Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
        ]
    ).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Infer missing relation qualifiers in GBM-AI graph records.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = enrich_graph_relation_qualifiers(args.graph_jsonl, args.output_jsonl)
    if args.json_output:
        save_qualifier_enrichment_json(report, args.json_output)
    if args.markdown_output:
        save_qualifier_enrichment_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_qualifier_enrichment_markdown(report))
    return 0


def _merge_qualifiers(current: RelationQualifiers, inferred: RelationQualifiers) -> tuple[RelationQualifiers, list[str]]:
    payload = current.model_dump()
    added: list[str] = []
    for key, value in inferred.model_dump().items():
        if payload.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
            payload[key] = value
            added.append(key)
    return RelationQualifiers.model_validate(payload), added


def _relation_context_text(record: KnowledgeGraphRecord, relation: GraphRelation) -> str:
    parts = [
        str(relation.properties.get("sentence") or ""),
        str(record.paper_properties.get("title") or ""),
        str(record.paper_properties.get("abstract") or ""),
    ]
    return " ".join(part for part in parts if part)


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


if __name__ == "__main__":
    raise SystemExit(main())
