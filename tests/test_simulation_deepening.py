"""Tests for Phase 5 post-MVP deepening (graph modulation, resistance, Monte Carlo)."""

from __future__ import annotations

import json
from pathlib import Path

from gbmbert.simulation.cli import fitting_main
from gbmbert.simulation.cli import main as simulation_main
from gbmbert.simulation.cli import monte_carlo_main
from gbmbert.simulation.fitting import FITTING_BOUNDARY, load_fitting_config, run_toy_parameter_fit
from gbmbert.simulation.graph_features import extract_graph_features, resolve_graph_parameter_modulation
from gbmbert.simulation.model import RESEARCH_WARNING, CompartmentState, GrowthParams, step_simulation
from gbmbert.simulation.monte_carlo import load_monte_carlo_config, run_monte_carlo
from gbmbert.simulation.report import format_monte_carlo_markdown, format_simulation_markdown
from gbmbert.simulation.resistance import load_resistance_params
from gbmbert.simulation.scenarios import load_scenario_pack, run_scenario_pack

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PACK = ROOT / "data" / "examples" / "simulation_scenario_pack.json"
GRAPH_SAMPLE = ROOT / "data" / "examples" / "graph_records_sample.jsonl"
RESISTANCE_CONFIG = ROOT / "configs" / "simulation" / "compartment_resistance_v1.json"
MONTE_CARLO_CONFIG = ROOT / "configs" / "simulation" / "monte_carlo_v1.json"
FITTING_CONFIG = ROOT / "configs" / "simulation" / "toy_fitting_v1.json"


def test_graph_relation_modulation_produces_parameter_scales() -> None:
    features = extract_graph_features(GRAPH_SAMPLE)
    modulation = resolve_graph_parameter_modulation(features, use_graph_modulation=True)

    assert features.delivery_modulation >= 1.0
    assert features.kill_modulation > 0.0
    assert features.parameter_provenance
    assert modulation.delivery_multiplier_scale == features.delivery_modulation
    assert "ENHANCES_DELIVERY_OF" in features.relation_type_counts


def test_resistance_axis_shifts_mix_under_kill_pressure() -> None:
    pack = load_scenario_pack(RESISTANCE_CONFIG)
    assert pack.resistance.enabled is True
    report = run_scenario_pack(pack)
    markdown = format_simulation_markdown(report)

    baseline = next(item for item in report.results if item["scenario_id"] == "baseline")
    tmz = next(item for item in report.results if item["scenario_id"] == "tmz")
    assert report.resistance_enabled is True
    assert tmz["final_total"] < baseline["final_total"]
    assert tmz["final_resistance_totals"] is not None
    assert tmz["final_resistance_totals"]["resistant"] >= baseline["final_resistance_totals"]["resistant"]
    assert "resistance:" in markdown.lower() or "Resistance axis enabled" in markdown
    assert RESEARCH_WARNING in markdown


def test_resistance_disabled_matches_legacy_path() -> None:
    resistance = load_resistance_params({"enabled": False})
    initial = CompartmentState(MES=0.3, NPC=0.25, OPC=0.25, AC=0.2)
    params = GrowthParams(
        intrinsic_growth_rate=0.08,
        carrying_capacity=4.0,
        transition_rate=0.02,
        base_kill_rate=0.05,
    )
    plain = step_simulation(initial, params, steps=6, scenario_id="tmz")
    with_flag = step_simulation(
        initial,
        params,
        steps=6,
        scenario_id="tmz",
        resistance_params=resistance,
    )
    assert plain.final_total == with_flag.final_total
    assert with_flag.resistance_enabled is False


def test_monte_carlo_is_seedable_and_reports_bands(tmp_path: Path) -> None:
    config = load_monte_carlo_config(MONTE_CARLO_CONFIG)
    # Tiny offline fixture pack for speed.
    tiny = {
        "name": "mc_tiny",
        "description": "tiny",
        "scenario_config": str(EXAMPLE_PACK.relative_to(ROOT)).replace("\\", "/"),
        "n_samples": 8,
        "seed": 11,
        "parameters": [
            {"name": "intrinsic_growth_rate", "dist": "normal", "mean": 0.08, "std": 0.01, "low": 0.02, "high": 0.16}
        ],
        "assumptions": ["test"],
    }
    config_path = tmp_path / "mc.json"
    config_path.write_text(json.dumps(tiny), encoding="utf-8")
    loaded = load_monte_carlo_config(config_path)
    first = run_monte_carlo(loaded, base_dir=ROOT)
    second = run_monte_carlo(loaded, base_dir=ROOT)
    markdown = format_monte_carlo_markdown(first)

    assert first.n_samples == 8
    assert first.seed == 11
    assert first.scenario_summaries
    assert first.comparison_table
    assert first.sample_comparisons[0]["overrides"] == second.sample_comparisons[0]["overrides"]
    assert "Uncertainty bands" in markdown or "uncertainty" in markdown.lower()
    assert RESEARCH_WARNING in markdown
    assert config.n_samples >= 1


