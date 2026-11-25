"""Scenario pack loader and baseline-vs-perturbation runner.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gbmbert.simulation.graph_features import (
    GraphParameterModulation,
    GraphSimulationFeatures,
    extract_graph_features,
    resolve_graph_parameter_modulation,
)
from gbmbert.simulation.model import (
    CELL_STATES,
    RESEARCH_WARNING,
    CompartmentState,
    GrowthParams,
    SimulationResult,
    step_simulation,
)
from gbmbert.simulation.resistance import ResistanceParams, load_resistance_params


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    label: str
    base_kill_rate: float = 0.0
    delivery_multiplier: float = 1.0
    notes: list[str] = field(default_factory=list)
    apply_synergy_bonus: bool = False


@dataclass(frozen=True)
class ScenarioPack:
    name: str
    description: str
    steps: int
    dt: float
    initial_state: CompartmentState
    growth: GrowthParams
    scenarios: list[ScenarioDefinition]
    assumptions: list[str]
    literature_anchors: list[dict[str, Any]] = field(default_factory=list)
    resistance: ResistanceParams = field(default_factory=ResistanceParams)
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["initial_state"] = self.initial_state.as_dict()
        payload["growth"] = {
            "intrinsic_growth_rate": self.growth.intrinsic_growth_rate,
            "carrying_capacity": self.growth.carrying_capacity,
            "transition_rate": self.growth.transition_rate,
            "base_kill_rate": self.growth.base_kill_rate,
            "delivery_multiplier": self.growth.delivery_multiplier,
            "evidence_modulation": self.growth.evidence_modulation,
            "state_kill_weights": dict(self.growth.state_kill_weights),
        }
        payload["resistance"] = self.resistance.to_dict()
        return payload


@dataclass(frozen=True)
class ScenarioRunReport:
    pack_name: str
    description: str
    warning: str
    assumptions: list[str]
    literature_anchors: list[dict[str, Any]]
    graph_features: dict[str, Any] | None
    graph_modulation: dict[str, Any] | None
    results: list[dict[str, Any]]
    comparisons: list[dict[str, Any]]
    comparison_table: list[dict[str, Any]]
    simulated: list[str]
    not_simulated: list[str]
    resistance_enabled: bool = False
    phase: str = "Phase 5 research prototype"
    clinical_validity_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_scenario_pack(path: str | Path) -> ScenarioPack:
    """Load a Phase 5 scenario pack JSON config."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    initial_raw = payload["initial_state"]
    missing = [name for name in CELL_STATES if name not in initial_raw]
    if missing:
        raise ValueError(f"initial_state missing compartments: {', '.join(missing)}")
    initial = CompartmentState(**{name: float(initial_raw[name]) for name in CELL_STATES})
    growth_raw = payload["growth"]
    growth = GrowthParams(
        intrinsic_growth_rate=float(growth_raw["intrinsic_growth_rate"]),
        carrying_capacity=float(growth_raw["carrying_capacity"]),
        transition_rate=float(growth_raw.get("transition_rate", 0.02)),
        base_kill_rate=float(growth_raw.get("base_kill_rate", 0.0)),
        delivery_multiplier=float(growth_raw.get("delivery_multiplier", 1.0)),
        evidence_modulation=float(growth_raw.get("evidence_modulation", 1.0)),
        state_kill_weights={
            str(key): float(value) for key, value in (growth_raw.get("state_kill_weights") or {}).items()
        }
        or {"MES": 0.7, "NPC": 1.0, "OPC": 1.0, "AC": 0.9},
        transition_matrix=growth_raw.get("transition_matrix"),
    )
    scenarios = [
        ScenarioDefinition(
            scenario_id=str(item["scenario_id"]),
            label=str(item["label"]),
            base_kill_rate=float(item.get("base_kill_rate", 0.0)),
            delivery_multiplier=float(item.get("delivery_multiplier", 1.0)),
            notes=[str(note) for note in item.get("notes") or []],
            apply_synergy_bonus=bool(item.get("apply_synergy_bonus", "fus" in str(item.get("scenario_id", "")).lower())),
        )
        for item in payload["scenarios"]
    ]
    if not scenarios:
        raise ValueError("scenario pack must define at least one scenario")
    return ScenarioPack(
        name=str(payload.get("name") or Path(path).stem),
        description=str(payload.get("description") or ""),
        steps=int(payload.get("steps", 24)),
        dt=float(payload.get("dt", 1.0)),
        initial_state=initial,
        growth=growth,
        scenarios=scenarios,
        assumptions=[str(item) for item in payload.get("assumptions") or []],
        literature_anchors=list(payload.get("literature_anchors") or []),
        resistance=load_resistance_params(payload.get("resistance")),
    )


