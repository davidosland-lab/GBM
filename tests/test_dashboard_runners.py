"""Tests for Phase 7 live dashboard runners (in-process Python APIs)."""

from __future__ import annotations

import json
from pathlib import Path

from gbmbert.dashboard.app import DASHBOARD_PAGES
from gbmbert.dashboard.runners import (
    run_entity_extraction_live,
    run_graph_inspect_live,
    run_knowledge_graph_explore_live,
    run_literature_search_live,
    run_monte_carlo_live,
    run_prediction_curation_apply_live,
    run_prediction_curation_export_live,
    run_prediction_curation_load_live,
    run_toy_fitting_live,
    run_gold_pack_ops_status_live,
    run_training_artifacts_audit_live,
    run_training_artifacts_browse_live,
    run_training_artifacts_refresh_manifest_live,
    run_treatment_ranking_live,
    run_tumour_simulation_live,
)
from gbmbert.ingest.pubmed import PubMedIngestionError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PACK = ROOT / "data" / "examples" / "simulation_scenario_pack.json"
GRAPH_SAMPLE = ROOT / "data" / "examples" / "graph_records_sample.jsonl"
PUBMED_SAMPLE = ROOT / "data" / "examples" / "pubmed_records_sample.jsonl"
TREATMENT_CONFIG = ROOT / "configs" / "treatment" / "strategy_research_v1.json"
FITTING_CONFIG = ROOT / "configs" / "simulation" / "toy_fitting_v1.json"
MC_CONFIG = ROOT / "configs" / "simulation" / "monte_carlo_v1.json"
REVIEW_QUEUE = ROOT / "data" / "review" / "evidence_smoke_prediction_reviewed_queue.jsonl"
PREDICTIONS = ROOT / "reports" / "training" / "evidence_smoke_fixture" / "evidence_smoke_predictions.jsonl"


def test_all_dashboard_pages_are_live_runners() -> None:
    statuses = {page.key: page.status for page in DASHBOARD_PAGES}
    assert set(statuses.values()) == {"live-runner"}
    assert statuses["knowledge_graph_explorer"] == "live-runner"
    assert statuses["prediction_curation"] == "live-runner"
    assert statuses["training_artifacts"] == "live-runner"
    assert statuses["monte_carlo_results"] == "live-runner"


def test_run_tumour_simulation_live_inline_and_optional_write(tmp_path: Path) -> None:
    result = run_tumour_simulation_live(
        config_path=EXAMPLE_PACK,
        graph_jsonl=GRAPH_SAMPLE,
        use_graph_modulation=True,
        write_reports=True,
        markdown_output=tmp_path / "live.md",
        json_output=tmp_path / "live.json",
        base_dir=ROOT,
    )
    assert result.kind == "tumour_simulation"
    assert result.clinical_validity_claimed is False
    assert "Research-use only" in result.warning
    assert result.payload["comparison_table"]
    assert (tmp_path / "live.md").exists()
    assert (tmp_path / "live.json").exists()


def test_run_treatment_ranking_live_with_knobs(tmp_path: Path) -> None:
    # Point strategy at the tiny fixture via a temp config.
    payload = json.loads(TREATMENT_CONFIG.read_text(encoding="utf-8"))
    payload["simulation_config"] = str(EXAMPLE_PACK.relative_to(ROOT)).replace("\\", "/")
    config_path = tmp_path / "strategy.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_treatment_ranking_live(
        config_path=config_path,
        graph_jsonl=GRAPH_SAMPLE,
        intensity_scale=1.25,
        schedule_duty_cycle=0.75,
        write_reports=False,
        base_dir=ROOT,
    )
    assert result.kind == "treatment_ranking"
    assert result.payload["is_clinical_decision_support"] is False
    assert result.payload["scenario_knobs"]["intensity_scale"] == 1.25
    assert result.payload["ranking_provenance"]["patient_eligibility"] is False
    assert "toy_toxicity_burden" in result.payload["comparison_table"][0]
    assert result.payload["rankings"][0]["rank"] == 1


