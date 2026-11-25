"""Live research runners for the Phase 7 Streamlit dashboard.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

Calls existing Python APIs (no shell hacks). Optional report writes reuse
the same Markdown/JSON writers as the CLIs.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from gbmbert.annotation.schema import Paper
from gbmbert.extraction.pipeline import BiomedicalNERPipeline, paper_to_source_text
from gbmbert.ingest.pubmed import PubMedIngestionError, fetch_pubmed_records, search_pubmed
from gbmbert.knowledge_graph.explorer import GraphExplorerService
from gbmbert.knowledge_graph.quality import analyze_graph_records_jsonl, format_quality_report_markdown
from gbmbert.knowledge_graph.schema import EvidenceTier, NodeLabel, RelationType
from gbmbert.pipeline import create_lexicon_ner_pipeline
from gbmbert.simulation.fitting import (
    load_fitting_config,
    run_toy_parameter_fit,
    save_fitting_json,
    save_fitting_markdown,
)
from gbmbert.simulation.monte_carlo import load_monte_carlo_config, run_monte_carlo
from gbmbert.simulation.report import (
    format_monte_carlo_markdown,
    format_simulation_markdown,
    save_monte_carlo_json,
    save_monte_carlo_markdown,
    save_simulation_json,
    save_simulation_markdown,
)
from gbmbert.simulation.scenarios import load_scenario_pack, run_scenario_pack
from gbmbert.training.prediction_curation import (
    export_curated_evidence,
    format_curated_evidence_report_markdown,
    format_prediction_review_summary_markdown,
    load_prediction_review_queue_jsonl,
    save_prediction_review_queue_jsonl,
    summarize_prediction_review_queue,
)
from gbmbert.training.registry_audit import (
    audit_checkpoint_registry,
    format_registry_audit_markdown,
    save_registry_audit_json,
    save_registry_audit_markdown,
)
from gbmbert.treatment.engine import load_treatment_strategy_config, rank_treatment_scenarios
from gbmbert.treatment.report import (
    format_treatment_strategy_markdown,
    save_treatment_strategy_json,
    save_treatment_strategy_markdown,
)

RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)


@dataclass(frozen=True)
class LiveRunResult:
    kind: str
    payload: dict[str, Any]
    markdown: str
    wrote_reports: bool
    markdown_path: str | None
    json_path: str | None
    clinical_validity_claimed: bool
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "payload": self.payload,
            "markdown": self.markdown,
            "wrote_reports": self.wrote_reports,
            "markdown_path": self.markdown_path,
            "json_path": self.json_path,
            "clinical_validity_claimed": self.clinical_validity_claimed,
            "warning": self.warning,
        }


def _resolve(path: str | Path | None, base_dir: Path) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def run_tumour_simulation_live(
    *,
    config_path: str | Path,
    graph_jsonl: str | Path | None = None,
    use_graph_modulation: bool = False,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    root = Path(base_dir).resolve()
    config = _resolve(config_path, root)
    if config is None or not config.exists():
        raise FileNotFoundError(f"Simulation config not found: {config_path}")
    pack = load_scenario_pack(config)
    report = run_scenario_pack(
        pack,
        graph_jsonl=_resolve(graph_jsonl, root),
        use_graph_modulation=use_graph_modulation,
    )
    md_path = _resolve(markdown_output, root) if write_reports else None
    json_path = _resolve(json_output, root) if write_reports else None
    if write_reports:
        if md_path is None:
            md_path = root / "reports/simulation/dashboard_live_simulation.md"
        if json_path is None:
            json_path = root / "reports/simulation/dashboard_live_simulation.json"
        save_simulation_markdown(report, md_path)
        save_simulation_json(report, json_path)
    return LiveRunResult(
        kind="tumour_simulation",
        payload=report.to_dict(),
        markdown=format_simulation_markdown(report),
        wrote_reports=write_reports,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=report.clinical_validity_claimed,
    )


def run_monte_carlo_live(
    *,
    config_path: str | Path,
    graph_jsonl: str | Path | None = None,
    use_graph_modulation: bool = False,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
    n_samples_override: int | None = None,
) -> LiveRunResult:
    root = Path(base_dir).resolve()
    config_file = _resolve(config_path, root)
    if config_file is None or not config_file.exists():
        raise FileNotFoundError(f"Monte Carlo config not found: {config_path}")
    config = load_monte_carlo_config(config_file)
    if n_samples_override is not None:
        if n_samples_override < 1:
            raise ValueError("n_samples_override must be at least 1")
        config = type(config)(
            name=config.name,
            description=config.description,
            scenario_config=config.scenario_config,
            n_samples=int(n_samples_override),
            seed=config.seed,
            parameters=list(config.parameters),
            assumptions=list(config.assumptions),
            quantiles=list(config.quantiles),
        )
    report = run_monte_carlo(
        config,
        graph_jsonl=_resolve(graph_jsonl, root),
        use_graph_modulation=use_graph_modulation,
        base_dir=root,
    )
    md_path = _resolve(markdown_output, root) if write_reports else None
    json_path = _resolve(json_output, root) if write_reports else None
    if write_reports:
        if md_path is None:
            md_path = root / "reports/simulation/dashboard_live_monte_carlo.md"
        if json_path is None:
            json_path = root / "reports/simulation/dashboard_live_monte_carlo.json"
        save_monte_carlo_markdown(report, md_path)
        save_monte_carlo_json(report, json_path)
    return LiveRunResult(
        kind="monte_carlo",
        payload=report.to_dict(),
        markdown=format_monte_carlo_markdown(report),
        wrote_reports=write_reports,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=report.clinical_validity_claimed,
    )


def run_treatment_ranking_live(
    *,
    config_path: str | Path,
    graph_jsonl: str | Path | None = None,
    use_graph_modulation: bool = False,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
    intensity_scale: float | None = None,
    schedule_duty_cycle: float | None = None,
) -> LiveRunResult:
    root = Path(base_dir).resolve()
    config_file = _resolve(config_path, root)
    if config_file is None or not config_file.exists():
        raise FileNotFoundError(f"Treatment strategy config not found: {config_path}")
    config = load_treatment_strategy_config(config_file)
    report = rank_treatment_scenarios(
        config,
        graph_jsonl=_resolve(graph_jsonl, root),
        use_graph_modulation=use_graph_modulation,
        base_dir=root,
        intensity_scale=intensity_scale,
        schedule_duty_cycle=schedule_duty_cycle,
    )
    md_path = _resolve(markdown_output, root) if write_reports else None
    json_path = _resolve(json_output, root) if write_reports else None
    if write_reports:
        if md_path is None:
            md_path = root / "reports/treatment/dashboard_live_strategy.md"
        if json_path is None:
            json_path = root / "reports/treatment/dashboard_live_strategy.json"
        save_treatment_strategy_markdown(report, md_path)
        save_treatment_strategy_json(report, json_path)
    return LiveRunResult(
        kind="treatment_ranking",
        payload=report.to_dict(),
        markdown=format_treatment_strategy_markdown(report),
        wrote_reports=write_reports,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=report.clinical_validity_claimed,
    )


def run_toy_fitting_live(
    *,
    config_path: str | Path,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    root = Path(base_dir).resolve()
    config_file = _resolve(config_path, root)
    if config_file is None or not config_file.exists():
        raise FileNotFoundError(f"Fitting config not found: {config_path}")
    config = load_fitting_config(config_file)
    report = run_toy_parameter_fit(config, base_dir=root)
    md_path = _resolve(markdown_output, root) if write_reports else None
    json_path = _resolve(json_output, root) if write_reports else None
    if write_reports:
        if md_path is None:
            md_path = root / "reports/simulation/dashboard_live_fitting.md"
        if json_path is None:
            json_path = root / "reports/simulation/dashboard_live_fitting.json"
        save_fitting_markdown(report, md_path)
        save_fitting_json(report, json_path)
    return LiveRunResult(
        kind="toy_parameter_fit",
        payload=report.to_dict(),
        markdown=report.to_markdown(),
        wrote_reports=write_reports,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=report.clinical_validity_claimed,
    )


def _write_optional_reports(
    *,
    root: Path,
    write_reports: bool,
    markdown_output: str | Path | None,
    json_output: str | Path | None,
    default_md: str,
    default_json: str,
    markdown: str,
    payload: dict[str, Any],
) -> tuple[Path | None, Path | None, bool]:
    if not write_reports:
        return None, None, False
    md_path = _resolve(markdown_output, root) or (root / default_md)
    json_path = _resolve(json_output, root) or (root / default_json)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path, True


def _plain_label(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    text = str(value)
    if text.startswith("EntityType.") or text.startswith("NodeLabel.") or text.startswith("RelationType."):
        return text.split(".", 1)[-1]
    return text


def _load_local_pubmed_jsonl(
    path: Path,
    *,
    limit: int | None = None,
    query: str = "",
) -> list[dict[str, Any]]:
    """Load local PubMed JSONL, optionally filter the full file, then apply retmax."""

    rows: list[dict[str, Any]] = []
    needle = query.strip().lower()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            pmid = str(row.get("pmid") or "")
            if not pmid:
                continue
            title = row.get("title") or ""
            abstract = row.get("abstract") or ""
            if needle and needle not in f"{title} {abstract}".lower():
                continue
            rows.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "journal": row.get("journal") or "",
                    "publication_date": row.get("publication_date") or "",
                    "year": row.get("year") or "",
                    "authors": row.get("authors") or row.get("author_list") or [],
                    "doi": row.get("doi") or row.get("DOI") or "",
                    "full_text_url": row.get("full_text_url")
                    or row.get("fulltext_url")
                    or row.get("pmc_url")
                    or row.get("url")
                    or "",
                    "pmcid": row.get("pmcid") or row.get("PMCID") or "",
                    "local_pdf": row.get("local_pdf")
                    or row.get("pdf_path")
                    or row.get("local_path")
                    or "",
                    "mesh_terms": row.get("mesh_terms") or [],
                }
            )
            if limit is not None and len(rows) >= limit:
                break
    return rows


def run_literature_search_live(
    *,
    query: str = "",
    retmax: int = 10,
    offline: bool = True,
    local_jsonl: str | Path | None = "data/examples/pubmed_records_sample.jsonl",
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
    search_fn: Callable[..., list[str]] | None = None,
    fetch_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> LiveRunResult:
    """Search PubMed live, or browse a local JSONL fixture when offline."""

    root = Path(base_dir).resolve()
    if retmax < 1:
        raise ValueError("retmax must be at least 1")
    mode = "offline_local_jsonl"
    error: str | None = None
    records: list[dict[str, Any]] = []
    pmids: list[str] = []

    if offline:
        local_path = _resolve(local_jsonl, root)
        if local_path is None or not local_path.exists():
            raise FileNotFoundError(
                f"Offline literature search requires a local PubMed JSONL; not found: {local_jsonl}"
            )
        # Filter the full local JSONL first, then apply retmax.
        records = _load_local_pubmed_jsonl(local_path, limit=retmax, query=query)
        pmids = [str(row["pmid"]) for row in records]
        local_jsonl_resolved = str(local_path)
    else:
        local_jsonl_resolved = None
        search = search_fn or search_pubmed
        fetch = fetch_fn or fetch_pubmed_records
        if not query.strip():
            raise ValueError("Live NCBI search requires a non-empty query")
        try:
            pmids = search(query.strip(), retmax=retmax)
            records = fetch(pmids) if pmids else []
            mode = "ncbi_live"
        except PubMedIngestionError as exc:
            error = (
                f"NCBI/network unavailable: {exc}. "
                "Retry with offline=True and a local PubMed JSONL fixture."
            )
            mode = "ncbi_error"
            local_path = _resolve(local_jsonl, root)
            if local_path is not None and local_path.exists():
                records = _load_local_pubmed_jsonl(local_path, limit=retmax, query=query)
                pmids = [str(row["pmid"]) for row in records]
                mode = "ncbi_error_fallback_local"
                local_jsonl_resolved = str(local_path)

    payload: dict[str, Any] = {
        "query": query,
        "retmax": retmax,
        "mode": mode,
        "offline": offline,
        "pmid_count": len(pmids),
        "pmids": pmids,
        "records": records,
        "local_jsonl": local_jsonl_resolved,
        "error": error,
        "clinical_validity_claimed": False,
        "warning": RESEARCH_WARNING,
    }
    lines = [
        "# Literature search (research live runner)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Mode: `{mode}`",
        f"- Query: `{query or '(local browse)'}`",
        f"- PMID count: {len(pmids)}",
    ]
    if error:
        lines.extend(["", f"- Error: {error}"])
    if records:
        lines.extend(["", "## Records", ""])
        for row in records[:20]:
            lines.append(f"- PMID {row.get('pmid')}: {row.get('title') or '(no title)'}")
    markdown = "\n".join(lines) + "\n"
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_literature.md",
        default_json="reports/dashboard/dashboard_live_literature.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="literature_search",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_entity_extraction_live(
    *,
    text: str = "",
    pmid: str = "0",
    title: str = "",
    abstract: str = "",
    entity_mode: str = "lexicon",
    lexicon_path: str | Path | None = "configs/extraction/lexicon_gbm_v1.json",
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
    ner_pipeline: Callable[[str], list[dict[str, Any]]] | None = None,
) -> LiveRunResult:
    """Extract entities via offline lexicon (default) or an injected/model NER pipeline."""

    root = Path(base_dir).resolve()
    mode = entity_mode.strip().lower() or "lexicon"
    if mode not in {"lexicon", "model"}:
        raise ValueError("entity_mode must be 'lexicon' or 'model'")

    source_title = title
    source_abstract = abstract or text
    if not source_title and not source_abstract:
        raise ValueError("Provide text, or title/abstract, for entity extraction")
    paper = Paper(
        pmid=str(pmid or "0"),
        title=source_title or "Dashboard live extract",
        abstract=source_abstract,
    )
    source = paper_to_source_text(paper)

    if ner_pipeline is not None:
        pipeline = BiomedicalNERPipeline(ner_pipeline=ner_pipeline)
        used_mode = "injected"
    elif mode == "lexicon":
        lexicon = _resolve(lexicon_path, root)
        pipeline = BiomedicalNERPipeline(
            ner_pipeline=create_lexicon_ner_pipeline(lexicon if lexicon and lexicon.exists() else None)
        )
        used_mode = "lexicon"
    else:
        # Model mode may require network/model download; surface clear errors to the UI.
        try:
            pipeline = BiomedicalNERPipeline()
            used_mode = "model"
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                f"Model NER unavailable ({exc}). Use entity_mode='lexicon' for offline extraction."
            ) from exc

    result = pipeline.extract_from_paper(paper)
    entities: list[dict[str, Any]] = []
    for entity in result.entities:
        dumped = entity.model_dump()
        dumped["label"] = _plain_label(dumped.get("label"))
        entities.append(dumped)
    label_counts = dict(Counter(str(item.get("label")) for item in entities))
    payload: dict[str, Any] = {
        "pmid": paper.pmid,
        "mode": used_mode,
        "source_text": source,
        "entity_count": len(entities),
        "label_counts": label_counts,
        "entities": entities,
        "clinical_validity_claimed": False,
        "warning": RESEARCH_WARNING,
    }
    lines = [
        "# Entity extraction (research live runner)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Mode: `{used_mode}`",
        f"- PMID: `{paper.pmid}`",
        f"- Entity count: {len(entities)}",
        f"- Labels: `{label_counts}`",
        "",
        "## Entities",
        "",
    ]
    for item in entities[:50]:
        lines.append(
            f"- {item.get('label')}: `{item.get('text')}` "
            f"[{item.get('start')}:{item.get('end')}]"
        )
    markdown = "\n".join(lines) + "\n"
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_entities.md",
        default_json="reports/dashboard/dashboard_live_entities.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="entity_extraction",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_graph_inspect_live(
    *,
    graph_jsonl: str | Path = "data/examples/graph_records_sample.jsonl",
    top_n: int = 10,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Inspect local graph-record JSONL (offline-friendly Neo4j alternative)."""

    root = Path(base_dir).resolve()
    path = _resolve(graph_jsonl, root)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Graph JSONL not found: {graph_jsonl}")
    report = analyze_graph_records_jsonl(path, top_n=top_n)
    payload = report.to_dict()
    payload["graph_jsonl"] = str(path)
    payload["mode"] = "local_graph_jsonl"
    payload["clinical_validity_claimed"] = False
    payload["warning"] = RESEARCH_WARNING
    markdown = (
        f"{RESEARCH_WARNING}\n\n"
        f"Mode: local graph JSONL (offline-friendly Neo4j alternative)\n\n"
        f"{format_quality_report_markdown(report)}"
    )
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_graph_inspect.md",
        default_json="reports/dashboard/dashboard_live_graph_inspect.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="graph_inspect",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def _parse_node_labels(values: list[str] | None) -> list[NodeLabel]:
    if not values:
        return []
    parsed: list[NodeLabel] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        parsed.append(NodeLabel(text))
    return parsed


