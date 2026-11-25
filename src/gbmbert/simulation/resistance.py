"""Optional resistance-axis populations for Phase 5 toy simulation.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Assumptions (explicit, toy only):
- Each Neftel-inspired compartment may be split into sensitive / persister /
  resistant subpopulations (up to 12 logical populations).
- Kill pressure preferentially removes sensitive cells; persisters and
  resistant cells have reduced kill weights.
- Treatment pressure can induce sensitive -> persister -> resistant leakage
  at fixed toy rates (not inferred from patient data).
- Totals remain research units; nothing here is clinically calibrated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from gbmbert.simulation.model import CELL_STATES, RESEARCH_WARNING

RESISTANCE_STATUSES = ("sensitive", "persister", "resistant")

DEFAULT_RESISTANCE_KILL_MULTIPLIERS = {
    "sensitive": 1.0,
    "persister": 0.35,
    "resistant": 0.1,
}


@dataclass(frozen=True)
class ResistanceParams:
    """Toy resistance-axis parameters (research knobs only)."""

    enabled: bool = False
    initial_fractions: dict[str, float] = field(
        default_factory=lambda: {"sensitive": 0.85, "persister": 0.12, "resistant": 0.03}
    )
    kill_multipliers: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_RESISTANCE_KILL_MULTIPLIERS)
    )
    induction_rate: float = 0.02
    progression_rate: float = 0.01
    assumptions: list[str] = field(
        default_factory=lambda: [
            "Resistance axis is a research construct (sensitive/persister/resistant), not a validated biomarker map.",
            "Induction/progression rates are fixed toy knobs activated under kill pressure.",
            "Subpopulation kill multipliers are scenario research weights, not PK/PD effect sizes.",
        ]
    )

    def normalized_fractions(self) -> dict[str, float]:
        raw = {name: max(0.0, float(self.initial_fractions.get(name, 0.0))) for name in RESISTANCE_STATUSES}
        total = sum(raw.values()) or 1.0
        return {name: value / total for name, value in raw.items()}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResistanceAwareState:
    """Cell-state × resistance-status abundance matrix (toy research units)."""

    abundances: dict[str, dict[str, float]]

    @classmethod
    def from_compartment_totals(
        cls,
        totals: dict[str, float],
        fractions: dict[str, float],
    ) -> ResistanceAwareState:
        abundances = {
            state: {status: float(totals.get(state, 0.0)) * float(fractions.get(status, 0.0)) for status in RESISTANCE_STATUSES}
            for state in CELL_STATES
        }
        return cls(abundances=abundances)

    def clamp_nonnegative(self) -> ResistanceAwareState:
        return ResistanceAwareState(
            abundances={
                state: {status: max(0.0, float(values.get(status, 0.0))) for status in RESISTANCE_STATUSES}
                for state, values in self.abundances.items()
            }
        )

    def compartment_totals(self) -> dict[str, float]:
        return {
            state: sum(float(self.abundances.get(state, {}).get(status, 0.0)) for status in RESISTANCE_STATUSES)
            for state in CELL_STATES
        }

    def resistance_totals(self) -> dict[str, float]:
        return {
            status: sum(float(self.abundances.get(state, {}).get(status, 0.0)) for state in CELL_STATES)
            for status in RESISTANCE_STATUSES
        }

    def total(self) -> float:
        return sum(self.compartment_totals().values())

    def as_flat_dict(self) -> dict[str, float]:
        flat: dict[str, float] = {}
        for state in CELL_STATES:
            for status in RESISTANCE_STATUSES:
                flat[f"{state}_{status}"] = float(self.abundances.get(state, {}).get(status, 0.0))
        flat.update(self.compartment_totals())
        flat.update({f"resistance_{status}": value for status, value in self.resistance_totals().items()})
        flat["total"] = self.total()
        return flat

    def to_dict(self) -> dict[str, Any]:
        return {
            "abundances": self.abundances,
            "compartment_totals": self.compartment_totals(),
            "resistance_totals": self.resistance_totals(),
            "total": self.total(),
            "warning": RESEARCH_WARNING,
        }


def apply_resistance_kill(
    state: ResistanceAwareState,
    *,
    effective_kill: float,
    state_kill_weights: dict[str, float],
    resistance_params: ResistanceParams,
    dt: float,
) -> ResistanceAwareState:
    """Apply status-specific kill and treatment-induced resistance leakage."""

    kill_multipliers = resistance_params.kill_multipliers
    next_abundances: dict[str, dict[str, float]] = {
        state_name: {status: 0.0 for status in RESISTANCE_STATUSES} for state_name in CELL_STATES
    }
    pressure = min(1.0, max(0.0, effective_kill))

    for state_name in CELL_STATES:
        state_weight = float(state_kill_weights.get(state_name, 1.0))
        current = state.abundances.get(state_name, {})
        survivors = {}
        for status in RESISTANCE_STATUSES:
            multiplier = float(kill_multipliers.get(status, 1.0))
            kill_fraction = min(0.95, effective_kill * state_weight * multiplier * dt)
            survivors[status] = max(0.0, float(current.get(status, 0.0)) * (1.0 - kill_fraction))

        # Treatment-pressure-driven leakage: sensitive → persister → resistant.
        induction = survivors["sensitive"] * resistance_params.induction_rate * pressure * dt
        progression = survivors["persister"] * resistance_params.progression_rate * pressure * dt
        next_abundances[state_name]["sensitive"] = survivors["sensitive"] - induction
        next_abundances[state_name]["persister"] = survivors["persister"] + induction - progression
        next_abundances[state_name]["resistant"] = survivors["resistant"] + progression

    return ResistanceAwareState(abundances=next_abundances).clamp_nonnegative()


_DEFAULT_FRACTIONS = {"sensitive": 0.85, "persister": 0.12, "resistant": 0.03}


def load_resistance_params(raw: dict[str, Any] | None) -> ResistanceParams:
    if not raw:
        return ResistanceParams(enabled=False)
    fractions = raw.get("initial_fractions") or {}
    multipliers = raw.get("kill_multipliers") or {}
    return ResistanceParams(
        enabled=bool(raw.get("enabled", True)),
        initial_fractions={
            status: float(fractions.get(status, _DEFAULT_FRACTIONS[status]))
            for status in RESISTANCE_STATUSES
        },
        kill_multipliers={
            status: float(multipliers.get(status, DEFAULT_RESISTANCE_KILL_MULTIPLIERS[status]))
            for status in RESISTANCE_STATUSES
        },
        induction_rate=float(raw.get("induction_rate", 0.02)),
        progression_rate=float(raw.get("progression_rate", 0.01)),
        assumptions=[str(item) for item in raw.get("assumptions") or []]
        or list(ResistanceParams().assumptions),
    )
