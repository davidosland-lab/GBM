"""Guard reports for loading evidence-overlay graph artifacts into Neo4j."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.curation import load_graph_records
from gbmbert.datasets import RESEARCH_WARNING


@dataclass(frozen=True)
class OverlayLoadGuardReport:
    graph_path: str
    record_count: int
    relation_count: int
    overlay_relation_count: int
    pending_overlay_count: int
    missing_original_tier_count: int
    safe_to_load: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_overlay_load_guard_report(graph_jsonl: str | Path) -> OverlayLoadGuardReport:
    """Inspect an overlay graph before any Neo4j load command is run."""

    records = load_graph_records(graph_jsonl)
    relation_count = 0
    overlay_relation_count = 0
    pending_overlay_count = 0
    missing_original_tier_count = 0
    warnings: list[str] = []
    for record in records:
        for relation in record.relations:
            relation_count += 1
            properties = relation.properties
            if "evidence_overlay_tier" not in properties:
                continue
            overlay_relation_count += 1
            if properties.get("evidence_overlay_review_status") == "pending":
                pending_overlay_count += 1
            if "evidence_overlay_original_tier" not in properties:
                missing_original_tier_count += 1

    if relation_count == 0:
        warnings.append("Graph contains no relations to load")
    if overlay_relation_count == 0:
        warnings.append("Graph contains no evidence overlay metadata")
    if pending_overlay_count:
        warnings.append(f"{pending_overlay_count} overlay relation(s) have pending review status")
    if missing_original_tier_count:
        warnings.append(f"{missing_original_tier_count} overlay relation(s) missing original tier metadata")
    return OverlayLoadGuardReport(
        graph_path=str(graph_jsonl),
        record_count=len(records),
        relation_count=relation_count,
        overlay_relation_count=overlay_relation_count,
        pending_overlay_count=pending_overlay_count,
        missing_original_tier_count=missing_original_tier_count,
        safe_to_load=not warnings,
        warnings=warnings,
    )


def save_overlay_load_guard_json(report: OverlayLoadGuardReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_overlay_load_guard_markdown(report: OverlayLoadGuardReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_overlay_load_guard_markdown(report), encoding="utf-8")
    return output_path


def format_overlay_load_guard_markdown(report: OverlayLoadGuardReport) -> str:
    lines = [
        "# GBM-AI Neo4j Overlay Load Guard",
        "",
        RESEARCH_WARNING,
        "",
        f"- Graph: `{report.graph_path}`",
        f"- Records: {report.record_count}",
        f"- Relations: {report.relation_count}",
        f"- Overlay relations: {report.overlay_relation_count}",
        f"- Pending overlay relations: {report.pending_overlay_count}",
        f"- Missing original tier metadata: {report.missing_original_tier_count}",
        f"- Safe to load: {report.safe_to_load}",
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect an evidence-overlay graph before Neo4j loading.")
    parser.add_argument("graph_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_overlay_load_guard_report(args.graph_jsonl)
    if args.json_output:
        save_overlay_load_guard_json(report, args.json_output)
    if args.markdown_output:
        save_overlay_load_guard_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_overlay_load_guard_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
