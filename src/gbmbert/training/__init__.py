"""GBM-BERT fine-tuning scaffolding.

This package prepares configurations and dataset adapters only. It does not
train a model or download model weights.
"""

from gbmbert.training.config import TrainingConfig, TrainingTask, load_training_config
from gbmbert.training.datasets import DatasetSummary, summarize_dataset_for_config
from gbmbert.training.evaluation import EvaluationReport, evaluate_predictions
from gbmbert.training.execution import TrainingExecutionResult, TrainingRunManifest, execute_evidence_training
from gbmbert.training.hf_datasets import load_label_map, load_prepared_dataset
from gbmbert.training.inference import score_evidence_jsonl
from gbmbert.training.model_card import ModelCard, build_model_card
from gbmbert.training.preparation import (
    BaselineReport,
    DatasetCard,
    ExperimentManifest,
    LabelMapSummary,
    SplitManifest,
)
from gbmbert.training.runner import TrainingGateReport, build_training_gate_report
from gbmbert.training.smoke_training import run_training_smoke

__all__ = [
    "BaselineReport",
    "DatasetCard",
    "DatasetSummary",
    "EvaluationReport",
    "ExperimentManifest",
    "LabelMapSummary",
    "ModelCard",
    "SplitManifest",
    "TrainingConfig",
    "TrainingExecutionResult",
    "TrainingGateReport",
    "TrainingRunManifest",
    "TrainingTask",
    "build_training_gate_report",
    "build_model_card",
    "evaluate_predictions",
    "execute_evidence_training",
    "load_label_map",
    "load_prepared_dataset",
    "load_training_config",
    "run_training_smoke",
    "score_evidence_jsonl",
    "summarize_dataset_for_config",
]
