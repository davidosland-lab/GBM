"""Baseline rule-based biomedical relation extraction."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
import re
from typing import Any, Iterable

from pydantic import ValidationError

from gbmbert.annotation.schema import EntityType
from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.extraction.entities import ExtractedEntity
from gbmbert.extraction.relation_rules import RELATION_RULES, RelationRule
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
    is_allowed_edge,
)

ENTITY_TO_NODE_LABEL: dict[EntityType, NodeLabel] = {
    EntityType.GENE: NodeLabel.GENE,
    EntityType.DRUG: NodeLabel.DRUG,
    EntityType.DISEASE: NodeLabel.DISEASE,
    EntityType.PATHWAY: NodeLabel.PATHWAY,
    EntityType.BIOMARKER: NodeLabel.BIOMARKER,
    EntityType.CELL_TYPE: NodeLabel.CELL_TYPE,
    EntityType.CELL_STATE: NodeLabel.CELL_STATE,
    EntityType.TREATMENT: NodeLabel.TREATMENT,
    EntityType.DELIVERY_MODIFIER: NodeLabel.DELIVERY_MODIFIER,
    EntityType.OUTCOME: NodeLabel.OUTCOME,
}

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")


@dataclass(frozen=True)
class SentenceSpan:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class RelationAuditFinding:
    source_pmid: str
    relation_index: int
    relation: str
    head: str
    tail: str
    evidence_tier: int
    confidence: float
    trigger: str
    sentence: str
    extraction_method: str
    qualifier_count: int
    flags: list[str]


@dataclass(frozen=True)
class RelationExtractionAuditReport:
    graph_path: str
    relation_count: int
    flagged_relation_count: int
    missing_trigger_count: int
    missing_sentence_count: int
    missing_method_count: int
    missing_qualifier_count: int
    low_confidence_count: int
    relation_type_counts: list[dict[str, int | str]]
    findings: list[RelationAuditFinding]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_path": self.graph_path,
            "relation_count": self.relation_count,
            "flagged_relation_count": self.flagged_relation_count,
            "missing_trigger_count": self.missing_trigger_count,
            "missing_sentence_count": self.missing_sentence_count,
            "missing_method_count": self.missing_method_count,
            "missing_qualifier_count": self.missing_qualifier_count,
            "low_confidence_count": self.low_confidence_count,
            "relation_type_counts": self.relation_type_counts,
            "findings": [finding.__dict__ for finding in self.findings],
            "warnings": self.warnings,
        }


def extract_relations(
    text: str,
    entities: Iterable[ExtractedEntity],
    source_pmid: str,
    evidence_tier: EvidenceTier = EvidenceTier.HYPOTHESIS,
) -> list[GraphRelation]:
    """Extract schema-valid candidate relations from sentence-local entities."""

    entity_list = sorted(entities, key=lambda entity: (entity.start, entity.end))
    relations: dict[tuple[str, str, str], GraphRelation] = {}
    for sentence in split_sentences(text):
        sentence_entities = [
            entity
            for entity in entity_list
            if entity.start < sentence.end and entity.end > sentence.start
        ]
        if len(sentence_entities) < 2:
            continue
        for rule in RELATION_RULES:
            trigger = rule.match(sentence.text)
            if not trigger:
                continue
            for head_entity, tail_entity in oriented_entity_pairs(sentence_entities, rule):
                relation = build_relation(
                    head_entity=head_entity,
                    tail_entity=tail_entity,
                    rule=rule,
                    trigger=trigger,
                    sentence=sentence,
                    source_pmid=source_pmid,
                    evidence_tier=evidence_tier,
                )
                if relation is None:
                    continue
                key = (
                    relation.head.label.value,
                    str(relation.head.key_value).casefold(),
                    relation.relation.value,
                    relation.tail.label.value,
                    str(relation.tail.key_value).casefold(),
                )
                relations[key] = relation
    return list(relations.values())


def audit_relation_extraction_graph(
    graph_jsonl: str | Path,
    *,
    low_confidence_threshold: float = 0.55,
    include_clean: bool = False,
) -> RelationExtractionAuditReport:
    """Audit rule-based relation provenance in graph-record JSONL."""

    records = _load_audit_graph_records(graph_jsonl)
    relation_type_counts: Counter[str] = Counter()
    findings: list[RelationAuditFinding] = []
    missing_trigger_count = 0
    missing_sentence_count = 0
    missing_method_count = 0
    missing_qualifier_count = 0
    low_confidence_count = 0
    relation_count = 0

    for record in records:
        for relation_index, relation in enumerate(record.relations, start=1):
            relation_count += 1
            relation_type_counts[relation.relation.value] += 1
            properties = relation.properties
            trigger = str(properties.get("trigger") or "")
            sentence = str(properties.get("sentence") or "")
            method = str(properties.get("extraction_method") or properties.get("source") or "")
            qualifier_count = _relation_qualifier_count(relation.qualifiers)
            flags: list[str] = []
            if not trigger:
                missing_trigger_count += 1
                flags.append("missing trigger")
            if not sentence:
                missing_sentence_count += 1
                flags.append("missing source sentence")
            if not method:
                missing_method_count += 1
                flags.append("missing extraction method")
            if qualifier_count == 0:
                missing_qualifier_count += 1
                flags.append("no inferred qualifiers")
            if relation.confidence < low_confidence_threshold:
                low_confidence_count += 1
                flags.append(f"confidence < {low_confidence_threshold}")
            if relation.source_pmid != record.pmid:
                flags.append("relation source PMID does not match graph record")
            if flags or include_clean:
                findings.append(
                    RelationAuditFinding(
                        source_pmid=relation.source_pmid,
                        relation_index=relation_index,
                        relation=relation.relation.value,
                        head=f"{relation.head.label.value}:{relation.head.key_value}",
                        tail=f"{relation.tail.label.value}:{relation.tail.key_value}",
                        evidence_tier=int(relation.evidence_tier),
                        confidence=relation.confidence,
                        trigger=trigger,
                        sentence=sentence,
                        extraction_method=method,
                        qualifier_count=qualifier_count,
                        flags=flags,
                    )
                )
    warnings: list[str] = []
    if not records:
        warnings.append("No graph records found")
    if relation_count == 0:
        warnings.append("No relations found for audit")
    if missing_trigger_count:
        warnings.append(f"{missing_trigger_count} relation(s) missing trigger provenance")
    if missing_sentence_count:
        warnings.append(f"{missing_sentence_count} relation(s) missing source sentence")
    if missing_method_count:
        warnings.append(f"{missing_method_count} relation(s) missing extraction method")
    return RelationExtractionAuditReport(
        graph_path=str(graph_jsonl),
        relation_count=relation_count,
        flagged_relation_count=sum(1 for finding in findings if finding.flags),
        missing_trigger_count=missing_trigger_count,
        missing_sentence_count=missing_sentence_count,
        missing_method_count=missing_method_count,
        missing_qualifier_count=missing_qualifier_count,
        low_confidence_count=low_confidence_count,
        relation_type_counts=[{"key": key, "count": count} for key, count in sorted(relation_type_counts.items())],
        findings=findings,
        warnings=warnings,
    )


def save_relation_extraction_audit_json(report: RelationExtractionAuditReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_relation_extraction_audit_markdown(report: RelationExtractionAuditReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_relation_extraction_audit_markdown(report), encoding="utf-8")
    return output_path


def format_relation_extraction_audit_markdown(report: RelationExtractionAuditReport) -> str:
    finding_lines = (
        [
            (
                f"- PMID {finding.source_pmid} relation {finding.relation_index} `{finding.relation}` "
                f"{finding.head} -> {finding.tail}: {', '.join(finding.flags) if finding.flags else 'clean'}"
            )
            for finding in report.findings[:50]
        ]
        if report.findings
        else ["- none"]
    )
    lines = [
        "# GBM-AI Relation Extraction Audit",
        "",
        RESEARCH_WARNING,
        "",
        f"- Graph: `{report.graph_path}`",
        f"- Relations: {report.relation_count}",
        f"- Flagged relations: {report.flagged_relation_count}",
        f"- Missing triggers: {report.missing_trigger_count}",
        f"- Missing sentences: {report.missing_sentence_count}",
        f"- Missing extraction methods: {report.missing_method_count}",
        f"- Missing qualifiers: {report.missing_qualifier_count}",
        f"- Low confidence: {report.low_confidence_count}",
        "",
        "## Relation Types",
        *([f"- {item['key']}: {item['count']}" for item in report.relation_type_counts] if report.relation_type_counts else ["- none"]),
        "",
        "## Findings",
        *finding_lines,
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def split_sentences(text: str) -> list[SentenceSpan]:
    """Split text into simple sentence spans while preserving character offsets."""

    spans = []
    for match in _SENTENCE_RE.finditer(text):
        raw = match.group(0)
        stripped = raw.strip()
        if not stripped:
            continue
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw.rstrip())
        start = match.start() + leading
        end = match.start() + trailing
        spans.append(SentenceSpan(text=text[start:end], start=start, end=end))
    return spans


def oriented_entity_pairs(
    entities: Iterable[ExtractedEntity],
    rule: RelationRule,
) -> list[tuple[ExtractedEntity, ExtractedEntity]]:
    """Return entity pairs oriented according to a rule's allowed label pairs."""

    pairs = []
    for left, right in combinations(entities, 2):
        left_label = ENTITY_TO_NODE_LABEL.get(left.label)
        right_label = ENTITY_TO_NODE_LABEL.get(right.label)
        if left_label is None or right_label is None:
            continue
        if (left_label, right_label) in rule.label_pairs:
            pairs.append((left, right))
        if (right_label, left_label) in rule.label_pairs and not (
            left_label == right_label and left.start <= right.start
        ):
            pairs.append((right, left))
    return pairs


