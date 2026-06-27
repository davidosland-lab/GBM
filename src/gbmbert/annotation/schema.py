"""Pydantic models for literature-derived biomedical annotations."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityType(str, Enum):
    """Supported biomedical entity labels for initial annotation."""

    GENE = "GENE"
    DRUG = "DRUG"
    DISEASE = "DISEASE"
    PATHWAY = "PATHWAY"
    BIOMARKER = "BIOMARKER"
    CELL_TYPE = "CELL_TYPE"
    CELL_STATE = "CELL_STATE"
    TREATMENT = "TREATMENT"
    DELIVERY_MODIFIER = "DELIVERY_MODIFIER"
    OUTCOME = "OUTCOME"
    TRIAL_PHASE = "TRIAL_PHASE"
    UNKNOWN = "UNKNOWN"


class RelationType(str, Enum):
    """Supported relation labels for early knowledge extraction."""

    MENTIONS = "MENTIONS"
    TARGETS = "TARGETS"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    PREDICTS = "PREDICTS"
    IMPROVES = "IMPROVES"
    WORSENS = "WORSENS"
    ACTIVATES = "ACTIVATES"
    INHIBITS = "INHIBITS"
    HAS_EVIDENCE = "HAS_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class EvidenceLevel(int, Enum):
    """Evidence classes used by later evidence classification work."""

    HYPOTHESIS = 0
    IN_VITRO = 1
    ANIMAL = 2
    RETROSPECTIVE_HUMAN = 3
    PHASE_I_II = 4
    RANDOMIZED_EVIDENCE = 5


class Paper(BaseModel):
    """A PubMed literature record retained as source provenance."""

    model_config = ConfigDict(str_strip_whitespace=True)

    pmid: str = Field(..., min_length=1)
    title: str = ""
    abstract: str = ""
    journal: str = ""
    publication_date: str = ""
    mesh_terms: list[str] = Field(default_factory=list)

    @field_validator("pmid")
    @classmethod
    def pmid_must_be_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("pmid must contain only digits")
        return value


class Entity(BaseModel):
    """A normalized biomedical mention found in a paper."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1)
    label: EntityType = EntityType.UNKNOWN
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    normalized_text: str | None = None
    source_pmid: str | None = None

    @field_validator("end")
    @classmethod
    def end_must_not_be_before_start(cls, value: int, info: object) -> int:
        data = getattr(info, "data", {})
        start = data.get("start")
        if start is not None and value < start:
            raise ValueError("end must be greater than or equal to start")
        return value

    @field_validator("source_pmid")
    @classmethod
    def source_pmid_must_be_numeric(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("source_pmid must contain only digits")
        return value


class Relation(BaseModel):
    """A relation between two biomedical entities."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subject: Entity
    predicate: RelationType
    object: Entity
    source_pmid: str = Field(..., min_length=1)
    confidence: float = Field(1.0, ge=0.0, le=1.0)

    @field_validator("source_pmid")
    @classmethod
    def source_pmid_must_be_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("source_pmid must contain only digits")
        return value


class EvidenceClaim(BaseModel):
    """A literature-backed claim with evidence classification."""

    model_config = ConfigDict(str_strip_whitespace=True)

    claim: str = Field(..., min_length=1)
    source_pmid: str = Field(..., min_length=1)
    evidence_level: EvidenceLevel = EvidenceLevel.HYPOTHESIS
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    classification_method: str | None = None
    evidence_cues: list[str] = Field(default_factory=list)

    @field_validator("source_pmid")
    @classmethod
    def source_pmid_must_be_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("source_pmid must contain only digits")
        return value