def test_run_monte_carlo_and_fitting_live(tmp_path: Path) -> None:
    mc_payload = json.loads(MC_CONFIG.read_text(encoding="utf-8"))
    mc_payload["scenario_config"] = str(EXAMPLE_PACK.relative_to(ROOT)).replace("\\", "/")
    mc_payload["n_samples"] = 6
    mc_config = tmp_path / "mc.json"
    mc_config.write_text(json.dumps(mc_payload), encoding="utf-8")

    mc = run_monte_carlo_live(
        config_path=mc_config,
        n_samples_override=4,
        write_reports=False,
        base_dir=ROOT,
    )
    assert mc.kind == "monte_carlo"
    assert mc.payload["n_samples"] == 4
    assert mc.payload["comparison_table"]

    fit = run_toy_fitting_live(
        config_path=FITTING_CONFIG,
        write_reports=True,
        markdown_output=tmp_path / "fit.md",
        json_output=tmp_path / "fit.json",
        base_dir=ROOT,
    )
    assert fit.kind == "toy_parameter_fit"
    assert fit.payload["is_pk_pd"] is False
    assert fit.payload["clinical_validity_claimed"] is False
    assert "Not PK/PD" in fit.markdown
    assert (tmp_path / "fit.md").exists()


def test_literature_search_live_offline_filters_full_jsonl_then_retmax(tmp_path: Path) -> None:
    # Build a fixture where the matching row is beyond a naive first-N truncate.
    local = tmp_path / "pubmed.jsonl"
    rows = [
        {"pmid": "1", "title": "unrelated oncology note", "abstract": "no match here", "journal": "J"},
        {"pmid": "2", "title": "another filler", "abstract": "still no", "journal": "J"},
        {"pmid": "3", "title": "glioblastoma biomarker study", "abstract": "MGMT", "journal": "J"},
    ]
    local.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    offline = run_literature_search_live(
        query="glioblastoma",
        retmax=1,
        offline=True,
        local_jsonl=local,
        write_reports=True,
        markdown_output=tmp_path / "lit.md",
        json_output=tmp_path / "lit.json",
        base_dir=tmp_path,
    )
    assert offline.kind == "literature_search"
    assert offline.payload["mode"] == "offline_local_jsonl"
    assert offline.payload["pmid_count"] == 1
    assert offline.payload["records"][0]["pmid"] == "3"
    assert offline.clinical_validity_claimed is False
    assert "Research-use only" in offline.warning
    assert (tmp_path / "lit.md").exists()

    def _boom(query: str, retmax: int = 10, sort: str = "relevance") -> list[str]:
        raise PubMedIngestionError("simulated NCBI outage")

    fallback = run_literature_search_live(
        query="glioblastoma",
        retmax=3,
        offline=False,
        local_jsonl=PUBMED_SAMPLE,
        search_fn=_boom,
        write_reports=False,
        base_dir=ROOT,
    )
    assert fallback.payload["mode"] == "ncbi_error_fallback_local"
    assert fallback.payload["error"]
    assert fallback.payload["pmid_count"] >= 1


def test_entity_and_graph_live_runners(tmp_path: Path) -> None:
    entities = run_entity_extraction_live(
        text="MGMT methylation predicts temozolomide response in glioblastoma cohorts.",
        pmid="29097493",
        entity_mode="lexicon",
        write_reports=True,
        markdown_output=tmp_path / "ent.md",
        json_output=tmp_path / "ent.json",
        base_dir=ROOT,
    )
    assert entities.kind == "entity_extraction"
    assert entities.payload["mode"] == "lexicon"
    assert entities.payload["entity_count"] >= 1
    assert entities.clinical_validity_claimed is False
    assert all(isinstance(item.get("label"), str) for item in entities.payload["entities"])
    assert "." not in entities.payload["entities"][0]["label"] or entities.payload["entities"][0]["label"].isupper()

    graph = run_graph_inspect_live(
        graph_jsonl=GRAPH_SAMPLE,
        write_reports=False,
        base_dir=ROOT,
    )
    assert graph.kind == "graph_inspect"
    assert graph.payload["mode"] == "local_graph_jsonl"
    assert graph.payload["unique_pmid_count"] >= 1
    assert graph.payload["relation_count"] >= 1