def test_richer_report_includes_comparison_table() -> None:
    pack = load_scenario_pack(EXAMPLE_PACK)
    report = run_scenario_pack(pack, graph_jsonl=GRAPH_SAMPLE, use_graph_modulation=True)
    markdown = format_simulation_markdown(report)
    assert report.comparison_table
    assert "| scenario |" in markdown
    assert "Parameter provenance" in markdown or "Delivery modulation" in markdown


def test_monte_carlo_cli_writes_reports(tmp_path: Path) -> None:
    tiny = {
        "name": "mc_cli",
        "description": "cli",
        "scenario_config": str(EXAMPLE_PACK.relative_to(ROOT)).replace("\\", "/"),
        "n_samples": 5,
        "seed": 3,
        "parameters": [
            {"name": "carrying_capacity", "dist": "fixed", "mean": 4.0}
        ],
    }
    config_path = tmp_path / "mc_cli.json"
    config_path.write_text(json.dumps(tiny), encoding="utf-8")
    md_out = tmp_path / "mc.md"
    json_out = tmp_path / "mc.json"
    # Run from repo root semantics via base_dir inside CLI uses cwd; invoke API path instead for path stability.
    report = run_monte_carlo(load_monte_carlo_config(config_path), base_dir=ROOT)
    assert report.clinical_validity_claimed is False
    exit_code = monte_carlo_main(
        [
            "--config",
            str(config_path),
            "--markdown-output",
            str(md_out),
            "--json-output",
            str(json_out),
        ]
    )
    # CLI resolves scenario_config relative to cwd; rewrite config with absolute scenario path for CLI.
    if exit_code != 0 or not json_out.exists():
        tiny["scenario_config"] = str(EXAMPLE_PACK)
        config_path.write_text(json.dumps(tiny), encoding="utf-8")
        exit_code = monte_carlo_main(
            [
                "--config",
                str(config_path),
                "--markdown-output",
                str(md_out),
                "--json-output",
                str(json_out),
            ]
        )
    assert exit_code == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["n_samples"] == 5
    assert RESEARCH_WARNING in md_out.read_text(encoding="utf-8")


def test_resistance_cli_path(tmp_path: Path) -> None:
    md_out = tmp_path / "res.md"
    json_out = tmp_path / "res.json"
    exit_code = simulation_main(
        [
            "--config",
            str(RESISTANCE_CONFIG),
            "--markdown-output",
            str(md_out),
            "--json-output",
            str(json_out),
        ]
    )
    assert exit_code == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["resistance_enabled"] is True


def test_toy_parameter_fitting_is_not_pk_pd(tmp_path: Path) -> None:
    config = load_fitting_config(FITTING_CONFIG)
    # Shrink draws for speed while keeping the same targets/priors.
    tiny = {
        **config.to_dict(),
        "n_draws": 24,
        "n_keep": 6,
        "scenario_config": str(EXAMPLE_PACK.relative_to(ROOT)).replace("\\", "/"),
    }
    config_path = tmp_path / "fit.json"
    config_path.write_text(json.dumps(tiny), encoding="utf-8")
    report = run_toy_parameter_fit(load_fitting_config(config_path), base_dir=ROOT)
    markdown = report.to_markdown()

    assert report.is_pk_pd is False
    assert report.clinical_validity_claimed is False
    assert report.n_keep >= 1
    assert report.posterior_summary
    assert FITTING_BOUNDARY in markdown
    assert "Not PK/PD" in markdown

    md_out = tmp_path / "fit.md"
    json_out = tmp_path / "fit_out.json"
    tiny["scenario_config"] = str(EXAMPLE_PACK)
    config_path.write_text(json.dumps(tiny), encoding="utf-8")
    exit_code = fitting_main(
        [
            "--config",
            str(config_path),
            "--markdown-output",
            str(md_out),
            "--json-output",
            str(json_out),
        ]
    )
    assert exit_code == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["is_pk_pd"] is False
