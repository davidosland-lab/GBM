import pytest
from pydantic import ValidationError

from gbmbert.annotation.schema import (
    Entity,
    EntityType,
    EvidenceClaim,
    EvidenceLevel,
    Paper,
    Relation,
    RelationType,
)


def test_paper_schema_validates_pubmed_record() -> None:
    paper = Paper(
        pmid="12345678",
        title="MGMT methylation and temozolomide response in glioblastoma",
        abstract="A research abstract.",
        journal="Neuro-Oncology",
        publication_date="2024-01-01",
        mesh_terms=["Glioblastoma", "Temozolomide"],
    )

    assert paper.pmid == "12345678"
    assert paper.mesh_terms == ["Glioblastoma", "Temozolomide"]


def test_paper_rejects_non_numeric_pmid() -> None:
    with pytest.raises(ValidationError):
        Paper(pmid="PMID123")


def test_entity_schema_validates_offsets_and_confidence() -> None:
    entity = Entity(
        text="EGFR",
        label=EntityType.GENE,
        start=5,
        end=9,
        confidence=0.98,
        normalized_text="EGFR",
        source_pmid="12345678",
    )

    assert entity.label is EntityType.GENE
    assert entity.normalized_text == "EGFR"


def test_entity_rejects_invalid_span() -> None:
    with pytest.raises(ValidationError):
        Entity(text="EGFR", label=EntityType.GENE, start=10, end=4)


def test_relation_schema_validates_nested_entities() -> None:
    subject = Entity(text="MGMT methylation", label=EntityType.BIOMARKER, start=0, end=16)
    object_entity = Entity(text="temozolomide response", label=EntityType.OUTCOME, start=26, end=47)

    relation = Relation(
        subject=subject,
        predicate=RelationType.PREDICTS,
        object=object_entity,
        source_pmid="12345678",
        confidence=0.75,
    )

    assert relation.predicate is RelationType.PREDICTS
    assert relation.object.text == "temozolomide response"


def test_evidence_claim_schema_validates_claim() -> None:
    claim = EvidenceClaim(
        claim="MGMT methylation predicts response to temozolomide in glioblastoma cohorts.",
        source_pmid="12345678",
        evidence_level=EvidenceLevel.RETROSPECTIVE_HUMAN,
    )

    assert claim.evidence_level is EvidenceLevel.RETROSPECTIVE_HUMAN
    assert claim.entities == []
    assert claim.relations == []
