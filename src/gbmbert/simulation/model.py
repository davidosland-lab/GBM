"""Discrete-time multi-compartment tumour growth toy model.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Simulated (research prototype):
- Compartment abundances over discrete time steps
- Logistic growth, simple transitions, and toy kill/pressure terms
- Optional resistance-axis subpopulations (sensitive/persister/resistant)

Not simulated:
- Patient-specific outcomes, imaging-constrained geometry, validated PK/PD,
  spatial invasion, immune dynamics beyond toy scalars, or clinical response
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)

CELL_STATES = ("MES", "NPC", "OPC", "AC")


@dataclass(frozen=True)
class CompartmentState:
    """Neftel-inspired four-state abundance vector (toy research units)."""

    MES: float
    NPC: float
    OPC: float
    AC: float

    def total(self) -> float:
        return self.MES + self.NPC + self.OPC + self.AC

    def as_dict(self) -> dict[str, float]:
        return {"MES": self.MES, "NPC": self.NPC, "OPC": self.OPC, "AC": self.AC}

    def clamp_nonnegative(self) -> CompartmentState:
        return CompartmentState(
            MES=max(0.0, self.MES),
            NPC=max(0.0, self.NPC),
            OPC=max(0.0, self.OPC),
            AC=max(0.0, self.AC),
        )


@dataclass(frozen=True)
class GrowthParams:
    """Literature-inspired toy parameters (explicit assumptions, not validated)."""

    intrinsic_growth_rate: float
    carrying_capacity: float
    transition_rate: float
    base_kill_rate: float
    delivery_multiplier: float = 1.0
    evidence_modulation: float = 1.0
    state_kill_weights: dict[str, float] = field(
        default_factory=lambda: {"MES": 0.7, "NPC": 1.0, "OPC": 1.0, "AC": 0.9}
    )
    transition_matrix: dict[str, dict[str, float]] | None = None

    def resolved_transition_matrix(self) -> dict[str, dict[str, float]]:
        if self.transition_matrix is not None:
            return self.transition_matrix
        # Symmetric leakage between adjacent Neftel-like states (toy only).
        rate = self.transition_rate
        return {
            "MES": {"MES": 1.0 - 2 * rate, "NPC": rate, "OPC": 0.0, "AC": rate},
            "NPC": {"MES": rate, "NPC": 1.0 - 2 * rate, "OPC": rate, "AC": 0.0},
            "OPC": {"MES": 0.0, "NPC": rate, "OPC": 1.0 - 2 * rate, "AC": rate},
            "AC": {"MES": rate, "NPC": 0.0, "OPC": rate, "AC": 1.0 - 2 * rate},
        }


@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    label: str
    steps: int
    dt: float
    trajectory: list[dict[str, float]]
    final_state: dict[str, float]
    final_total: float
    assumptions: list[str]
    parameters: dict[str, Any]
    warning: str = RESEARCH_WARNING
    resistance_enabled: bool = False
    final_resistance_totals: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def step_simulation(
    initial: CompartmentState,
    params: GrowthParams,
    *,
    steps: int,
    dt: float = 1.0,
    scenario_id: str = "baseline",
    label: str = "Baseline growth",
    assumptions: list[str] | None = None,
    resistance_params: Any | None = None,
) -> SimulationResult:
    """Run a discrete-time logistic growth + transition + kill toy trajectory."""

    if steps < 1:
        raise ValueError("steps must be at least 1")
    if dt <= 0:
        raise ValueError("dt must be positive")
    if params.carrying_capacity <= 0:
        raise ValueError("carrying_capacity must be positive")

    from gbmbert.simulation.resistance import (
        ResistanceAwareState,
        ResistanceParams,
        apply_resistance_kill,
    )

    resistance: ResistanceParams | None = resistance_params if isinstance(resistance_params, ResistanceParams) else None
    use_resistance = bool(resistance and resistance.enabled)

    state = initial.clamp_nonnegative()
    resistant_state: ResistanceAwareState | None = None
    if use_resistance and resistance is not None:
        resistant_state = ResistanceAwareState.from_compartment_totals(
            state.as_dict(),
            resistance.normalized_fractions(),
        )
        trajectory_row = {"t": 0.0, **resistant_state.as_flat_dict()}
    else:
        trajectory_row = {"t": 0.0, **state.as_dict(), "total": state.total()}
    trajectory = [trajectory_row]
    matrix = params.resolved_transition_matrix()
    effective_kill = params.base_kill_rate * params.delivery_multiplier * params.evidence_modulation

    for step_index in range(1, steps + 1):
        if use_resistance and resistant_state is not None and resistance is not None:
            totals = resistant_state.compartment_totals()
            total = max(sum(totals.values()), 1e-12)
            growth_factor = params.intrinsic_growth_rate * (1.0 - total / params.carrying_capacity)
            grown_totals = {name: totals[name] * (1.0 + growth_factor * dt) for name in CELL_STATES}
            transitioned = {name: 0.0 for name in CELL_STATES}
            for source in CELL_STATES:
                for target, weight in matrix[source].items():
                    transitioned[target] += grown_totals[source] * weight
            # Preserve current resistance mix while redistributing cell-state totals.
            current_mix = resistant_state.resistance_totals()
            mix_total = sum(current_mix.values()) or 1.0
            fractions = {status: current_mix[status] / mix_total for status in current_mix}
            redistributed = ResistanceAwareState.from_compartment_totals(transitioned, fractions)
            resistant_state = apply_resistance_kill(
                redistributed,
                effective_kill=effective_kill,
                state_kill_weights=params.state_kill_weights,
                resistance_params=resistance,
                dt=dt,
            )
            state = CompartmentState(**resistant_state.compartment_totals())
            trajectory.append({"t": step_index * dt, **resistant_state.as_flat_dict()})
        else:
            total = max(state.total(), 1e-12)
            growth_factor = params.intrinsic_growth_rate * (1.0 - total / params.carrying_capacity)
            grown = {
                name: getattr(state, name) * (1.0 + growth_factor * dt)
                for name in CELL_STATES
            }
            transitioned = {name: 0.0 for name in CELL_STATES}
            for source in CELL_STATES:
                for target, weight in matrix[source].items():
                    transitioned[target] += grown[source] * weight
            killed = {
                name: transitioned[name]
                * (1.0 - min(0.95, effective_kill * params.state_kill_weights.get(name, 1.0) * dt))
                for name in CELL_STATES
            }
            state = CompartmentState(**killed).clamp_nonnegative()
            trajectory.append({"t": step_index * dt, **state.as_dict(), "total": state.total()})

    default_assumptions = [
        "Discrete-time logistic growth with a shared carrying capacity (toy).",
        "Neftel-inspired compartments are research labels only; rates are not clinically calibrated.",
        "Kill/pressure terms are scenario knobs, not validated drug effect sizes.",
        "Outputs are for in-silico hypothesis exploration, not diagnosis or treatment selection.",
    ]
    if use_resistance and resistance is not None:
        default_assumptions.extend(resistance.assumptions)

    final_resistance = resistant_state.resistance_totals() if resistant_state is not None else None
    return SimulationResult(
        scenario_id=scenario_id,
        label=label,
        steps=steps,
        dt=dt,
        trajectory=trajectory,
        final_state=state.as_dict(),
        final_total=state.total(),
        assumptions=list(assumptions or default_assumptions),
        parameters={
            "intrinsic_growth_rate": params.intrinsic_growth_rate,
            "carrying_capacity": params.carrying_capacity,
            "transition_rate": params.transition_rate,
            "base_kill_rate": params.base_kill_rate,
            "delivery_multiplier": params.delivery_multiplier,
            "evidence_modulation": params.evidence_modulation,
            "effective_kill": effective_kill,
            "state_kill_weights": dict(params.state_kill_weights),
            "initial_state": initial.as_dict(),
            "resistance": resistance.to_dict() if resistance is not None else None,
        },
        resistance_enabled=use_resistance,
        final_resistance_totals=final_resistance,
    )
