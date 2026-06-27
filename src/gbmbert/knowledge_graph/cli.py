"""Command-line loader for GBM-AI knowledge graph JSONL records."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.knowledge_graph.loader import GraphLoader, LoaderConfig, LoaderStats

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GraphLoadReport:
    source_path: str
    record_type: str
    dry_run: bool
    apply_constraints: bool
    skip_invalid_records: bool
    stats: LoaderStats

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "record_type": self.record_type,
            "dry_run": self.dry_run,
            "apply_constraints": self.apply_constraints,
            "skip_invalid_records": self.skip_invalid_records,
            "stats": asdict(self.stats),
        }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load GBM-AI graph records into Neo4j.")
    parser.add_argument("jsonl", type=Path, help="Graph-record JSONL path.")
    parser.add_argument(
        "--record-type",
        choices=["auto", "pubmed", "trial"],
        default="auto",
        help="Graph record type to load.",
    )
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument("--dry-run", action="store_true", help="Log Cypher instead of writing.")
    parser.add_argument("--skip-invalid-records", action="store_true")
    parser.add_argument("--no-constraints", action="store_true")
    parser.add_argument("--report-json-output", type=Path)
    parser.add_argument("--report-markdown-output", type=Path)
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.dry_run:
        driver = _DryRunDriver()
    else:
        if not args.password:
            parser.error("NEO4J_PASSWORD is required unless --dry-run is used")
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("Install neo4j to load records into a live database") from exc
        driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))

    loader = GraphLoader(
        driver,
        LoaderConfig(
            dry_run=args.dry_run,
            skip_invalid_records=args.skip_invalid_records,
            apply_constraints=not args.no_constraints,
        ),
    )
    record_type = detect_record_type(args.jsonl) if args.record_type == "auto" else args.record_type
    if record_type == "trial":
        stats = loader.load_trial_jsonl(args.jsonl)
    else:
        stats = loader.load_pubmed_jsonl(args.jsonl)
    report = GraphLoadReport(
        source_path=str(args.jsonl),
        record_type=record_type,
        dry_run=args.dry_run,
        apply_constraints=not args.no_constraints,
        skip_invalid_records=args.skip_invalid_records,
        stats=stats,
    )
    if args.report_json_output:
        save_load_report_json(report, args.report_json_output)
    if args.report_markdown_output:
        save_load_report_markdown(report, args.report_markdown_output)
    LOGGER.info("Graph load complete: %s", stats)
    return 0


def save_load_report_json(report: GraphLoadReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_load_report_markdown(report: GraphLoadReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_load_report_markdown(report), encoding="utf-8")
    return output_path


def format_load_report_markdown(report: GraphLoadReport) -> str:
    stats = report.stats
    lines = [
        "# GBM-AI Graph Load Report",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Source: `{report.source_path}`",
        f"- Record type: {report.record_type}",
        f"- Dry run: {report.dry_run}",
        f"- Constraints: {report.apply_constraints}",
        f"- Skip invalid records: {report.skip_invalid_records}",
        "",
        "## Stats",
        f"- Records seen: {stats.records_seen}",
        f"- Records loaded: {stats.records_loaded}",
        f"- Records skipped: {stats.records_skipped}",
        f"- Nodes merged: {stats.nodes_merged}",
        f"- Mentions merged: {stats.mentions_merged}",
        f"- Relations merged: {stats.relations_merged}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def detect_record_type(path: Path) -> str:
    """Detect graph-record JSONL type from the first non-empty row."""

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                return "pubmed"
            if "nct_id" in payload:
                return "trial"
            return "pubmed"
    return "pubmed"


class _DryRunSession:
    def __enter__(self) -> _DryRunSession:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def run(self, query: str, **parameters: object) -> None:
        LOGGER.info("DRY RUN session query:\n%s\nparams=%s", query, parameters)


class _DryRunDriver:
    def session(self) -> _DryRunSession:
        return _DryRunSession()


if __name__ == "__main__":
    raise SystemExit(main())
