"""Typed schema for the GBM-AI labeled property graph."""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NodeLabel(StrEnum):
    PAPER = "Paper"
    GENE = "Gene"
    DRUG = "Drug"
    PATHWAY = "Pathway"
    BIOMARKER = "Biomarker"
    TREATMENT = "Treatment"
    OUTCOME = "Outcome"
    CELL_TYPE = "CellType"
    CELL_STATE = "CellState"
    DELIVERY_MODIFIER = "DeliveryModifier"
    TRIAL = "Trial"
    DISEASE = "Disease"
    EVIDENCE_LEVEL = "EvidenceLevel"


class RelationType(StrEnum):
    MENTIONS = "MENTIONS"
    TARGETS = "TARGETS"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    PREDICTS = "PREDICTS"
    IMPROVES = "IMPROVES"
    WORSENS = "WORSENS"
    ACTIVATES = "ACTIVATES"
    INHIBITS = "INHIBITS"
    ENHANCES_DELIVERY_OF = "ENHANCES_DELIVERY_OF"
    SYNERGIZES_WITH = "SYNERGIZES_WITH"
    TRANSITIONS_TO = "TRANSITIONS_TO"
    MODULATES_POLARIZATION_OF = "MODULATES_POLARIZATION_OF"
    HAS_EVIDENCE = "HAS_EVIDENCE"


class EvidenceTier(IntEnum):
    HYPOTHESIS = 0
    IN_VITRO = 1
    ANIMAL = 2
    RETROSPECTIVE_HUMAN = 3
    PHASE_I_II = 4
    RANDOMIZED_EVIDENCE = 5


class MutationStatus(StrEnum):
    IDH_WILDTYPE = "idh_wildtype"
    IDH_MUTANT = "idh_mutant"
    MGMT_METHYLATED = "mgmt_methylated"
    MGMT_UNMETHYLATED = "mgmt_unmethylated"
    EGFR_AMPLIFIED = "egfr_amplified"


class SpeciesModel(StrEnum):
    HUMAN = "human"
    MOUSE = "mouse"
    RAT = "rat"
    CELL_LINE = "cell_line"
    ORGANOID = "organoid"
    XENOGRAFT = "xenograft"
    UNKNOWN = "unknown"


