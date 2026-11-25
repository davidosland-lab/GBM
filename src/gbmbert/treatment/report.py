"""Markdown/JSON writers for Phase 6 treatment-scenario ranking reports.

Research-use only. Not medical advice. Not clinical decision support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gbmbert.simulation.model import RESEARCH_WARNING
from gbmbert.treatment.engine import BOUNDARY_BANNER, TreatmentStrategyReport


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


def format_treatment_strategy_markdown(report: TreatmentStrategyReport) -> str:
    lines = [
        "# Phase 6 Treatment Scenario Ranking (Research Prototype)",
        "",
        RESEARCH_WARNING,
        "",
        BOUNDARY_BANNER,
        "",
        f"- Config: `{report.config_name}`",
        f"- Simulation pack: `{report.simulation_pack_name}`",
        f"- Phase: {report.phase}",
        f"- Clinical validity claimed: `{report.clinical_validity_claimed}`",
        f"- Clinical decision support: `{report.is_clinical_decision_support}`",
        "",
        report.description,
        "",
        "## Boundary",
        "",
        "### Compared (research)",
    ]
    lines.extend(f"- {item}" for item in report.simulated)
    lines.extend(["", "### Not provided"])
    lines.extend(f"- {item}" for item in report.not_simulated)
    lines.extend(["", "## Assumptions"])
    lines.extend(f"- {item}" for item in report.assumptions)
    lines.extend(["", "## Ranking weights (toy)"])
    for key, value in report.weights.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Scenario research knobs (simulation parameters only — not real schedules)"])
    for key, value in report.scenario_knobs.items():
        lines.append(f"- `{key}`: {value}")
    if report.ranking_provenance:
        lines.extend(["", "## Ranking provenance"])
        lines.append(f"- Method: `{report.ranking_provenance.get('method')}`")
        lines.append(f"- Toxicity model: `{report.ranking_provenance.get('toxicity_model')}`")
        lines.append(
            f"- Patient eligibility: `{report.ranking_provenance.get('patient_eligibility')}` "
            "(must remain false)"
        )
        for note in report.ranking_provenance.get("notes") or []:
            lines.append(f"- {note}")
    if report.literature_anchors:
        lines.extend(["", "## Literature anchors (explicit, non-clinical)"])
        for anchor in report.literature_anchors:
            pmid = anchor.get("pmid") or anchor.get("source_pmid") or "n/a"
            note = anchor.get("note") or anchor.get("summary") or ""
            lines.append(f"- PMID `{pmid}`: {note}")
    if report.graph_features:
        features = report.graph_features
        lines.extend(
            [
                "",
                "## Optional graph evidence signals",
                f"- Relations: {features.get('relation_count')}",
                f"- Mean evidence tier: {features.get('mean_evidence_tier')}",
                f"- Evidence modulation: {features.get('evidence_modulation')}",
            ]
        )
    lines.extend(["", "## Scenario ranking table (research scores only)"])
    lines.extend(
        _markdown_table(
            report.comparison_table,
            [
                ("rank", "rank"),
                ("scenario_id", "scenario"),
                ("label", "label"),
                ("research_score", "research_score"),
                ("relative_reduction", "relative_reduction"),
                ("final_total", "final_total"),
                ("toy_toxicity_burden", "toy_toxicity"),
                ("delivery_multiplier", "delivery_multiplier"),
                ("intensity_scale", "intensity"),
                ("schedule_duty_cycle", "duty_cycle"),
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Reminder",
            "",
            "These ranks compare toy simulation scenarios. They are not prescriptions, "
            "not dosing advice, and not clinical decision support. Toy toxicity scores "
            "are synthetic research burdens, not clinical adverse-event models. "
            "Intensity/schedule knobs are simulation parameters only. Do not use for "
            "diagnosis, treatment selection, patient eligibility, or clinical decision-making.",
            "",
        ]
    )
    return "\n".join(lines)


def save_treatment_strategy_json(report: TreatmentStrategyReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_treatment_strategy_markdown(report: TreatmentStrategyReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_treatment_strategy_markdown(report), encoding="utf-8")
    return output
