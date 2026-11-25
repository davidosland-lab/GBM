"""Optional graph-derived research features for Phase 5 toy simulation.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Evidence tiers and relation types from graph records are used only as
transparent research weights. They do not validate clinical effect sizes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gbmbert.simulation.model import RESEARCH_WARNING

DELIVERY_RELATIONS = frozenset({"ENHANCES_DELIVERY_OF"})
RESPONSE_RELATIONS = frozenset({"PREDICTS", "IMPROVES", "ASSOCIATED_WITH"})
SYNERGY_RELATIONS = frozenset({"SYNERGIZES_WITH"})
TRANSITION_RELATIONS = frozenset({"TRANSITIONS_TO", "MODULATES_POLARIZATION_OF"})


@dataclass(frozen=True)
class GraphSimulationFeatures:
    source_path: str
    relation_count: int
    evidence_tier_counts: dict[str, int]
    mean_evidence_tier: float | None
    evidence_modulation: float
    delivery_modulation: float
    kill_modulation: float
    synergy_modulation: float
    transition_modulation: float
    relation_type_counts: dict[str, int]
    parameter_provenance: list[dict[str, Any]]
    sample_relations: list[dict[str, Any]]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphParameterModulation:
    """Resolved research knobs derived from graph features (toy only)."""

    evidence_modulation: float = 1.0
    delivery_multiplier_scale: float = 1.0
    base_kill_rate_scale: float = 1.0
    transition_rate_scale: float = 1.0
    synergy_bonus: float = 0.0
    provenance: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tier_weight(tier: int | None, default: float = 0.5) -> float:
    if tier is None:
        return default
    return max(0.0, min(1.0, float(tier) / 5.0))


def extract_graph_features(
    path: str | Path,
    *,
    max_samples: int = 5,
    modulation_floor: float = 0.75,
    modulation_ceiling: float = 1.25,
) -> GraphSimulationFeatures:
    """Summarize graph-record JSONL into research modulation features."""

    input_path = Path(path)
    tier_counts: dict[str, int] = {}
    relation_type_counts: dict[str, int] = {}
    tiers: list[int] = []
    samples: list[dict[str, Any]] = []
    warnings: list[str] = []
    provenance: list[dict[str, Any]] = []
    relation_count = 0

    delivery_weights: list[float] = []
    kill_weights: list[float] = []
    synergy_weights: list[float] = []
    transition_weights: list[float] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.append(f"Line {line_number}: invalid JSON ({exc.msg})")
                continue
            for relation in record.get("relations") or []:
                relation_count += 1
                rel_name = str(relation.get("relation") or "UNKNOWN")
                relation_type_counts[rel_name] = relation_type_counts.get(rel_name, 0) + 1
                tier = relation.get("evidence_tier")
                tier_int: int | None
                try:
                    tier_int = int(tier) if tier is not None else None
                except (TypeError, ValueError):
                    warnings.append(f"Line {line_number}: non-integer evidence_tier={tier!r}")
                    tier_int = None
                if tier_int is not None:
                    tiers.append(tier_int)
                    key = str(tier_int)
                    tier_counts[key] = tier_counts.get(key, 0) + 1

                weight = _tier_weight(tier_int)
                confidence = relation.get("confidence")
                try:
                    conf = float(confidence) if confidence is not None else 0.5
                except (TypeError, ValueError):
                    conf = 0.5
                combined = 0.5 * weight + 0.5 * max(0.0, min(1.0, conf))

                head = (relation.get("head") or {}).get("key_value")
                tail = (relation.get("tail") or {}).get("key_value")
                pmid = relation.get("source_pmid")

                if rel_name in DELIVERY_RELATIONS:
                    delivery_weights.append(combined)
                    provenance.append(
                        {
                            "parameter": "delivery_modulation",
                            "relation": rel_name,
                            "source_pmid": pmid,
                            "evidence_tier": tier_int,
                            "head": head,
                            "tail": tail,
                            "research_weight": round(combined, 4),
                        }
                    )
                elif rel_name in RESPONSE_RELATIONS:
                    kill_weights.append(combined)
                    provenance.append(
                        {
                            "parameter": "kill_modulation",
                            "relation": rel_name,
                            "source_pmid": pmid,
                            "evidence_tier": tier_int,
                            "head": head,
                            "tail": tail,
                            "research_weight": round(combined, 4),
                        }
                    )
                elif rel_name in SYNERGY_RELATIONS:
                    synergy_weights.append(combined)
                    provenance.append(
                        {
                            "parameter": "synergy_modulation",
                            "relation": rel_name,
                            "source_pmid": pmid,
                            "evidence_tier": tier_int,
                            "head": head,
                            "tail": tail,
                            "research_weight": round(combined, 4),
                        }
                    )
                elif rel_name in TRANSITION_RELATIONS:
                    transition_weights.append(combined)
                    provenance.append(
                        {
                            "parameter": "transition_modulation",
                            "relation": rel_name,
                            "source_pmid": pmid,
                            "evidence_tier": tier_int,
                            "head": head,
                            "tail": tail,
                            "research_weight": round(combined, 4),
                        }
                    )

                if len(samples) < max_samples:
                    samples.append(
                        {
                            "source_pmid": pmid,
                            "relation": rel_name,
                            "evidence_tier": tier_int,
                            "head": head,
                            "tail": tail,
                        }
                    )

    if not tiers:
        warnings.append("No evidence_tier values found; using neutral modulation=1.0")
        mean_tier = None
        evidence_modulation = 1.0
    else:
        mean_tier = sum(tiers) / len(tiers)
        normalized = mean_tier / 5.0
        evidence_modulation = modulation_floor + (modulation_ceiling - modulation_floor) * normalized

    def _axis_modulation(weights: list[float], *, floor: float, ceiling: float, neutral: float = 1.0) -> float:
        if not weights:
            return neutral
        mean_w = sum(weights) / len(weights)
        return floor + (ceiling - floor) * mean_w

    delivery_modulation = _axis_modulation(delivery_weights, floor=1.0, ceiling=1.35, neutral=1.0)
    kill_modulation = _axis_modulation(kill_weights, floor=0.9, ceiling=1.2, neutral=1.0)
    synergy_modulation = _axis_modulation(synergy_weights, floor=1.0, ceiling=1.15, neutral=1.0)
    transition_modulation = _axis_modulation(transition_weights, floor=0.9, ceiling=1.15, neutral=1.0)

    if delivery_weights:
        provenance.insert(
            0,
            {
                "parameter": "delivery_modulation",
                "aggregation": "mean_tier_confidence",
                "value": round(delivery_modulation, 4),
                "n_relations": len(delivery_weights),
            },
        )
    if kill_weights:
        provenance.insert(
            0,
            {
                "parameter": "kill_modulation",
                "aggregation": "mean_tier_confidence",
                "value": round(kill_modulation, 4),
                "n_relations": len(kill_weights),
            },
        )

    return GraphSimulationFeatures(
        source_path=str(input_path),
        relation_count=relation_count,
        evidence_tier_counts=dict(sorted(tier_counts.items(), key=lambda item: int(item[0]))),
        mean_evidence_tier=mean_tier,
        evidence_modulation=evidence_modulation,
        delivery_modulation=delivery_modulation,
        kill_modulation=kill_modulation,
        synergy_modulation=synergy_modulation,
        transition_modulation=transition_modulation,
        relation_type_counts=dict(sorted(relation_type_counts.items())),
        parameter_provenance=provenance[:40],
        sample_relations=samples,
        warnings=warnings,
    )


def resolve_graph_parameter_modulation(
    features: GraphSimulationFeatures,
    *,
    use_graph_modulation: bool,
) -> GraphParameterModulation:
    """Map extracted graph features into scenario-parameter scales (research only)."""

    if not use_graph_modulation:
        return GraphParameterModulation(
            assumptions=[
                "Graph features summarized but not applied to scenario parameters "
                "(pass --use-graph-modulation to enable research weights)."
            ]
        )
    return GraphParameterModulation(
        evidence_modulation=features.evidence_modulation,
        delivery_multiplier_scale=features.delivery_modulation,
        base_kill_rate_scale=features.kill_modulation,
        transition_rate_scale=features.transition_modulation,
        synergy_bonus=max(0.0, features.synergy_modulation - 1.0),
        provenance=list(features.parameter_provenance),
        assumptions=[
            "KG-driven modulation uses relation-type research weights only "
            "(ENHANCES_DELIVERY_OF -> delivery scale, PREDICTS/IMPROVES -> kill scale, "
            "SYNERGIZES_WITH -> combo bonus, TRANSITIONS_TO -> transition scale).",
            "Modulation bounds are explicit toy clamps, not calibrated effect sizes.",
            f"Resolved scales: evidence={features.evidence_modulation:.3f}, "
            f"delivery={features.delivery_modulation:.3f}, "
            f"kill={features.kill_modulation:.3f}, "
            f"transition={features.transition_modulation:.3f}, "
            f"synergy={features.synergy_modulation:.3f}.",
        ],
    )