def build_relation(
    head_entity: ExtractedEntity,
    tail_entity: ExtractedEntity,
    rule: RelationRule,
    trigger: str,
    sentence: SentenceSpan,
    source_pmid: str,
    evidence_tier: EvidenceTier,
) -> GraphRelation | None:
    """Build a GraphRelation, returning None if schema validation rejects it."""

    head = entity_to_graph_node(head_entity)
    tail = entity_to_graph_node(tail_entity)
    if head is None or tail is None:
        return None
    if not is_allowed_edge(rule.relation, head.label, tail.label):
        return None
    confidence = min(head_entity.confidence, tail_entity.confidence, rule.confidence)
    try:
        return GraphRelation(
            head=head,
            relation=rule.relation,
            tail=tail,
            source_pmid=source_pmid,
            evidence_tier=evidence_tier,
            confidence=confidence,
            qualifiers=infer_relation_qualifiers(rule.relation, sentence.text),
            properties={
                "trigger": trigger,
                "sentence": sentence.text,
                "sentence_start": sentence.start,
                "sentence_end": sentence.end,
                "extraction_method": "rule_based_v1",
            },
        )
    except ValidationError:
        return None


def infer_relation_qualifiers(relation: RelationType, sentence: str) -> RelationQualifiers:
    """Infer narrow relation context from explicit sentence text."""

    text = sentence.casefold()
    qualifier = RelationQualifiers(
        species_model=infer_species_model(text),
        trial_phase=infer_trial_phase(text),
        evidence_context=infer_evidence_context(text),
    )
    if relation == RelationType.PREDICTS:
        qualifier.mutation_status = infer_mutation_status(text)
    return qualifier


