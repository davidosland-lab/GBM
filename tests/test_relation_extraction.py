from gbmbert.annotation.schema import EntityType, Paper
from gbmbert.extraction.entities import EntityExtractionResult, ExtractedEntity
from gbmbert.extraction.relations import audit_relation_extraction_graph, extract_relations, format_relation_extraction_audit_markdown, split_sentences
from gbmbert.knowledge_graph.build_records import build_graph_records
from gbmbert.knowledge_graph.schema import EvidenceTier, GraphNode, GraphRelation, KnowledgeGraphRecord, MutationStatus, NodeLabel, RelationType, SpeciesModel


def entity_from_text(
    source: str,
    text: str,
    label: EntityType,
    normalized_text: str | None = None,
) -> ExtractedEntity:
    start = source.index(text)
    return ExtractedEntity(
        text=text,
        label=label,
        start=start,
        end=start + len(text),
        confidence=0.9,
        normalized_text=normalized_text or text,
    )


def test_split_sentences_preserves_offsets() -> None:
    text = "MGMT predicts response. EGFR is separate."

    spans = split_sentences(text)

    assert [(span.text, span.start, span.end) for span in spans] == [
        ("MGMT predicts response.", 0, 23),
        ("EGFR is separate.", 24, 41),
    ]


def test_extract_relations_predicts_biomarker_outcome() -> None:
    text = "MGMT methylation predicts temozolomide response in glioblastoma."
    entities = [
        entity_from_text(text, "MGMT methylation", EntityType.BIOMARKER),
        entity_from_text(text, "temozolomide response", EntityType.OUTCOME),
    ]

    relations = extract_relations(text, entities, source_pmid="12345678")

    assert len(relations) == 1
    relation = relations[0]
    assert relation.relation is RelationType.PREDICTS
    assert relation.head.label is NodeLabel.BIOMARKER
    assert relation.head.key_value == "MGMT methylation"
    assert relation.tail.label is NodeLabel.OUTCOME
    assert relation.tail.key_value == "temozolomide response"
    assert relation.source_pmid == "12345678"
    assert relation.properties["trigger"] == "predicts"


def test_extract_relations_adds_prediction_qualifiers_from_sentence() -> None:
    text = "In a retrospective human cohort, MGMT methylation predicts temozolomide response in IDH-wildtype patients."
    entities = [
        entity_from_text(text, "MGMT methylation", EntityType.BIOMARKER),
        entity_from_text(text, "temozolomide response", EntityType.OUTCOME),
    ]

    relations = extract_relations(text, entities, source_pmid="12345678")

    assert len(relations) == 1
    qualifiers = relations[0].qualifiers
    assert qualifiers.mutation_status is MutationStatus.IDH_WILDTYPE
    assert qualifiers.species_model is SpeciesModel.HUMAN
    assert qualifiers.evidence_context == "retrospective"


def test_extract_relations_associated_with_gene_outcome() -> None:
    text = "EGFR amplification is associated with poor prognosis in GBM."
    entities = [
        entity_from_text(text, "EGFR amplification", EntityType.GENE, "EGFR"),
        entity_from_text(text, "poor prognosis", EntityType.OUTCOME),
    ]

    relations = extract_relations(text, entities, source_pmid="12345678")

    assert len(relations) == 1
    assert relations[0].relation is RelationType.ASSOCIATED_WITH
    assert relations[0].head.key_value == "EGFR"
    assert relations[0].tail.key_value == "poor prognosis"


def test_extract_relations_enhances_delivery_of_drug() -> None:
    text = "Focused ultrasound enhances delivery of temozolomide across the BBB."
    entities = [
        entity_from_text(
            text,
            "Focused ultrasound",
            EntityType.DELIVERY_MODIFIER,
            "focused ultrasound",
        ),
        entity_from_text(text, "temozolomide", EntityType.DRUG),
    ]

    relations = extract_relations(text, entities, source_pmid="12345678")

    assert len(relations) == 1
    assert relations[0].relation is RelationType.ENHANCES_DELIVERY_OF
    assert relations[0].head.label is NodeLabel.DELIVERY_MODIFIER
    assert relations[0].tail.label is NodeLabel.DRUG


def test_extract_relations_requires_same_sentence() -> None:
    text = "MGMT methylation was measured. Temozolomide response was improved."
    entities = [
        entity_from_text(text, "MGMT methylation", EntityType.BIOMARKER),
        entity_from_text(text, "Temozolomide response", EntityType.OUTCOME),
    ]

    assert extract_relations(text, entities, source_pmid="12345678") == []


def test_extract_relations_filters_invalid_topology() -> None:
    text = "EGFR improves poor prognosis in glioblastoma."
    entities = [
        entity_from_text(text, "EGFR", EntityType.GENE),
        entity_from_text(text, "poor prognosis", EntityType.OUTCOME),
    ]

    assert extract_relations(text, entities, source_pmid="12345678") == []


def test_build_graph_records_includes_rule_based_relations() -> None:
    title = "MGMT methylation predicts temozolomide response"
    paper = Paper(pmid="12345678", title=title)
    entity_result = EntityExtractionResult(
        pmid="12345678",
        entities=[
            entity_from_text(title, "MGMT methylation", EntityType.BIOMARKER),
            entity_from_text(title, "temozolomide response", EntityType.OUTCOME),
        ],
    )

    record = list(build_graph_records([paper], [entity_result]))[0]

    assert len(record.relations) == 1
    assert record.relations[0].relation is RelationType.PREDICTS


def test_relation_extraction_audit_flags_missing_provenance(tmp_path) -> None:
    graph_path = tmp_path / "graph_records.jsonl"
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[biomarker, outcome],
        relations=[
            GraphRelation(
                head=biomarker,
                relation=RelationType.PREDICTS,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.HYPOTHESIS,
                confidence=0.4,
                properties={},
            )
        ],
    )
    graph_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    report = audit_relation_extraction_graph(graph_path)
    markdown = format_relation_extraction_audit_markdown(report)

    assert report.relation_count == 1
    assert report.flagged_relation_count == 1
    assert report.missing_trigger_count == 1
    assert report.missing_sentence_count == 1
    assert report.low_confidence_count == 1
    assert "Relation Extraction Audit" in markdown
