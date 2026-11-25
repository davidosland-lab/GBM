"""CLI for Phase 6 research treatment-scenario ranking.

Research-use only. Not medical advice. Not clinical decision support.
Not intended for diagnosis, treatment selection, or clinical decision-making.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gbmbert.simulation.model import RESEARCH_WARNING
from gbmbert.treatment.engine import BOUNDARY_BANNER, load_treatment_strategy_config, rank_treatment_scenarios
from gbmbert.treatment.report import (
    format_treatment_strategy_markdown,
    save_treatment_strategy_json,
    save_treatment_strategy_markdown,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rank Phase 5 toy simulation scenarios under explicit research weights. "
            + RESEARCH_WARNING
            + " "
            + BOUNDARY_BANNER
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/treatment/strategy_research_v1.json"),
        help="Treatment strategy ranking JSON config",
    )
    parser.add_argument(
        "--graph-jsonl",
        type=Path,
        default=None,
        help="Optional graph-record JSONL for research evidence-support signals",
    )
    parser.add_argument(
        "--use-graph-modulation",
        action="store_true",
        help="Apply graph modulation when re-running the linked Phase 5 scenario pack",
    )
    parser.add_argument(
        "--intensity-scale",
        type=float,
        default=None,
        help="Override research intensity_scale simulation knob (not a real dose)",
    )
    parser.add_argument(
        "--schedule-duty-cycle",
        type=float,
        default=None,
        help="Override research schedule_duty_cycle simulation knob (not a real schedule)",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/treatment/phase6_strategy_example.md"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/treatment/phase6_strategy_example.json"),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    config = load_treatment_strategy_config(args.config)
    report = rank_treatment_scenarios(
        config,
        graph_jsonl=args.graph_jsonl,
        use_graph_modulation=args.use_graph_modulation,
        base_dir=Path.cwd(),
        intensity_scale=args.intensity_scale,
        schedule_duty_cycle=args.schedule_duty_cycle,
    )
    save_treatment_strategy_json(report, args.json_output)
    save_treatment_strategy_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_treatment_strategy_markdown(report))
        print(f"\nWrote Markdown: {args.markdown_output}")
        print(f"Wrote JSON: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
