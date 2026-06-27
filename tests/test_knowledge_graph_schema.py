import pytest
from pydantic import ValidationError

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
    node_key,
)


def test_node_key_maps_labels_to_unique_properties() -> None:
    assert node_key(NodeLabel.PAPER) == "pmid"
    assert node_key(NodeLabel.GENE) == "symbol"
    assert node_key(NodeLabel.TRIAL) == "nct_id"


def test_allowed_edge_accepts_canonical_handoff_examples() -> None:
    assert is_allowed_edge(
        RelationType.PREDICTS,
        NodeLabel.BIOMARKER,
        NodeLabel.OUTCOME,
    )
    assert is_allowed_edge(
        RelationType.ASSOCIATED_WITH,
        NodeLabel.GENE,
        NodeLabel.OUTCOME,
    )


def test_allowed_edge_accepts_scope_v2_graph_extensions() -> None:
    assert is_allowed_edge(
        RelationType.ENHANCES_DELIVERY_OF,
        NodeLabel.DELIVERY_MODIFIER,
        NodeLabel.DRUG,
    )
    assert is_allowed_edge(
        RelationType.SYNERGIZES_WITH,
        NodeLabel.TREATMENT,
        NodeLabel.TREATMENT,
    )
    assert is_allowed_edge(
        RelationType.TRANSITIONS_TO,
        NodeLabel.CELL_STATE,
        NodeLabel.CELL_STATE,
    )
    assert is_allowed_edge(
        RelationType.MODULATES_POLARIZATION_OF,
        NodeLabel.DRUG,
        NodeLabel.CELL_TYPE,
    )


def test_graph_relation_rejects_invalid_topology() -> None:
    gene = GraphNode(label=NodeLabel.GENE, key_value="EGFR")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="Poor Prognosis")

    with pytest.raises(ValidationError):
        GraphRelation(
            head=gene,
            relation=RelationType.IMPROVES,
            tail=outcome,
            source_pmid="12345678",
        )


def test_has_evidence_is_loader_managed() -> None:
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="Temozolomide Response")
    evidence = GraphNode(label=NodeLabel.EVIDENCE_LEVEL, key_value=3)

    with pytest.raises(ValidationError):
        GraphRelation(
            head=outcome,
            relation=RelationType.HAS_EVIDENCE,
            tail=evidence,
            source_pmid="12345678",
        )


def test_knowledge_graph_record_requires_matching_source_pmids() -> None:
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="Temozolomide Response")
    relation = GraphRelation(
        head=biomarker,
        relation=RelationType.PREDICTS,
        tail=outcome,
        source_pmid="87654321",
        evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
    )

    with pytest.raises(ValidationError):
        KnowledgeGraphRecord(pmid="12345678", relations=[relation])


def test_relation_qualifiers_flatten_to_graph_properties() -> None:
    qualifiers = RelationQualifiers(
        cohort="newly diagnosed GBM",
        species_model=SpeciesModel.HUMAN,
        mutation_status=MutationStatus.IDH_WILDTYPE,
        trial_phase="phase_iii",
        evidence_context="randomized",
    )
    biomarker = GraphNode(label=NodeLabel.BIOMARKER, key_value="MGMT methylation")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="Temozolomide Response")

    relation = GraphRelation(
        head=biomarker,
        relation=RelationType.PREDICTS,
        tail=outcome,
        source_pmid="12345678",
        qualifiers=qualifiers,
        properties={"sentence": "MGMT methylation predicts response in IDH-wildtype patients."},
    )

    assert relation.graph_properties()["mutation_status"] == "idh_wildtype"
    assert relation.graph_properties()["species_model"] == "human"
    assert relation.graph_properties()["sentence"].startswith("MGMT")


def test_mutation_status_qualifier_is_limited_to_predicts_relations() -> None:
    drug = GraphNode(label=NodeLabel.DRUG, key_value="temozolomide")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="response")

    with pytest.raises(ValidationError):
        GraphRelation(
            head=drug,
            relation=RelationType.IMPROVES,
            tail=outcome,
            source_pmid="12345678",
            qualifiers=RelationQualifiers(mutation_status=MutationStatus.IDH_MUTANT),
        )
