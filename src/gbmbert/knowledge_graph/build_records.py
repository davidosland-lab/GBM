"""Build knowledge-graph JSONL records from PubMed and entity extraction JSONL."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path

from gbmbert.annotation.schema import EntityType, EvidenceClaim, Paper
from gbmbert.extraction.entities import EntityExtractionResult, ExtractedEntity
from gbmbert.extraction.evidence import load_evidence_claims_jsonl
from gbmbert.extraction.io import load_entity_jsonl, load_pubmed_jsonl
from gbmbert.extraction.pipeline import paper_to_source_text
from gbmbert.extraction.relations import extract_relations
from gbmbert.knowledge_graph.schema import EvidenceTier, GraphNode, KnowledgeGraphRecord, NodeLabel

LOGGER = logging.getLogger(__name__)

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


def build_graph_records(
    papers: Iterable[Paper],
    entity_results: Iterable[EntityExtractionResult],
    evidence_claims: Iterable[EvidenceClaim] | None = None,
) -> Iterator[KnowledgeGraphRecord]:
    """Yield graph records that preserve paper provenance, mentions, and relations."""

    paper_by_pmid = {paper.pmid: paper for paper in papers}
    evidence_by_pmid = {claim.source_pmid: claim for claim in evidence_claims or []}
    seen_pmids: set[str] = set()
    for result in entity_results:
        seen_pmids.add(result.pmid)
        paper = paper_by_pmid.get(result.pmid)
        if paper is None:
            LOGGER.warning("Entity result for PMID %s has no matching paper record", result.pmid)
            continue
        evidence_claim = evidence_by_pmid.get(paper.pmid)
        evidence_tier = evidence_tier_for_claim(evidence_claim)
        relations = extract_relations(
            text=paper_to_source_text(paper),
            entities=result.entities,
            source_pmid=paper.pmid,
            evidence_tier=evidence_tier,
        )
        if evidence_claim is not None:
            for relation in relations:
                relation.properties.update(evidence_claim_properties(evidence_claim))
        yield KnowledgeGraphRecord(
            pmid=paper.pmid,
            paper_properties=paper_properties(paper),
            nodes=entities_to_nodes(result.entities),
            relations=relations,
        )

    for pmid, paper in paper_by_pmid.items():
        if pmid not in seen_pmids:
            LOGGER.info("No entity extraction result for PMID %s; emitting paper-only graph record", pmid)
            yield KnowledgeGraphRecord(
                pmid=paper.pmid,
                paper_properties=paper_properties(paper),
                nodes=[],
                relations=[],
            )


def entities_to_nodes(entities: Iterable[ExtractedEntity]) -> list[GraphNode]:
    """Convert extracted entities into de-duplicated graph nodes."""

    nodes: dict[tuple[NodeLabel, str], GraphNode] = {}
    for entity in entities:
        label = ENTITY_TO_NODE_LABEL.get(entity.label)
        if label is None:
            continue
        key_value = (entity.normalized_text or entity.text).strip()
        if not key_value:
            continue
        key = (label, key_value.casefold())
        existing = nodes.get(key)
        mention = entity_mention_properties(entity)
        if existing is None:
            nodes[key] = GraphNode(
                label=label,
                key_value=key_value,
                properties={
                    "display_name": key_value,
                    "aliases": sorted({entity.text}),
                    "mentions": [mention],
                },
            )
        else:
            aliases = set(existing.properties.get("aliases", []))
            aliases.add(entity.text)
            mentions = list(existing.properties.get("mentions", []))
            mentions.append(mention)
            existing.properties["aliases"] = sorted(aliases)
            existing.properties["mentions"] = mentions
    return list(nodes.values())


def paper_properties(paper: Paper) -> dict[str, object]:
    """Return graph properties for a Paper node."""

    return {
        "title": paper.title,
        "abstract": paper.abstract,
        "journal": paper.journal,
        "publication_date": paper.publication_date,
        "mesh_terms": paper.mesh_terms,
    }


def entity_mention_properties(entity: ExtractedEntity) -> dict[str, object]:
    """Return lossless mention metadata for an entity occurrence."""

    return {
        "text": entity.text,
        "label": entity.label.value,
        "start": entity.start,
        "end": entity.end,
        "confidence": entity.confidence,
        "normalized_text": entity.normalized_text,
    }


def evidence_tier_for_claim(claim: EvidenceClaim | None) -> EvidenceTier:
    """Convert annotation evidence levels into graph evidence tiers."""

    if claim is None:
        return EvidenceTier.HYPOTHESIS
    return EvidenceTier(int(claim.evidence_level.value))


def evidence_claim_properties(claim: EvidenceClaim) -> dict[str, object]:
    """Return transparent evidence-classification provenance for relations."""

    properties = {
        "evidence_classification_method": claim.classification_method,
        "evidence_confidence": claim.confidence,
        "evidence_cues": claim.evidence_cues,
    }
    return {key: value for key, value in properties.items() if value is not None}


def save_graph_records_jsonl(
    records: Iterable[KnowledgeGraphRecord],
    path: str | Path,
) -> Path:
    """Write knowledge graph records as newline-delimited JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json())
            handle.write("\n")
    return output_path


def build_graph_records_from_jsonl(
    pubmed_jsonl: str | Path,
    entity_jsonl: str | Path,
    output_jsonl: str | Path,
    evidence_jsonl: str | Path | None = None,
) -> Path:
    """Load PubMed/entity JSONL inputs and write graph-ready JSONL output."""

    papers = list(load_pubmed_jsonl(pubmed_jsonl))
    entity_results = list(load_entity_jsonl(entity_jsonl))
    evidence_claims = load_evidence_claims_jsonl(evidence_jsonl) if evidence_jsonl else []
    LOGGER.info(
        "Loaded %d papers, %d entity result records, and %d evidence claims",
        len(papers),
        len(entity_results),
        len(evidence_claims),
    )
    records = build_graph_records(
        papers,
        entity_results,
        evidence_claims,
    )
    return save_graph_records_jsonl(records, output_jsonl)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build KnowledgeGraphRecord JSONL from PubMed and entity JSONL."
    )
    parser.add_argument("pubmed_jsonl", type=Path, help="Input PubMed paper JSONL path.")
    parser.add_argument("entity_jsonl", type=Path, help="Input entity extraction JSONL path.")
    parser.add_argument("output_jsonl", type=Path, help="Output graph-record JSONL path.")
    parser.add_argument("--evidence-jsonl", type=Path, help="Optional evidence classification JSONL path.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    output_path = build_graph_records_from_jsonl(
        pubmed_jsonl=args.pubmed_jsonl,
        entity_jsonl=args.entity_jsonl,
        output_jsonl=args.output_jsonl,
        evidence_jsonl=args.evidence_jsonl,
    )
    LOGGER.info("Saved graph records to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
