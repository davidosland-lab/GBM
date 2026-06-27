"""Configuration models for future GBM-BERT fine-tuning runs."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


APPROVED_BASE_MODELS = {
    "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
    "dmis-lab/biobert-base-cased-v1.2",
}


class TrainingTask(StrEnum):
    NER = "ner"
    RELATION_EXTRACTION = "relation_extraction"
    EVIDENCE_CLASSIFICATION = "evidence_classification"


class TrainingConfig(BaseModel):
    """Validated no-training configuration for GBM-BERT fine-tuning."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    task: TrainingTask
    base_model: str = Field(..., min_length=1)
    train_path: Path
    validation_path: Path | None = None
    output_dir: Path
    label_set: list[str] = Field(default_factory=list)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    training_enabled: bool = False

    @field_validator("base_model")
    @classmethod
    def base_model_must_be_pretrained_biomedical_model(cls, value: str) -> str:
        if value not in APPROVED_BASE_MODELS:
            raise ValueError("base_model must be an approved PubMedBERT or BioBERT checkpoint")
        return value

    @field_validator("label_set")
    @classmethod
    def label_set_must_not_be_empty(cls, value: list[str]) -> list[str]:
        labels = [label.strip() for label in value if label.strip()]
        if not labels:
            raise ValueError("label_set must contain at least one label")
        return labels

    @model_validator(mode="after")
    def output_must_not_overlap_inputs(self) -> "TrainingConfig":
        input_paths = {self.train_path}
        if self.validation_path is not None:
            input_paths.add(self.validation_path)
        if self.output_dir in input_paths:
            raise ValueError("output_dir must not be the same path as an input dataset")
        return self

    @property
    def is_training_enabled(self) -> bool:
        return self.training_enabled


def load_training_config(path: str | Path) -> TrainingConfig:
    """Load a training scaffold config from JSON."""

    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Training config not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid training config JSON: {config_path}") from exc
    return TrainingConfig.model_validate(payload)
