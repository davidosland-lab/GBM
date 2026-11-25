"""CLI for Phase 5 research prototype tumour simulation.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gbmbert.simulation.fitting import (
    format_fitting_markdown,
    load_fitting_config,
    run_toy_parameter_fit,
    save_fitting_json,
    save_fitting_markdown,
)
from gbmbert.simulation.model import RESEARCH_WARNING
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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Phase 5 research prototype compartment tumour simulation. "
            + RESEARCH_WARNING
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/simulation/compartment_toy_v1.json"),
        help="Scenario pack JSON config",
    )
    parser.add_argument(
        "--graph-jsonl",
        type=Path,
        default=None,
        help="Optional graph-record JSONL for evidence-tier research features",
    )
    parser.add_argument(
        "--use-graph-modulation",
        action="store_true",
        help="Apply graph relation-type modulation to scenario parameters (research weights only)",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/simulation/phase5_mvp_example.md"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/simulation/phase5_mvp_example.json"),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    return parser


def build_monte_carlo_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 5 Monte Carlo parameter sweeps for the toy tumour simulation. "
            + RESEARCH_WARNING
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/simulation/monte_carlo_v1.json"),
        help="Monte Carlo sweep JSON config",
    )
    parser.add_argument(
        "--graph-jsonl",
        type=Path,
        default=None,
        help="Optional graph-record JSONL for research feature modulation",
    )
    parser.add_argument(
        "--use-graph-modulation",
        action="store_true",
        help="Apply graph modulation inside each Monte Carlo replicate (research only)",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/simulation/phase5_monte_carlo_example.md"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/simulation/phase5_monte_carlo_example.json"),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    pack = load_scenario_pack(args.config)
    report = run_scenario_pack(
        pack,
        graph_jsonl=args.graph_jsonl,
        use_graph_modulation=args.use_graph_modulation,
    )
    save_simulation_json(report, args.json_output)
    save_simulation_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_simulation_markdown(report))
        print(f"\nWrote Markdown: {args.markdown_output}")
        print(f"Wrote JSON: {args.json_output}")
    return 0


def monte_carlo_main(argv: list[str] | None = None) -> int:
    args = build_monte_carlo_arg_parser().parse_args(argv)
    config = load_monte_carlo_config(args.config)
    report = run_monte_carlo(
        config,
        graph_jsonl=args.graph_jsonl,
        use_graph_modulation=args.use_graph_modulation,
        base_dir=Path.cwd(),
    )
    save_monte_carlo_json(report, args.json_output)
    save_monte_carlo_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_monte_carlo_markdown(report))
        print(f"\nWrote Markdown: {args.markdown_output}")
        print(f"Wrote JSON: {args.json_output}")
    return 0


def build_fitting_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 5 toy parameter fitting / approximate posterior-style sampling. "
            "Not PK/PD. Not clinically validated. "
            + RESEARCH_WARNING
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/simulation/toy_fitting_v1.json"),
        help="Toy fitting JSON config",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/simulation/phase5_fitting_example.md"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/simulation/phase5_fitting_example.json"),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    return parser


def fitting_main(argv: list[str] | None = None) -> int:
    args = build_fitting_arg_parser().parse_args(argv)
    config = load_fitting_config(args.config)
    report = run_toy_parameter_fit(config, base_dir=Path.cwd())
    save_fitting_json(report, args.json_output)
    save_fitting_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_fitting_markdown(report))
        print(f"\nWrote Markdown: {args.markdown_output}")
        print(f"Wrote JSON: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
