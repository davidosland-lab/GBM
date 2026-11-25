"""Lightweight toy parameter fitting / posterior-style sampling (research stub).

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Hard boundary:
- This is NOT pharmacokinetic/pharmacodynamic (PK/PD) modelling.
- Samples are approximate posterior-style particles against *toy* targets only.
- Not empirically calibrated clinical posteriors; not a digital twin.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gbmbert.simulation.model import RESEARCH_WARNING
from gbmbert.simulation.monte_carlo import ParameterDistribution
from gbmbert.simulation.scenarios import load_scenario_pack, run_scenario_pack

FITTING_BOUNDARY = (
    "Research stub only. Not PK/PD. Not clinically validated posteriors. "
    "Toy-target acceptance sampling for in-silico exploration — "
    "not patient-ready inference."
)


@dataclass(frozen=True)
class FittingConfig:
    name: str
    description: str
    scenario_config: str
    targets: dict[str, float]
    parameters: list[ParameterDistribution]
    n_draws: int = 200
    n_keep: int = 20
    seed: int = 0
    relative_tolerance: float = 0.25
    assumptions: list[str] = field(default_factory=list)
    graph_constraint_weight: float = 0.0
    graph_jsonl: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FittingReport:
    config_name: str
    description: str
    warning: str
    boundary: str
    seed: int
    n_draws: int
    n_accepted: int
    n_keep: int
    relative_tolerance: float
    targets: dict[str, float]
    parameter_specs: list[dict[str, Any]]
    accepted_particles: list[dict[str, Any]]
    posterior_summary: dict[str, dict[str, float]]
    best_particle: dict[str, Any] | None
    assumptions: list[str]
    graph_features: dict[str, Any] | None
    phase: str = "Phase 5 toy parameter-fitting research stub"
    clinical_validity_claimed: bool = False
    is_pk_pd: bool = False
    simulated: list[str] = field(
        default_factory=lambda: [
            "Rejection / approximate posterior-style sampling against toy scenario targets",
            "Optional soft graph-derived constraint term (research weight only)",
            "Particle summaries (mean/std of accepted draws) for research exploration",
        ]
    )
    not_simulated: list[str] = field(
        default_factory=lambda: [
            "Pharmacokinetics / pharmacodynamics (explicitly out of scope)",
            "Spatially resolved biophysics or imaging-constrained geometry",
            "Empirically calibrated clinical posteriors or patient-ready inference",
            "Clinical decision support or treatment prescriptions",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        return format_fitting_markdown(self)


def load_fitting_config(path: str | Path) -> FittingConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    parameters = [
        ParameterDistribution(
            name=str(item["name"]),
            dist=str(item.get("dist", "normal")),
            mean=float(item["mean"]),
            std=float(item.get("std", 0.0)),
            low=float(item["low"]) if item.get("low") is not None else None,
            high=float(item["high"]) if item.get("high") is not None else None,
        )
        for item in payload.get("parameters") or []
    ]
    if not parameters:
        raise ValueError("Fitting config must define at least one parameter distribution")
    targets = {str(key): float(value) for key, value in (payload.get("targets") or {}).items()}
    if not targets:
        raise ValueError("Fitting config must define at least one toy target (scenario_id -> final_total)")
    n_draws = int(payload.get("n_draws", 200))
    n_keep = int(payload.get("n_keep", 20))
    if n_draws < 1 or n_keep < 1:
        raise ValueError("n_draws and n_keep must be at least 1")
    return FittingConfig(
        name=str(payload.get("name") or Path(path).stem),
        description=str(payload.get("description") or ""),
        scenario_config=str(payload["scenario_config"]),
        targets=targets,
        parameters=parameters,
        n_draws=n_draws,
        n_keep=min(n_keep, n_draws),
        seed=int(payload.get("seed", 0)),
        relative_tolerance=float(payload.get("relative_tolerance", 0.25)),
        assumptions=[str(item) for item in payload.get("assumptions") or []],
        graph_constraint_weight=float(payload.get("graph_constraint_weight", 0.0)),
        graph_jsonl=str(payload["graph_jsonl"]) if payload.get("graph_jsonl") else None,
    )


def _relative_error(predicted: float, target: float) -> float:
    scale = max(abs(target), 1e-9)
    return abs(predicted - target) / scale


def _score_particle(
    comparisons: list[dict[str, Any]],
    targets: dict[str, float],
    *,
    graph_features: dict[str, Any] | None,
    graph_constraint_weight: float,
) -> float:
    errors = []
    by_id = {str(row["scenario_id"]): float(row["final_total"]) for row in comparisons}
    for scenario_id, target in targets.items():
        if scenario_id not in by_id:
            return math.inf
        errors.append(_relative_error(by_id[scenario_id], target))
    score = sum(errors) / len(errors)
    if graph_constraint_weight > 0 and graph_features:
        # Soft preference for higher research evidence modulation (toy constraint only).
        evidence = float(graph_features.get("evidence_modulation") or 1.0)
        score += graph_constraint_weight * max(0.0, 1.0 - evidence)
    return score


def run_toy_parameter_fit(
    config: FittingConfig,
    *,
    base_dir: str | Path | None = None,
) -> FittingReport:
    """Approximate posterior-style sampling against toy scenario targets."""

    root = Path(base_dir) if base_dir is not None else Path.cwd()
    pack = load_scenario_pack(root / config.scenario_config)
    rng = random.Random(config.seed)
    graph_path = root / config.graph_jsonl if config.graph_jsonl else None
    particles: list[dict[str, Any]] = []
    graph_features: dict[str, Any] | None = None

    for draw_index in range(config.n_draws):
        overrides = {spec.name: spec.sample(rng) for spec in config.parameters}
        report = run_scenario_pack(
            pack,
            graph_jsonl=graph_path,
            use_graph_modulation=bool(graph_path),
            growth_overrides=overrides,
        )
        if graph_features is None:
            graph_features = report.graph_features
        score = _score_particle(
            report.comparisons,
            config.targets,
            graph_features=report.graph_features,
            graph_constraint_weight=config.graph_constraint_weight,
        )
        particles.append(
            {
                "draw_index": draw_index,
                "overrides": overrides,
                "score": round(score, 6),
                "accepted": score <= config.relative_tolerance,
                "predictions": {
                    str(row["scenario_id"]): round(float(row["final_total"]), 6)
                    for row in report.comparisons
                    if str(row["scenario_id"]) in config.targets
                },
            }
        )

    accepted = [particle for particle in particles if particle["accepted"]]
    accepted.sort(key=lambda row: row["score"])
    # Prefer accepted particles; if none pass tolerance, keep best scores for diagnostics.
    pool = accepted if accepted else sorted(particles, key=lambda row: row["score"])
    kept = pool[: config.n_keep]

    posterior_summary: dict[str, dict[str, float]] = {}
    param_names = [spec.name for spec in config.parameters]
    for name in param_names:
        values = [float(particle["overrides"][name]) for particle in kept if name in particle["overrides"]]
        if not values:
            continue
        mean = sum(values) / len(values)
        var = sum((value - mean) ** 2 for value in values) / len(values)
        posterior_summary[name] = {
            "mean": round(mean, 6),
            "std": round(math.sqrt(var), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "n": float(len(values)),
        }

    assumptions = list(config.assumptions) + [
        FITTING_BOUNDARY,
        f"Toy targets: {config.targets}",
        f"Acceptance relative_tolerance={config.relative_tolerance}; seed={config.seed}.",
        "Accepted particles are research samples, not validated clinical posteriors.",
        "This module is explicitly not PK/PD and not spatially resolved biophysics.",
    ]
    return FittingReport(
        config_name=config.name,
        description=config.description,
        warning=RESEARCH_WARNING,
        boundary=FITTING_BOUNDARY,
        seed=config.seed,
        n_draws=config.n_draws,
        n_accepted=len(accepted),
        n_keep=len(kept),
        relative_tolerance=config.relative_tolerance,
        targets=dict(config.targets),
        parameter_specs=[spec.__dict__ for spec in config.parameters],
        accepted_particles=kept,
        posterior_summary=posterior_summary,
        best_particle=kept[0] if kept else None,
        assumptions=assumptions,
        graph_features=graph_features,
    )


def format_fitting_markdown(report: FittingReport) -> str:
    lines = [
        "# Phase 5 Toy Parameter Fitting (Research Stub)",
        "",
        RESEARCH_WARNING,
        "",
        FITTING_BOUNDARY,
        "",
        f"- Config: `{report.config_name}`",
        f"- Phase: {report.phase}",
        f"- Clinical validity claimed: `{report.clinical_validity_claimed}`",
        f"- Is PK/PD: `{report.is_pk_pd}` (must remain false)",
        f"- Seed: `{report.seed}`",
        f"- Draws / accepted / kept: `{report.n_draws}` / `{report.n_accepted}` / `{report.n_keep}`",
        f"- Relative tolerance: `{report.relative_tolerance}`",
        "",
        report.description,
        "",
        "## Boundary",
        "",
        "### Simulated (research)",
    ]
    lines.extend(f"- {item}" for item in report.simulated)
    lines.extend(["", "### Not simulated / out of scope"])
    lines.extend(f"- {item}" for item in report.not_simulated)
    lines.extend(["", "## Assumptions"])
    lines.extend(f"- {item}" for item in report.assumptions)
    lines.extend(["", "## Toy targets (scenario_id -> final_total)"])
    for key, value in report.targets.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Approximate posterior-style summary (accepted/kept particles)"])
    if report.posterior_summary:
        lines.append("| parameter | mean | std | min | max | n |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for name, stats in report.posterior_summary.items():
            lines.append(
                f"| {name} | {stats['mean']:.4f} | {stats['std']:.4f} | "
                f"{stats['min']:.4f} | {stats['max']:.4f} | {int(stats['n'])} |"
            )
    else:
        lines.append("- none")
    if report.best_particle:
        lines.extend(
            [
                "",
                "## Best particle (lowest toy score)",
                f"- Score: `{report.best_particle.get('score')}`",
                f"- Overrides: `{report.best_particle.get('overrides')}`",
                f"- Predictions: `{report.best_particle.get('predictions')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Reminder",
            "",
            "These particles approximate a research posterior against toy targets only. "
            "They are not PK/PD, not clinical posteriors, and not for diagnosis or treatment selection.",
            "",
        ]
    )
    return "\n".join(lines)


def save_fitting_json(report: FittingReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_fitting_markdown(report: FittingReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_fitting_markdown(report), encoding="utf-8")
    return output