def infer_mutation_status(text: str) -> MutationStatus | None:
    if "idh-wildtype" in text or "idh wildtype" in text or "idh-wt" in text:
        return MutationStatus.IDH_WILDTYPE
    if "idh-mutant" in text or "idh mutant" in text or "idh-mutated" in text:
        return MutationStatus.IDH_MUTANT
    if "mgmt methylated" in text or "mgmt-methylated" in text:
        return MutationStatus.MGMT_METHYLATED
    if "mgmt unmethylated" in text or "mgmt-unmethylated" in text:
        return MutationStatus.MGMT_UNMETHYLATED
    if "egfr amplified" in text or "egfr amplification" in text:
        return MutationStatus.EGFR_AMPLIFIED
    return None


def infer_species_model(text: str) -> SpeciesModel | None:
    if "in vitro" in text or "cell line" in text or "cell-line" in text:
        return SpeciesModel.CELL_LINE
    if "organoid" in text:
        return SpeciesModel.ORGANOID
    if "xenograft" in text or "pdX".casefold() in text:
        return SpeciesModel.XENOGRAFT
    if "mouse" in text or "murine" in text:
        return SpeciesModel.MOUSE
    if "rat " in text or " rat" in text:
        return SpeciesModel.RAT
    if "patient" in text or "human" in text or "clinical" in text:
        return SpeciesModel.HUMAN
    return None


def infer_trial_phase(text: str) -> str | None:
    if "phase iii" in text or "phase 3" in text:
        return "phase_iii"
    if "phase ii" in text or "phase 2" in text:
        return "phase_ii"
    if "phase i/ii" in text or "phase 1/2" in text:
        return "phase_i_ii"
    if "phase i" in text or "phase 1" in text:
        return "phase_i"
    return None


def infer_evidence_context(text: str) -> str | None:
    if "randomized" in text or "randomised" in text:
        return "randomized"
    if "retrospective" in text:
        return "retrospective"
    if "prospective" in text:
        return "prospective"
    if "case report" in text:
        return "case_report"
    if "preclinical" in text:
        return "preclinical"
    return None


def entity_to_graph_node(entity: ExtractedEntity) -> GraphNode | None:
    """Convert an extracted entity into a graph node for relation endpoints."""

    label = ENTITY_TO_NODE_LABEL.get(entity.label)
    if label is None:
        return None
    key_value = (entity.normalized_text or entity.text).strip()
    if not key_value:
        return None
    return GraphNode(
        label=label,
        key_value=key_value,
        properties={
            "display_name": key_value,
            "aliases": sorted({entity.text}),
        },
    )


def build_audit_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit rule-based relation extraction provenance in graph JSONL.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.55)
    parser.add_argument("--include-clean", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def audit_main(argv: list[str] | None = None) -> int:
    args = build_audit_arg_parser().parse_args(argv)
    report = audit_relation_extraction_graph(
        args.graph_jsonl,
        low_confidence_threshold=args.low_confidence_threshold,
        include_clean=args.include_clean,
    )
    if args.json_output:
        save_relation_extraction_audit_json(report, args.json_output)
    if args.markdown_output:
        save_relation_extraction_audit_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_relation_extraction_audit_markdown(report))
    return 0


def _relation_qualifier_count(qualifiers: RelationQualifiers) -> int:
    payload = qualifiers.model_dump()
    return sum(1 for value in payload.values() if value not in (None, "", [], {}))


def _load_audit_graph_records(path: str | Path) -> list[KnowledgeGraphRecord]:
    input_path = Path(path)
    records: list[KnowledgeGraphRecord] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(KnowledgeGraphRecord.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return records
