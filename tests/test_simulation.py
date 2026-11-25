"""Tests for Phase 5 research prototype tumour simulation."""

from __future__ import annotations

import json
from pathlib import Path

from gbmbert.simulation.cli import main as simulation_main
from gbmbert.simulation.graph_features import extract_graph_features
from gbmbert.simulation.model import RESEARCH_WARNING, CompartmentState, GrowthParams, step_simulation
from gbmbert.simulation.report import format_simulation_markdown
from gbmbert.simulation.scenarios import load_scenario_pack, run_scenario_pack

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "simulation" / "compartment_toy_v1.json"
EXAMPLE_PACK = ROOT / "data" / "examples" / "simulation_scenario_pack.json"
GRAPH_SAMPLE = ROOT / "data" / "examples" / "graph_records_sample.jsonl"


def test_step_simulation_reduces_burden_under_kill_pressure() -> None:
    initial = CompartmentState(MES=0.3, NPC=0.25, OPC=0.25, AC=0.2)
    baseline = step_simulation(
        initial,
        GrowthParams(intrinsic_growth_rate=0.08, carrying_capacity=4.0, transition_rate=0.02, base_kill_rate=0.0),
        steps=12,
        scenario_id="baseline",
    )
    treated = step_simulation(
        initial,
        GrowthParams(
            intrinsic_growth_rate=0.08,
            carrying_capacity=4.0,
            transition_rate=0.02,
            base_kill_rate=0.08,
            delivery_multiplier=1.5,
        ),
        steps=12,
        scenario_id="treated",
    )

    assert treated.final_total < baseline.final_total
    assert RESEARCH_WARNING in treated.warning
    assert treated.trajectory[0]["total"] == initial.total()


def test_scenario_pack_comparisons_and_boundary_language() -> None:
    pack = load_scenario_pack(EXAMPLE_PACK)
    report = run_scenario_pack(pack, graph_jsonl=GRAPH_SAMPLE, use_graph_modulation=False)
    markdown = format_simulation_markdown(report)

    assert report.clinical_validity_claimed is False
    assert any(item["scenario_id"] == "tmz_fus" for item in report.comparisons)
    tmz = next(item for item in report.comparisons if item["scenario_id"] == "tmz")
    fus = next(item for item in report.comparisons if item["scenario_id"] == "tmz_fus")
    assert fus["final_total"] <= tmz["final_total"]
    assert RESEARCH_WARNING in markdown
    assert "Not simulated" in markdown
    assert "clinical decision support" in markdown.lower() or "Phase 6" in markdown
    assert report.graph_features is not None
    assert report.graph_features["relation_count"] >= 1
    assert report.comparison_table


def test_graph_modulation_changes_effective_pressure() -> None:
    features = extract_graph_features(GRAPH_SAMPLE)
    pack = load_scenario_pack(EXAMPLE_PACK)
    plain = run_scenario_pack(pack, graph_jsonl=GRAPH_SAMPLE, use_graph_modulation=False)
    modulated = run_scenario_pack(pack, graph_jsonl=GRAPH_SAMPLE, use_graph_modulation=True)

    plain_tmz = next(item for item in plain.results if item["scenario_id"] == "tmz")
    mod_tmz = next(item for item in modulated.results if item["scenario_id"] == "tmz")
    assert features.evidence_modulation != 1.0 or features.mean_evidence_tier is not None
    assert mod_tmz["parameters"]["evidence_modulation"] == features.evidence_modulation
    assert plain_tmz["parameters"]["evidence_modulation"] == 1.0


def test_repo_config_loads_and_cli_writes_reports(tmp_path: Path) -> None:
    assert CONFIG.exists()
    markdown_output = tmp_path / "sim.md"
    json_output = tmp_path / "sim.json"
    exit_code = simulation_main(
        [
            "--config",
            str(EXAMPLE_PACK),
            "--graph-jsonl",
            str(GRAPH_SAMPLE),
            "--markdown-output",
            str(markdown_output),
            "--json-output",
            str(json_output),
        ]
    )
    assert exit_code == 0
    payload = json.loads(json_output.read_text(encoding="utf-8"))
    text = markdown_output.read_text(encoding="utf-8")
    assert payload["pack_name"] == "simulation_scenario_pack_example"
    assert RESEARCH_WARNING in text
    assert payload["clinical_validity_claimed"] is False