def test_knowledge_graph_explore_live(tmp_path: Path) -> None:
    result = run_knowledge_graph_explore_live(
        graph_jsonl=GRAPH_SAMPLE,
        search="MGMT",
        limit=20,
        write_reports=True,
        markdown_output=tmp_path / "kg.md",
        json_output=tmp_path / "kg.json",
        base_dir=ROOT,
    )
    assert result.kind == "knowledge_graph_explore"
    assert result.payload["mode"] == "local_graph_explorer"
    assert result.payload["edge_count"] >= 1
    assert result.payload["nodes"]
    assert result.payload["edges"]
    edge = result.payload["edges"][0]
    assert "source_pmid_list" in edge
    assert "pubmed_urls" in edge
    assert isinstance(edge["source_pmid_list"], list)
    assert result.payload["quality"]["relation_count"] >= 1
    assert result.clinical_validity_claimed is False
    assert (tmp_path / "kg.md").exists()


def test_prediction_curation_live_load_apply_export(tmp_path: Path) -> None:
    loaded = run_prediction_curation_load_live(
        queue_jsonl=REVIEW_QUEUE,
        status_filter="pending",
        limit=10,
        write_reports=False,
        base_dir=ROOT,
    )
    assert loaded.kind == "prediction_curation_load"
    assert loaded.payload["item_count"] >= 1
    assert loaded.payload["items"]
    item_id = loaded.payload["items"][0]["item_id"]

    out_queue = tmp_path / "reviewed.jsonl"
    applied = run_prediction_curation_apply_live(
        queue_jsonl=REVIEW_QUEUE,
        decisions=[
            {
                "item_id": item_id,
                "review_status": "accepted",
                "review_notes": "dashboard smoke accept",
                "reviewer": "pytest",
            }
        ],
        output_jsonl=out_queue,
        write_reports=False,
        base_dir=ROOT,
    )
    assert applied.kind == "prediction_curation_apply"
    assert applied.payload["applied_count"] == 1
    assert out_queue.exists()

    if PREDICTIONS.exists():
        curated = run_prediction_curation_export_live(
            predictions_jsonl=PREDICTIONS,
            reviewed_queue_jsonl=out_queue,
            output_jsonl=tmp_path / "curated.jsonl",
            fail_on_pending=False,
            write_reports=False,
            base_dir=ROOT,
        )
        assert curated.kind == "prediction_curation_export"
        assert curated.payload["curated_row_count"] >= 0
        assert (tmp_path / "curated.jsonl").exists()


def test_training_artifacts_live_browse_audit_and_manifest(tmp_path: Path) -> None:
    browse = run_training_artifacts_browse_live(write_reports=False, base_dir=ROOT)
    assert browse.kind == "training_artifacts_browse"
    assert browse.payload["mode"] == "training_artifacts_browse"
    assert "governance_report_details" in browse.payload
    assert browse.clinical_validity_claimed is False

    ops = run_gold_pack_ops_status_live(
        write_reports=True,
        markdown_output=tmp_path / "ops.md",
        json_output=tmp_path / "ops.json",
        base_dir=ROOT,
    )
    assert ops.kind == "gold_pack_ops_status"
    assert "task_counts" in ops.payload
    assert "next_actions" in ops.payload
    assert ops.clinical_validity_claimed is False
    assert (tmp_path / "ops.json").exists()

    audit = run_training_artifacts_audit_live(
        write_reports=True,
        markdown_output=tmp_path / "audit.md",
        json_output=tmp_path / "audit.json",
        base_dir=ROOT,
    )
    assert audit.kind == "training_artifacts_audit"
    assert "passed" in audit.payload
    assert (tmp_path / "audit.md").exists()

    try:
        run_training_artifacts_refresh_manifest_live(confirm=False, base_dir=ROOT)
        raise AssertionError("expected confirm gate")
    except ValueError as exc:
        assert "confirm" in str(exc).lower()

    refreshed = run_training_artifacts_refresh_manifest_live(
        confirm=True,
        output_json=tmp_path / "manifest.json",
        markdown_output=tmp_path / "manifest.md",
        base_dir=ROOT,
    )
    assert refreshed.kind == "training_artifacts_refresh_manifest"
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "manifest.md").exists()
