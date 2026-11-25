"""Research-only treatment scenario ranking over Phase 5 simulation outputs.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Hard boundary:
- Compares/ranks in-silico *scenarios*, never real-patient prescriptions.
- Not CDS, not a medical device, not clinically validated.
- Scores use transparent toy weights; they are not optimized dosing schedules.
- Intensity / schedule knobs are simulation parameters only — not real regimens.
- Toxicity/burden terms are toy research scores, not clinical toxicity models.
- No patient eligibility / CDS logic.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from gbmbert.simulation.graph_features import extract_graph_features
from gbmbert.simulation.model import RESEARCH_WARNING
from gbmbert.simulation.scenarios import (
    ScenarioDefinition,
    ScenarioPack,
    ScenarioRunReport,
    load_scenario_pack,
    run_scenario_pack,
)

BOUNDARY_BANNER = (
    "Research-use only. Not medical advice. Not clinical decision support (CDS). "
    "Not intended for diagnosis, treatment selection, dosing, or clinical decision-making. "
    "Scenario ranks are toy in-silico comparisons, not prescriptions. "
    "No patient eligibility screening. Intensity/schedule knobs are simulation parameters only."
)


@dataclass(frozen=True)
class RankingWeights:
    relative_reduction: float = 0.45
    final_burden_inverse: float = 0.20
    delivery_efficiency: float = 0.10
    evidence_support: float = 0.10
    toxicity_inverse: float = 0.15

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class ScenarioResearchKnobs:
    """Toy simulation-parameter knobs — not real dosing schedules or regimens."""

    intensity_scale: float = 1.0
    schedule_duty_cycle: float = 1.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class TreatmentStrategyConfig:
    name: str
    description: str
    simulation_config: str
    weights: RankingWeights = field(default_factory=RankingWeights)
    scenario_knobs: ScenarioResearchKnobs = field(default_factory=ScenarioResearchKnobs)
    assumptions: list[str] = field(default_factory=list)
    literature_anchors: list[dict[str, Any]] = field(default_factory=list)
    exclude_baseline_from_ranking: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["weights"] = self.weights.to_dict()
        payload["scenario_knobs"] = self.scenario_knobs.to_dict()
        return payload


@dataclass(frozen=True)
class TreatmentStrategyReport:
    config_name: str
    description: str
    warning: str
    boundary: str
    assumptions: list[str]
    literature_anchors: list[dict[str, Any]]
    simulation_pack_name: str
    graph_features: dict[str, Any] | None
    rankings: list[dict[str, Any]]
    comparison_table: list[dict[str, Any]]
    simulation_comparisons: list[dict[str, Any]]
    weights: dict[str, float]
    scenario_knobs: dict[str, float]
    ranking_provenance: dict[str, Any]
    simulated: list[str]
    not_simulated: list[str]
    phase: str = "Phase 6 treatment strategy research prototype"
    clinical_validity_claimed: bool = False
    is_clinical_decision_support: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_treatment_strategy_config(path: str | Path) -> TreatmentStrategyConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    weights_raw = payload.get("weights") or {}
    knobs_raw = payload.get("scenario_knobs") or {}
    return TreatmentStrategyConfig(
        name=str(payload.get("name") or Path(path).stem),
        description=str(payload.get("description") or ""),
        simulation_config=str(payload["simulation_config"]),
        weights=RankingWeights(
            relative_reduction=float(weights_raw.get("relative_reduction", 0.45)),
            final_burden_inverse=float(weights_raw.get("final_burden_inverse", 0.20)),
            delivery_efficiency=float(weights_raw.get("delivery_efficiency", 0.10)),
            evidence_support=float(weights_raw.get("evidence_support", 0.10)),
            toxicity_inverse=float(weights_raw.get("toxicity_inverse", 0.15)),
        ),
        scenario_knobs=ScenarioResearchKnobs(
            intensity_scale=float(knobs_raw.get("intensity_scale", 1.0)),
            schedule_duty_cycle=float(knobs_raw.get("schedule_duty_cycle", 1.0)),
        ),
        assumptions=[str(item) for item in payload.get("assumptions") or []],
        literature_anchors=list(payload.get("literature_anchors") or []),
        exclude_baseline_from_ranking=bool(payload.get("exclude_baseline_from_ranking", True)),
    )


def apply_research_scenario_knobs(
    pack: ScenarioPack,
    knobs: ScenarioResearchKnobs,
) -> ScenarioPack:
    """Scale scenario kill pressure by intensity × duty-cycle research knobs.

    These knobs are *simulation parameters* for scenario exploration.
    They are not real dosing schedules, fractionation, or PK/PD regimens.
    """

    intensity = max(0.0, float(knobs.intensity_scale))
    duty = min(1.0, max(0.0, float(knobs.schedule_duty_cycle)))
    effective = intensity * duty
    note = (
        f"Research scenario knobs applied: intensity_scale={intensity}, "
        f"schedule_duty_cycle={duty} (effective kill scale={effective}). "
        "Not a real dosing schedule."
    )
    scaled: list[ScenarioDefinition] = []
    for scenario in pack.scenarios:
        if scenario.scenario_id == "baseline" or scenario.base_kill_rate <= 0:
            scaled.append(scenario)
            continue
        scaled.append(
            replace(
                scenario,
                base_kill_rate=scenario.base_kill_rate * effective,
                notes=list(scenario.notes) + [note],
            )
        )
    return replace(pack, scenarios=scaled, assumptions=list(pack.assumptions) + [note])


def toy_toxicity_burden(
    *,
    base_kill_rate: float,
    delivery_multiplier: float,
    intensity_scale: float,
    schedule_duty_cycle: float,
) -> float:
    """Toy research toxicity/burden score (higher = more synthetic burden).

    Not a clinical toxicity model. Not AE prediction. Not eligibility logic.
    """

    duty = min(1.0, max(0.0, schedule_duty_cycle))
    intensity = max(0.0, intensity_scale)
    # Higher kill × delivery × intensity increases toy burden; sparse duty reduces it.
    return max(0.0, base_kill_rate) * max(0.0, delivery_multiplier) * intensity * (0.25 + 0.75 * duty)


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high <= low:
        return [1.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def rank_treatment_scenarios(
    config: TreatmentStrategyConfig,
    *,
    simulation_report: ScenarioRunReport | None = None,
    graph_jsonl: str | Path | None = None,
    use_graph_modulation: bool = False,
    base_dir: str | Path | None = None,
    intensity_scale: float | None = None,
    schedule_duty_cycle: float | None = None,
) -> TreatmentStrategyReport:
    """Rank Phase 5 simulation scenarios under explicit toy research weights."""

    root = Path(base_dir) if base_dir is not None else Path.cwd()
    knobs = ScenarioResearchKnobs(
        intensity_scale=(
            float(intensity_scale)
            if intensity_scale is not None
            else config.scenario_knobs.intensity_scale
        ),
        schedule_duty_cycle=(
            float(schedule_duty_cycle)
            if schedule_duty_cycle is not None
            else config.scenario_knobs.schedule_duty_cycle
        ),
    )
    pack = load_scenario_pack(root / config.simulation_config)
    pack = apply_research_scenario_knobs(pack, knobs)

    if simulation_report is None:
        simulation_report = run_scenario_pack(
            pack,
            graph_jsonl=graph_jsonl,
            use_graph_modulation=use_graph_modulation,
        )
    else:
        # When a precomputed report is supplied, still record knobs for provenance,
        # but do not silently claim they were applied to that report.
        pass

    graph_features = simulation_report.graph_features
    if graph_features is None and graph_jsonl is not None:
        graph_features = extract_graph_features(graph_jsonl).to_dict()

    evidence_support = 0.0
    if graph_features:
        mean_tier = graph_features.get("mean_evidence_tier")
        if mean_tier is not None:
            evidence_support = float(mean_tier) / 5.0
        evidence_support = max(
            evidence_support,
            float(graph_features.get("kill_modulation") or 1.0) - 1.0,
        )

    candidates = []
    for comparison, result in zip(simulation_report.comparisons, simulation_report.results, strict=False):
        scenario_id = str(comparison["scenario_id"])
        if config.exclude_baseline_from_ranking and scenario_id == "baseline":
            continue
        params = result.get("parameters") or {}
        delivery = float(params.get("delivery_multiplier") or 1.0)
        kill = float(params.get("base_kill_rate") or 0.0)
        # Recover nominal kill (pre-knob) for toxicity display when possible.
        nominal_kill = kill / max(knobs.intensity_scale * knobs.schedule_duty_cycle, 1e-9)
        toxicity = toy_toxicity_burden(
            base_kill_rate=nominal_kill,
            delivery_multiplier=delivery,
            intensity_scale=knobs.intensity_scale,
            schedule_duty_cycle=knobs.schedule_duty_cycle,
        )
        candidates.append(
            {
                "scenario_id": scenario_id,
                "label": comparison["label"],
                "final_total": float(comparison["final_total"]),
                "relative_reduction_vs_baseline": float(comparison["relative_reduction_vs_baseline"]),
                "delivery_multiplier": delivery,
                "base_kill_rate": kill,
                "delivery_efficiency": delivery * max(kill, 1e-9),
                "evidence_support": evidence_support,
                "toy_toxicity_burden": toxicity,
                "intensity_scale": knobs.intensity_scale,
                "schedule_duty_cycle": knobs.schedule_duty_cycle,
            }
        )

    if not candidates:
        candidates = [
            {
                "scenario_id": item["scenario_id"],
                "label": item["label"],
                "final_total": float(item["final_total"]),
                "relative_reduction_vs_baseline": float(item["relative_reduction_vs_baseline"]),
                "delivery_multiplier": 1.0,
                "base_kill_rate": 0.0,
                "delivery_efficiency": 0.0,
                "evidence_support": evidence_support,
                "toy_toxicity_burden": 0.0,
                "intensity_scale": knobs.intensity_scale,
                "schedule_duty_cycle": knobs.schedule_duty_cycle,
            }
            for item in simulation_report.comparisons
        ]

    rel_scores = _normalize([item["relative_reduction_vs_baseline"] for item in candidates])
    burden_scores = _normalize([-item["final_total"] for item in candidates])
    delivery_scores = _normalize([item["delivery_efficiency"] for item in candidates])
    evidence_scores = [item["evidence_support"] for item in candidates]
    if evidence_scores and max(evidence_scores) > 0:
        evidence_norm = _normalize(evidence_scores)
    else:
        evidence_norm = [0.0 for _ in candidates]
    # Lower toy toxicity is better → invert before normalize.
    toxicity_scores = _normalize([-item["toy_toxicity_burden"] for item in candidates])

    weights = config.weights
    rankings = []
    for index, item in enumerate(candidates):
        score = (
            weights.relative_reduction * rel_scores[index]
            + weights.final_burden_inverse * burden_scores[index]
            + weights.delivery_efficiency * delivery_scores[index]
            + weights.evidence_support * evidence_norm[index]
            + weights.toxicity_inverse * toxicity_scores[index]
        )
        rankings.append(
            {
                **item,
                "research_score": round(score, 6),
                "component_scores": {
                    "relative_reduction": round(rel_scores[index], 6),
                    "final_burden_inverse": round(burden_scores[index], 6),
                    "delivery_efficiency": round(delivery_scores[index], 6),
                    "evidence_support": round(evidence_norm[index], 6),
                    "toxicity_inverse": round(toxicity_scores[index], 6),
                },
            }
        )
    rankings.sort(key=lambda row: row["research_score"], reverse=True)
    for rank, row in enumerate(rankings, start=1):
        row["rank"] = rank

    comparison_table = [
        {
            "rank": row["rank"],
            "scenario_id": row["scenario_id"],
            "label": row["label"],
            "research_score": round(row["research_score"], 4),
            "relative_reduction": round(row["relative_reduction_vs_baseline"], 4),
            "final_total": round(row["final_total"], 4),
            "toy_toxicity_burden": round(row["toy_toxicity_burden"], 4),
            "delivery_multiplier": round(row["delivery_multiplier"], 4),
            "intensity_scale": round(row["intensity_scale"], 4),
            "schedule_duty_cycle": round(row["schedule_duty_cycle"], 4),
        }
        for row in rankings
    ]

    ranking_provenance = {
        "method": "transparent_weighted_sum_over_normalized_toy_components",
        "weights": weights.to_dict(),
        "scenario_knobs": knobs.to_dict(),
        "components": [
            "relative_reduction",
            "final_burden_inverse",
            "delivery_efficiency",
            "evidence_support",
            "toxicity_inverse",
        ],
        "normalization": "min_max_per_component_across_ranked_scenarios",
        "toxicity_model": "toy_kill_x_delivery_x_intensity_x_duty_proxy",
        "clinical_decision_support": False,
        "patient_eligibility": False,
        "real_dosing_schedule_search": False,
        "notes": [
            "Higher research_score means better under the configured toy objective only.",
            "toxicity_inverse rewards lower toy_toxicity_burden (research score, not clinical AEs).",
            "intensity_scale and schedule_duty_cycle are simulation knobs, not prescriptions.",
        ],
    }

    assumptions = list(config.assumptions) + [
        "Ranks compare Phase 5 toy simulation scenarios only.",
        "Scores use explicit transparent weights; they are not clinically optimized.",
        "Toy toxicity/burden is a synthetic research score — not clinical toxicity or AE prediction.",
        "Intensity/schedule knobs scale simulation kill pressure only — not real dosing schedules.",
        "No patient eligibility, CDS, or prescription generation.",
        "Higher research_score means better in-silico scenario under the configured toy objective - not a treatment recommendation.",
        BOUNDARY_BANNER,
    ]

    return TreatmentStrategyReport(
        config_name=config.name,
        description=config.description,
        warning=RESEARCH_WARNING,
        boundary=BOUNDARY_BANNER,
        assumptions=assumptions,
        literature_anchors=list(config.literature_anchors),
        simulation_pack_name=simulation_report.pack_name or pack.name,
        graph_features=graph_features,
        rankings=rankings,
        comparison_table=comparison_table,
        simulation_comparisons=list(simulation_report.comparisons),
        weights=weights.to_dict(),
        scenario_knobs=knobs.to_dict(),
        ranking_provenance=ranking_provenance,
        simulated=[
            "Ranking of Phase 5 simulation scenarios under toy multi-criteria weights",
            "Optional graph evidence-support term as a research score component",
            "Toy efficacy vs toy toxicity/burden trade-off scores (research only)",
            "Optional intensity_scale / schedule_duty_cycle simulation-parameter knobs",
            "Transparent comparison tables and ranking provenance for in-silico exploration",
        ],
        not_simulated=[
            "Real-patient treatment selection, dosing, or scheduling",
            "Clinical decision support or prescription generation",
            "Validated efficacy/toxicity trade-off optimization",
            "Patient eligibility screening or real-world inclusion criteria",
            "Regulatory or bedside recommendations",
        ],
    )
