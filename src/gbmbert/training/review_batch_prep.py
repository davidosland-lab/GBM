"""Real-annotation review-batch prep/finalize helper (PR161-real).

Two observe-only phases that turn real PubMed abstracts into a human-reviewed
curated round which the PR158 rebuild orchestrator then discovers:

  prep      ingest (optional) -> offline lexicon pipeline -> export review queue
            -> init reviewed-queue skeleton + entities, under a staging dir, with
            a human-review INSTRUCTIONS file. The offline lexicon entity mode is
            used so the prep runs without Hugging Face access.

  finalize  after a human fills in the reviewed-queue judgments, validate that no
            row is still ``pending``, derive the evidence_round{N} rows from the
            accepted evidence claims, and promote the three round files into the
            curated-expansion dir so ``gbmbert-rebuild-curated-rounds`` picks them
            up.

Research-use only. The entity spans are lexicon-suggested (not span-reviewed);
the evidence tiers and relations are the human-reviewed signal. This helper does
not promote a dataset or claim a validated GBM-BERT model exists.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from gbmbert.datasets import RESEARCH_WARNING

DEFAULT_CURATED_DIR = Path("data/training/curated_expansion")
DEFAULT_STAGING_ROOT = Path("data/research/review_batches")
DEFAULT_LEXICON = Path("configs/extraction/lexicon_gbm_v1.json")
DEFAULT_MAX_CONFIDENCE = 0.95
PENDING_STATUS = "pending"
ACCEPTED_STATUS = "accepted"
REJECTED_STATUS = "rejected"

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class PrepStep:
    name: str
    command: list[str]
    passed: bool
    returncode: int
    detail: str


@dataclass(frozen=True)
class ReviewBatchPrepReport:
    created_at_utc: str
    round_number: int
    staging_dir: str
    pubmed_jsonl: str
    reviewed_queue_path: str
    entities_path: str
    instructions_path: str
    passed: bool
    step_count: int
    steps: list[PrepStep]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewBatchFinalizeReport:
    created_at_utc: str
    round_number: int
    staging_dir: str
    curated_dir: str
    reviewed_total: int
    pending_count: int
    accepted_evidence: int
    accepted_relations: int
    rejected_count: int
    ready: bool
    promoted: bool
    curated_files: list[str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- prep


def build_prep_commands(
    *,
    round_number: int,
    pubmed_jsonl: str | Path,
    staging_dir: str | Path,
    reviewer: str,
    lexicon: str | Path = DEFAULT_LEXICON,
    max_confidence: float = DEFAULT_MAX_CONFIDENCE,
    query_pack: str | None = None,
) -> list[tuple[str, list[str]]]:
    """Build the ordered (name, command) list for the prep phase."""

    staging = Path(staging_dir)
    pubmed_path = Path(pubmed_jsonl)
    pipeline_dir = staging / "pipeline"
    review_queue = staging / "review_queue.jsonl"
    reviewed_queue = staging / f"gold_reviewed_queue_round{round_number}.jsonl"

    commands: list[tuple[str, list[str]]] = []
    if query_pack:
        commands.append(
            (
                "search_pubmed",
                [
                    _console_script("gbmbert-search-pubmed"),
                    "--query-pack",
                    query_pack,
                    "--output",
                    str(pubmed_path),
                ],
            )
        )
    commands.extend(
        [
            (
                "literature_pipeline_lexicon",
                [
                    _console_script("gbmbert-run-pipeline"),
                    str(pubmed_path),
                    "--output-dir",
                    str(pipeline_dir),
                    "--entity-mode",
                    "lexicon",
                    "--lexicon",
                    str(lexicon),
                ],
            ),
            (
                "export_review_queue",
                [
                    _console_script("gbmbert-export-review-queue"),
                    "--evidence-jsonl",
                    str(pipeline_dir / "evidence_claims.jsonl"),
                    "--graph-jsonl",
                    str(pipeline_dir / "graph_records.jsonl"),
                    "--output",
                    str(review_queue),
                    "--max-confidence",
                    str(max_confidence),
                ],
            ),
            (
                "init_reviewed_queue",
                [
                    _console_script("gbmbert-init-reviewed-queue"),
                    str(review_queue),
                    str(reviewed_queue),
                    "--reviewer",
                    reviewer,
                ],
            ),
        ]
    )
    return commands


def run_review_batch_prep(
    *,
    round_number: int,
    pubmed_jsonl: str | Path,
    staging_dir: str | Path | None = None,
    reviewer: str,
    lexicon: str | Path = DEFAULT_LEXICON,
    max_confidence: float = DEFAULT_MAX_CONFIDENCE,
    query_pack: str | None = None,
    runner: CommandRunner | None = None,
) -> ReviewBatchPrepReport:
    """Run the prep phase: build a human-review skeleton from real abstracts."""

    staging = Path(staging_dir) if staging_dir else DEFAULT_STAGING_ROOT / f"round{round_number}"
    staging.mkdir(parents=True, exist_ok=True)
    command_runner = runner or _run_command
    pubmed_path = Path(pubmed_jsonl)
    reviewed_queue = staging / f"gold_reviewed_queue_round{round_number}.jsonl"
    entities_target = staging / f"gold_entities_round{round_number}.jsonl"
    instructions = staging / "INSTRUCTIONS.md"

    steps: list[PrepStep] = []
    for name, command in build_prep_commands(
        round_number=round_number,
        pubmed_jsonl=pubmed_path,
        staging_dir=staging,
        reviewer=reviewer,
        lexicon=lexicon,
        max_confidence=max_confidence,
        query_pack=query_pack,
    ):
        result = command_runner(command)
        steps.append(
            PrepStep(
                name=name,
                command=command,
                passed=result.returncode == 0,
                returncode=result.returncode,
                detail=_command_detail(result),
            )
        )

    warnings = [f"{step.name} failed: {step.detail}" for step in steps if not step.passed]

    # Promote the lexicon entities into the round's entity file (best-effort).
    pipeline_entities = staging / "pipeline" / "entities.jsonl"
    if pipeline_entities.exists():
        shutil.copyfile(pipeline_entities, entities_target)
    else:
        warnings.append(f"pipeline entities not found, entities file not staged: {pipeline_entities}")

    instructions.write_text(_prep_instructions(round_number, reviewed_queue, entities_target), encoding="utf-8")

    return ReviewBatchPrepReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        round_number=round_number,
        staging_dir=str(staging),
        pubmed_jsonl=str(pubmed_path),
        reviewed_queue_path=str(reviewed_queue),
        entities_path=str(entities_target),
        instructions_path=str(instructions),
        passed=not warnings,
        step_count=len(steps),
        steps=steps,
        warnings=warnings,
    )


# ----------------------------------------------------------------------- finalize


def finalize_review_batch(
    *,
    round_number: int,
    staging_dir: str | Path | None = None,
    curated_dir: str | Path = DEFAULT_CURATED_DIR,
) -> ReviewBatchFinalizeReport:
    """Validate a human-reviewed batch and, when complete, promote it to the curated dir."""

    staging = Path(staging_dir) if staging_dir else DEFAULT_STAGING_ROOT / f"round{round_number}"
    curated = Path(curated_dir)
    reviewed_path = staging / f"gold_reviewed_queue_round{round_number}.jsonl"
    entities_path = staging / f"gold_entities_round{round_number}.jsonl"

    warnings: list[str] = []
    rows = _read_jsonl(reviewed_path) if reviewed_path.exists() else []
    if not reviewed_path.exists():
        warnings.append(f"reviewed queue not found: {reviewed_path}")

    pending = [r for r in rows if str(r.get("review_status") or PENDING_STATUS) == PENDING_STATUS]
    rejected = [r for r in rows if str(r.get("review_status")) == REJECTED_STATUS]
    accepted = [r for r in rows if str(r.get("review_status")) == ACCEPTED_STATUS]
    accepted_evidence = [r for r in accepted if str(r.get("item_type")) == "evidence_claim"]
    accepted_relations = [r for r in accepted if str(r.get("item_type")) == "graph_relation"]

    if pending:
        warnings.append(f"{len(pending)} reviewed-queue row(s) still '{PENDING_STATUS}'; annotate them before finalizing")
    for row in accepted_evidence:
        if _evidence_tier(row) is None:
            warnings.append(f"accepted evidence claim missing a numeric tier: {row.get('item_id')}")
    for row in accepted_relations:
        if not str(row.get("corrected_relation_type") or row.get("relation_type") or "").strip():
            warnings.append(f"accepted relation missing relation_type: {row.get('item_id')}")
    if not entities_path.exists():
        warnings.append(f"entities file not found: {entities_path}")
    if rows and not accepted_evidence:
        warnings.append("no accepted evidence claims; the round would add no evidence examples")

    ready = bool(rows) and not warnings
    promoted = False
    curated_files: list[str] = []
    if ready:
        curated.mkdir(parents=True, exist_ok=True)
        evidence_rows = [_evidence_row_from_reviewed(row) for row in accepted_evidence]
        evidence_target = curated / f"evidence_round{round_number}.jsonl"
        _write_jsonl(evidence_target, evidence_rows)
        reviewed_target = curated / f"gold_reviewed_queue_round{round_number}.jsonl"
        entities_target = curated / f"gold_entities_round{round_number}.jsonl"
        _write_jsonl(reviewed_target, accepted)  # only accepted rows enter the corpus
        shutil.copyfile(entities_path, entities_target)
        curated_files = [str(evidence_target), str(reviewed_target), str(entities_target)]
        promoted = True

    return ReviewBatchFinalizeReport(
        created_at_utc=datetime.now(UTC).isoformat(),
        round_number=round_number,
        staging_dir=str(staging),
        curated_dir=str(curated),
        reviewed_total=len(rows),
        pending_count=len(pending),
        accepted_evidence=len(accepted_evidence),
        accepted_relations=len(accepted_relations),
        rejected_count=len(rejected),
        ready=ready,
        promoted=promoted,
        curated_files=curated_files,
        warnings=warnings,
    )


# ------------------------------------------------------------------------- output


def save_prep_report_json(report: ReviewBatchPrepReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def save_finalize_report_json(report: ReviewBatchFinalizeReport, path: str | Path) -> Path:
    return _write_json(report.to_dict(), path)


def format_prep_report_markdown(report: ReviewBatchPrepReport) -> str:
    lines = [
        "# Review Batch Prep",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Round: {report.round_number}",
        f"- Staging dir: `{report.staging_dir}`",
        f"- Reviewed-queue skeleton: `{report.reviewed_queue_path}`",
        f"- Entities: `{report.entities_path}`",
        f"- Instructions: `{report.instructions_path}`",
        f"- Passed: {report.passed}",
        "",
        "## Steps",
    ]
    for step in report.steps:
        lines.append(f"- {step.name}: {'pass' if step.passed else 'fail'} (rc {step.returncode})")
    lines.extend(["", "## Warnings", *([f"- {w}" for w in report.warnings] if report.warnings else ["- none"])])
    return "\n".join(lines).rstrip() + "\n"


def format_finalize_report_markdown(report: ReviewBatchFinalizeReport) -> str:
    lines = [
        "# Review Batch Finalize",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created UTC: {report.created_at_utc}",
        f"- Round: {report.round_number}",
        f"- Curated dir: `{report.curated_dir}`",
        f"- Reviewed rows: {report.reviewed_total}",
        f"- Pending: {report.pending_count}",
        f"- Accepted evidence: {report.accepted_evidence}",
        f"- Accepted relations: {report.accepted_relations}",
        f"- Rejected: {report.rejected_count}",
        f"- Ready: {report.ready}",
        f"- Promoted to curated dir: {report.promoted}",
        "",
        "## Promoted Files",
        *([f"- `{path}`" for path in report.curated_files] if report.curated_files else ["- none"]),
        "",
        "## Warnings",
        *([f"- {w}" for w in report.warnings] if report.warnings else ["- none"]),
    ]
    if report.promoted:
        lines.extend(["", "Run `gbmbert-rebuild-curated-rounds` then `gbmbert-verify-local` to integrate this round."])
    return "\n".join(lines).rstrip() + "\n"


# ----------------------------------------------------------------------------- CLI


def build_prep_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prep a human-review batch from real PubMed abstracts (offline lexicon mode).")
    parser.add_argument("--round", type=int, required=True, dest="round_number")
    parser.add_argument("--pubmed-jsonl", type=Path, required=True, help="Real PubMed records JSONL (input or search output path).")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--query-pack", default=None, help="If set, fetch the pubmed-jsonl from this PubMed query pack first.")
    parser.add_argument("--staging-dir", type=Path, default=None)
    parser.add_argument("--lexicon", type=Path, default=DEFAULT_LEXICON)
    parser.add_argument("--max-confidence", type=float, default=DEFAULT_MAX_CONFIDENCE)
    parser.add_argument("--json", action="store_true")
    return parser


def build_finalize_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Finalize a human-reviewed batch and promote it into the curated rounds.")
    parser.add_argument("--round", type=int, required=True, dest="round_number")
    parser.add_argument("--staging-dir", type=Path, default=None)
    parser.add_argument("--curated-dir", type=Path, default=DEFAULT_CURATED_DIR)
    parser.add_argument("--json", action="store_true")
    return parser


def prep_main(argv: list[str] | None = None) -> int:
    args = build_prep_arg_parser().parse_args(argv)
    report = run_review_batch_prep(
        round_number=args.round_number,
        pubmed_jsonl=args.pubmed_jsonl,
        staging_dir=args.staging_dir,
        reviewer=args.reviewer,
        lexicon=args.lexicon,
        max_confidence=args.max_confidence,
        query_pack=args.query_pack,
    )
    save_prep_report_json(report, Path(report.staging_dir) / "prep_report.json")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_prep_report_markdown(report))
    return 0 if report.passed else 1


def finalize_main(argv: list[str] | None = None) -> int:
    args = build_finalize_arg_parser().parse_args(argv)
    report = finalize_review_batch(
        round_number=args.round_number,
        staging_dir=args.staging_dir,
        curated_dir=args.curated_dir,
    )
    save_finalize_report_json(report, Path(report.staging_dir) / "finalize_report.json")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_finalize_report_markdown(report))
    return 0 if report.ready else 1


# ------------------------------------------------------------------------- helpers


def _evidence_row_from_reviewed(row: dict[str, Any]) -> dict[str, Any]:
    tier = _evidence_tier(row)
    pmid = str(row.get("source_pmid") or "").strip()
    return {
        "item_id": str(row.get("item_id") or f"reviewed-evidence:{pmid}:{tier}"),
        "label": int(tier) if tier is not None else 0,
        "review_notes": str(row.get("review_notes") or "Human-reviewed evidence claim."),
        "review_status": ACCEPTED_STATUS,
        "reviewer": str(row.get("reviewer") or ""),
        "source_pmid": pmid,
        "task": "evidence",
        "text": str(row.get("text") or ""),
        "warning": RESEARCH_WARNING,
    }


def _evidence_tier(row: dict[str, Any]) -> int | None:
    raw = row.get("corrected_evidence_tier")
    if raw is None:
        raw = row.get("evidence_tier")
    try:
        return int(raw) if raw is not None and str(raw) != "" else None
    except (TypeError, ValueError):
        return None


def _prep_instructions(round_number: int, reviewed_queue: Path, entities: Path) -> str:
    return "\n".join(
        [
            f"# Review Batch Round {round_number} — Instructions",
            "",
            RESEARCH_WARNING,
            "",
            f"Annotate the reviewed-queue skeleton, then finalize round {round_number}.",
            "",
            f"1. Open `{reviewed_queue}`. Each line is one item (evidence_claim or graph_relation).",
            "2. For every row, set `review_status` to `accepted` or `rejected` (it starts as `pending`).",
            "   - evidence_claim: verify/correct `evidence_tier` (0-5) or set `corrected_evidence_tier`.",
            "   - graph_relation: verify/correct `relation_type` or set `corrected_relation_type`.",
            "   - add a one-line `review_notes` rationale.",
            f"3. Entity spans in `{entities}` are lexicon-suggested (not span-reviewed); leave or trim as needed.",
            f"4. Run `gbmbert-finalize-review-batch --round {round_number}`. It promotes the round into the",
            "   curated-expansion dir only when no row is still `pending`. Only accepted rows enter the corpus.",
            "5. Run `gbmbert-rebuild-curated-rounds` then `gbmbert-verify-local`.",
            "",
            "Research-use only. Tiers and relations are the human-reviewed signal; this does not promote a",
            "dataset or claim a validated GBM-BERT model exists.",
        ]
    )


def _console_script(name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    script = Path(sys.executable).parent / f"{name}{suffix}"
    return str(script) if script.exists() else name


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def _command_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return (" | ".join(lines[-3:]))[:600] or f"returncode={result.returncode}"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def _write_json(payload: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output