def _parse_relation_types(values: list[str] | None) -> list[RelationType]:
    if not values:
        return []
    parsed: list[RelationType] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        parsed.append(RelationType(text))
    return parsed


def run_knowledge_graph_explore_live(
    *,
    graph_jsonl: str | Path = "data/examples/graph_records_sample.jsonl",
    search: str = "",
    node_labels: list[str] | None = None,
    relation_types: list[str] | None = None,
    min_evidence_tier: int = 0,
    limit: int = 100,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Interactive local graph explorer (Cypher-less tables via GraphExplorerService)."""

    root = Path(base_dir).resolve()
    path = _resolve(graph_jsonl, root)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Graph JSONL not found: {graph_jsonl}")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    try:
        tier = EvidenceTier(int(min_evidence_tier))
    except ValueError as exc:
        raise ValueError("min_evidence_tier must be a valid EvidenceTier (0-5)") from exc

    service = GraphExplorerService.from_jsonl(path)
    try:
        inspection = service.inspection(recent_limit=8)
        metadata = service.metadata()
        neighborhood = service.neighborhood(
            search=search,
            node_labels=_parse_node_labels(node_labels),
            relation_types=_parse_relation_types(relation_types),
            min_evidence_tier=tier,
            limit=limit,
        )
    finally:
        service.close()

    quality = analyze_graph_records_jsonl(path, top_n=10)
    nodes = list(neighborhood.get("nodes") or [])
    edges = list(neighborhood.get("edges") or [])
    node_rows = [
        {
            "id": item.get("id"),
            "label": _plain_label((item.get("labels") or ["?"])[0] if isinstance(item.get("labels"), list) else item.get("label")),
            "key": item.get("key") or item.get("key_value") or "",
            "title": (item.get("properties") or {}).get("title")
            or (item.get("properties") or {}).get("name")
            or item.get("display")
            or "",
        }
        for item in nodes[:limit]
    ]
    edge_rows = []
    for item in edges[:limit]:
        pmid_list = [str(pmid) for pmid in (item.get("source_pmids") or [])[:8] if pmid]
        edge_rows.append(
            {
                "type": _plain_label(item.get("type")),
                "source": item.get("source"),
                "target": item.get("target"),
                "evidence_tier": item.get("evidence_tier"),
                "confidence": item.get("confidence"),
                "source_pmids": ", ".join(pmid_list),
                "source_pmid_list": pmid_list,
                "pubmed_urls": [
                    f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" for pmid in pmid_list if str(pmid).isdigit()
                ],
            }
        )
    payload: dict[str, Any] = {
        "graph_jsonl": str(path),
        "mode": "local_graph_explorer",
        "search": search,
        "min_evidence_tier": int(tier),
        "limit": limit,
        "inspection": inspection,
        "metadata": metadata,
        "quality": quality.to_dict(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": node_rows,
        "edges": edge_rows,
        "clinical_validity_claimed": False,
        "warning": RESEARCH_WARNING,
    }
    counts = inspection.get("counts") if isinstance(inspection, dict) else {}
    lines = [
        "# Knowledge graph explorer (research live runner)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Source: `{path}`",
        f"- Mode: local JSONL (Cypher-less table view)",
        f"- Search: `{search or '(none)'}`",
        f"- Nodes matched: {len(nodes)}",
        f"- Edges matched: {len(edges)}",
        f"- Graph nodes (inspection): {(counts or {}).get('nodes')}",
        f"- Graph relationships (inspection): {(counts or {}).get('relationships')}",
        "",
        format_quality_report_markdown(quality),
    ]
    markdown = "\n".join(lines) + "\n"
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_kg_explorer.md",
        default_json="reports/dashboard/dashboard_live_kg_explorer.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="knowledge_graph_explore",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_prediction_curation_load_live(
    *,
    queue_jsonl: str | Path = "data/review/evidence_smoke_prediction_reviewed_queue.jsonl",
    status_filter: str = "pending",
    limit: int = 50,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Load a prediction review / AL queue for interactive curation."""

    root = Path(base_dir).resolve()
    path = _resolve(queue_jsonl, root)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Prediction review queue JSONL not found: {queue_jsonl}")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    items = load_prediction_review_queue_jsonl(path)
    summary = summarize_prediction_review_queue(path)
    wanted = status_filter.strip().lower()
    filtered = [
        item
        for item in items
        if wanted in {"", "all"} or item.review_status == wanted
    ][:limit]
    item_rows = [
        {
            "item_id": item.item_id,
            "source_pmid": item.source_pmid,
            "text": item.text[:240],
            "prediction_label": item.prediction_label,
            "predicted_evidence_tier": item.predicted_evidence_tier,
            "confidence": item.confidence,
            "review_status": item.review_status,
            "reviewer": item.reviewer,
            "review_notes": item.review_notes,
            "corrected_evidence_tier": item.corrected_evidence_tier,
            "reasons": list(item.reasons),
        }
        for item in filtered
    ]
    payload: dict[str, Any] = {
        "queue_jsonl": str(path),
        "mode": "prediction_curation_load",
        "status_filter": wanted or "all",
        "item_count": len(items),
        "filtered_count": len(filtered),
        "pending_count": summary.pending_count,
        "summary": summary.to_dict(),
        "items": item_rows,
        "clinical_validity_claimed": False,
        "warning": RESEARCH_WARNING,
    }
    markdown = (
        f"{RESEARCH_WARNING}\n\n"
        f"Mode: prediction curation load\n\n"
        f"{format_prediction_review_summary_markdown(summary)}"
    )
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_curation_load.md",
        default_json="reports/dashboard/dashboard_live_curation_load.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="prediction_curation_load",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_prediction_curation_apply_live(
    *,
    queue_jsonl: str | Path,
    decisions: list[dict[str, Any]],
    output_jsonl: str | Path | None = None,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Apply accept/correct/reject decisions and write a reviewed queue JSONL."""

    root = Path(base_dir).resolve()
    path = _resolve(queue_jsonl, root)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Prediction review queue JSONL not found: {queue_jsonl}")
    if not decisions:
        raise ValueError("decisions must include at least one review decision")
    items = load_prediction_review_queue_jsonl(path)
    by_id = {item.item_id: item for item in items}
    missing = [str(row.get("item_id") or "") for row in decisions if str(row.get("item_id") or "") not in by_id]
    if any(missing):
        raise KeyError(f"Unknown item_id(s): {', '.join(mid for mid in missing if mid) or '(blank)'}")
    now = datetime.now(UTC).isoformat()
    applied = 0
    for row in decisions:
        item_id = str(row["item_id"])
        status = str(row.get("review_status") or "").strip().lower()
        if status not in {"accepted", "corrected", "rejected", "pending"}:
            raise ValueError(f"Invalid review_status for {item_id}: {status}")
        notes = str(row.get("review_notes") or "")
        reviewer = str(row.get("reviewer") or row.get("reviewer_id") or "dashboard")
        update: dict[str, Any] = {
            "review_status": status,
            "review_notes": notes,
            "reviewer": reviewer,
            "reviewer_id": reviewer,
            "decision_timestamp_utc": now if status != "pending" else "",
        }
        if status == "corrected":
            tier = row.get("corrected_evidence_tier")
            if tier is None or str(tier).strip() == "":
                raise ValueError(f"corrected decision for {item_id} requires corrected_evidence_tier")
            update["corrected_evidence_tier"] = int(tier)
        else:
            update["corrected_evidence_tier"] = None
        by_id[item_id] = by_id[item_id].model_copy(update=update)
        applied += 1
    updated_items = [by_id[item.item_id] for item in items]
    out_path = _resolve(output_jsonl, root) if output_jsonl else path
    if out_path is None:
        out_path = path
    save_prediction_review_queue_jsonl(updated_items, out_path)
    summary = summarize_prediction_review_queue(out_path)
    payload: dict[str, Any] = {
        "queue_jsonl": str(path),
        "output_jsonl": str(out_path),
        "mode": "prediction_curation_apply",
        "applied_count": applied,
        "item_count": len(updated_items),
        "pending_count": summary.pending_count,
        "summary": summary.to_dict(),
        "clinical_validity_claimed": False,
        "warning": RESEARCH_WARNING,
    }
    markdown = (
        f"{RESEARCH_WARNING}\n\n"
        f"Mode: prediction curation apply ({applied} decision(s))\n\n"
        f"Wrote: `{out_path}`\n\n"
        f"{format_prediction_review_summary_markdown(summary)}"
    )
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_curation_apply.md",
        default_json="reports/dashboard/dashboard_live_curation_apply.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="prediction_curation_apply",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_prediction_curation_export_live(
    *,
    predictions_jsonl: str | Path,
    reviewed_queue_jsonl: str | Path,
    output_jsonl: str | Path = "data/processed/dashboard_curated_evidence.jsonl",
    fail_on_pending: bool = False,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Export curated evidence JSONL from reviewed prediction decisions."""

    root = Path(base_dir).resolve()
    predictions_path = _resolve(predictions_jsonl, root)
    reviewed_path = _resolve(reviewed_queue_jsonl, root)
    out_path = _resolve(output_jsonl, root)
    if predictions_path is None or not predictions_path.exists():
        raise FileNotFoundError(f"Predictions JSONL not found: {predictions_jsonl}")
    if reviewed_path is None or not reviewed_path.exists():
        raise FileNotFoundError(f"Reviewed queue JSONL not found: {reviewed_queue_jsonl}")
    if out_path is None:
        raise ValueError("output_jsonl is required")
    report = export_curated_evidence(
        predictions_jsonl=predictions_path,
        reviewed_queue_jsonl=reviewed_path,
        output_jsonl=out_path,
        fail_on_pending=fail_on_pending,
    )
    payload = report.to_dict()
    payload["mode"] = "prediction_curation_export"
    payload["clinical_validity_claimed"] = False
    payload["warning"] = RESEARCH_WARNING
    markdown = (
        f"{RESEARCH_WARNING}\n\n"
        f"Mode: curated evidence export\n\n"
        f"{format_curated_evidence_report_markdown(report)}"
    )
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_curation_export.md",
        default_json="reports/dashboard/dashboard_live_curation_export.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="prediction_curation_export",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_training_artifacts_browse_live(
    *,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Browse training packs / registry / governance summaries (read-only)."""

    root = Path(base_dir).resolve()
    from gbmbert.dashboard.app import training_artifacts_dashboard_context

    context = training_artifacts_dashboard_context(root)
    registry_path = root / "models" / "checkpoint_registry.json"
    checkpoints: list[dict[str, Any]] = []
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = {"error": "Invalid JSON", "path": str(registry_path)}
        if isinstance(registry, dict):
            for item in registry.get("checkpoints") or []:
                if isinstance(item, dict):
                    checkpoints.append(
                        {
                            "name": item.get("name"),
                            "task": item.get("task"),
                            "status": item.get("status"),
                            "checkpoint_dir": item.get("checkpoint_dir") or item.get("output_dir") or "",
                            "base_model": item.get("base_model") or "",
                        }
                    )
    governance = list(context.get("governance_report_details") or [])
    governance_by_title = {
        str(row.get("title")): row for row in governance if isinstance(row, dict)
    }
    pack_rows = []
    for title in ("Evidence pack", "Relation pack", "Gold pack"):
        pack_payload = context["payloads"].get(title) if isinstance(context.get("payloads"), dict) else None
        detail = governance_by_title.get(title) or {}
        pack_rows.append(
            {
                "pack": title,
                "ready": bool(isinstance(pack_payload, dict) and pack_payload.get("ready") is True),
                "status": detail.get("status")
                or ("ready" if isinstance(pack_payload, dict) and pack_payload.get("ready") else "missing"),
                "json_path": detail.get("json_path") or "",
                "markdown_path": detail.get("markdown_path") or "",
            }
        )
    payload: dict[str, Any] = {
        "mode": "training_artifacts_browse",
        "available_report_count": context.get("available_report_count"),
        "ready_pack_count": context.get("ready_pack_count"),
        "registry_entry_count": context.get("registry_entry_count"),
        "registry_audit_passed": context.get("registry_audit_passed"),
        "relation_config_status": context.get("relation_config_status"),
        "current_config_passed_count": context.get("current_config_passed_count"),
        "current_config_failed_count": context.get("current_config_failed_count"),
        "scaffold_config_count": context.get("scaffold_config_count"),
        "label_drift_warning_count": context.get("label_drift_warning_count"),
        "launcher_menu_safe": context.get("launcher_menu_safe"),
        "curated_fixture_safe": context.get("curated_fixture_safe"),
        "gold_pack_promotable": context.get("gold_pack_promotable"),
        "promotion_blockers": context.get("promotion_blockers") or [],
        "soft_densify_gaps": context.get("soft_densify_gaps") or [],
        "gold_pack_next_actions": context.get("gold_pack_next_actions") or [],
        "dual_review_pending_total": context.get("dual_review_pending_total"),
        "active_learning_pending_total": context.get("active_learning_pending_total"),
        "gold_pack_task_counts": context.get("gold_pack_task_counts") or {},
        "governance_report_details": governance,
        "checkpoints": checkpoints,
        "pack_rows": pack_rows,
        "clinical_validity_claimed": False,
        "warning": RESEARCH_WARNING,
    }
    lines = [
        "# Training artifacts browse (research live runner)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Available reports: {payload['available_report_count']}",
        f"- Ready packs: {payload['ready_pack_count']}",
        f"- Registry entries: {payload['registry_entry_count']}",
        f"- Registry audit: {payload['registry_audit_passed']}",
        f"- Current config failures: {payload['current_config_failed_count']}",
        f"- Scaffold configs: {payload['scaffold_config_count']}",
        "",
        "## Checkpoints",
        "",
    ]
    for item in checkpoints[:40]:
        lines.append(
            f"- `{item.get('name')}` task={item.get('task')} status={item.get('status')} "
            f"dir=`{item.get('checkpoint_dir')}`"
        )
    markdown = "\n".join(lines) + "\n"
    md_path, json_path, wrote = _write_optional_reports(
        root=root,
        write_reports=write_reports,
        markdown_output=markdown_output,
        json_output=json_output,
        default_md="reports/dashboard/dashboard_live_training_browse.md",
        default_json="reports/dashboard/dashboard_live_training_browse.json",
        markdown=markdown,
        payload=payload,
    )
    return LiveRunResult(
        kind="training_artifacts_browse",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_gold_pack_ops_status_live(
    *,
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Build gold-pack ops status (counts, blockers, soft densify, backlog, next actions)."""

    root = Path(base_dir).resolve()
    from gbmbert.training.gold_pack_ops import (
        build_gold_pack_ops_status,
        format_gold_pack_ops_status_markdown,
        save_gold_pack_ops_status_json,
        save_gold_pack_ops_status_markdown,
    )

    report = build_gold_pack_ops_status(
        gold_pack_report=root / "reports/training/gold_pack/gold_training_pack.json",
        threshold_config=root / "configs/training/gold_pack_promotion_thresholds.json",
        review_batch_root=root / "data/research/review_batches",
        active_learning_batch_paths=[
            root / "data/processed/curation_regression_pack/active_learning_batches_round26.jsonl",
            root / "data/processed/curation_regression_pack/active_learning_batches.jsonl",
            root / "data/review/active_learning_batches.jsonl",
        ],
    )
    payload = report.to_dict()
    payload["mode"] = "gold_pack_ops_status"
    markdown = format_gold_pack_ops_status_markdown(report)
    md_path = None
    json_path = None
    wrote = False
    if write_reports:
        md_path = Path(markdown_output) if markdown_output else root / "reports/training/gold_pack/gold_pack_ops_status.md"
        json_path = Path(json_output) if json_output else root / "reports/training/gold_pack/gold_pack_ops_status.json"
        if not md_path.is_absolute():
            md_path = root / md_path
        if not json_path.is_absolute():
            json_path = root / json_path
        save_gold_pack_ops_status_markdown(report, md_path)
        save_gold_pack_ops_status_json(report, json_path)
        wrote = True
    return LiveRunResult(
        kind="gold_pack_ops_status",
        payload=payload,
        markdown=markdown,
        wrote_reports=wrote,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_training_artifacts_audit_live(
    *,
    registry_path: str | Path = "models/checkpoint_registry.json",
    reports_dir: str | Path = "reports/training",
    write_reports: bool = False,
    markdown_output: str | Path | None = None,
    json_output: str | Path | None = None,
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Run a safe read-only checkpoint registry audit (no GPU training)."""

    root = Path(base_dir).resolve()
    reg = _resolve(registry_path, root)
    report_root = _resolve(reports_dir, root) or (root / "reports" / "training")
    if reg is None or not reg.exists():
        raise FileNotFoundError(f"Checkpoint registry not found: {registry_path}")
    report = audit_checkpoint_registry(reg, reports_dir=report_root)
    payload = report.to_dict()
    payload["mode"] = "training_artifacts_audit"
    payload["clinical_validity_claimed"] = False
    payload["warning"] = RESEARCH_WARNING
    markdown = f"{RESEARCH_WARNING}\n\n{format_registry_audit_markdown(report)}"
    md_path = _resolve(markdown_output, root) if write_reports else None
    json_path = _resolve(json_output, root) if write_reports else None
    if write_reports:
        if md_path is None:
            md_path = root / "reports/dashboard/dashboard_live_registry_audit.md"
        if json_path is None:
            json_path = root / "reports/dashboard/dashboard_live_registry_audit.json"
        save_registry_audit_markdown(report, md_path)
        save_registry_audit_json(report, json_path)
    return LiveRunResult(
        kind="training_artifacts_audit",
        payload=payload,
        markdown=markdown,
        wrote_reports=write_reports,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(json_path) if json_path else None,
        clinical_validity_claimed=False,
    )


def run_training_artifacts_refresh_manifest_live(
    *,
    confirm: bool = False,
    output_json: str | Path = "reports/training/dashboard_training_manifest.json",
    markdown_output: str | Path | None = "reports/training/dashboard_training_manifest.md",
    base_dir: str | Path = ".",
) -> LiveRunResult:
    """Refresh the dashboard training manifest snapshot (explicit confirm required)."""

    if not confirm:
        raise ValueError("Refresh requires confirm=True (explicit UI confirmation)")
    root = Path(base_dir).resolve()
    from gbmbert.training.governance import (
        build_dashboard_training_manifest,
        save_dashboard_training_manifest_markdown,
    )

    out_json = _resolve(output_json, root)
    if out_json is None:
        raise ValueError("output_json is required")
    report = build_dashboard_training_manifest(out_json, root=root)
    md_path = _resolve(markdown_output, root) if markdown_output else None
    if md_path is not None:
        save_dashboard_training_manifest_markdown(report, md_path)
    payload = report.to_dict()
    payload["mode"] = "training_artifacts_refresh_manifest"
    payload["clinical_validity_claimed"] = False
    payload["warning"] = RESEARCH_WARNING
    markdown = (
        f"{RESEARCH_WARNING}\n\n"
        f"# Dashboard training manifest refresh\n\n"
        f"- Output JSON: `{out_json}`\n"
        f"- Available reports: {payload.get('available_report_count')}\n"
        f"- Ready packs: {payload.get('ready_pack_count')}\n"
        f"- Registry entries: {payload.get('registry_entry_count')}\n"
    )
    return LiveRunResult(
        kind="training_artifacts_refresh_manifest",
        payload=payload,
        markdown=markdown,
        wrote_reports=True,
        markdown_path=str(md_path) if md_path else None,
        json_path=str(out_json),
        clinical_validity_claimed=False,
    )
