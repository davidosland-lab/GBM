"""Schemas and label helpers for biomedical entity extraction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from gbmbert.annotation.schema import EntityType

SUPPORTED_ENTITY_TYPES: tuple[EntityType, ...] = (
    EntityType.GENE,
    EntityType.DRUG,
    EntityType.DISEASE,
    EntityType.PATHWAY,
    EntityType.BIOMARKER,
    EntityType.CELL_TYPE,
    EntityType.CELL_STATE,
    EntityType.TREATMENT,
    EntityType.DELIVERY_MODIFIER,
    EntityType.OUTCOME,
    EntityType.TRIAL_PHASE,
    EntityType.UNKNOWN,
)

_LABEL_ALIASES: dict[str, EntityType] = {
    "GENE": EntityType.GENE,
    "GENES": EntityType.GENE,
    "PROTEIN": EntityType.GENE,
    "BIOLOGICAL STRUCTURE": EntityType.CELL_TYPE,
    "CHEMICAL": EntityType.DRUG,
    "CHEMICALS": EntityType.DRUG,
    "DRUG": EntityType.DRUG,
    "DRUGS": EntityType.DRUG,
    "MEDICATION": EntityType.DRUG,
    "DISEASE": EntityType.DISEASE,
    "DISEASES": EntityType.DISEASE,
    "DISORDER": EntityType.DISEASE,
    "DISEASE DISORDER": EntityType.DISEASE,
    "SIGN SYMPTOM": EntityType.DISEASE,
    "PATHWAY": EntityType.PATHWAY,
    "BIOMARKER": EntityType.BIOMARKER,
    "BIOLOGICAL ATTRIBUTE": EntityType.BIOMARKER,
    "LAB VALUE": EntityType.BIOMARKER,
    "CELL": EntityType.CELL_TYPE,
    "CELL LINE": EntityType.CELL_TYPE,
    "CELL TYPE": EntityType.CELL_TYPE,
    "CELL_TYPE": EntityType.CELL_TYPE,
    "CELL STATE": EntityType.CELL_STATE,
    "CELL_STATE": EntityType.CELL_STATE,
    "TREATMENT": EntityType.TREATMENT,
    "THERAPY": EntityType.TREATMENT,
    "THERAPEUTIC PROCEDURE": EntityType.TREATMENT,
    "DELIVERY MODIFIER": EntityType.DELIVERY_MODIFIER,
    "DELIVERY_MODIFIER": EntityType.DELIVERY_MODIFIER,
    "OUTCOME": EntityType.OUTCOME,
    "SURVIVAL": EntityType.OUTCOME,
    "TRIAL PHASE": EntityType.TRIAL_PHASE,
    "TRIAL_PHASE": EntityType.TRIAL_PHASE,
}


class ExtractedEntity(BaseModel):
    """A single entity extracted from a PubMed paper."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1)
    label: EntityType = EntityType.UNKNOWN
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    normalized_text: str = Field(..., min_length=1)

    @field_validator("end")
    @classmethod
    def end_must_not_be_before_start(cls, value: int, info: Any) -> int:
        start = info.data.get("start")
        if start is not None and value < start:
            raise ValueError("end must be greater than or equal to start")
        return value


class EntityExtractionResult(BaseModel):
    """Entity extraction output for one PubMed paper."""

    model_config = ConfigDict(str_strip_whitespace=True)

    pmid: str = Field(..., min_length=1)
    entities: list[ExtractedEntity] = Field(default_factory=list)

    @field_validator("pmid")
    @classmethod
    def pmid_must_be_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("pmid must contain only digits")
        return value


def normalize_label(label: str | None) -> EntityType:
    """Map model-specific NER labels into the supported entity ontology."""

    if not label:
        return EntityType.UNKNOWN

    clean_label = label.replace("B-", "").replace("I-", "").strip()
    clean_label = clean_label.replace("-", " ")
    clean_label = clean_label.replace("_", " ").upper()
    return _LABEL_ALIASES.get(clean_label, EntityType.UNKNOWN)


def entity_from_model_output(output: dict[str, Any], source_text: str) -> ExtractedEntity:
    """Convert a Hugging Face NER output dictionary into a stable entity model."""

    from gbmbert.extraction.normalize import normalize_text

    start = int(output.get("start", 0) or 0)
    end = int(output.get("end", start) or start)
    raw_text = str(output.get("word") or output.get("text") or "").strip()
    if 0 <= start <= end <= len(source_text):
        raw_text = source_text[start:end].strip() or raw_text
    if not raw_text:
        raw_text = "UNKNOWN"

    label = normalize_label(str(output.get("entity_group") or output.get("entity") or ""))
    confidence = float(output.get("score", 0.0) or 0.0)
    return ExtractedEntity(
        text=raw_text,
        label=label,
        start=start,
        end=end,
        confidence=max(0.0, min(confidence, 1.0)),
        normalized_text=normalize_text(raw_text),
    )
