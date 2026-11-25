"""Phase 7 Streamlit research operations console for GBM-AI.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gbmbert.dashboard.paper_links import (
    collect_pmids,
    counts_to_chart_rows,
    render_paper_row,
    render_pmid_open_list,
    with_pubmed_link_column,
)
from gbmbert.dashboard.visuals import (
    DASHBOARD_VISUAL_CSS,
    evidence_chips_html,
    render_highlighted_text,
    render_relation_triples,
    score_bar_html,
)
from gbmbert.dashboard.review_topics import (
    active_review_topic,
    review_topic_for_query_pack,
    review_topic_from_label,
    review_topic_labels,
)
from gbmbert.dashboard.visual_workspace import render_visual_workspace_page
from gbmbert.ingest.query_packs import list_query_packs, load_query_pack

RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)
FALLBACK_PUBMED_JSONL = "data/examples/pubmed_records_sample.jsonl"

_DASHBOARD_CSS = (
    DASHBOARD_VISUAL_CSS
    + """
<style>
section.main .block-container { padding-top: 1.2rem; max-width: 1200px; }
div[data-testid="stMetric"] {
  background: var(--gbm-bg, #f4f6f8);
  border: 1px solid var(--gbm-border, #d7dde5);
  border-radius: 6px;
  padding: 0.55rem 0.75rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--gbm-border, #d7dde5);
}
</style>
"""
)


@dataclass(frozen=True)
class DashboardPage:
    title: str
    key: str
    status: str
    body: str


DASHBOARD_PAGES: tuple[DashboardPage, ...] = (
    DashboardPage(
        title="Visual Workspace",
        key="visual_workspace",
        status="live-runner",
        body=(
            "Relationship-first review of the selected topic: browse articles, presentations, "
            "procedures, symptoms, entities, claims, and artifact lineage from the same visual "
            "surface. Research review only — not a clinical knowledge base."
        ),
    ),
    DashboardPage(
        title="Literature Search",
        key="literature_search",
        status="live-runner",
        body=(
            "Live research runner: offline-local PubMed JSONL browse by default, optional NCBI "
            "E-utilities search when network is available. Not a clinical literature service."
        ),
    ),
    DashboardPage(
        title="Entity Explorer",
        key="entity_explorer",
        status="live-runner",
        body=(
            "Live research runner: offline lexicon entity extraction plus local graph-record "
            "inspect. Optional model NER when available. Not clinically validated NER."
        ),
    ),
    DashboardPage(
        title="Knowledge Graph Explorer",
        key="knowledge_graph_explorer",
        status="live-runner",
        body=(
            "Live research runner: load local graph JSONL, inspect nodes/relations, search/filter, "
            "and view quality metrics in Cypher-less tables. Not a clinical knowledge base."
        ),
    ),
    DashboardPage(
        title="Prediction Curation",
        key="prediction_curation",
        status="live-runner",
        body=(
            "Live research runner: load prediction review / active-learning queues, "
            "accept/correct/reject with notes, write reviewed JSONL, and optionally export "
            "curated evidence. Research curation only — not clinical validation."
        ),
    ),
    DashboardPage(
        title="Training Artifacts",
        key="training_artifacts",
        status="live-runner",
        body=(
            "Live research runner: browse packs/checkpoints/registry/governance summaries, "
            "open local paths, and run safe read-only registry audits or confirmed manifest "
            "refreshes. No surprise GPU training. Not a validated clinical model registry."
        ),
    ),
    DashboardPage(
        title="Tumour Simulator",
        key="tumour_simulator",
        status="live-runner",
        body=(
            "Phase 5 research prototype: run the offline compartment toy model live, or load saved "
            "reports. Not a clinical digital twin; not for treatment selection. Not PK/PD."
        ),
    ),
    DashboardPage(
        title="Treatment Explorer",
        key="treatment_explorer",
        status="live-runner",
        body=(
            "Phase 6 research prototype: run scenario ranking live with toy efficacy/toxicity "
            "trade-offs and optional intensity/schedule *simulation* knobs. "
            "Not CDS. Not prescriptions. Not medical advice. No patient eligibility."
        ),
    ),
    DashboardPage(
        title="Monte Carlo",
        key="monte_carlo_results",
        status="live-runner",
        body=(
            "Phase 5 Monte Carlo research sweeps: run seedable toy parameter draws live, or review "
            "saved uncertainty-band summaries. Not clinical prediction intervals."
        ),
    ),
)


def page_titles() -> list[str]:
    return [page.title for page in DASHBOARD_PAGES]


def page_sidebar_labels() -> list[str]:
    return [f"{page.title} · {page.status}" for page in DASHBOARD_PAGES]


def page_from_sidebar_label(label: str) -> DashboardPage:
    for page in DASHBOARD_PAGES:
        if label == f"{page.title} · {page.status}" or label == page.title:
            return page
    raise KeyError(f"Unknown dashboard page label: {label}")


def _plain_entity_label(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    text = str(value)
    if "." in text and text.split(".", 1)[0] in {"EntityType", "NodeLabel", "RelationType"}:
        return text.split(".", 1)[-1]
    return text


def render_warning(st: object) -> None:
    st.warning(RESEARCH_WARNING)


def _inject_dashboard_styles(st: object) -> None:
    st.markdown(_DASHBOARD_CSS, unsafe_allow_html=True)


def _empty_state(st: object, message: str) -> None:
    st.info(message)


def _metric_row(st: object, metrics: list[tuple[str, object]]) -> None:
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def _render_counts_chart(st: object, counts: dict[str, Any] | None, *, title: str) -> None:
    rows = counts_to_chart_rows(counts)
    if not rows:
        return
    st.caption(title)
    try:
        st.bar_chart(rows, x="label", y="count", use_container_width=True)
    except TypeError:
        # Older Streamlit chart signatures fall back to a simple mapping.
        st.bar_chart({row["label"]: row["count"] for row in rows})


def _dataframe_with_links(
    st: object,
    rows: list[dict[str, Any]],
    *,
    pmid_key: str = "pmid",
    height: int | None = None,
) -> None:
    if not rows:
        _empty_state(st, "No rows to display.")
        return
    enriched = with_pubmed_link_column(rows, pmid_key=pmid_key)
    column_config = None
    if hasattr(st, "column_config"):
        column_config = {
            "pubmed_url": st.column_config.LinkColumn("Open PubMed", display_text="PubMed"),
        }
    kwargs: dict[str, Any] = {"use_container_width": True, "hide_index": True}
    if column_config is not None:
        kwargs["column_config"] = column_config
    if height is not None:
        kwargs["height"] = height
    try:
        st.dataframe(enriched, **kwargs)
    except TypeError:
        st.dataframe(enriched, use_container_width=True)


def _extract_payload_pmids(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    buckets: list[object] = [
        payload.get("pmid"),
        payload.get("pmids"),
        payload.get("literature_anchors"),
        payload.get("source_pmids"),
    ]
    graph = payload.get("graph_features") or payload.get("graph_modulation")
    if isinstance(graph, dict):
        buckets.append(graph.get("feature_rows") or graph.get("rows") or graph)
    elif graph is not None:
        buckets.append(graph)
    for key in ("features", "feature_rows", "modulation_features"):
        if key in payload:
            buckets.append(payload.get(key))
    return collect_pmids(*buckets)


def _render_referenced_papers(
    st: object,
    payload: dict[str, Any] | None,
    *,
    key_prefix: str,
    title: str = "Referenced papers",
) -> None:
    if not isinstance(payload, dict):
        return
    anchors = payload.get("literature_anchors")
    if isinstance(anchors, list) and anchors:
        st.subheader(title)
        for idx, anchor in enumerate(anchors):
            render_paper_row(
                st,
                anchor if isinstance(anchor, dict) else {"pmid": anchor},
                key_prefix=f"{key_prefix}_anchor_{idx}",
                show_abstract=False,
            )
        return
    pmids = _extract_payload_pmids(payload)
    if pmids:
        render_pmid_open_list(st, pmids, key_prefix=key_prefix, title=title)


def _status_badge(st: object, status: str) -> None:
    live_statuses = {"workflow-linked", "report-linked", "prototype-linked", "live-runner"}
    if status == "live-runner":
        st.success(
            "Live research runner available (calls Python APIs in-process). "
            "Still research-use only — not clinically validated."
        )
    elif status in live_statuses:
        st.info(f"Live research surface ({status}). Still research-use only — not clinically validated.")
    else:
        st.caption(f"Scaffold status: {status}")


def render_page(st: object, page: DashboardPage) -> None:
    render_warning(st)
    st.header(page.title)
    st.caption(f"Status: {page.status}")
    _status_badge(st, page.status)
    st.write(page.body)
    if page.key == "visual_workspace":
        render_visual_workspace_page(st)
    if page.key == "literature_search":
        render_literature_search_page(st)
    if page.key == "entity_explorer":
        render_entity_explorer_page(st)
    if page.key == "knowledge_graph_explorer":
        render_knowledge_graph_explorer_page(st)
    if page.key == "tumour_simulator":
        render_tumour_simulator_page(st)
    if page.key == "treatment_explorer":
        render_treatment_explorer_page(st)
    if page.key == "monte_carlo_results":
        render_monte_carlo_page(st)
    if page.key == "prediction_curation":
        render_prediction_curation_page(st)
    if page.key == "training_artifacts":
        render_training_artifacts_page(st)


def _render_saved_markdown_reports(st: object, reports: list[dict[str, object]], *, skip_titles: set[str] | None = None) -> None:
    skipped = skip_titles or set()
    for report in reports:
        if not report.get("exists") or report.get("title") in skipped:
            continue
        title = str(report.get("title") or "Saved report")
        with st.expander(f"Saved report: {title}", expanded=False):
            st.caption(str(report.get("path") or ""))
            st.markdown(str(report.get("content") or ""))


def _load_json_if_present(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "path": str(path)}
    if isinstance(payload, dict):
        return payload
    return {"error": "Expected JSON object", "path": str(path)}


def simulation_dashboard_context(root: str | Path = ".") -> dict[str, object]:
    base = Path(root)
    markdown_paths = {
        "Phase 5 MVP report": base / "reports/simulation/phase5_mvp_example.md",
        "Resistance-axis report": base / "reports/simulation/phase5_resistance_example.md",
        "Monte Carlo report": base / "reports/simulation/phase5_monte_carlo_example.md",
    }
    json_paths = {
        "Phase 5 MVP report": base / "reports/simulation/phase5_mvp_example.json",
        "Resistance-axis report": base / "reports/simulation/phase5_resistance_example.json",
        "Monte Carlo report": base / "reports/simulation/phase5_monte_carlo_example.json",
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
    payloads = {title: _load_json_if_present(path) for title, path in json_paths.items()}
    mvp = payloads.get("Phase 5 MVP report") or {}
    comparison_count = len(mvp.get("comparisons") or []) if isinstance(mvp, dict) else 0
    return {
        "reports": reports,
        "payloads": payloads,
        "available_report_count": sum(1 for item in reports if item["exists"]),
        "scenario_comparison_count": comparison_count,
        "resistance_enabled": bool(isinstance(mvp, dict) and mvp.get("resistance_enabled")),
        "clinical_validity_claimed": bool(isinstance(mvp, dict) and mvp.get("clinical_validity_claimed")),
    }


def treatment_dashboard_context(root: str | Path = ".") -> dict[str, object]:
    base = Path(root)
    markdown_path = base / "reports/treatment/phase6_strategy_example.md"
    json_path = base / "reports/treatment/phase6_strategy_example.json"
    payload = _load_json_if_present(json_path)
    rankings = payload.get("rankings") if isinstance(payload, dict) else None
    return {
        "reports": [
            {
                "title": "Phase 6 strategy ranking",
                "path": str(markdown_path),
                "exists": markdown_path.exists(),
                "content": markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else "",
            }
        ],
        "payload": payload,
        "available_report_count": 1 if markdown_path.exists() or json_path.exists() else 0,
        "ranking_count": len(rankings or []),
        "is_clinical_decision_support": bool(
            isinstance(payload, dict) and payload.get("is_clinical_decision_support")
        ),
        "top_scenario": (rankings[0].get("scenario_id") if rankings else ""),
    }


def monte_carlo_dashboard_context(root: str | Path = ".") -> dict[str, object]:
    base = Path(root)
    markdown_path = base / "reports/simulation/phase5_monte_carlo_example.md"
    json_path = base / "reports/simulation/phase5_monte_carlo_example.json"
    payload = _load_json_if_present(json_path)
    table = payload.get("comparison_table") if isinstance(payload, dict) else None
    return {
        "reports": [
            {
                "title": "Monte Carlo uncertainty bands",
                "path": str(markdown_path),
                "exists": markdown_path.exists(),
                "content": markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else "",
            }
        ],
        "payload": payload,
        "available_report_count": 1 if markdown_path.exists() or json_path.exists() else 0,
        "scenario_count": len(table or []),
        "seed": payload.get("seed") if isinstance(payload, dict) else None,
        "n_samples": payload.get("n_samples") if isinstance(payload, dict) else None,
    }


def render_literature_search_page(st: object) -> None:
    st.warning(
        "Literature search is a research live runner. "
        "Offline mode uses local JSONL fixtures. NCBI mode requires network and NCBI credentials/email. "
        "Not medical advice. Not for clinical decision-making."
    )
    st.subheader("Live literature runner")
    topic = active_review_topic(st)
    offline = st.checkbox("Offline (local JSONL; recommended default)", value=True, key="lit_offline")
    query_pack_names = list_query_packs()
    query_pack_options = ["(custom query)", *query_pack_names]
    default_query_pack = (
        query_pack_options.index(topic.query_pack) if topic.query_pack in query_pack_options else 0
    )
    selected_query_pack = st.selectbox(
        "Saved query pack",
        query_pack_options,
        index=default_query_pack,
        key="lit_query_pack",
    )
    if selected_query_pack == "(custom query)":
        query = st.text_input(
            "Query (filters local rows offline; required for NCBI)",
            value=topic.sample_query,
            key="lit_query_v2",
        )
    else:
        pack = load_query_pack(selected_query_pack)
        st.caption(pack.description)
        query = st.selectbox("Topic query", pack.queries, key="lit_pack_query")
    retmax = st.number_input("Max records", min_value=1, max_value=50, value=8, key="lit_retmax")
    pack_topic = review_topic_for_query_pack(selected_query_pack)
    local_jsonl = st.text_input(
        "Local PubMed JSONL",
        value=pack_topic.pubmed_jsonl if pack_topic else FALLBACK_PUBMED_JSONL,
        key=f"lit_local_{selected_query_pack}",
    )
    write_reports = st.checkbox("Also write reports under reports/dashboard/", value=False, key="lit_write")
    if st.button("Run literature search", key="lit_run"):
        from gbmbert.dashboard.runners import run_literature_search_live

        try:
            with st.spinner("Searching literature (offline local JSONL or NCBI)..."):
                result = run_literature_search_live(
                    query=query,
                    retmax=int(retmax),
                    offline=bool(offline),
                    local_jsonl=local_jsonl,
                    write_reports=write_reports,
                    base_dir=".",
                )
            _show_live_run_result(st, result)
            if result.payload.get("error"):
                st.error(str(result.payload["error"]))
            records = list(result.payload.get("records") or [])
            _metric_row(
                st,
                [
                    ("Mode", result.payload.get("mode") or "—"),
                    ("PMID count", result.payload.get("pmid_count") or 0),
                    ("Records shown", len(records)),
                ],
            )
            st.subheader("Papers")
            st.caption(
                "Evidence cards with PMID badges and open actions. "
                "Inline entity highlighting appears when a record includes span offsets."
            )
            if not records:
                _empty_state(
                    st,
                    "No matching papers. Try a broader query, raise Max records, "
                    "or confirm the local PubMed JSONL path.",
                )
            else:
                for idx, row in enumerate(records):
                    spans = row.get("entities") or row.get("spans") if isinstance(row, dict) else None
                    render_paper_row(
                        st,
                        row,
                        key_prefix=f"lit_card_{idx}",
                        show_abstract=True,
                        spans=spans if isinstance(spans, list) else None,
                    )
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Literature search failed: {exc}")
    else:
        _empty_state(
            st,
            "Run a search to show paper cards with title, authors/year, and PubMed/DOI open buttons. "
            "PubMed links work in the browser even when the dashboard itself is offline.",
        )
    st.subheader("CLI hooks")
    st.caption("Example offline terminal commands (not an app offline status).")
    st.code(
        "gbmbert-run-smoke-baseline --offline\n"
        "gbmbert-artifact-index\n"
        "# Or NCBI-backed query packs via ingest CLIs when network is available.",
        language="powershell",
    )


def render_entity_explorer_page(st: object) -> None:
    topic = active_review_topic(st)
    st.warning(
        "Entity explorer is a research live runner. "
        f"Default extraction uses the offline {topic.label.lower()} lexicon. "
        "Graph inspect uses local graph-record JSONL (no Neo4j required). "
        "Not clinically validated."
    )
    st.subheader("Live entity extraction")
    text = st.text_area("Text to extract", value=topic.sample_text, height=140, key="ent_text_v2")
    entity_mode = st.selectbox("Entity mode", ["lexicon", "model"], index=0, key="ent_mode")
    write_reports = st.checkbox("Also write reports under reports/dashboard/", value=False, key="ent_write")
    source_pmid = st.text_input(
        "Source PMID (for paper open + provenance)",
        value=topic.sample_pmid,
        key="ent_pmid",
    )
    if st.button("Run entity extraction", key="ent_run"):
        from gbmbert.dashboard.runners import run_entity_extraction_live

        try:
            with st.spinner("Extracting entities..."):
                result = run_entity_extraction_live(
                    text=text,
                    pmid=source_pmid or topic.sample_pmid,
                    entity_mode=entity_mode,
                    lexicon_path=topic.lexicon_path,
                    write_reports=write_reports,
                    base_dir=".",
                )
            _show_live_run_result(st, result)
            entities = result.payload.get("entities") or []
            label_counts = result.payload.get("label_counts") or {}
            _metric_row(
                st,
                [
                    ("Entities", result.payload.get("entity_count") or len(entities)),
                    ("Mode", result.payload.get("mode") or entity_mode),
                    ("Source PMID", result.payload.get("pmid") or source_pmid),
                ],
            )
            render_pmid_open_list(
                st,
                [result.payload.get("pmid") or source_pmid],
                key_prefix="ent_source",
                title="Source paper",
                empty_message="No source PMID on this extraction.",
            )
            _render_counts_chart(st, label_counts, title="Entity label counts")
            st.subheader("Highlighted text")
            st.caption(
                "PubTator / displaCy-style inline spans colored by entity type. "
                "Research extraction only — not clinically validated NER."
            )
            source_for_highlight = str(result.payload.get("source_text") or text or "")
            if entities:
                render_highlighted_text(st, source_for_highlight, entities)
            else:
                _empty_state(st, "No entities extracted from this text.")
            st.subheader("Entities")
            if entities:
                st.dataframe(
                    [
                        {
                            "label": _plain_entity_label(item.get("label")),
                            "text": item.get("text"),
                            "start": item.get("start"),
                            "end": item.get("end"),
                            "score": item.get("score") or item.get("confidence") or "",
                        }
                        for item in entities
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                _empty_state(st, "No entity rows to list.")
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Entity extraction failed: {exc}")

    st.subheader("Live graph inspect (local JSONL)")
    graph_jsonl = st.text_input(
        "Graph records JSONL",
        value=topic.graph_jsonl,
        key="ent_graph_v2",
    )
    if st.button("Inspect graph records", key="ent_graph_run"):
        from gbmbert.dashboard.runners import run_graph_inspect_live

        try:
            with st.spinner("Inspecting local graph JSONL..."):
                result = run_graph_inspect_live(
                    graph_jsonl=graph_jsonl,
                    write_reports=write_reports,
                    base_dir=".",
                )
            _show_live_run_result(st, result)
            _metric_row(
                st,
                [
                    ("Unique PMIDs", result.payload.get("unique_pmid_count") or 0),
                    ("Relations", result.payload.get("relation_count") or 0),
                ],
            )
            _render_counts_chart(
                st,
                result.payload.get("label_counts"),
                title="Node label counts",
            )
            _render_counts_chart(
                st,
                result.payload.get("relation_type_counts"),
                title="Relation type counts",
            )
            with st.expander("Raw quality JSON", expanded=False):
                st.json(
                    {
                        "unique_pmid_count": result.payload.get("unique_pmid_count"),
                        "relation_count": result.payload.get("relation_count"),
                        "label_counts": result.payload.get("label_counts"),
                        "relation_type_counts": result.payload.get("relation_type_counts"),
                    }
                )
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Graph inspect failed: {exc}")

    st.subheader("CLI hooks")
    st.code(
        "gbmbert-explorer --sample-data data/examples/graph_records_sample.jsonl --open\n"
        "# Lexicon pipeline / graph quality CLIs remain available for batch runs.",
        language="powershell",
    )


def _chart_comparison_table(st: object, rows: list[dict[str, Any]], *, title: str) -> None:
    if not rows:
        return
    st.subheader(title)
    # Prefer common numeric outcome columns when present.
    preferred = (
        "mean_final_total",
        "median_final_total",
        "relative_reduction_vs_baseline_median",
        "research_score",
        "toy_efficacy",
        "toxicity_inverse",
        "final_total",
    )
    y_key = next((key for key in preferred if key in rows[0]), None)
    label_key = "scenario_id" if "scenario_id" in rows[0] else ("label" if "label" in rows[0] else None)
    if y_key and label_key:
        chart_rows = [
            {"scenario": str(row.get(label_key) or ""), "value": float(row.get(y_key) or 0)}
            for row in rows
            if row.get(label_key) is not None
        ]
        if chart_rows:
            st.caption(f"{y_key} by scenario (research toy metrics)")
            try:
                st.bar_chart(chart_rows, x="scenario", y="value", use_container_width=True)
            except TypeError:
                st.bar_chart({row["scenario"]: row["value"] for row in chart_rows})
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _show_live_run_result(st: object, result: object) -> None:
    st.success(f"Live run complete ({result.kind}). Research-use only.")
    st.caption(result.warning)
    if result.clinical_validity_claimed:
        st.error("Unexpected clinical_validity_claimed=true — treat as a bug.")
    payload = result.payload
    if isinstance(payload, dict) and payload.get("comparison_table"):
        _chart_comparison_table(
            st,
            list(payload["comparison_table"]),
            title="Live comparison",
        )
    if isinstance(payload, dict) and payload.get("posterior_summary"):
        st.subheader("Toy posterior-style summary (not PK/PD)")
        st.json(payload["posterior_summary"])
    if isinstance(payload, dict) and payload.get("ranking_provenance"):
        with st.expander("Ranking provenance", expanded=False):
            st.json(payload["ranking_provenance"])
    # Literature/entity pages render their own paper cards; avoid duplicate PMID lists.
    kind = str(getattr(result, "kind", "") or "")
    if isinstance(payload, dict) and kind not in {
        "literature_search",
        "entity_extraction",
        "knowledge_graph_explore",
        "graph_inspect",
        "prediction_curation_load",
        "prediction_curation_apply",
        "prediction_curation_export",
    }:
        if payload.get("literature_anchors") or payload.get("graph_features") or payload.get(
            "graph_modulation"
        ):
            _render_referenced_papers(
                st,
                payload,
                key_prefix=f"live_{kind or 'run'}",
            )
    if result.wrote_reports:
        st.info(f"Wrote Markdown: `{result.markdown_path}`\n\nWrote JSON: `{result.json_path}`")
    with st.expander("Full Markdown report"):
        st.markdown(result.markdown)


def render_tumour_simulator_page(st: object) -> None:
    st.warning(
        "Phase 5 is a research prototype tumour simulation. "
        "Do not claim clinical validity or patient-ready predictions. "
        "Not PK/PD. Not a spatial biophysical digital twin."
    )
    st.subheader("Live research runner")
    config_choice = st.selectbox(
        "Scenario pack config",
        [
            "configs/simulation/compartment_toy_v1.json",
            "configs/simulation/compartment_resistance_v1.json",
            "data/examples/simulation_scenario_pack.json",
        ],
        key="sim_config",
    )
    use_graph = st.checkbox("Apply graph modulation (research weights)", value=False, key="sim_graph")
    write_reports = st.checkbox("Also write reports under reports/simulation/", value=False, key="sim_write")
    if st.button("Run tumour simulation", key="sim_run"):
        from gbmbert.dashboard.runners import run_tumour_simulation_live

        try:
            result = run_tumour_simulation_live(
                config_path=config_choice,
                graph_jsonl="data/examples/graph_records_sample.jsonl" if use_graph else None,
                use_graph_modulation=use_graph,
                write_reports=write_reports,
                base_dir=".",
            )
            _show_live_run_result(st, result)
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Live simulation failed: {exc}")

    st.subheader("Toy parameter fitting stub (not PK/PD)")
    st.caption(
        "Approximate posterior-style sampling against toy targets only. "
        "Explicitly not pharmacokinetics/pharmacodynamics."
    )
    if st.button("Run toy parameter fit", key="fit_run"):
        from gbmbert.dashboard.runners import run_toy_fitting_live

        try:
            result = run_toy_fitting_live(
                config_path="configs/simulation/toy_fitting_v1.json",
                write_reports=write_reports,
                base_dir=".",
            )
            _show_live_run_result(st, result)
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Toy fitting failed: {exc}")

    context = simulation_dashboard_context()
    st.subheader("Saved reports")
    _metric_row(
        st,
        [
            ("Available simulation reports", context["available_report_count"]),
            ("Scenario comparisons (MVP JSON)", context["scenario_comparison_count"]),
            ("Clinical validity claimed", "yes" if context["clinical_validity_claimed"] else "no"),
        ],
    )
    mvp = context["payloads"].get("Phase 5 MVP report")
    if isinstance(mvp, dict) and mvp.get("comparison_table"):
        _chart_comparison_table(
            st,
            list(mvp["comparison_table"]),
            title="Scenario comparison (from report)",
        )
        _render_referenced_papers(st, mvp, key_prefix="sim_saved", title="Literature anchors")
    elif not context["available_report_count"]:
        _empty_state(st, "No saved simulation reports found under reports/simulation/.")
    _render_saved_markdown_reports(
        st,
        context["reports"],
        skip_titles={"Monte Carlo report"},
    )
    st.subheader("CLI hooks")
    st.code(
        "gbmbert-run-tumour-simulation --config configs/simulation/compartment_toy_v1.json "
        "--graph-jsonl data/examples/graph_records_sample.jsonl --use-graph-modulation "
        "--markdown-output reports/simulation/phase5_mvp_example.md "
        "--json-output reports/simulation/phase5_mvp_example.json\n\n"
        "gbmbert-fit-simulation-parameters --config configs/simulation/toy_fitting_v1.json "
        "--markdown-output reports/simulation/phase5_fitting_example.md "
        "--json-output reports/simulation/phase5_fitting_example.json",
        language="powershell",
    )


def render_treatment_explorer_page(st: object) -> None:
    st.warning(
        "Phase 6 ranks toy simulation scenarios only. "
        "Not CDS. Not prescriptions. Not medical advice. "
        "No patient eligibility. Intensity/schedule knobs are simulation parameters only."
    )
    st.subheader("Live research runner")
    intensity = st.slider(
        "Research intensity_scale (simulation knob — not a real dose)",
        min_value=0.25,
        max_value=2.0,
        value=1.0,
        step=0.25,
        key="tx_intensity",
    )
    duty = st.slider(
        "Research schedule_duty_cycle (simulation knob — not a real schedule)",
        min_value=0.25,
        max_value=1.0,
        value=1.0,
        step=0.25,
        key="tx_duty",
    )
    use_graph = st.checkbox("Apply graph modulation", value=False, key="tx_graph")
    write_reports = st.checkbox("Also write reports under reports/treatment/", value=False, key="tx_write")
    if st.button("Run treatment scenario ranking", key="tx_run"):
        from gbmbert.dashboard.runners import run_treatment_ranking_live

        try:
            result = run_treatment_ranking_live(
                config_path="configs/treatment/strategy_research_v1.json",
                graph_jsonl="data/examples/graph_records_sample.jsonl" if use_graph else None,
                use_graph_modulation=use_graph,
                write_reports=write_reports,
                intensity_scale=float(intensity),
                schedule_duty_cycle=float(duty),
                base_dir=".",
            )
            _show_live_run_result(st, result)
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Live ranking failed: {exc}")

    context = treatment_dashboard_context()
    st.subheader("Saved reports")
    metrics = [
        ("Available treatment reports", context["available_report_count"]),
        ("Ranked scenarios", context["ranking_count"]),
        ("CDS flag", "enabled" if context["is_clinical_decision_support"] else "disabled (required)"),
    ]
    if context["top_scenario"]:
        metrics.append(("Top research scenario id", context["top_scenario"]))
    _metric_row(st, metrics)
    payload = context["payload"]
    if isinstance(payload, dict) and payload.get("comparison_table"):
        _chart_comparison_table(
            st,
            list(payload["comparison_table"]),
            title="Ranking (from report)",
        )
        _render_referenced_papers(st, payload, key_prefix="tx_saved", title="Referenced papers")
    elif not context["available_report_count"]:
        _empty_state(st, "No saved treatment reports found under reports/treatment/.")
    _render_saved_markdown_reports(st, context["reports"])
    st.code(
        "gbmbert-rank-treatment-scenarios --config configs/treatment/strategy_research_v1.json "
        "--graph-jsonl data/examples/graph_records_sample.jsonl "
        "--intensity-scale 1.0 --schedule-duty-cycle 1.0 "
        "--markdown-output reports/treatment/phase6_strategy_example.md "
        "--json-output reports/treatment/phase6_strategy_example.json",
        language="powershell",
    )


def render_monte_carlo_page(st: object) -> None:
    st.warning(
        "Monte Carlo bands are research quantiles over toy parameter draws — "
        "not clinical prediction intervals."
    )
    st.subheader("Live research runner")
    n_samples = st.number_input(
        "n_samples override (keep small for interactive runs)",
        min_value=2,
        max_value=80,
        value=8,
        step=2,
        key="mc_n",
    )
    write_reports = st.checkbox("Also write reports under reports/simulation/", value=False, key="mc_write")
    if st.button("Run Monte Carlo sweep", key="mc_run"):
        from gbmbert.dashboard.runners import run_monte_carlo_live

        try:
            # Prefer the tiny fixture pack via a temp override is avoided; use default MC
            # config but clamp samples for dashboard interactivity.
            result = run_monte_carlo_live(
                config_path="configs/simulation/monte_carlo_v1.json",
                write_reports=write_reports,
                n_samples_override=int(n_samples),
                base_dir=".",
            )
            _show_live_run_result(st, result)
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Live Monte Carlo failed: {exc}")

    context = monte_carlo_dashboard_context()
    st.subheader("Saved reports")
    metrics = [
        ("Available Monte Carlo reports", context["available_report_count"]),
        ("Scenarios summarized", context["scenario_count"]),
    ]
    if context["seed"] is not None:
        metrics.append(("Seed", context["seed"]))
    if context["n_samples"] is not None:
        metrics.append(("Samples", context["n_samples"]))
    _metric_row(st, metrics)
    payload = context["payload"]
    if isinstance(payload, dict) and payload.get("comparison_table"):
        table = list(payload["comparison_table"])
        _chart_comparison_table(st, table, title="Uncertainty-band comparison")
        # Band low/high as a simple range chart when present.
        if table and "band_low" in table[0] and "band_high" in table[0]:
            band_rows = [
                {
                    "scenario": str(row.get("scenario_id") or row.get("label") or ""),
                    "band_low": float(row.get("band_low") or 0),
                    "band_high": float(row.get("band_high") or 0),
                    "median": float(row.get("median_final_total") or 0),
                }
                for row in table
            ]
            st.caption("Research quantile bands (not clinical prediction intervals)")
            try:
                st.line_chart(
                    band_rows,
                    x="scenario",
                    y=["band_low", "median", "band_high"],
                    use_container_width=True,
                )
            except TypeError:
                st.line_chart(
                    {
                        "band_low": [row["band_low"] for row in band_rows],
                        "median": [row["median"] for row in band_rows],
                        "band_high": [row["band_high"] for row in band_rows],
                    }
                )
        _render_referenced_papers(st, payload, key_prefix="mc_saved", title="Referenced papers")
    elif not context["available_report_count"]:
        _empty_state(st, "No saved Monte Carlo reports found under reports/simulation/.")
    _render_saved_markdown_reports(st, context["reports"])
    st.code(
        "gbmbert-run-simulation-monte-carlo --config configs/simulation/monte_carlo_v1.json "
        "--markdown-output reports/simulation/phase5_monte_carlo_example.md "
        "--json-output reports/simulation/phase5_monte_carlo_example.json",
        language="powershell",
    )


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


def render_knowledge_graph_explorer_page(st: object) -> None:
    st.warning(
        "Knowledge Graph Explorer is a research live runner. "
        "Loads local graph-record JSONL (no Neo4j required). "
        "Not a clinical knowledge base."
    )
    st.subheader("Live graph explorer")
    topic = active_review_topic(st)
    graph_jsonl = st.text_input(
        "Graph records JSONL",
        value=topic.graph_jsonl,
        key="kg_graph_v2",
    )
    search = st.text_input("Search (node/relation text)", value="", key="kg_search")
    min_tier = st.number_input("Min evidence tier", min_value=0, max_value=5, value=0, key="kg_tier")
    limit = st.number_input("Max edges", min_value=1, max_value=500, value=50, key="kg_limit")
    write_reports = st.checkbox("Also write reports under reports/dashboard/", value=False, key="kg_write")
    if st.button("Explore graph", key="kg_run"):
        from gbmbert.dashboard.runners import run_knowledge_graph_explore_live

        try:
            with st.spinner("Exploring local graph JSONL..."):
                result = run_knowledge_graph_explore_live(
                    graph_jsonl=graph_jsonl,
                    search=search,
                    min_evidence_tier=int(min_tier),
                    limit=int(limit),
                    write_reports=write_reports,
                    base_dir=".",
                )
            _show_live_run_result(st, result)
            inspection = result.payload.get("inspection") or {}
            counts = inspection.get("counts") if isinstance(inspection, dict) else {}
            quality = result.payload.get("quality") or {}
            if isinstance(counts, dict) or isinstance(quality, dict):
                _metric_row(
                    st,
                    [
                        ("Nodes", (counts or {}).get("nodes", 0)),
                        ("Relationships", (counts or {}).get("relationships", 0)),
                        ("Unique PMIDs", (quality or {}).get("unique_pmid_count", 0)),
                        ("Relations (quality)", (quality or {}).get("relation_count", 0)),
                    ],
                )
            if isinstance(quality, dict):
                st.subheader("Quality metrics")
                _render_counts_chart(st, quality.get("label_counts"), title="Node labels")
                _render_counts_chart(
                    st,
                    quality.get("relation_type_counts"),
                    title="Relation types",
                )
                with st.expander("Raw quality JSON", expanded=False):
                    st.json(
                        {
                            "unique_pmid_count": quality.get("unique_pmid_count"),
                            "relation_count": quality.get("relation_count"),
                            "label_counts": quality.get("label_counts"),
                            "relation_type_counts": quality.get("relation_type_counts"),
                        }
                    )
            nodes = result.payload.get("nodes") or []
            edges = result.payload.get("edges") or []
            st.subheader("Nodes")
            if nodes:
                st.dataframe(nodes, use_container_width=True, hide_index=True)
            else:
                _empty_state(st, "No nodes matched the current filters.")
            st.subheader("Relation triples")
            st.caption(
                "Subject–predicate–object rows with evidence-tier / confidence chrome "
                "(pubmedKB-style). Research graph only — not a clinical knowledge base."
            )
            if edges:
                shown = render_relation_triples(st, edges, limit=int(limit))
                st.caption(f"Showing {shown} of {len(edges)} matched relations.")
                table_rows = []
                edge_pmids: list[str] = []
                for edge in edges:
                    pmid_list = list(edge.get("source_pmid_list") or [])
                    if not pmid_list and edge.get("source_pmids"):
                        pmid_list = collect_pmids(edge.get("source_pmids"))
                    edge_pmids.extend(pmid_list)
                    first = pmid_list[0] if pmid_list else ""
                    table_rows.append(
                        {
                            "type": edge.get("type"),
                            "source": edge.get("source"),
                            "target": edge.get("target"),
                            "evidence_tier": edge.get("evidence_tier"),
                            "confidence": edge.get("confidence"),
                            "source_pmids": edge.get("source_pmids"),
                            "pmid": first,
                        }
                    )
                with st.expander("Relations table", expanded=False):
                    _dataframe_with_links(st, table_rows, pmid_key="pmid")
                render_pmid_open_list(
                    st,
                    edge_pmids,
                    key_prefix="kg_edge_pmids",
                    title="Papers cited on matched relations",
                    empty_message="Matched relations have no source PMIDs.",
                )
            else:
                _empty_state(st, "No relations matched the current filters.")
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Graph explorer failed: {exc}")
    else:
        _empty_state(st, "Explore the graph to see node/relation tables, quality charts, and openable PMIDs.")
    st.subheader("CLI hooks")
    st.code(
        "gbmbert-explorer --sample-data data/examples/graph_records_sample.jsonl --open\n"
        "gbmbert-inspect-graph --json",
        language="powershell",
    )


def render_prediction_curation_page(st: object) -> None:
    st.warning(
        "Prediction curation is a research live runner. "
        "Decisions write reviewed-queue JSONL for research gold packs only. "
        "Not clinical validation."
    )
    st.subheader("Live review queue")
    queue_jsonl = st.text_input(
        "Reviewed / review queue JSONL",
        value="data/review/evidence_smoke_prediction_reviewed_queue.jsonl",
        key="cur_queue",
    )
    status_filter = st.selectbox(
        "Status filter",
        ["pending", "all", "accepted", "corrected", "rejected"],
        index=0,
        key="cur_status",
    )
    limit = st.number_input("Max items to show", min_value=1, max_value=200, value=25, key="cur_limit")
    reviewer = st.text_input("Reviewer id", value="dashboard", key="cur_reviewer")
    output_jsonl = st.text_input(
        "Output reviewed queue JSONL",
        value="data/processed/dashboard_prediction_reviewed_queue.jsonl",
        key="cur_output",
    )
    if st.button("Load review queue", key="cur_load"):
        from gbmbert.dashboard.runners import run_prediction_curation_load_live

        try:
            with st.spinner("Loading review queue..."):
                result = run_prediction_curation_load_live(
                    queue_jsonl=queue_jsonl,
                    status_filter=status_filter,
                    limit=int(limit),
                    write_reports=False,
                    base_dir=".",
                )
            st.session_state["curation_loaded_items"] = result.payload.get("items") or []
            st.session_state["curation_loaded_queue"] = queue_jsonl
            _show_live_run_result(st, result)
            _metric_row(
                st,
                [
                    ("Queue items", result.payload.get("item_count", 0)),
                    ("Pending", result.payload.get("pending_count", 0)),
                    ("Shown", result.payload.get("filtered_count", 0)),
                ],
            )
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Load queue failed: {exc}")

    items = list(st.session_state.get("curation_loaded_items") or [])
    if items:
        st.subheader("Pending / filtered items")
        table_rows = [
            {
                "item_id": item.get("item_id"),
                "pmid": item.get("source_pmid"),
                "tier": item.get("predicted_evidence_tier"),
                "confidence": item.get("confidence"),
                "status": item.get("review_status"),
                "text": (item.get("text") or "")[:120],
            }
            for item in items
        ]
        _dataframe_with_links(st, table_rows, pmid_key="pmid")
        render_pmid_open_list(
            st,
            [item.get("source_pmid") for item in items],
            key_prefix="cur_queue_pmids",
            title="Source papers in queue",
            empty_message="Loaded items have no source PMIDs.",
        )
        item_ids = [str(item.get("item_id") or "") for item in items if item.get("item_id")]
        selected_id = st.selectbox("Item to decide", item_ids, key="cur_item")
        selected_item = next(
            (item for item in items if str(item.get("item_id") or "") == selected_id),
            None,
        )
        if selected_item:
            st.caption("Selected evidence card")
            chips = evidence_chips_html(
                pmid=selected_item.get("source_pmid"),
                evidence_tier=selected_item.get("predicted_evidence_tier"),
                score=selected_item.get("confidence"),
                extra=[selected_item.get("review_status")],
            )
            if chips:
                st.markdown(chips, unsafe_allow_html=True)
            score_html = score_bar_html(selected_item.get("confidence"), label="conf")
            if score_html and not chips:
                st.markdown(score_html, unsafe_allow_html=True)
            entity_spans = selected_item.get("entities") or selected_item.get("spans")
            evidence_text = str(selected_item.get("text") or "")
            if evidence_text and isinstance(entity_spans, list) and entity_spans:
                st.caption("Evidence text with entity spans")
                render_highlighted_text(st, evidence_text, entity_spans)
            elif evidence_text:
                st.write(evidence_text)
            if selected_item.get("source_pmid"):
                render_paper_row(
                    st,
                    {
                        "pmid": selected_item.get("source_pmid"),
                        "title": (selected_item.get("text") or "")[:160],
                        "note": f"status={selected_item.get('review_status')}",
                        "predicted_evidence_tier": selected_item.get("predicted_evidence_tier"),
                        "confidence": selected_item.get("confidence"),
                    },
                    key_prefix="cur_selected",
                    show_abstract=False,
                    evidence_tier=selected_item.get("predicted_evidence_tier"),
                    score=selected_item.get("confidence"),
                )
        decision = st.selectbox(
            "Decision",
            ["accepted", "corrected", "rejected", "pending"],
            index=0,
            key="cur_decision",
        )
        notes = st.text_area("Review notes", value="", key="cur_notes")
        corrected_tier = st.number_input(
            "Corrected evidence tier (required for corrected)",
            min_value=0,
            max_value=5,
            value=0,
            key="cur_corrected_tier",
        )
        if st.button("Apply decision and write queue", key="cur_apply"):
            from gbmbert.dashboard.runners import run_prediction_curation_apply_live

            try:
                payload = {
                    "item_id": selected_id,
                    "review_status": decision,
                    "review_notes": notes,
                    "reviewer": reviewer,
                }
                if decision == "corrected":
                    payload["corrected_evidence_tier"] = int(corrected_tier)
                result = run_prediction_curation_apply_live(
                    queue_jsonl=st.session_state.get("curation_loaded_queue") or queue_jsonl,
                    decisions=[payload],
                    output_jsonl=output_jsonl,
                    write_reports=False,
                    base_dir=".",
                )
                _show_live_run_result(st, result)
                st.info(f"Wrote reviewed queue: `{result.payload.get('output_jsonl')}`")
            except Exception as exc:  # pragma: no cover - Streamlit path
                st.error(f"Apply decision failed: {exc}")
    else:
        _empty_state(st, "Load a review queue to browse items with openable source PMIDs.")

    st.subheader("Optional curated evidence export")
    predictions_jsonl = st.text_input(
        "Source predictions JSONL",
        value="reports/training/evidence_smoke_fixture/evidence_smoke_predictions.jsonl",
        key="cur_pred",
    )
    curated_out = st.text_input(
        "Curated evidence output JSONL",
        value="data/processed/dashboard_curated_evidence.jsonl",
        key="cur_curated_out",
    )
    if st.button("Export curated evidence", key="cur_export"):
        from gbmbert.dashboard.runners import run_prediction_curation_export_live

        try:
            result = run_prediction_curation_export_live(
                predictions_jsonl=predictions_jsonl,
                reviewed_queue_jsonl=output_jsonl,
                output_jsonl=curated_out,
                fail_on_pending=False,
                write_reports=False,
                base_dir=".",
            )
            _show_live_run_result(st, result)
            st.json(
                {
                    "curated_row_count": result.payload.get("curated_row_count"),
                    "accepted_count": result.payload.get("accepted_count"),
                    "corrected_count": result.payload.get("corrected_count"),
                    "rejected_count": result.payload.get("rejected_count"),
                    "pending_count": result.payload.get("pending_count"),
                    "warnings": result.payload.get("warnings"),
                }
            )
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Export curated evidence failed: {exc}")

    context = curation_dashboard_context()
    st.subheader("Saved curation reports")
    metrics = [("Available reports", context["available_report_count"])]
    payloads = context["payloads"]
    if payloads.get("Handoff"):
        metrics.append(("Handoff artifacts", payloads["Handoff"].get("artifact_count", 0)))
    if payloads.get("Workflow"):
        metrics.append(("Workflow warnings", len(payloads["Workflow"].get("warnings", []))))
    if context["latest_run_id"]:
        metrics.append(("Latest curation run", context["latest_run_id"]))
    if context["handoff_validation_valid"] is not None:
        metrics.append(
            ("Handoff validation", "valid" if context["handoff_validation_valid"] else "needs review")
        )
    if context["active_learning_batch_count"]:
        metrics.append(("Active learning batches", context["active_learning_batch_count"]))
    if context["artifact_count"]:
        metrics.append(("Indexed artifacts", context["artifact_count"]))
    _metric_row(st, metrics[:4])
    if len(metrics) > 4:
        _metric_row(st, metrics[4:])
    _render_saved_markdown_reports(st, context["reports"])
    if not context["available_report_count"]:
        _empty_state(st, "No saved curation reports yet.")
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
        "Training label drift": base / "reports/training/training_label_drift.md",
        "Curated fixture import": base / "reports/training/curated_fixture_import.md",
        "Curated provenance diff": base / "reports/training/curated_provenance_diff.md",
        "Gold-pack promotion review": base / "reports/training/gold_pack/gold_pack_promotion_review.md",
        "Gold-pack ops status": base / "reports/training/gold_pack/gold_pack_ops_status.md",
        "Launcher menu check": base / "reports/platform_regression/launcher_menu_check.md",
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
        "Training label drift": base / "reports/training/training_label_drift.json",
        "Curated fixture import": base / "reports/training/curated_fixture_import.json",
        "Curated provenance diff": base / "reports/training/curated_provenance_diff.json",
        "Gold-pack promotion review": base / "reports/training/gold_pack/gold_pack_promotion_review.json",
        "Gold-pack ops status": base / "reports/training/gold_pack/gold_pack_ops_status.json",
        "Launcher menu check": base / "reports/platform_regression/launcher_menu_check.json",
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
    label_drift_warnings = int(payloads.get("Training label drift", {}).get("warning_count") or 0) if isinstance(payloads.get("Training label drift"), dict) else 0
    launcher_menu_safe = payloads.get("Launcher menu check", {}).get("safe") if isinstance(payloads.get("Launcher menu check"), dict) else None
    curated_fixture_safe = payloads.get("Curated fixture import", {}).get("safe") if isinstance(payloads.get("Curated fixture import"), dict) else None
    gold_pack_promotable = payloads.get("Gold-pack promotion review", {}).get("promotable") if isinstance(payloads.get("Gold-pack promotion review"), dict) else None
    ops_payload = payloads.get("Gold-pack ops status") if isinstance(payloads.get("Gold-pack ops status"), dict) else {}
    promotion_payload = (
        payloads.get("Gold-pack promotion review") if isinstance(payloads.get("Gold-pack promotion review"), dict) else {}
    )
    promotion_blockers = list(ops_payload.get("promotion_blockers") or promotion_payload.get("blockers") or [])
    soft_densify_gaps = list(ops_payload.get("soft_densify_gaps") or [])
    next_actions = list(ops_payload.get("next_actions") or [])
    dual_review_pending_total = int(ops_payload.get("dual_review_pending_total") or 0) if ops_payload else None
    active_learning_pending_total = int(ops_payload.get("active_learning_pending_total") or 0) if ops_payload else None
    task_counts = ops_payload.get("task_counts") if isinstance(ops_payload.get("task_counts"), dict) else {}
    governance_details = _training_governance_details(markdown_paths, json_paths, payloads)
    return {
        "reports": reports,
        "payloads": payloads,
        "governance_report_details": governance_details,
        "available_report_count": sum(1 for item in reports if item["exists"]),
        "ready_pack_count": ready_packs,
        "registry_entry_count": registry_entries,
        "registry_audit_passed": registry_passed,
        "relation_config_status": config_status,
        "current_config_passed_count": current_config_passed,
        "current_config_failed_count": current_config_failed,
        "scaffold_config_count": scaffold_config_count,
        "label_drift_warning_count": label_drift_warnings,
        "launcher_menu_safe": launcher_menu_safe,
        "curated_fixture_safe": curated_fixture_safe,
        "gold_pack_promotable": gold_pack_promotable,
        "promotion_blockers": promotion_blockers,
        "soft_densify_gaps": soft_densify_gaps,
        "gold_pack_next_actions": next_actions,
        "dual_review_pending_total": dual_review_pending_total,
        "active_learning_pending_total": active_learning_pending_total,
        "gold_pack_task_counts": task_counts,
    }


def render_training_artifacts_page(st: object) -> None:
    st.warning(
        "Training Artifacts is a research live runner. "
        "Browse packs/checkpoints/registry summaries and run safe read-only audits. "
        "GPU training is not launched from this page. Not clinically validated."
    )
    st.subheader("Live artifact browser")
    if st.button("Refresh browse snapshot", key="train_browse"):
        from gbmbert.dashboard.runners import run_training_artifacts_browse_live

        try:
            result = run_training_artifacts_browse_live(write_reports=False, base_dir=".")
            _show_live_run_result(st, result)
            st.session_state["training_browse_payload"] = result.payload
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Training browse failed: {exc}")

    browse = st.session_state.get("training_browse_payload")
    if not browse:
        from gbmbert.dashboard.runners import run_training_artifacts_browse_live

        try:
            browse = run_training_artifacts_browse_live(write_reports=False, base_dir=".").payload
            st.session_state["training_browse_payload"] = browse
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Training browse failed: {exc}")
            browse = {}

    if browse:
        _metric_row(
            st,
            [
                ("Available reports", browse.get("available_report_count", 0)),
                ("Ready packs", browse.get("ready_pack_count", 0)),
                ("Registry entries", browse.get("registry_entry_count", 0)),
                ("Current config failures", browse.get("current_config_failed_count", 0)),
                ("Scaffold configs", browse.get("scaffold_config_count", 0)),
            ],
        )
        if browse.get("pack_rows"):
            st.subheader("Training packs")
            st.dataframe(browse["pack_rows"], use_container_width=True, hide_index=True)
            _render_counts_chart(
                st,
                {
                    "ready": sum(1 for row in browse["pack_rows"] if row.get("ready")),
                    "not_ready": sum(1 for row in browse["pack_rows"] if not row.get("ready")),
                },
                title="Pack readiness",
            )
        else:
            _empty_state(st, "No training pack rows in the browse snapshot.")
        if browse.get("checkpoints"):
            st.subheader("Checkpoint registry")
            st.dataframe(browse["checkpoints"], use_container_width=True, hide_index=True)
            for row in browse["checkpoints"]:
                path = str(row.get("checkpoint_dir") or "")
                if path:
                    st.caption(f"Open path: `{path}`")
        if browse.get("governance_report_details"):
            st.subheader("Governance details")
            st.dataframe(
                browse["governance_report_details"],
                use_container_width=True,
                hide_index=True,
            )

    st.subheader("Gold-pack ops status (read-only)")
    write_ops = st.checkbox("Write ops status under reports/training/gold_pack/", value=False, key="train_ops_write")
    if st.button("Refresh gold-pack ops status", key="train_ops"):
        from gbmbert.dashboard.runners import run_gold_pack_ops_status_live

        try:
            result = run_gold_pack_ops_status_live(write_reports=write_ops, base_dir=".")
            _show_live_run_result(st, result)
            st.session_state["gold_pack_ops_payload"] = result.payload
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Gold-pack ops status failed: {exc}")

    ops_live = st.session_state.get("gold_pack_ops_payload")
    if isinstance(ops_live, dict) and ops_live:
        _render_gold_pack_ops_panel(st, ops_live)

    st.subheader("Safe read-only registry audit")
    write_audit = st.checkbox("Write audit reports under reports/dashboard/", value=False, key="train_audit_write")
    if st.button("Run registry audit", key="train_audit"):
        from gbmbert.dashboard.runners import run_training_artifacts_audit_live

        try:
            result = run_training_artifacts_audit_live(
                write_reports=write_audit,
                base_dir=".",
            )
            _show_live_run_result(st, result)
            st.metric("Audit passed", "yes" if result.payload.get("passed") else "findings")
            st.metric("Checkpoint count", result.payload.get("checkpoint_count", 0))
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Registry audit failed: {exc}")

    st.subheader("Refresh training manifest (confirmed)")
    confirm_refresh = st.checkbox(
        "I confirm refreshing the dashboard training manifest snapshot (no GPU train)",
        value=False,
        key="train_refresh_confirm",
    )
    if st.button("Refresh dashboard training manifest", key="train_refresh"):
        from gbmbert.dashboard.runners import run_training_artifacts_refresh_manifest_live

        try:
            result = run_training_artifacts_refresh_manifest_live(
                confirm=bool(confirm_refresh),
                base_dir=".",
            )
            _show_live_run_result(st, result)
            st.info(f"Manifest JSON: `{result.json_path}`")
        except Exception as exc:  # pragma: no cover - Streamlit path
            st.error(f"Manifest refresh failed: {exc}")

    context = training_artifacts_dashboard_context()
    st.subheader("Saved training reports")
    if context["relation_config_status"]:
        st.metric("Relation config review", context["relation_config_status"])
    st.metric("Label drift warnings", context["label_drift_warning_count"])
    if context["launcher_menu_safe"] is not None:
        st.metric("Launcher check", "safe" if context["launcher_menu_safe"] else "findings")
    if context["curated_fixture_safe"] is not None:
        st.metric("Curated import", "safe" if context["curated_fixture_safe"] else "findings")
    if context["gold_pack_promotable"] is not None:
        st.metric("Gold-pack promotion", "ready" if context["gold_pack_promotable"] else "blocked")
    if context["dual_review_pending_total"] is not None:
        st.metric("Dual-review pending", context["dual_review_pending_total"])
    if context["active_learning_pending_total"] is not None:
        st.metric("AL pending", context["active_learning_pending_total"])
    if context["registry_audit_passed"] is not None:
        st.metric("Saved registry audit", "passed" if context["registry_audit_passed"] else "findings")
    _render_gold_pack_ops_panel(
        st,
        {
            "promotable": context.get("gold_pack_promotable"),
            "promotion_blockers": context.get("promotion_blockers") or [],
            "soft_densify_gaps": context.get("soft_densify_gaps") or [],
            "next_actions": context.get("gold_pack_next_actions") or [],
            "task_counts": context.get("gold_pack_task_counts") or {},
            "dual_review_pending_total": context.get("dual_review_pending_total"),
            "active_learning_pending_total": context.get("active_learning_pending_total"),
        },
        heading="Saved gold-pack readiness",
    )
    _render_saved_markdown_reports(st, context["reports"])
    if not context["available_report_count"]:
        st.code(
            "gbmbert-build-relation-training-pack\n"
            "gbmbert-review-training-config\n"
            "gbmbert-compare-training-packs\n"
            "gbmbert-audit-model-registry\n"
            "gbmbert-gold-pack-ops-status",
            language="powershell",
        )


def _render_gold_pack_ops_panel(st: object, payload: dict[str, object], *, heading: str = "Promotion readiness") -> None:
    st.subheader(heading)
    st.caption(
        "Hard promotion floors vs soft densify gaps. Research governance only — not clinical validation."
    )
    task_counts = payload.get("task_counts") if isinstance(payload.get("task_counts"), dict) else {}
    if task_counts:
        _metric_row(
            st,
            [
                ("Evidence", task_counts.get("evidence", 0)),
                ("NER", task_counts.get("ner", 0)),
                ("Relation", task_counts.get("relation", 0)),
                ("Dual-review pending", payload.get("dual_review_pending_total") or 0),
                ("AL pending", payload.get("active_learning_pending_total") or 0),
            ],
        )
    blockers = list(payload.get("promotion_blockers") or [])
    if blockers:
        st.error("Hard promotion blockers")
        for blocker in blockers:
            st.write(f"- {blocker}")
    else:
        promotable = payload.get("promotable")
        if promotable is True:
            st.success("Hard promotion floors met (research promotable ≠ clinically validated).")
        elif promotable is False:
            st.warning("Promotion blocked (see blockers or refresh ops status).")
    gaps = list(payload.get("soft_densify_gaps") or [])
    if gaps:
        st.markdown("**Soft densify gaps (non-blocking)**")
        rows = []
        for gap in gaps:
            if isinstance(gap, dict):
                rows.append(
                    {
                        "task": gap.get("task"),
                        "label": gap.get("label"),
                        "count": gap.get("count"),
                        "soft_floor": gap.get("soft_floor"),
                        "delta": gap.get("delta"),
                    }
                )
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
    actions = list(payload.get("next_actions") or [])
    if actions:
        st.markdown("**Next actions**")
        for action in actions:
            st.write(f"- {action}")


def _training_governance_details(
    markdown_paths: dict[str, Path],
    json_paths: dict[str, Path],
    payloads: dict[str, object],
) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []
    for title in sorted(set(markdown_paths) | set(json_paths)):
        markdown_path = markdown_paths.get(title)
        json_path = json_paths.get(title)
        payload = payloads.get(title)
        details.append(
            {
                "title": title,
                "status": _governance_payload_status(payload),
                "markdown_path": str(markdown_path) if markdown_path else "",
                "markdown_exists": bool(markdown_path and markdown_path.exists()),
                "json_path": str(json_path) if json_path else "",
                "json_exists": bool(json_path and json_path.exists()),
            }
        )
    return details


def _governance_payload_status(payload: object) -> str:
    if not isinstance(payload, dict):
        return "missing"
    if payload.get("error"):
        return "invalid"
    for key, passed, failed in (
        ("safe", "safe", "findings"),
        ("passed", "passed", "findings"),
        ("valid", "valid", "needs review"),
        ("ready", "ready", "not ready"),
        ("promotable", "promotion-ready", "blocked"),
    ):
        if key in payload:
            return passed if payload.get(key) else failed
    if payload:
        return "available"
    return "missing"


def render_app() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover - exercised by launcher/runtime.
        raise RuntimeError("Install the dashboard extra with: pip install -e .[dashboard]") from exc

    topic = active_review_topic(st)
    st.set_page_config(page_title=topic.console_title, layout="wide")
    _inject_dashboard_styles(st)
    selected_topic_label = st.sidebar.radio(
        "Review topic",
        review_topic_labels(),
        index=review_topic_labels().index(topic.label),
        key="review_topic_label",
    )
    topic = review_topic_from_label(selected_topic_label)
    st.session_state["review_topic_key"] = topic.key
    st.title(topic.console_title)
    render_warning(st)
    st.caption(
        "Research operations console — live runners for literature → extract → graph → "
        f"curation → training artifacts. Defaults point at the {topic.label.lower()} corpus "
        f"({topic.runbook_path}); switch topics in the sidebar. "
        "Visual chrome follows biomedical NLP demos (PubTator / Gradio HighlightedText / pubmedKB): "
        "type-colored spans, evidence cards, SPO triples, score chips. Clinical-slate + teal accents. "
        "Paper PMIDs open PubMed/DOI in the browser. Not a production clinical UI or hospital CDS."
    )
    selected_label = st.sidebar.radio("Page", page_sidebar_labels())
    selected = page_from_sidebar_label(selected_label)
    render_page(st, selected)


if __name__ == "__main__":
    render_app()
