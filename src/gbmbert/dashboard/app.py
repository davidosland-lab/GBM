"""Phase 7 Streamlit dashboard skeleton for GBM-AI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)


@dataclass(frozen=True)
class DashboardPage:
    title: str
    key: str
    status: str
    body: str


DASHBOARD_PAGES: tuple[DashboardPage, ...] = (
    DashboardPage(
        title="Literature Search",
        key="literature_search",
        status="scaffold",
        body="PubMed query-pack and ClinicalTrials.gov registry ingestion outputs will be reviewed here.",
    ),
    DashboardPage(
        title="Entity Explorer",
        key="entity_explorer",
        status="scaffold",
        body="Extracted entities, normalization aliases, and source PMID coverage will be inspected here.",
    ),
    DashboardPage(
        title="Knowledge Graph Explorer",
        key="knowledge_graph_explorer",
        status="prototype-linked",
        body="Use the local Knowledge Graph Explorer prototype for graph review until this Streamlit page is implemented.",
    ),
    DashboardPage(
        title="Prediction Curation",
        key="prediction_curation",
        status="workflow-linked",
        body="GBM-BERT prediction quality, review queues, curated evidence, overlay graphs, and guard reports are reviewed here.",
    ),
    DashboardPage(
        title="Training Artifacts",
        key="training_artifacts",
        status="workflow-linked",
        body="GBM-BERT training packs, readiness reports, config reviews, model cards, and registry audits are reviewed here.",
    ),
    DashboardPage(
        title="Tumour Simulator",
        key="tumour_simulator",
        status="future",
        body="Simulator controls are intentionally not implemented yet.",
    ),
    DashboardPage(
        title="Treatment Explorer",
        key="treatment_explorer",
        status="future",
        body="Treatment strategy exploration is intentionally not implemented yet and must never recommend treatment for a real patient.",
    ),
    DashboardPage(
        title="Monte Carlo Results",
        key="monte_carlo_results",
        status="future",
        body="Monte Carlo result review is intentionally not implemented yet.",
    ),
)


def page_titles() -> list[str]:
    return [page.title for page in DASHBOARD_PAGES]


def render_warning(st: object) -> None:
    st.warning(RESEARCH_WARNING)


def render_page(st: object, page: DashboardPage) -> None:
    render_warning(st)
    st.header(page.title)
    st.caption(f"Status: {page.status}")
    st.write(page.body)
    if page.key == "knowledge_graph_explorer":
        st.code(
            "gbmbert-explorer --sample-data data/examples/graph_records_sample.jsonl --open",
            language="powershell",
        )
    if page.key == "prediction_curation":
        render_prediction_curation_page(st)
    if page.key == "training_artifacts":
        render_training_artifacts_page(st)


def curation_dashboard_context(root: str | Path = ".") -> dict[str, object]:
    base = Path(root)
    markdown_paths = {
        "Prediction quality": base / "reports/review/curation_smoke_workflow/prediction_quality.md",
        "Review summary": base / "reports/review/curation_smoke_workflow/prediction_review_summary.md",
        "Curated evidence audit": base / "reports/review/curation_smoke_workflow/curated_evidence_audit.md",
        "Overlay diff": base / "reports/review/curation_smoke_workflow/evidence_overlay_diff.md",
        "Handoff manifest": base / "data/processed/curation_handoff_bundle/curation_handoff_bundle.md",
        "Curation run browser": base / "reports/review/curation_run_browser.md",
        "Active learning batch status": base / "reports/review/curation_regression_pack/active_learning_batch_status.md",
        "Artifact detail": base / "reports/artifact_detail.md",
    }
    json_paths = {
        "Workflow": base / "reports/review/curation_smoke_workflow/curation_smoke_workflow.json",
        "Handoff": base / "data/processed/curation_handoff_bundle/curation_handoff_bundle.json",
        "Handoff validation": base / "reports/review/curation_regression_pack/curation_handoff_validation.json",
        "Regression pack": base / "reports/review/curation_regression_pack/curation_regression_pack.json",
        "Active learning batches": base / "reports/review/curation_regression_pack/active_learning_batches.json",
        "Active learning batch status": base / "reports/review/curation_regression_pack/active_learning_batch_status.json",
        "Run registry": base / "reports/review/curation_run_registry.json",
        "Artifact index": base / "reports/artifact_index.json",
    }
    reports = [
        {
            "title": title,
            "path": str(path),
            "exists": path.exists(),
            "content": path.read_text(encoding="utf-8") if path.exists() else "",
        }
        for title, path in markdown_paths.items()
    ]
    payloads = {}
    for title, path in json_paths.items():
        if path.exists():
            try:
                payloads[title] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payloads[title] = {"error": "Invalid JSON", "path": str(path)}
    latest_run = ""
    if isinstance(payloads.get("Run registry"), dict):
        entries = payloads["Run registry"].get("entries", [])
        if entries:
            latest_run = str(entries[-1].get("run_id") or "")
    validation_valid = None
    if isinstance(payloads.get("Handoff validation"), dict):
        validation_valid = payloads["Handoff validation"].get("valid")
    artifact_count = 0
    if isinstance(payloads.get("Artifact index"), dict):
        artifact_count = int(payloads["Artifact index"].get("artifact_count") or 0)
    batch_count = 0
    if isinstance(payloads.get("Active learning batches"), dict):
        batch_count = int(payloads["Active learning batches"].get("batch_count") or 0)
    if isinstance(payloads.get("Active learning batch status"), dict):
        batch_count = int(payloads["Active learning batch status"].get("batch_count") or batch_count)
    return {
        "reports": reports,
        "payloads": payloads,
        "available_report_count": sum(1 for item in reports if item["exists"]),
        "latest_run_id": latest_run,
        "handoff_validation_valid": validation_valid,
        "artifact_count": artifact_count,
        "active_learning_batch_count": batch_count,
    }


def render_prediction_curation_page(st: object) -> None:
    context = curation_dashboard_context()
    st.metric("Available reports", context["available_report_count"])
    payloads = context["payloads"]
    if payloads.get("Handoff"):
        st.metric("Handoff artifacts", payloads["Handoff"].get("artifact_count", 0))
    if payloads.get("Workflow"):
        st.metric("Workflow warnings", len(payloads["Workflow"].get("warnings", [])))
    if context["latest_run_id"]:
        st.metric("Latest curation run", context["latest_run_id"])
    if context["handoff_validation_valid"] is not None:
        st.metric("Handoff validation", "valid" if context["handoff_validation_valid"] else "needs review")
    if context["active_learning_batch_count"]:
        st.metric("Active learning batches", context["active_learning_batch_count"])
    if context["artifact_count"]:
        st.metric("Indexed artifacts", context["artifact_count"])
    for report in context["reports"]:
        if report["exists"]:
            st.subheader(report["title"])
            st.caption(report["path"])
            st.markdown(report["content"])
    if not context["available_report_count"]:
        st.code("gbmbert-run-curation-smoke-workflow\ngbmbert-build-curation-handoff", language="powershell")


def training_artifacts_dashboard_context(root: str | Path = ".") -> dict[str, object]:
    base = Path(root)
    markdown_paths = {
        "Evidence pack": base / "reports/training/evidence_pack/evidence_training_pack.md",
        "Relation pack": base / "reports/training/relation_pack/relation_training_pack.md",
        "Gold pack": base / "reports/training/gold_pack/gold_training_pack.md",
        "Relation config review": base / "reports/training/relation_training_config_review.md",
        "Training pack comparison": base / "reports/training/training_pack_comparison.md",
        "Training config suite": base / "reports/training/training_config_suite_review.md",
        "Model registry audit": base / "reports/training/model_registry_audit.md",
        "Evidence smoke model card": base / "reports/training/evidence_smoke_fixture/evidence_smoke_model_card.md",
    }
    json_paths = {
        "Evidence pack": base / "reports/training/evidence_pack/evidence_training_pack.json",
        "Relation pack": base / "reports/training/relation_pack/relation_training_pack.json",
        "Gold pack": base / "reports/training/gold_pack/gold_training_pack.json",
        "Evidence readiness": base / "reports/training/evidence_pack/evidence_training_pack_readiness.json",
        "Relation readiness": base / "reports/training/relation_pack/relation_training_pack_readiness.json",
        "Gold readiness": base / "reports/training/gold_pack/training_readiness.json",
        "Relation config review": base / "reports/training/relation_training_config_review.json",
        "Training pack comparison": base / "reports/training/training_pack_comparison.json",
        "Training config suite": base / "reports/training/training_config_suite_review.json",
        "Model registry audit": base / "reports/training/model_registry_audit.json",
        "Checkpoint registry": base / "models/checkpoint_registry.json",
    }
    reports = [
        {
            "title": title,
            "path": str(path),
            "exists": path.exists(),
            "content": path.read_text(encoding="utf-8") if path.exists() else "",
        }
        for title, path in markdown_paths.items()
    ]
    payloads = {}
    for title, path in json_paths.items():
        if path.exists():
            try:
                payloads[title] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payloads[title] = {"error": "Invalid JSON", "path": str(path)}
    ready_packs = sum(
        1
        for title in ("Evidence pack", "Relation pack", "Gold pack")
        if isinstance(payloads.get(title), dict) and payloads[title].get("ready") is True
    )
    registry_entries = 0
    if isinstance(payloads.get("Checkpoint registry"), dict):
        registry_entries = len(payloads["Checkpoint registry"].get("checkpoints", []))
    registry_passed = None
    if isinstance(payloads.get("Model registry audit"), dict):
        registry_passed = payloads["Model registry audit"].get("passed")
    config_status = ""
    if isinstance(payloads.get("Relation config review"), dict):
        config_status = str(payloads["Relation config review"].get("status") or "")
    current_config_passed = 0
    current_config_failed = 0
    scaffold_config_count = 0
    if isinstance(payloads.get("Training config suite"), dict):
        suite = payloads["Training config suite"]
        current_config_passed = int(suite.get("passed_count") or 0)
        current_config_failed = int(suite.get("blocking_failed_count") or suite.get("failed_count") or 0)
        scaffold_config_count = int(suite.get("scaffold_count") or 0)
    return {
        "reports": reports,
        "payloads": payloads,
        "available_report_count": sum(1 for item in reports if item["exists"]),
        "ready_pack_count": ready_packs,
        "registry_entry_count": registry_entries,
        "registry_audit_passed": registry_passed,
        "relation_config_status": config_status,
        "current_config_passed_count": current_config_passed,
        "current_config_failed_count": current_config_failed,
        "scaffold_config_count": scaffold_config_count,
    }


def render_training_artifacts_page(st: object) -> None:
    context = training_artifacts_dashboard_context()
    st.metric("Available reports", context["available_report_count"])
    st.metric("Ready packs", context["ready_pack_count"])
    if context["relation_config_status"]:
        st.metric("Relation config review", context["relation_config_status"])
    st.metric("Current config failures", context["current_config_failed_count"])
    st.metric("Scaffold configs", context["scaffold_config_count"])
    if context["registry_entry_count"]:
        st.metric("Registry entries", context["registry_entry_count"])
    if context["registry_audit_passed"] is not None:
        st.metric("Registry audit", "passed" if context["registry_audit_passed"] else "findings")
    for report in context["reports"]:
        if report["exists"]:
            st.subheader(report["title"])
            st.caption(report["path"])
            st.markdown(report["content"])
    if not context["available_report_count"]:
        st.code(
            "gbmbert-build-relation-training-pack\n"
            "gbmbert-review-training-config\n"
            "gbmbert-compare-training-packs\n"
            "gbmbert-audit-model-registry",
            language="powershell",
        )


def render_app() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover - exercised by launcher/runtime.
        raise RuntimeError("Install the dashboard extra with: pip install -e .[dashboard]") from exc

    st.set_page_config(page_title="GBM-AI Dashboard", layout="wide")
    st.title("GBM-AI Dashboard")
    render_warning(st)
    selected_title = st.sidebar.radio("Page", page_titles())
    selected = next(page for page in DASHBOARD_PAGES if page.title == selected_title)
    render_page(st, selected)


if __name__ == "__main__":
    render_app()
