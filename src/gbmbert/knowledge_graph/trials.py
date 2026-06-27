"""Build graph-ready registry records from ClinicalTrials.gov JSONL."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gbmbert.ingest.clinicaltrials import ClinicalTrialRecord
from gbmbert.knowledge_graph.schema import GraphNode, NodeLabel, RelationType, is_allowed_edge

LOGGER = logging.getLogger(__name__)


class TrialGraphRelation(BaseModel):
    """A registry-backed relation keyed by NCT ID provenance."""

    model_config = ConfigDict(str_strip_whitespace=True)

    head: GraphNode
    relation: RelationType
    tail: GraphNode
    source_id: str = Field(..., min_length=1)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_id")
    @classmethod
    def source_id_must_be_nct_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.startswith("NCT"):
            raise ValueError("source_id must start with NCT")
        return value

    @model_validator(mode="after")
    def topology_must_be_allowed(self) -> "TrialGraphRelation":
        if not is_allowed_edge(self.relation, self.head.label, self.tail.label):
            raise ValueError(
                f"{self.head.label} -[{self.relation}]-> {self.tail.label} is not allowed"
            )
        return self


class ClinicalTrialGraphRecord(BaseModel):
    """Graph facts derived from one ClinicalTrials.gov registry record."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nct_id: str = Field(..., min_length=1)
    trial_properties: dict[str, Any] = Field(default_factory=dict)
    nodes: list[GraphNode] = Field(default_factory=list)
    relations: list[TrialGraphRelation] = Field(default_factory=list)

    @field_validator("nct_id")
    @classmethod
    def nct_id_must_be_registry_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.startswith("NCT"):
            raise ValueError("nct_id must start with NCT")
        return value

    @model_validator(mode="after")
    def relations_must_match_nct_id(self) -> "ClinicalTrialGraphRecord":
        for relation in self.relations:
            if relation.source_id != self.nct_id:
                raise ValueError("relation source_id must match record nct_id")
        return self


def load_trials_jsonl(path: str | Path) -> Iterator[ClinicalTrialRecord]:
    """Load normalized ClinicalTrials.gov JSONL records."""

    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield ClinicalTrialRecord.model_validate(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc


def build_trial_graph_records(
    trials: Iterable[ClinicalTrialRecord],
) -> Iterator[ClinicalTrialGraphRecord]:
    """Yield graph records that preserve ClinicalTrials.gov registry provenance."""

    for trial in trials:
        trial_node = trial_to_node(trial)
        nodes: dict[tuple[NodeLabel, str], GraphNode] = {}
        relations: list[TrialGraphRelation] = []
        for condition in trial.conditions:
            disease_node = disease_to_node(condition)
            _add_node(nodes, disease_node)
            relations.append(
                TrialGraphRelation(
                    head=trial_node,
                    relation=RelationType.ASSOCIATED_WITH,
                    tail=disease_node,
                    source_id=trial.nct_id,
                    confidence=1.0,
                    properties=registry_relation_properties(trial, "condition"),
                )
            )
        for intervention in trial.interventions:
            treatment_node = treatment_to_node(intervention)
            _add_node(nodes, treatment_node)
            relations.append(
                TrialGraphRelation(
                    head=trial_node,
                    relation=RelationType.ASSOCIATED_WITH,
                    tail=treatment_node,
                    source_id=trial.nct_id,
                    confidence=1.0,
                    properties=registry_relation_properties(trial, "intervention"),
                )
            )

        yield ClinicalTrialGraphRecord(
            nct_id=trial.nct_id,
            trial_properties=trial_node.keyed_properties(),
            nodes=list(nodes.values()),
            relations=relations,
        )


def trial_to_node(trial: ClinicalTrialRecord) -> GraphNode:
    """Convert a registry record into a Trial node."""

    title = trial.brief_title or trial.official_title or trial.nct_id
    return GraphNode(
        label=NodeLabel.TRIAL,
        key_value=trial.nct_id,
        properties={
            "display_name": title,
            "brief_title": trial.brief_title,
            "official_title": trial.official_title,
            "overall_status": trial.overall_status,
            "phases": trial.phases,
            "study_type": trial.study_type,
            "conditions": trial.conditions,
            "interventions": trial.interventions,
            "start_date": trial.start_date,
            "primary_completion_date": trial.primary_completion_date,
            "completion_date": trial.completion_date,
            "enrollment_count": trial.enrollment_count,
            "sponsor": trial.sponsor,
            "has_results": trial.has_results,
            "last_update_posted": trial.last_update_posted,
            "source_url": trial.source_url,
            "query": trial.query,
            "source": "clinicaltrials.gov",
        },
    )


def disease_to_node(condition: str) -> GraphNode:
    return GraphNode(
        label=NodeLabel.DISEASE,
        key_value=condition,
        properties={"display_name": condition, "source": "clinicaltrials.gov"},
    )


def treatment_to_node(intervention: str) -> GraphNode:
    return GraphNode(
        label=NodeLabel.TREATMENT,
        key_value=intervention,
        properties={"display_name": intervention, "source": "clinicaltrials.gov"},
    )


def registry_relation_properties(trial: ClinicalTrialRecord, registry_field: str) -> dict[str, Any]:
    return {
        "source_id": trial.nct_id,
        "source_url": trial.source_url,
        "source": "clinicaltrials.gov",
        "registry_field": registry_field,
        "overall_status": trial.overall_status,
        "phases": trial.phases,
        "has_results": trial.has_results,
    }


def save_trial_graph_records_jsonl(
    records: Iterable[ClinicalTrialGraphRecord],
    path: str | Path,
) -> Path:
    """Write ClinicalTrials.gov graph records as newline-delimited JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json())
            handle.write("\n")
    LOGGER.info("Saved ClinicalTrials.gov graph records to %s", output_path)
    return output_path


def build_trial_graph_records_from_jsonl(
    trials_jsonl: str | Path,
    output_jsonl: str | Path,
) -> Path:
    trials = list(load_trials_jsonl(trials_jsonl))
    LOGGER.info("Loaded %d ClinicalTrials.gov records", len(trials))
    return save_trial_graph_records_jsonl(build_trial_graph_records(trials), output_jsonl)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build graph-ready registry JSONL from ClinicalTrials.gov records."
    )
    parser.add_argument("trials_jsonl", type=Path, help="Input ClinicalTrials.gov JSONL path.")
    parser.add_argument("output_jsonl", type=Path, help="Output trial graph-record JSONL path.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    build_trial_graph_records_from_jsonl(args.trials_jsonl, args.output_jsonl)
    return 0


def _add_node(nodes: dict[tuple[NodeLabel, str], GraphNode], node: GraphNode) -> None:
    nodes[(node.label, str(node.key_value).casefold())] = node


if __name__ == "__main__":
    raise SystemExit(main())