def run_scenario_pack(
    pack: ScenarioPack,
    *,
    graph_jsonl: str | Path | None = None,
    use_graph_modulation: bool = False,
    growth_overrides: dict[str, float] | None = None,
) -> ScenarioRunReport:
    """Run all scenarios in a pack and compute baseline comparisons."""

    graph_features: GraphSimulationFeatures | None = None
    modulation = GraphParameterModulation()
    if graph_jsonl is not None:
        graph_features = extract_graph_features(graph_jsonl)
        modulation = resolve_graph_parameter_modulation(
            graph_features,
            use_graph_modulation=use_graph_modulation,
        )

    overrides = growth_overrides or {}
    intrinsic = float(overrides.get("intrinsic_growth_rate", pack.growth.intrinsic_growth_rate))
    carrying = float(overrides.get("carrying_capacity", pack.growth.carrying_capacity))
    transition_rate = float(overrides.get("transition_rate", pack.growth.transition_rate))
    transition_rate *= modulation.transition_rate_scale

    evidence_modulation = (
        modulation.evidence_modulation if use_graph_modulation else pack.growth.evidence_modulation
    )

    results: list[SimulationResult] = []
    for scenario in pack.scenarios:
        delivery = scenario.delivery_multiplier * modulation.delivery_multiplier_scale
        kill = scenario.base_kill_rate * modulation.base_kill_rate_scale
        if scenario.apply_synergy_bonus and modulation.synergy_bonus:
            delivery *= 1.0 + modulation.synergy_bonus
        params = GrowthParams(
            intrinsic_growth_rate=intrinsic,
            carrying_capacity=carrying,
            transition_rate=transition_rate,
            base_kill_rate=kill,
            delivery_multiplier=delivery,
            evidence_modulation=evidence_modulation,
            state_kill_weights=dict(pack.growth.state_kill_weights),
            transition_matrix=pack.growth.transition_matrix,
        )
        assumptions = list(pack.assumptions) + list(scenario.notes)
        if use_graph_modulation:
            assumptions.extend(modulation.assumptions)
        if pack.resistance.enabled:
            assumptions.extend(pack.resistance.assumptions)
        results.append(
            step_simulation(
                pack.initial_state,
                params,
                steps=pack.steps,
                dt=pack.dt,
                scenario_id=scenario.scenario_id,
                label=scenario.label,
                assumptions=assumptions,
                resistance_params=pack.resistance if pack.resistance.enabled else None,
            )
        )

    baseline = next((item for item in results if item.scenario_id == "baseline"), results[0])
    comparisons = []
    comparison_table = []
    for item in results:
        delta = baseline.final_total - item.final_total
        relative = (delta / baseline.final_total) if baseline.final_total else 0.0
        mid = item.trajectory[len(item.trajectory) // 2] if item.trajectory else {}
        comparisons.append(
            {
                "scenario_id": item.scenario_id,
                "label": item.label,
                "final_total": item.final_total,
                "delta_vs_baseline_total": delta,
                "relative_reduction_vs_baseline": relative,
                "midpoint_total": float(mid.get("total", item.final_total)),
                "resistance_enabled": item.resistance_enabled,
                "final_resistance_totals": item.final_resistance_totals,
            }
        )
        comparison_table.append(
            {
                "scenario_id": item.scenario_id,
                "label": item.label,
                "final_total": round(item.final_total, 4),
                "midpoint_total": round(float(mid.get("total", item.final_total)), 4),
                "delta_vs_baseline": round(delta, 4),
                "relative_reduction": round(relative, 4),
                "MES": round(item.final_state["MES"], 4),
                "NPC": round(item.final_state["NPC"], 4),
                "OPC": round(item.final_state["OPC"], 4),
                "AC": round(item.final_state["AC"], 4),
            }
        )

    simulated = [
        "Discrete-time Neftel-inspired compartment abundances",
        "Logistic growth with shared carrying capacity",
        "Toy state transitions and kill/pressure scenario knobs",
        "Optional evidence-tier and relation-type research weighting from graph JSONL",
    ]
    if pack.resistance.enabled:
        simulated.append("Optional resistance-axis subpopulations (sensitive/persister/resistant)")

    return ScenarioRunReport(
        pack_name=pack.name,
        description=pack.description,
        warning=RESEARCH_WARNING,
        assumptions=list(pack.assumptions) + (list(modulation.assumptions) if use_graph_modulation else []),
        literature_anchors=list(pack.literature_anchors),
        graph_features=graph_features.to_dict() if graph_features else None,
        graph_modulation=modulation.to_dict() if graph_jsonl is not None else None,
        results=[item.to_dict() for item in results],
        comparisons=comparisons,
        comparison_table=comparison_table,
        simulated=simulated,
        not_simulated=[
            "Patient-specific clinical outcomes or imaging-constrained geometry",
            "Validated pharmacokinetics / pharmacodynamics",
            "Spatial invasion, vasculature, or full immune digital twin",
            "Clinical decision support or patient-ready treatment prescriptions",
            "Clinical validity or patient-ready predictions",
        ],
        resistance_enabled=pack.resistance.enabled,
    )
