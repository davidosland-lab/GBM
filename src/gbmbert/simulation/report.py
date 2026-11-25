"""Markdown/JSON report writers for Phase 5 simulation runs.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gbmbert.simulation.model import RESEARCH_WARNING
from gbmbert.simulation.monte_carlo import MonteCarloReport
from gbmbert.simulation.scenarios import ScenarioRunReport


def _markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["| (none) |", "| --- |", "| no rows |"]
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                cells.append(f"{value:.4f}")
            else:
                cells.append(str(value))
        body.append("| " + " | ".join(cells) + " |")
    return [header, sep, *body]


def format_simulation_markdown(report: ScenarioRunReport) -> str:
    lines = [
        "# Phase 5 Tumour Simulation Report (Research Prototype)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Pack: `{report.pack_name}`",
        f"- Phase: {report.phase}",
        f"- Clinical validity claimed: `{report.clinical_validity_claimed}`",
        f"- Resistance axis enabled: `{report.resistance_enabled}`",
        "",
        report.description,
        "",
        "## Boundary",
        "",
        "### Simulated",
    ]
    lines.extend(f"- {item}" for item in report.simulated)
    lines.extend(["", "### Not simulated"])
    lines.extend(f"- {item}" for item in report.not_simulated)
    lines.extend(["", "## Assumptions"])
    if report.assumptions:
        lines.extend(f"- {item}" for item in report.assumptions)
    else:
        lines.append("- none")
    lines.extend(["", "## Literature anchors (explicit, non-clinical)"])
    if report.literature_anchors:
        for anchor in report.literature_anchors:
            pmid = anchor.get("pmid") or anchor.get("source_pmid") or "n/a"
            note = anchor.get("note") or anchor.get("summary") or ""
            lines.append(f"- PMID `{pmid}`: {note}")
    else:
        lines.append("- none")

    if report.graph_features:
        features = report.graph_features
        lines.extend(
            [
                "",
                "## Graph research features",
                f"- Source: `{features.get('source_path')}`",
                f"- Relations: {features.get('relation_count')}",
                f"- Mean evidence tier: {features.get('mean_evidence_tier')}",
                f"- Evidence modulation: {features.get('evidence_modulation')}",
                f"- Delivery modulation: {features.get('delivery_modulation')}",
                f"- Kill modulation: {features.get('kill_modulation')}",
                f"- Synergy modulation: {features.get('synergy_modulation')}",
                f"- Transition modulation: {features.get('transition_modulation')}",
            ]
        )
        relation_counts = features.get("relation_type_counts") or {}
        if relation_counts:
            lines.append("- Relation types: " + ", ".join(f"{key}={value}" for key, value in relation_counts.items()))
        warnings = features.get("warnings") or []
        if warnings:
            lines.append("- Warnings:")
            lines.extend(f"  - {item}" for item in warnings)
        provenance = features.get("parameter_provenance") or []
        if provenance:
            lines.extend(["", "### Parameter provenance (research weights)"])
            for item in provenance[:12]:
                if "value" in item:
                    lines.append(
                        f"- `{item.get('parameter')}`={item.get('value')} "
                        f"(n={item.get('n_relations')}, aggregation={item.get('aggregation')})"
                    )
                else:
                    lines.append(
                        f"- `{item.get('parameter')}` via `{item.get('relation')}` "
                        f"PMID `{item.get('source_pmid')}` tier={item.get('evidence_tier')} "
                        f"weight={item.get('research_weight')}"
                    )

    lines.extend(["", "## Scenario comparison table (toy totals)"])
    lines.extend(
        _markdown_table(
            report.comparison_table or report.comparisons,
            [
                ("scenario_id", "scenario"),
                ("label", "label"),
                ("final_total", "final_total"),
                ("midpoint_total", "midpoint_total"),
                ("delta_vs_baseline", "delta_vs_baseline"),
                ("relative_reduction", "relative_reduction"),
            ],
        )
    )

    lines.extend(["", "## Final compartment states"])
    for result in report.results:
        state = result["final_state"]
        lines.append(
            f"- `{result['scenario_id']}`: MES={state['MES']:.4f}, NPC={state['NPC']:.4f}, "
            f"OPC={state['OPC']:.4f}, AC={state['AC']:.4f}, total={result['final_total']:.4f}"
        )
        resistance = result.get("final_resistance_totals")
        if resistance:
            lines.append(
                f"  - resistance: sensitive={resistance.get('sensitive', 0):.4f}, "
                f"persister={resistance.get('persister', 0):.4f}, "
                f"resistant={resistance.get('resistant', 0):.4f}"
            )

    lines.extend(
        [
            "",
            "## Reminder",
            "",
            "Phase 5 is a research prototype. Do not use these trajectories for diagnosis, "
            "treatment selection, or clinical decision-making. Scenario rankings from Phase 6 "
            "are research comparisons under toy assumptions, not prescriptions or CDS.",
            "",
        ]
    )
    return "\n".join(lines)


def format_monte_carlo_markdown(report: MonteCarloReport) -> str:
    lines = [
        "# Phase 5 Monte Carlo Simulation Report (Research Prototype)",
        "",
        RESEARCH_WARNING,
        "",
        f"- Config: `{report.config_name}`",
        f"- Phase: {report.phase}",
        f"- Seed: `{report.seed}`",
        f"- Samples: `{report.n_samples}`",
        f"- Clinical validity claimed: `{report.clinical_validity_claimed}`",
        "",
        report.description,
        "",
        "## Boundary",
        "",
        "### Simulated",
    ]
    lines.extend(f"- {item}" for item in report.simulated)
    lines.extend(["", "### Not simulated"])
    lines.extend(f"- {item}" for item in report.not_simulated)
    lines.extend(["", "## Assumptions"])
    lines.extend(f"- {item}" for item in report.assumptions)
    lines.extend(["", "## Parameter distributions"])
    for spec in report.parameter_specs:
        lines.append(
            f"- `{spec['name']}`: dist={spec['dist']}, mean={spec['mean']}, std={spec.get('std')}, "
            f"low={spec.get('low')}, high={spec.get('high')}"
        )
    lines.extend(["", "## Scenario uncertainty bands (toy final_total)"])
    lines.extend(
        _markdown_table(
            report.comparison_table,
            [
                ("scenario_id", "scenario"),
                ("label", "label"),
                ("median_final_total", "median"),
                ("band_low", "q05"),
                ("band_high", "q95"),
                ("mean_final_total", "mean"),
                ("relative_reduction_vs_baseline_median", "rel_reduction_vs_baseline"),
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Reminder",
            "",
            "Monte Carlo bands are research quantiles over toy parameter draws. "
            "They are not clinical prediction intervals and must not be used for "
            "diagnosis, treatment selection, or clinical decision-making.",
            "",
        ]
    )
    return "\n".join(lines)


def save_simulation_json(report: ScenarioRunReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_simulation_markdown(report: ScenarioRunReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_simulation_markdown(report), encoding="utf-8")
    return output


def save_monte_carlo_json(report: MonteCarloReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_monte_carlo_markdown(report: MonteCarloReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_monte_carlo_markdown(report), encoding="utf-8")
    return output