class RelationQualifiers(BaseModel):
    """Context that narrows how a literature relation should be interpreted."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cohort: str | None = None
    species_model: SpeciesModel | None = None
    mutation_status: MutationStatus | None = None
    trial_phase: str | None = None
    evidence_context: str | None = None

    def to_properties(self) -> dict[str, str]:
        return {
            key: str(value.value if isinstance(value, StrEnum) else value)
            for key, value in self.model_dump(exclude_none=True).items()
        }


NODE_KEY: dict[NodeLabel, str] = {
    NodeLabel.PAPER: "pmid",
    NodeLabel.GENE: "symbol",
    NodeLabel.DRUG: "name",
    NodeLabel.PATHWAY: "name",
    NodeLabel.BIOMARKER: "name",
    NodeLabel.TREATMENT: "name",
    NodeLabel.OUTCOME: "name",
    NodeLabel.CELL_TYPE: "name",
    NodeLabel.CELL_STATE: "name",
    NodeLabel.DELIVERY_MODIFIER: "name",
    NodeLabel.TRIAL: "nct_id",
    NodeLabel.DISEASE: "name",
    NodeLabel.EVIDENCE_LEVEL: "tier",
}

ALLOWED_EDGES: dict[RelationType, set[tuple[NodeLabel, NodeLabel]]] = {
    RelationType.MENTIONS: {
        (NodeLabel.PAPER, NodeLabel.GENE),
        (NodeLabel.PAPER, NodeLabel.DRUG),
        (NodeLabel.PAPER, NodeLabel.PATHWAY),
        (NodeLabel.PAPER, NodeLabel.BIOMARKER),
        (NodeLabel.PAPER, NodeLabel.TREATMENT),
        (NodeLabel.PAPER, NodeLabel.OUTCOME),
        (NodeLabel.PAPER, NodeLabel.CELL_TYPE),
        (NodeLabel.PAPER, NodeLabel.CELL_STATE),
        (NodeLabel.PAPER, NodeLabel.DELIVERY_MODIFIER),
        (NodeLabel.PAPER, NodeLabel.TRIAL),
        (NodeLabel.PAPER, NodeLabel.DISEASE),
    },
    RelationType.TARGETS: {
        (NodeLabel.DRUG, NodeLabel.GENE),
        (NodeLabel.TREATMENT, NodeLabel.GENE),
        (NodeLabel.DRUG, NodeLabel.PATHWAY),
        (NodeLabel.TREATMENT, NodeLabel.PATHWAY),
    },
    RelationType.ASSOCIATED_WITH: {
        (NodeLabel.GENE, NodeLabel.DISEASE),
        (NodeLabel.GENE, NodeLabel.OUTCOME),
        (NodeLabel.BIOMARKER, NodeLabel.OUTCOME),
        (NodeLabel.BIOMARKER, NodeLabel.DISEASE),
        (NodeLabel.CELL_TYPE, NodeLabel.OUTCOME),
        (NodeLabel.CELL_STATE, NodeLabel.OUTCOME),
        (NodeLabel.PATHWAY, NodeLabel.DISEASE),
        (NodeLabel.TRIAL, NodeLabel.TREATMENT),
        (NodeLabel.TRIAL, NodeLabel.DISEASE),
    },
    RelationType.PREDICTS: {
        (NodeLabel.BIOMARKER, NodeLabel.OUTCOME),
        (NodeLabel.GENE, NodeLabel.OUTCOME),
        (NodeLabel.DISEASE, NodeLabel.OUTCOME),
    },
    RelationType.IMPROVES: {
        (NodeLabel.DRUG, NodeLabel.OUTCOME),
        (NodeLabel.TREATMENT, NodeLabel.OUTCOME),
    },
    RelationType.WORSENS: {
        (NodeLabel.DRUG, NodeLabel.OUTCOME),
        (NodeLabel.TREATMENT, NodeLabel.OUTCOME),
        (NodeLabel.GENE, NodeLabel.OUTCOME),
        (NodeLabel.BIOMARKER, NodeLabel.OUTCOME),
    },
    RelationType.ACTIVATES: {
        (NodeLabel.GENE, NodeLabel.PATHWAY),
        (NodeLabel.DRUG, NodeLabel.PATHWAY),
        (NodeLabel.TREATMENT, NodeLabel.PATHWAY),
        (NodeLabel.PATHWAY, NodeLabel.PATHWAY),
    },
    RelationType.INHIBITS: {
        (NodeLabel.GENE, NodeLabel.PATHWAY),
        (NodeLabel.DRUG, NodeLabel.PATHWAY),
        (NodeLabel.TREATMENT, NodeLabel.PATHWAY),
        (NodeLabel.PATHWAY, NodeLabel.PATHWAY),
    },
    RelationType.ENHANCES_DELIVERY_OF: {
        (NodeLabel.DELIVERY_MODIFIER, NodeLabel.DRUG),
        (NodeLabel.DELIVERY_MODIFIER, NodeLabel.TREATMENT),
    },
    RelationType.SYNERGIZES_WITH: {
        (NodeLabel.TREATMENT, NodeLabel.TREATMENT),
        (NodeLabel.DRUG, NodeLabel.DRUG),
        (NodeLabel.DRUG, NodeLabel.TREATMENT),
        (NodeLabel.TREATMENT, NodeLabel.DRUG),
    },
    RelationType.TRANSITIONS_TO: {
        (NodeLabel.CELL_STATE, NodeLabel.CELL_STATE),
    },
    RelationType.MODULATES_POLARIZATION_OF: {
        (NodeLabel.DRUG, NodeLabel.CELL_TYPE),
        (NodeLabel.TREATMENT, NodeLabel.CELL_TYPE),
    },
    RelationType.HAS_EVIDENCE: {
        (NodeLabel.GENE, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.DRUG, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.PATHWAY, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.BIOMARKER, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.TREATMENT, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.OUTCOME, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.CELL_TYPE, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.CELL_STATE, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.DELIVERY_MODIFIER, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.TRIAL, NodeLabel.EVIDENCE_LEVEL),
        (NodeLabel.DISEASE, NodeLabel.EVIDENCE_LEVEL),
    },
}


def node_key(label: NodeLabel) -> str:
    return NODE_KEY[label]


def is_allowed_edge(relation: RelationType, head: NodeLabel, tail: NodeLabel) -> bool:
    return (head, tail) in ALLOWED_EDGES.get(relation, set())


class GraphNode(BaseModel):
    """A graph node keyed by its canonical label-specific identifier."""

    model_config = ConfigDict(str_strip_whitespace=True)

    label: NodeLabel
    key_value: str | int
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("key_value")
    @classmethod
    def key_value_must_not_be_blank(cls, value: str | int) -> str | int:
        if isinstance(value, str) and not value.strip():
            raise ValueError("key_value must not be blank")
        return value.strip() if isinstance(value, str) else value

    def keyed_properties(self) -> dict[str, Any]:
        return {node_key(self.label): self.key_value, **self.properties}


class GraphRelation(BaseModel):
    """A literature-backed relation between two graph nodes."""

    model_config = ConfigDict(str_strip_whitespace=True)

    head: GraphNode
    relation: RelationType
    tail: GraphNode
    source_pmid: str = Field(..., min_length=1)
    evidence_tier: EvidenceTier = EvidenceTier.HYPOTHESIS
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    qualifiers: RelationQualifiers = Field(default_factory=RelationQualifiers)
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_pmid")
    @classmethod
    def source_pmid_must_be_numeric(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("source_pmid must contain only digits")
        return value

    @model_validator(mode="after")
    def topology_must_be_allowed(self) -> GraphRelation:
        if self.relation == RelationType.HAS_EVIDENCE:
            raise ValueError("HAS_EVIDENCE is managed by the graph loader")
        if self.qualifiers.mutation_status is not None and self.relation != RelationType.PREDICTS:
            raise ValueError("mutation_status qualifier is currently supported only on PREDICTS relations")
        if not is_allowed_edge(self.relation, self.head.label, self.tail.label):
            raise ValueError(
                f"{self.head.label} -[{self.relation}]-> {self.tail.label} is not allowed"
            )
        return self

    def graph_properties(self) -> dict[str, Any]:
        return {**self.properties, **self.qualifiers.to_properties()}


class KnowledgeGraphRecord(BaseModel):
    """All graph facts extracted from a single source paper."""

    model_config = ConfigDict(str_strip_whitespace=True)

    pmid: str = Field(..., min_length=1)
    paper_properties: dict[str, Any] = Field(default_factory=dict)
    nodes: list[GraphNode] = Field(default_factory=list)
    relations: list[GraphRelation] = Field(default_factory=list)

    @field_validator("pmid")
    @classmethod
    def pmid_must_be_numeric(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("pmid must contain only digits")
        return value

    @model_validator(mode="after")
    def relations_must_match_record_pmid(self) -> KnowledgeGraphRecord:
        for relation in self.relations:
            if relation.source_pmid != self.pmid:
                raise ValueError("relation source_pmid must match record pmid")
        return self
