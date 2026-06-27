"""Pre-load quality reports for GBM-AI knowledge graph JSONL files."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from gbmbert.knowledge_graph.schema import KnowledgeGraphRecord
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord

LOGGER = logging.getLogger(__name__)

SAFETY_BOUNDARY = (
    "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, "
    "or clinical decision-making."
)


@dataclass(frozen=True)
class CountItem:
    key: str
    count: int


@dataclass(frozen=True)
class EntityCount:
    label: str
    key_value: str
    count: int


@dataclass(frozen=True)
class RelationPairCount:
    head: str
    relation: str
    tail: str
    count: int


@dataclass(frozen=True)
class GraphQualityReport:
    source_path: str
    record_count: int
    invalid_record_count: int
    unique_pmid_count: int
    unique_nct_count: int
    paper_only_record_count: int
    node_mention_count: int
    unique_node_count: int
    relation_count: int
    label_counts: list[CountItem]
    relation_type_counts: list[CountItem]
    evidence_tier_counts: list[CountItem]
    top_entities: list[EntityCount]
    top_relation_pairs: list[RelationPairCount]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_graph_records_jsonl(
    path: str | Path,
    *,
    top_n: int = 10,
    record_type: str = "pubmed",
) -> GraphQualityReport:
    """Validate graph-record JSONL and return pre-load quality statistics."""

    if record_type == "auto":
        record_type = detect_record_type(path)
    if record_type == "trial":
        return analyze_trial_graph_records_jsonl(path, top_n=top_n)
    if record_type != "pubmed":
        raise ValueError("record_type must be pubmed, trial, or auto")

    input_path = Path(path)
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    records: list[KnowledgeGraphRecord] = []
    invalid_record_count = 0
    warnings: list[str] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(KnowledgeGraphRecord.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                invalid_record_count += 1
                warnings.append(f"Line {line_number}: invalid JSON ({exc.msg})")
            except ValidationError as exc:
                invalid_record_count += 1
                warnings.append(f"Line {line_number}: schema validation failed ({exc.errors()[0]['msg']})")

    pmids: set[str] = set()
    unique_nodes: set[tuple[str, str]] = set()
    label_counts: Counter[str] = Counter()
    entity_counts: Counter[tuple[str, str]] = Counter()
    relation_type_counts: Counter[str] = Counter()
    evidence_tier_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str, str]] = Counter()
    paper_only_record_count = 0
    node_mention_count = 0
    relation_count = 0

    for record in records:
        pmids.add(record.pmid)
        if not record.paper_properties.get("title"):
            warnings.append(f"PMID {record.pmid}: missing paper title")
        if not record.paper_properties.get("abstract"):
            warnings.append(f"PMID {record.pmid}: missing paper abstract")
        if not record.nodes and not record.relations:
            paper_only_record_count += 1

        for node in record.nodes:
            label = node.label.value
            key_value = str(node.key_value)
            label_counts[label] += 1
            entity_counts[(label, key_value)] += 1
            unique_nodes.add((label, key_value.casefold()))
            if not node.properties.get("display_name"):
                warnings.append(f"PMID {record.pmid}: {label} node {key_value!r} has no display_name")

        for relation in record.relations:
            relation_count += 1
            relation_type = relation.relation.value
            relation_type_counts[relation_type] += 1
            evidence_tier_counts[str(int(relation.evidence_tier))] += 1
            head = _node_ref(relation.head)
            tail = _node_ref(relation.tail)
            pair_counts[(head, relation_type, tail)] += 1
            if relation.source_pmid != record.pmid:
                warnings.append(
                    f"PMID {record.pmid}: relation source PMID {relation.source_pmid} does not match record"
                )
            if not relation.properties.get("sentence"):
                warnings.append(f"PMID {record.pmid}: {relation_type} relation has no source sentence")
            if not relation.properties.get("extraction_method"):
                warnings.append(f"PMID {record.pmid}: {relation_type} relation has no extraction method")

        node_mention_count += len(record.nodes)

    if not records:
        warnings.append("No valid graph records found")
    if invalid_record_count:
        warnings.append(f"{invalid_record_count} invalid graph record(s) must be fixed before loading")

    return GraphQualityReport(
        source_path=str(input_path),
        record_count=len(records),
        invalid_record_count=invalid_record_count,
        unique_pmid_count=len(pmids),
        unique_nct_count=0,
        paper_only_record_count=paper_only_record_count,
        node_mention_count=node_mention_count,
        unique_node_count=len(unique_nodes),
        relation_count=relation_count,
        label_counts=_count_items(label_counts),
        relation_type_counts=_count_items(relation_type_counts),
        evidence_tier_counts=_count_items(evidence_tier_counts),
        top_entities=[
            EntityCount(label=label, key_value=key_value, count=count)
            for (label, key_value), count in entity_counts.most_common(top_n)
        ],
        top_relation_pairs=[
            RelationPairCount(head=head, relation=relation, tail=tail, count=count)
            for (head, relation, tail), count in pair_counts.most_common(top_n)
        ],
        warnings=warnings,
    )


def analyze_trial_graph_records_jsonl(
    path: str | Path,
    *,
    top_n: int = 10,
) -> GraphQualityReport:
    """Validate ClinicalTrials.gov graph-record JSONL and return quality statistics."""

    input_path = Path(path)
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    records: list[ClinicalTrialGraphRecord] = []
    invalid_record_count = 0
    warnings: list[str] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(ClinicalTrialGraphRecord.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                invalid_record_count += 1
                warnings.append(f"Line {line_number}: invalid JSON ({exc.msg})")
            except ValidationError as exc:
                invalid_record_count += 1
                warnings.append(f"Line {line_number}: schema validation failed ({exc.errors()[0]['msg']})")

    nct_ids: set[str] = set()
    unique_nodes: set[tuple[str, str]] = set()
    label_counts: Counter[str] = Counter()
    entity_counts: Counter[tuple[str, str]] = Counter()
    relation_type_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str, str]] = Counter()
    relation_count = 0
    node_mention_count = 0

    for record in records:
        nct_ids.add(record.nct_id)
        if not record.trial_properties.get("display_name"):
            warnings.append(f"{record.nct_id}: missing trial display_name")
        if not record.trial_properties.get("source_url"):
            warnings.append(f"{record.nct_id}: missing source_url")
        _count_node(
            label_counts=label_counts,
            entity_counts=entity_counts,
            unique_nodes=unique_nodes,
            label="Trial",
            key_value=record.nct_id,
        )
        for node in record.nodes:
            label = node.label.value
            key_value = str(node.key_value)
            _count_node(
                label_counts=label_counts,
                entity_counts=entity_counts,
                unique_nodes=unique_nodes,
                label=label,
                key_value=key_value,
            )
            if not node.properties.get("display_name"):
                warnings.append(f"{record.nct_id}: {label} node {key_value!r} has no display_name")

        for relation in record.relations:
            relation_count += 1
            relation_type = relation.relation.value
            relation_type_counts[relation_type] += 1
            head = _node_ref(relation.head)
            tail = _node_ref(relation.tail)
            pair_counts[(head, relation_type, tail)] += 1
            if relation.source_id != record.nct_id:
                warnings.append(
                    f"{record.nct_id}: relation source ID {relation.source_id} does not match record"
                )
            if not relation.properties.get("source_url"):
                warnings.append(f"{record.nct_id}: {relation_type} relation has no source_url")

        node_mention_count += 1 + len(record.nodes)

    if not records:
        warnings.append("No valid trial graph records found")
    if invalid_record_count:
        warnings.append(f"{invalid_record_count} invalid trial graph record(s) must be fixed before loading")

    return GraphQualityReport(
        source_path=str(input_path),
        record_count=len(records),
        invalid_record_count=invalid_record_count,
        unique_pmid_count=0,
        unique_nct_count=len(nct_ids),
        paper_only_record_count=0,
        node_mention_count=node_mention_count,
        unique_node_count=len(unique_nodes),
        relation_count=relation_count,
        label_counts=_count_items(label_counts),
        relation_type_counts=_count_items(relation_type_counts),
        evidence_tier_counts=[],
        top_entities=[
            EntityCount(label=label, key_value=key_value, count=count)
            for (label, key_value), count in entity_counts.most_common(top_n)
        ],
        top_relation_pairs=[
            RelationPairCount(head=head, relation=relation, tail=tail, count=count)
            for (head, relation, tail), count in pair_counts.most_common(top_n)
        ],
        warnings=warnings,
    )


def analyze_unified_graph_records(
    paths: list[str | Path],
    *,
    top_n: int = 10,
) -> GraphQualityReport:
    """Analyze PubMed and trial graph-record JSONL files into one combined report."""

    reports = [analyze_graph_records_jsonl(path, top_n=top_n, record_type="auto") for path in paths]
    return combine_quality_reports(reports, source_path=", ".join(str(Path(path)) for path in paths), top_n=top_n)


def combine_quality_reports(
    reports: list[GraphQualityReport],
    *,
    source_path: str = "combined",
    top_n: int = 10,
) -> GraphQualityReport:
    label_counts: Counter[str] = Counter()
    relation_type_counts: Counter[str] = Counter()
    evidence_tier_counts: Counter[str] = Counter()
    entity_counts: Counter[tuple[str, str]] = Counter()
    pair_counts: Counter[tuple[str, str, str]] = Counter()
    warnings: list[str] = []
    for report in reports:
        label_counts.update({item.key: item.count for item in report.label_counts})
        relation_type_counts.update({item.key: item.count for item in report.relation_type_counts})
        evidence_tier_counts.update({item.key: item.count for item in report.evidence_tier_counts})
        entity_counts.update({(item.label, item.key_value): item.count for item in report.top_entities})
        pair_counts.update({(item.head, item.relation, item.tail): item.count for item in report.top_relation_pairs})
        warnings.extend(f"{report.source_path}: {warning}" for warning in report.warnings)

    return GraphQualityReport(
        source_path=source_path,
        record_count=sum(report.record_count for report in reports),
        invalid_record_count=sum(report.invalid_record_count for report in reports),
        unique_pmid_count=sum(report.unique_pmid_count for report in reports),
        unique_nct_count=sum(report.unique_nct_count for report in reports),
        paper_only_record_count=sum(report.paper_only_record_count for report in reports),
        node_mention_count=sum(report.node_mention_count for report in reports),
        unique_node_count=sum(report.unique_node_count for report in reports),
        relation_count=sum(report.relation_count for report in reports),
        label_counts=_count_items(label_counts),
        relation_type_counts=_count_items(relation_type_counts),
        evidence_tier_counts=_count_items(evidence_tier_counts),
        top_entities=[
            EntityCount(label=label, key_value=key_value, count=count)
            for (label, key_value), count in entity_counts.most_common(top_n)
        ],
        top_relation_pairs=[
            RelationPairCount(head=head, relation=relation, tail=tail, count=count)
            for (head, relation, tail), count in pair_counts.most_common(top_n)
        ],
        warnings=warnings,
    )


def save_quality_report_json(report: GraphQualityReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    LOGGER.info("Saved graph quality JSON report to %s", output_path)
    return output_path


def save_quality_report_markdown(report: GraphQualityReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_quality_report_markdown(report), encoding="utf-8")
    LOGGER.info("Saved graph quality Markdown report to %s", output_path)
    return output_path


def format_quality_report_markdown(report: GraphQualityReport) -> str:
    """Format a graph quality report for human review."""

    lines = [
        "# GBM-AI Graph Quality Report",
        "",
        SAFETY_BOUNDARY,
        "",
        f"- Source: `{report.source_path}`",
        f"- Valid records: {report.record_count}",
        f"- Invalid records: {report.invalid_record_count}",
        f"- Unique PMIDs: {report.unique_pmid_count}",
        f"- Unique NCT IDs: {report.unique_nct_count}",
        f"- Paper-only records: {report.paper_only_record_count}",
        f"- Node mentions: {report.node_mention_count}",
        f"- Unique nodes: {report.unique_node_count}",
        f"- Relations: {report.relation_count}",
        "",
        "## Labels",
        *_format_count_items(report.label_counts),
        "",
        "## Relation Types",
        *_format_count_items(report.relation_type_counts),
        "",
        "## Evidence Tiers",
        *_format_count_items(report.evidence_tier_counts, prefix="tier "),
        "",
        "## Top Entities",
        *_format_entities(report.top_entities),
        "",
        "## Top Relation Pairs",
        *_format_pairs(report.top_relation_pairs),
        "",
        "## Warnings",
        *_format_strings(report.warnings),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a pre-load quality report for graph-record JSONL.")
    parser.add_argument("graph_jsonl", type=Path, help="Input graph-record JSONL path.")
    parser.add_argument("--trial-jsonl", type=Path, action="append", default=[], help="Optional trial graph-record JSONL path to include.")
    parser.add_argument(
        "--record-type",
        choices=["auto", "pubmed", "trial"],
        default="auto",
        help="Record type for the primary graph_jsonl input.",
    )
    parser.add_argument("--json-output", type=Path, help="Optional JSON report output path.")
    parser.add_argument("--markdown-output", type=Path, help="Optional Markdown report output path.")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of Markdown.")
    parser.add_argument("--fail-on-invalid", action="store_true", help="Exit non-zero when invalid records exist.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.trial_jsonl:
        report = analyze_unified_graph_records([args.graph_jsonl, *args.trial_jsonl], top_n=args.top_n)
    else:
        report = analyze_graph_records_jsonl(args.graph_jsonl, top_n=args.top_n, record_type=args.record_type)
    if args.json_output:
        save_quality_report_json(report, args.json_output)
    if args.markdown_output:
        save_quality_report_markdown(report, args.markdown_output)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_quality_report_markdown(report))

    if args.fail_on_invalid and report.invalid_record_count:
        return 1
    return 0


def _count_items(counter: Counter[str]) -> list[CountItem]:
    return [CountItem(key=key, count=count) for key, count in counter.most_common()]


def detect_record_type(path: str | Path) -> str:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                return "pubmed"
            if "nct_id" in payload:
                return "trial"
            return "pubmed"
    return "pubmed"


def _count_node(
    *,
    label_counts: Counter[str],
    entity_counts: Counter[tuple[str, str]],
    unique_nodes: set[tuple[str, str]],
    label: str,
    key_value: str,
) -> None:
    label_counts[label] += 1
    entity_counts[(label, key_value)] += 1
    unique_nodes.add((label, key_value.casefold()))


def _format_count_items(items: list[CountItem], prefix: str = "") -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {prefix}{item.key}: {item.count}" for item in items]


def _format_entities(items: list[EntityCount]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item.label} `{item.key_value}`: {item.count}" for item in items]


def _format_pairs(items: list[RelationPairCount]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- `{item.head}` -[{item.relation}]-> `{item.tail}`: {item.count}" for item in items]


def _format_strings(items: list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def _node_ref(node: Any) -> str:
    return f"{node.label.value}:{node.key_value}"


if __name__ == "__main__":
    raise SystemExit(main())
