"""Tests for Phase 6 research treatment-scenario ranking."""

from __future__ import annotations

import json
from pathlib import Path

from gbmbert.treatment.cli import main as treatment_main
from gbmbert.treatment.engine import BOUNDARY_BANNER, load_treatment_strategy_config, rank_treatment_scenarios
from gbmbert.treatment.report import format_treatment_strategy_markdown

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "treatment" / "strategy_research_v1.json"
GRAPH_SAMPLE = ROOT / "data" / "examples" / "graph_records_sample.jsonl"
EXAMPLE_SIM = ROOT / "data" / "examples" / "simulation_scenario_pack.json"


def test_rank_treatment_scenarios_orders_by_research_score() -> None:
    config = load_treatment_strategy_config(CONFIG)
    # Point at the tiny fixture pack for speed/determinism.
    tiny = {
        **config.to_dict(),
        "simulation_config": str(EXAMPLE_SIM.relative_to(ROOT)).replace("\\", "/"),
    }
    report = rank_treatment_scenarios(
        load_treatment_strategy_config_from_dict(tiny),
        graph_jsonl=GRAPH_SAMPLE,
        base_dir=ROOT,
    )
    markdown = format_treatment_strategy_markdown(report)

    assert report.clinical_validity_claimed is False
    assert report.is_clinical_decision_support is False
    assert report.rankings
    assert report.rankings[0]["rank"] == 1
    assert report.rankings[0]["scenario_id"] == "tmz_fus"
    assert all(row["scenario_id"] != "baseline" for row in report.rankings)
    assert BOUNDARY_BANNER in markdown
    assert "Not clinical decision support" in markdown or "not clinical decision support" in markdown.lower()
    assert "research_score" in markdown


def load_treatment_strategy_config_from_dict(payload: dict) -> object:
    from gbmbert.treatment.engine import RankingWeights, ScenarioResearchKnobs, TreatmentStrategyConfig

    weights = payload.get("weights") or {}
    knobs = payload.get("scenario_knobs") or {}
    return TreatmentStrategyConfig(
        name=str(payload["name"]),
        description=str(payload.get("description") or ""),
        simulation_config=str(payload["simulation_config"]),
        weights=RankingWeights(
            relative_reduction=float(weights.get("relative_reduction", 0.45)),
            final_burden_inverse=float(weights.get("final_burden_inverse", 0.20)),
            delivery_efficiency=float(weights.get("delivery_efficiency", 0.10)),
            evidence_support=float(weights.get("evidence_support", 0.10)),
            toxicity_inverse=float(weights.get("toxicity_inverse", 0.15)),
        ),
        scenario_knobs=ScenarioResearchKnobs(
            intensity_scale=float(knobs.get("intensity_scale", 1.0)),
            schedule_duty_cycle=float(knobs.get("schedule_duty_cycle", 1.0)),
        ),
        assumptions=[str(item) for item in payload.get("assumptions") or []],
        literature_anchors=list(payload.get("literature_anchors") or []),
        exclude_baseline_from_ranking=bool(payload.get("exclude_baseline_from_ranking", True)),
    )


def test_rank_includes_toy_toxicity_and_provenance() -> None:
    config = load_treatment_strategy_config(CONFIG)
    tiny = {
        **config.to_dict(),
        "simulation_config": str(EXAMPLE_SIM.relative_to(ROOT)).replace("\\", "/"),
        "scenario_knobs": {"intensity_scale": 1.5, "schedule_duty_cycle": 0.5},
    }
    report = rank_treatment_scenarios(
        load_treatment_strategy_config_from_dict(tiny),
        base_dir=ROOT,
    )
    assert report.scenario_knobs["intensity_scale"] == 1.5
    assert report.ranking_provenance["patient_eligibility"] is False
    assert report.ranking_provenance["real_dosing_schedule_search"] is False
    assert all("toy_toxicity_burden" in row for row in report.rankings)
    assert "toxicity_inverse" in report.weights
    assert "Not a real dosing schedule" in " ".join(report.assumptions) or any(
        "schedule_duty_cycle" in item for item in report.assumptions
    )


def test_treatment_cli_writes_reports(tmp_path: Path) -> None:
    config_payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    config_payload["simulation_config"] = str(EXAMPLE_SIM)
    config_path = tmp_path / "strategy.json"
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    md_out = tmp_path / "strategy.md"
    json_out = tmp_path / "strategy.json"
    exit_code = treatment_main(
        [
            "--config",
            str(config_path),
            "--graph-jsonl",
            str(GRAPH_SAMPLE),
            "--markdown-output",
            str(md_out),
            "--json-output",
            str(json_out),
        ]
    )
    assert exit_code == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    text = md_out.read_text(encoding="utf-8")
    assert payload["is_clinical_decision_support"] is False
    assert payload["rankings"][0]["scenario_id"] == "tmz_fus"
    assert "Research-use only" in text
