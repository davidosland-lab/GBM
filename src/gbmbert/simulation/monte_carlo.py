"""Seedable Monte Carlo parameter sweeps for Phase 5 toy simulation.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Samples growth-parameter uncertainty and aggregates outcome distributions.
This is an offline research prototype, not a clinical uncertainty analysis.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gbmbert.simulation.model import RESEARCH_WARNING
from gbmbert.simulation.scenarios import ScenarioPack, ScenarioRunReport, load_scenario_pack, run_scenario_pack


@dataclass(frozen=True)
class ParameterDistribution:
    name: str
    dist: str  # fixed | uniform | normal | lognormal
    mean: float
    std: float = 0.0
    low: float | None = None
    high: float | None = None

    def sample(self, rng: random.Random) -> float:
        if self.dist == "fixed":
            return self.mean
        if self.dist == "uniform":
            low = self.low if self.low is not None else self.mean - self.std
            high = self.high if self.high is not None else self.mean + self.std
            if high < low:
                low, high = high, low
            return rng.uniform(low, high)
        if self.dist == "normal":
            value = rng.gauss(self.mean, self.std if self.std > 0 else 1e-9)
        elif self.dist == "lognormal":
            # mean/std interpreted on the natural scale; convert approximately.
            sigma = self.std if self.std > 0 else 1e-9
            mu = math.log(max(self.mean, 1e-12)) - 0.5 * math.log(1.0 + (sigma / max(self.mean, 1e-12)) ** 2)
            value = rng.lognormvariate(mu, math.sqrt(math.log(1.0 + (sigma / max(self.mean, 1e-12)) ** 2)))
        else:
            raise ValueError(f"Unsupported distribution: {self.dist}")
        if self.low is not None:
            value = max(self.low, value)
        if self.high is not None:
            value = min(self.high, value)
        return value


@dataclass(frozen=True)
class MonteCarloConfig:
    name: str
    description: str
    scenario_config: str
    n_samples: int
    seed: int
    parameters: list[ParameterDistribution]
    assumptions: list[str] = field(default_factory=list)
    quantiles: list[float] = field(default_factory=lambda: [0.05, 0.5, 0.95])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MonteCarloReport:
    config_name: str
    description: str
    warning: str
    seed: int
    n_samples: int
    assumptions: list[str]
    parameter_specs: list[dict[str, Any]]
    scenario_summaries: list[dict[str, Any]]
    comparison_table: list[dict[str, Any]]
    sample_comparisons: list[dict[str, Any]]
    graph_features: dict[str, Any] | None
    phase: str = "Phase 5 Monte Carlo research prototype"
    clinical_validity_claimed: bool = False
    simulated: list[str] = field(
        default_factory=lambda: [
            "Seedable Monte Carlo sweeps over toy growth parameters",
            "Per-scenario outcome distributions (final_total)",
            "Quantile / uncertainty-band summaries for research comparison",
        ]
    )
    not_simulated: list[str] = field(
        default_factory=lambda: [
            "Clinical uncertainty quantification or validated posterior inference",
            "Patient-specific predictive intervals",
            "Treatment prescriptions or clinical decision support",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_monte_carlo_config(path: str | Path) -> MonteCarloConfig:
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
        raise ValueError("Monte Carlo config must define at least one parameter distribution")
    n_samples = int(payload.get("n_samples", 50))
    if n_samples < 1:
        raise ValueError("n_samples must be at least 1")
    return MonteCarloConfig(
        name=str(payload.get("name") or Path(path).stem),
        description=str(payload.get("description") or ""),
        scenario_config=str(payload["scenario_config"]),
        n_samples=n_samples,
        seed=int(payload.get("seed", 0)),
        parameters=parameters,
        assumptions=[str(item) for item in payload.get("assumptions") or []],
        quantiles=[float(q) for q in payload.get("quantiles") or [0.05, 0.5, 0.95]],
    )


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def run_monte_carlo(
    config: MonteCarloConfig,
    *,
    scenario_pack: ScenarioPack | None = None,
    graph_jsonl: str | Path | None = None,
    use_graph_modulation: bool = False,
    base_dir: str | Path | None = None,
) -> MonteCarloReport:
    """Run seedable Monte Carlo sweeps and aggregate scenario outcome distributions."""

    root = Path(base_dir) if base_dir is not None else Path.cwd()
    pack = scenario_pack or load_scenario_pack(root / config.scenario_config)
    rng = random.Random(config.seed)

    per_scenario_totals: dict[str, list[float]] = {}
    per_scenario_labels: dict[str, str] = {}
    sample_comparisons: list[dict[str, Any]] = []
    graph_features: dict[str, Any] | None = None

    for sample_index in range(config.n_samples):
        overrides = {spec.name: spec.sample(rng) for spec in config.parameters}
        report: ScenarioRunReport = run_scenario_pack(
            pack,
            graph_jsonl=graph_jsonl,
            use_graph_modulation=use_graph_modulation,
            growth_overrides=overrides,
        )
        if graph_features is None:
            graph_features = report.graph_features
        sample_row: dict[str, Any] = {"sample_index": sample_index, "overrides": overrides}
        for comparison in report.comparisons:
            scenario_id = str(comparison["scenario_id"])
            per_scenario_labels[scenario_id] = str(comparison["label"])
            per_scenario_totals.setdefault(scenario_id, []).append(float(comparison["final_total"]))
            sample_row[scenario_id] = float(comparison["final_total"])
        sample_comparisons.append(sample_row)

    scenario_summaries = []
    comparison_table = []
    baseline_id = "baseline" if "baseline" in per_scenario_totals else next(iter(per_scenario_totals), "")
    baseline_medians = per_scenario_totals.get(baseline_id, [])
    baseline_median = _quantile(baseline_medians, 0.5) if baseline_medians else 0.0

    for scenario_id, totals in per_scenario_totals.items():
        quantiles = {f"q{int(q * 100):02d}": _quantile(totals, q) for q in config.quantiles}
        mean_total = sum(totals) / len(totals)
        summary = {
            "scenario_id": scenario_id,
            "label": per_scenario_labels.get(scenario_id, scenario_id),
            "n": len(totals),
            "mean_final_total": mean_total,
            "std_final_total": (sum((value - mean_total) ** 2 for value in totals) / len(totals)) ** 0.5,
            "quantiles": quantiles,
            "uncertainty_band": {
                "low": quantiles.get("q05", _quantile(totals, 0.05)),
                "median": quantiles.get("q50", _quantile(totals, 0.5)),
                "high": quantiles.get("q95", _quantile(totals, 0.95)),
            },
        }
        scenario_summaries.append(summary)
        median = summary["uncertainty_band"]["median"]
        comparison_table.append(
            {
                "scenario_id": scenario_id,
                "label": summary["label"],
                "median_final_total": round(median, 4),
                "band_low": round(summary["uncertainty_band"]["low"], 4),
                "band_high": round(summary["uncertainty_band"]["high"], 4),
                "mean_final_total": round(mean_total, 4),
                "relative_reduction_vs_baseline_median": round(
                    ((baseline_median - median) / baseline_median) if baseline_median else 0.0,
                    4,
                ),
            }
        )

    assumptions = list(config.assumptions) + [
        f"Monte Carlo seed={config.seed}, n_samples={config.n_samples} (research prototype).",
        "Parameter draws are independent toy distributions, not empirically fitted posteriors.",
        "Uncertainty bands are sample quantiles of in-silico outcomes only.",
    ]
    return MonteCarloReport(
        config_name=config.name,
        description=config.description,
        warning=RESEARCH_WARNING,
        seed=config.seed,
        n_samples=config.n_samples,
        assumptions=assumptions,
        parameter_specs=[spec.__dict__ for spec in config.parameters],
        scenario_summaries=scenario_summaries,
        comparison_table=comparison_table,
        sample_comparisons=sample_comparisons[:20],
        graph_features=graph_features,
    )
