import json
from pathlib import Path

from gbmbert.annotation.schema import EntityType, EvidenceClaim, EvidenceLevel, Paper
from gbmbert.extraction.entities import EntityExtractionResult, ExtractedEntity
from gbmbert.knowledge_graph.build_records import (
    build_graph_records,
    build_graph_records_from_jsonl,
    entities_to_nodes,
)
from gbmbert.knowledge_graph.schema import KnowledgeGraphRecord, NodeLabel


def entity(
    text: str,
    label: EntityType,
    normalized_text: str | None = None,
    start: int = 0,
) -> ExtractedEntity:
    normalized = normalized_text or text
    return ExtractedEntity(
        text=text,
        label=label,
        start=start,
        end=start + len(text),
        confidence=0.9,
        normalized_text=normalized,
    )


def test_entities_to_nodes_maps_supported_entity_labels() -> None:
    nodes = entities_to_nodes(
        [
            entity("EGFR", EntityType.GENE),
            entity("temozolomide", EntityType.DRUG),
            entity("MES-like", EntityType.CELL_STATE),
            entity("FUS", EntityType.DELIVERY_MODIFIER, "focused ultrasound"),
            entity("unknown phrase", EntityType.UNKNOWN),
        ]
    )

    assert [(node.label, node.key_value) for node in nodes] == [
        (NodeLabel.GENE, "EGFR"),
        (NodeLabel.DRUG, "temozolomide"),
        (NodeLabel.CELL_STATE, "MES-like"),
        (NodeLabel.DELIVERY_MODIFIER, "focused ultrasound"),
    ]


def test_entities_to_nodes_deduplicates_by_label_and_normalized_text() -> None:
    nodes = entities_to_nodes(
        [
            entity("TMZ", EntityType.DRUG, "temozolomide", start=0),
            entity("temozolomide", EntityType.DRUG, "temozolomide", start=10),
        ]
    )

    assert len(nodes) == 1
    assert nodes[0].label is NodeLabel.DRUG
    assert nodes[0].key_value == "temozolomide"
    assert nodes[0].properties["aliases"] == ["TMZ", "temozolomide"]
    assert len(nodes[0].properties["mentions"]) == 2


def test_build_graph_records_preserves_paper_properties_and_mentions() -> None:
    paper = Paper(
        pmid="12345678",
        title="MGMT methylation in glioblastoma",
        abstract="TMZ response.",
        journal="Neuro-Oncology",
        publication_date="2024",
        mesh_terms=["Glioblastoma"],
    )
    entity_result = EntityExtractionResult(
        pmid="12345678",
        entities=[
            entity("MGMT methylation", EntityType.BIOMARKER),
            entity("TMZ response", EntityType.OUTCOME, "temozolomide response"),
        ],
    )

    records = list(build_graph_records([paper], [entity_result]))

    assert len(records) == 1
    assert records[0].pmid == "12345678"
    assert records[0].paper_properties["title"] == "MGMT methylation in glioblastoma"
    assert records[0].paper_properties["mesh_terms"] == ["Glioblastoma"]
    assert [(node.label, node.key_value) for node in records[0].nodes] == [
        (NodeLabel.BIOMARKER, "MGMT methylation"),
        (NodeLabel.OUTCOME, "temozolomide response"),
    ]
    assert records[0].relations == []


def test_build_graph_records_applies_evidence_claims_to_relations() -> None:
    paper = Paper(
        pmid="12345678",
        title="MGMT methylation predicts temozolomide response",
        abstract="A retrospective patient cohort found MGMT methylation predicts temozolomide response.",
    )
    text = f"{paper.title}\n\n{paper.abstract}"
    entity_result = EntityExtractionResult(
        pmid="12345678",
        entities=[
            entity("MGMT methylation", EntityType.BIOMARKER, start=text.find("MGMT methylation")),
            entity(
                "temozolomide response",
                EntityType.OUTCOME,
                start=text.find("temozolomide response"),
            ),
        ],
    )
    evidence_claim = EvidenceClaim(
        claim=paper.title,
        source_pmid="12345678",
        evidence_level=EvidenceLevel.RETROSPECTIVE_HUMAN,
        confidence=0.68,
        classification_method="rule_based_placeholder_v1",
        evidence_cues=["patient", "retrospective"],
    )

    records = list(build_graph_records([paper], [entity_result], [evidence_claim]))

    assert len(records[0].relations) == 1
    relation = records[0].relations[0]
    assert int(relation.evidence_tier) == 3
    assert relation.properties["evidence_classification_method"] == "rule_based_placeholder_v1"
    assert relation.properties["evidence_confidence"] == 0.68
    assert relation.properties["evidence_cues"] == ["patient", "retrospective"]


def test_build_graph_records_emits_paper_only_record_when_entities_missing() -> None:
    paper = Paper(pmid="12345678", title="Paper without extracted entities")

    records = list(build_graph_records([paper], []))

    assert len(records) == 1
    assert records[0].pmid == "12345678"
    assert records[0].nodes == []
    assert records[0].relations == []


def test_build_graph_records_skips_entity_results_without_matching_paper() -> None:
    entity_result = EntityExtractionResult(
        pmid="99999999",
        entities=[entity("EGFR", EntityType.GENE)],
    )

    assert list(build_graph_records([], [entity_result])) == []


def test_build_graph_records_from_jsonl_roundtrip(tmp_path: Path) -> None:
    pubmed_path = tmp_path / "pubmed.jsonl"
    entity_path = tmp_path / "entities.jsonl"
    output_path = tmp_path / "graph_records.jsonl"
    pubmed_path.write_text(
        json.dumps(
            {
                "pmid": "12345678",
                "title": "FUS and TMZ in GBM",
                "abstract": "Research-use record.",
                "journal": "Journal",
                "publication_date": "2025",
                "mesh_terms": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    entity_result = EntityExtractionResult(
        pmid="12345678",
        entities=[
            entity("FUS", EntityType.DELIVERY_MODIFIER, "focused ultrasound"),
            entity("TMZ", EntityType.DRUG, "temozolomide"),
        ],
    )
    entity_path.write_text(entity_result.model_dump_json() + "\n", encoding="utf-8")

    saved_path = build_graph_records_from_jsonl(pubmed_path, entity_path, output_path)
    loaded = [
        KnowledgeGraphRecord.model_validate(json.loads(line))
        for line in saved_path.read_text(encoding="utf-8").splitlines()
    ]

    assert saved_path == output_path
    assert len(loaded) == 1
    assert [(node.label, node.key_value) for node in loaded[0].nodes] == [
        (NodeLabel.DELIVERY_MODIFIER, "focused ultrasound"),
        (NodeLabel.DRUG, "temozolomide"),
    ]
