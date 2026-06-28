"""Curated round rebuild orchestrator for the GBM-AI training data chain.

One command that regenerates every report which depends on the curated
expansion fixtures: combined import, provenance diff, gold seed, gold pack,
evidence pack, relation pack, relation quality, the top-level governance
reports, promotion review/planning, the governance suites, and the governance
detail export/contract.

This is an observe-only research convenience wrapper around the existing
console scripts. It does NOT promote a dataset, train a model, or claim that a
validated GBM-BERT model exists. Platform verification (``gbmbert-verify-local``)
and the CI summary remain a separate downstream step.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from gbmbert.datasets import RESEARCH_WARNING

DEFAULT_CURATED_DIR = Path("data/training/curated_expansion")
DEFAULT_IMPORT_DIR = Path("data/training/curated_import")


@dataclass(frozen=True)
class CuratedRound:
    round_number: int
    evidence: str
    entity: str
    reviewed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RebuildStep:
    name: str
    command: list[str]
    passed: bool
    returncode: int
    detail: str


@dataclass(frozen=True)
class CuratedRoundRebuildReport:
    created_at_utc: str
    curated_dir: str
    import_dir: str
    round_count: int
    rounds: list[CuratedRound]
    passed: bool
    step_count: int
    passed_step_count: int
    failed_step_count: int
    steps: list[RebuildStep]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def discover_curated_rounds(curated_dir: str | Path = DEFAULT_CURATED_DIR) -> tuple[list[CuratedRound], list[str]]:
    """Discover ordered curated expansion rounds and any partial-round warnings.

    Round 1 is the base trio (``evidence_full_label`` / ``gold_entities`` /
    ``gold_reviewed_queue``); rounds 2+ are the ``*_round{N}`` trios. Only rounds
    whose three files all exist are returned; partial rounds become warnings.
    """

    root = Path(curated_dir)
    warnings: list[str] = []
    rounds: list[CuratedRound] = []

    specs: list[tuple[int, str, str, str]] = [
        (1, "evidence_full_label.jsonl", "gold_entities.jsonl", "gold_reviewed_queue.jsonl"),
    ]
    for number in _discovered_round_numbers(root):
        specs.append(
            (
                number,
                f"evidence_round{number}.jsonl",
                f"gold_entities_round{number}.jsonl",
                f"gold_reviewed_queue_round{number}.jsonl",
            )
        )

    for number, evidence_name, entity_name, reviewed_name in specs:
        evidence = root / evidence_name
        entity = root / entity_name
        reviewed = root / reviewed_name
        missing = [str(path) for path in (evidence, entity, reviewed) if not path.exists()]
        if missing:
            warnings.append(f"round {number} is missing files: {', '.join(missing)}")
            continue
        rounds.append(
            CuratedRound(
                round_number=number,
                evidence=str(evidence),
                entity=str(entity),
                reviewed=str(reviewed),
            )
        )

    if not rounds:
        warnings.append(f"no complete curated rounds found under {root}")
    return rounds, warnings


def build_rebuild_commands(
    rounds: list[CuratedRound],
    *,
    import_dir: str | Path = DEFAULT_IMPORT_DIR,
) -> list[tuple[str, list[str]]]:
    """Build the ordered (name, command) list for the curated round rebuild."""

    import_root = Path(import_dir)
    combined_evidence = str(import_root / "combined_evidence.jsonl")
    combined_entities = str(import_root / "combined_entities.jsonl")
    combined_reviewed = str(import_root / "combined_reviewed_queue.jsonl")
    gold_relations = "data/training/gold_seed/gold_relations.jsonl"

    evidence_flags: list[str] = []
    entity_flags: list[str] = []
    reviewed_flags: list[str] = []
    for curated_round in rounds:
        evidence_flags += ["--evidence-jsonl", curated_round.evidence]
        entity_flags += ["--entity-jsonl", curated_round.entity]
        reviewed_flags += ["--reviewed-queue-jsonl", curated_round.reviewed]
    fixture_flags = [*evidence_flags, *entity_flags, *reviewed_flags]

    return [
        (
            "curated_fixture_import",
            [
                _console_script("gbmbert-import-curated-training-fixture"),
                *fixture_flags,
                "--output-dir",
                str(import_root),
                "--no-copy",
                "--markdown-output",
                "reports/training/curated_fixture_import.md",
                "--json-output",
                "reports/training/curated_fixture_import.json",
            ],
        ),
        (
            "curated_provenance_diff",
            [
                _console_script("gbmbert-curated-provenance-diff"),
                *fixture_flags,
                "--markdown-output",
                "reports/training/curated_provenance_diff.md",
                "--json-output",
                "reports/training/curated_provenance_diff.json",
                "--allow-findings",
            ],
        ),
        (
            "gold_seed",
            [
                _console_script("gbmbert-build-gold-seed-dataset"),
                "data/training/gold_seed",
                "--reviewed-queue-jsonl",
                combined_reviewed,
                "--entity-jsonl",
                combined_entities,
                "--json-output",
                "reports/training/gold_seed_manifest.json",
                "--markdown-output",
                "reports/training/gold_seed_manifest.md",
            ],
        ),
        (
            "gold_training_pack",
            [
                _console_script("gbmbert-build-gold-training-pack"),
                "--reviewed-queue-jsonl",
                combined_reviewed,
                "--entity-jsonl",
                combined_entities,
                "--output-dir",
                "data/training/gold_pack",
                "--reports-dir",
                "reports/training/gold_pack",
                "--allow-not-ready",
            ],
        ),
        (
            "evidence_training_pack",
            [
                _console_script("gbmbert-build-evidence-training-pack"),
                combined_evidence,
                "--output-dir",
                "data/training/evidence_pack",
                "--reports-dir",
                "reports/training/evidence_pack",
                "--allow-not-ready",
            ],
        ),
        (
            "relation_training_pack",
            [
                _console_script("gbmbert-build-relation-training-pack"),
                gold_relations,
                "--output-dir",
                "data/training/relation_pack",
                "--reports-dir",
                "reports/training/relation_pack",
                "--allow-not-ready",
            ],
        ),
        (
            "relation_dataset_quality",
            [
                _console_script("gbmbert-relation-dataset-quality"),
                gold_relations,
                "--markdown-output",
                "reports/training/relation_dataset_quality.md",
                "--json-output",
                "reports/training/relation_dataset_quality.json",
            ],
        ),
        (
            "training_config_suite_review",
            [
                _console_script("gbmbert-review-training-config-suite"),
                "--markdown-output",
                "reports/training/training_config_suite_review.md",
                "--json-output",
                "reports/training/training_config_suite_review.json",
            ],
        ),
        (
            "training_label_drift",
            [
                _console_script("gbmbert-training-label-drift"),
                "--markdown-output",
                "reports/training/training_label_drift.md",
                "--json-output",
                "reports/training/training_label_drift.json",
            ],
        ),
        (
            "training_pack_leakage_audit",
            [
                _console_script("gbmbert-audit-training-pack-leakage"),
                "--markdown-output",
                "reports/training/training_pack_leakage_audit.md",
                "--json-output",
                "reports/training/training_pack_leakage_audit.json",
            ],
        ),
        (
            "training_pack_comparison",
            [
                _console_script("gbmbert-compare-training-packs"),
                "--markdown-output",
                "reports/training/training_pack_comparison.md",
                "--json-output",
                "reports/training/training_pack_comparison.json",
            ],
        ),
        (
            "training_provenance_audit",
            [
                _console_script("gbmbert-audit-training-provenance"),
                "--markdown-output",
                "reports/training/training_provenance_audit.md",
                "--json-output",
                "reports/training/training_provenance_audit.json",
            ],
        ),
        (
            "training_readiness_snapshot",
            [
                _console_script("gbmbert-training-readiness-snapshot"),
                "--markdown-output",
                "reports/training/training_readiness_snapshot.md",
                "--json-output",
                "reports/training/training_readiness_snapshot.json",
            ],
        ),
        (
            "dashboard_training_manifest",
            [
                _console_script("gbmbert-dashboard-training-manifest"),
                "--output",
                "reports/training/dashboard_training_manifest.json",
                "--markdown-output",
                "reports/training/dashboard_training_manifest.md",
            ],
        ),
        (
            "gold_pack_promotion_review",
            [
                _console_script("gbmbert-review-gold-pack-promotion"),
                "--gold-pack-report",
                "reports/training/gold_pack/gold_training_pack.json",
                "--threshold-config",
                "configs/training/gold_pack_promotion_thresholds.json",
                "--markdown-output",
                "reports/training/gold_pack/gold_pack_promotion_review.md",
                "--json-output",
                "reports/training/gold_pack/gold_pack_promotion_review.json",
                "--allow-blockers",
            ],
        ),
        (
            "gold_pack_promotion_plan",
            [
                _console_script("gbmbert-plan-gold-pack-promotion"),
                "--markdown-output",
                "reports/training/gold_pack/gold_pack_promotion_plan.md",
                "--json-output",
                "reports/training/gold_pack/gold_pack_promotion_plan.json",
            ],
        ),
        (
            "training_governance_suite",
            [
                _console_script("gbmbert-run-training-governance-suite"),
                "--output-dir",
                "reports/training/governance",
            ],
        ),
        (
            "strict_training_governance",
            [
                _console_script("gbmbert-run-strict-training-governance"),
                "--output-dir",
                "reports/training/governance_strict",
                "--allow-findings",
            ],
        ),
        (
            "governance_detail_export",
            [
                _console_script("gbmbert-export-governance-detail-links"),
                "--markdown-output",
                "reports/training/governance_detail_links.md",
                "--json-output",
                "reports/training/governance_detail_links.json",
            ],
        ),
        (
            "governance_detail_contract",
            [
                _console_script("gbmbert-check-governance-detail-contract"),
                "--detail-json",
                "reports/training/governance_detail_links.json",
                "--markdown-output",
                "reports/training/governance_detail_contract.md",
                "--json-output",
                "reports/training/governance_detail_contract.json",
            ],
        ),
    ]


def run_curated_round_rebuild(
    *,
    curated_dir: str | Path = DEFAULT_CURATED_DIR,
    import_dir: str | Path = DEFAULT_IMPORT_DIR,
    runner: CommandRunner | None = None,
) -> CuratedRoundRebuildReport:
    """Run the ordered curated round rebuild sequence and return a report."""

    rounds, warnings = discover_curated_rounds(curated_dir)
    command_runner = runner or _run_command
    steps: list[RebuildStep] = []

    if rounds:
        for name, command in build_rebuild_commands(rounds, import_dir=import_dir):
            result = command_runner(command)
            steps.append(
                RebuildStep(
                    name=name,
                    command=command,
                    passed=result.returncode == 0,
                    returncode=result.returncode,
                    detail=_command_detail(result),
                )
            )

    warnings = list(warnings) + [f"{step.name} failed: {step.detail}" for step in steps if not step.passed]
    return CuratedRoundRebuildReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        curated_dir=str(Path(curated_dir)),
        import_dir=str(Path(import_dir)),
        round_count=len(rounds),
        rounds=rounds,
        passed=bool(rounds) and not warnings,
        step_count=len(steps),
        passed_step_count=sum(1 for step in steps if step.passed),
        failed_step_count=sum(1 for step in steps if not step.passed),
        steps=steps,
        warnings=warnings,
    )


def save_curated_round_rebuild_json(report: CuratedRoundRebuildReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_curated_round_rebuild_markdown(report: CuratedRoundRebuildReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_curated_round_rebuild_markdown(report), encoding="utf-8")
    return output_path


def format_curated_round_rebuild_markdown(report: CuratedRoundRebuildReport) -> str:
    lines = [
        "# GBM-AI Curated Round Rebuild",
        "",
        RESEARCH_WARNING,
        "",
        "Observe-only research rebuild of the curated-fixture report chain. It does not "
        "promote a dataset, train a model, or claim a validated GBM-BERT model exists. Run "
        "`gbmbert-verify-local` and the CI summary afterward for platform verification.",
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Curated dir: `{report.curated_dir}`",
        f"- Import dir: `{report.import_dir}`",
        f"- Rounds: {report.round_count}",
        f"- Passed: {report.passed}",
        f"- Steps: {report.passed_step_count}/{report.step_count} passed",
        "",
        "## Rounds",
    ]
    lines.extend(
        [f"- Round {curated_round.round_number}: `{curated_round.evidence}`" for curated_round in report.rounds]
        or ["- none"]
    )
    lines.extend(["", "## Ordered Steps"])
    for step in report.steps:
        lines.extend(
            [
                f"### {step.name}",
                f"- Status: {'pass' if step.passed else 'fail'}",
                f"- Return code: {step.returncode}",
                f"- Detail: {step.detail or 'none'}",
                "",
            ]
        )
    lines.extend(["## Warnings", *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"])])
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild every report derived from the curated expansion fixtures.")
    parser.add_argument("--curated-dir", type=Path, default=DEFAULT_CURATED_DIR)
    parser.add_argument("--import-dir", type=Path, default=DEFAULT_IMPORT_DIR)
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/curated_round_rebuild.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/curated_round_rebuild.md"))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = run_curated_round_rebuild(curated_dir=args.curated_dir, import_dir=args.import_dir)
    save_curated_round_rebuild_json(report, args.json_output)
    save_curated_round_rebuild_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curated_round_rebuild_markdown(report))
    return 0 if report.passed else 1


def _discovered_round_numbers(root: Path) -> list[int]:
    numbers: list[int] = []
    for path in root.glob("evidence_round*.jsonl"):
        suffix = path.stem[len("evidence_round") :]
        if suffix.isdigit():
            numbers.append(int(suffix))
    return sorted(numbers)


def _console_script(name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    script = Path(sys.executable).parent / f"{name}{suffix}"
    return str(script) if script.exists() else name


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def _command_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    tail = " | ".join(lines[-3:])
    return tail[:600] or f"returncode={result.returncode}"


if __name__ == "__main__":
    raise SystemExit(main())
