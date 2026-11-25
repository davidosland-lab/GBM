"""Gold-pack operations status: pack health, backlog, and next actions.

Research-use only. Not medical advice. Not intended for diagnosis, treatment
selection, or clinical decision-making. Promotable ≠ clinically validated.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.ner_bio import SPARSE_ENTITY_TYPES
from gbmbert.training.promotion_review import review_gold_pack_promotion


DEFAULT_SOFT_DENSIFY_FLOORS: dict[str, dict[str, int]] = {
    "ner": {
        "CELL_STATE": 150,
        "PATHWAY": 120,
        "TRIAL_PHASE": 100,
        "UNKNOWN": 80,
    },
    "relation": {
        "IMPROVES": 60,
        "PREDICTS": 60,
        "WORSENS": 60,
    },
    "evidence": {
        "0": 120,
        "1": 120,
        "2": 120,
        "4": 120,
        "5": 120,
    },
}

DEFAULT_REVIEW_BATCH_ROOT = Path("data/research/review_batches")
DEFAULT_AL_BATCH_PATHS = (
    Path("data/processed/curation_regression_pack/active_learning_batches_round26.jsonl"),
    Path("data/processed/curation_regression_pack/active_learning_batches.jsonl"),
    Path("data/review/active_learning_batches.jsonl"),
)
DEFAULT_ENTITY_GLOB = "data/training/curated_expansion/gold_entities*.jsonl"
PENDING_STATUSES = {"pending", ""}
ACTIVE_QUEUE_NAME_HINTS = (
    "span_review",
    "entity_span",
    "active_learning",
    "gold_reviewed_queue",
    "dual_review",
)


@dataclass(frozen=True)
class SoftDensifyGap:
    task: str
    label: str
    count: int
    soft_floor: int
    delta: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BacklogQueue:
    path: str
    queue_kind: str
    total_rows: int
    pending_rows: int
    decided_rows: int
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GoldPackOpsStatusReport:
    created_at_utc: str
    gold_pack_report: str
    threshold_config: str
    pack_ready: bool
    promotable: bool
    task_counts: dict[str, int]
    label_counts: dict[str, dict[str, int]]
    source_pmid_count: int
    promotion_blockers: list[str]
    task_example_deltas: dict[str, int]
    label_example_deltas: dict[str, dict[str, int]]
    source_pmid_delta: int
    soft_densify_gaps: list[SoftDensifyGap]
    sparse_label_counts: dict[str, int]
    dual_review_backlog: list[BacklogQueue]
    active_learning_backlog: list[BacklogQueue]
    dual_review_pending_total: int
    active_learning_pending_total: int
    next_actions: list[str]
    differentiation_bet: str
    clinical_validity_claimed: bool = False
    warning: str = RESEARCH_WARNING
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["soft_densify_gaps"] = [gap.to_dict() for gap in self.soft_densify_gaps]
        payload["dual_review_backlog"] = [item.to_dict() for item in self.dual_review_backlog]
        payload["active_learning_backlog"] = [item.to_dict() for item in self.active_learning_backlog]
        return payload


@dataclass(frozen=True)
class SparseDensifyBatchReport:
    created_at_utc: str
    round_id: int
    output_dir: str
    r1_jsonl: str
    r2_jsonl: str
    csv_output: str
    instructions_path: str
    span_count: int
    document_count: int
    label_counts: dict[str, int]
    target_labels: list[str]
    pending_for_human: bool
    warning: str = RESEARCH_WARNING
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_gold_pack_ops_status(
    *,
    gold_pack_report: str | Path = Path("reports/training/gold_pack/gold_training_pack.json"),
    threshold_config: str | Path | None = Path("configs/training/gold_pack_promotion_thresholds.json"),
    soft_densify_floors: dict[str, dict[str, int]] | None = None,
    review_batch_root: str | Path = DEFAULT_REVIEW_BATCH_ROOT,
    active_learning_batch_paths: list[str | Path] | None = None,
) -> GoldPackOpsStatusReport:
    """Aggregate pack health, soft densify gaps, and review/AL backlog into one report."""

    review = review_gold_pack_promotion(
        gold_pack_report=gold_pack_report,
        threshold_config=threshold_config,
    )
    floors = soft_densify_floors or DEFAULT_SOFT_DENSIFY_FLOORS
    soft_gaps = _soft_densify_gaps(review.label_counts, floors)
    sparse_counts = {
        label: int(review.label_counts.get("ner", {}).get(label, 0))
        for label in (*SPARSE_ENTITY_TYPES, "UNKNOWN")
    }

    dual_backlog = _scan_review_backlog(Path(review_batch_root))
    al_paths = [Path(p) for p in (active_learning_batch_paths or DEFAULT_AL_BATCH_PATHS)]
    al_backlog = _scan_active_learning_backlog(al_paths)
    dual_pending = sum(item.pending_rows for item in dual_backlog)
    al_pending = sum(item.pending_rows for item in al_backlog)
    next_actions = _next_actions(
        promotable=review.promotable,
        blockers=review.blockers,
        soft_gaps=soft_gaps,
        dual_pending=dual_pending,
        al_pending=al_pending,
        dual_backlog=dual_backlog,
        al_backlog=al_backlog,
    )
    notes = [
        "Ops status is research-governance observability only.",
        "Hard promotion floors and soft densify targets are distinct; soft gaps do not block promotable.",
        "Do not invent dual-review labels; adjudicate pending queues as a human.",
    ]
    return GoldPackOpsStatusReport(
        created_at_utc=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        gold_pack_report=review.gold_pack_report,
        threshold_config=review.threshold_config,
        pack_ready=review.pack_ready,
        promotable=review.promotable,
        task_counts=dict(review.task_counts),
        label_counts={task: dict(labels) for task, labels in review.label_counts.items()},
        source_pmid_count=review.source_pmid_count,
        promotion_blockers=list(review.blockers),
        task_example_deltas=dict(review.task_example_deltas),
        label_example_deltas={task: dict(labels) for task, labels in review.label_example_deltas.items()},
        source_pmid_delta=review.source_pmid_delta,
        soft_densify_gaps=soft_gaps,
        sparse_label_counts=sparse_counts,
        dual_review_backlog=dual_backlog,
        active_learning_backlog=al_backlog,
        dual_review_pending_total=dual_pending,
        active_learning_pending_total=al_pending,
        next_actions=next_actions,
        differentiation_bet=(
            "Invest in gold-pack / curation / governance depth rather than lit-mining scale or clinical ranking."
        ),
        notes=notes,
    )


def export_sparse_densify_dual_review_batch(
    *,
    round_id: int = 33,
    entities_glob: str = DEFAULT_ENTITY_GLOB,
    output_dir: str | Path | None = None,
    target_labels: tuple[str, ...] | list[str] | None = None,
    max_spans_per_label: int = 12,
    reviewer_r1: str = "",
    reviewer_r2: str = "",
    root: str | Path = ".",
) -> SparseDensifyBatchReport:
    """Export a pending dual-review queue for sparse NER labels (no invented decisions)."""

    labels = tuple(target_labels or (*SPARSE_ENTITY_TYPES, "UNKNOWN"))
    base = Path(root)
    out_dir = Path(output_dir) if output_dir else base / f"data/research/review_batches/round{round_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = _select_sparse_spans(
        entities_glob=entities_glob,
        target_labels=labels,
        max_spans_per_label=max_spans_per_label,
        root=base,
    )
    rows: list[dict[str, Any]] = []
    label_counts: dict[str, int] = {}
    pmids: set[str] = set()
    for index, item in enumerate(selected):
        label = str(item["label"])
        label_counts[label] = label_counts.get(label, 0) + 1
        pmids.add(str(item["source_pmid"]))
        rows.append(
            {
                "item_id": f"span:round{round_id}:{item['source_pmid']}:{index}",
                "item_type": "entity_span",
                "source_pmid": item["source_pmid"],
                "text": item["text"],
                "context_text": item["context_text"],
                "label": label,
                "start": item["start"],
                "end": item["end"],
                "confidence": item.get("confidence"),
                "normalized_text": item.get("normalized_text") or str(item["text"]).lower(),
                "review_status": "pending",
                "corrected_label": None,
                "corrected_start": None,
                "corrected_end": None,
                "corrected_text": None,
                "reviewer": reviewer_r1,
                "review_notes": f"round{round_id} sparse densify dual-review r1 pending",
                "source_entities_file": item["source_file"],
            }
        )
    r1_path = out_dir / f"span_review_r1_round{round_id}.jsonl"
    r2_path = out_dir / f"span_review_r2_round{round_id}.jsonl"
    csv_path = out_dir / f"span_review_dual_round{round_id}.csv"
    instructions_path = out_dir / "INSTRUCTIONS.md"
    _write_jsonl(r1_path, rows)
    r2_rows = []
    for row in rows:
        copy = dict(row)
        copy["reviewer"] = reviewer_r2
        copy["review_notes"] = f"round{round_id} sparse densify dual-review r2 pending"
        r2_rows.append(copy)
    _write_jsonl(r2_path, r2_rows)
    _write_span_csv(csv_path, rows)
    instructions = _format_sparse_batch_instructions(
        round_id=round_id,
        labels=labels,
        span_count=len(rows),
        document_count=len(pmids),
        label_counts=label_counts,
        r1_path=r1_path,
        r2_path=r2_path,
        csv_path=csv_path,
    )
    instructions_path.write_text(instructions, encoding="utf-8")
    return SparseDensifyBatchReport(
        created_at_utc=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        round_id=round_id,
        output_dir=str(out_dir),
        r1_jsonl=str(r1_path),
        r2_jsonl=str(r2_path),
        csv_output=str(csv_path),
        instructions_path=str(instructions_path),
        span_count=len(rows),
        document_count=len(pmids),
        label_counts=dict(sorted(label_counts.items())),
        target_labels=list(labels),
        pending_for_human=True,
        notes=[
            "All rows left pending for human dual-review; no labels invented.",
            "After adjudication, write consensus JSONL and promote via curated_expansion + rebuild.",
        ],
    )


def save_gold_pack_ops_status_json(report: GoldPackOpsStatusReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_gold_pack_ops_status_markdown(report: GoldPackOpsStatusReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_gold_pack_ops_status_markdown(report), encoding="utf-8")
    return output


def format_gold_pack_ops_status_markdown(report: GoldPackOpsStatusReport) -> str:
    lines = [
        "# Gold Pack Ops Status",
        "",
        RESEARCH_WARNING,
        "",
        f"- Created (UTC): `{report.created_at_utc}`",
        f"- Differentiation bet: {report.differentiation_bet}",
        f"- Gold pack report: `{report.gold_pack_report}`",
        f"- Threshold config: `{report.threshold_config or 'not provided'}`",
        f"- Pack ready: {report.pack_ready}",
        f"- Promotable (hard floors): {report.promotable}",
        f"- Source PMIDs: {report.source_pmid_count} (delta to floor: {report.source_pmid_delta})",
        f"- Dual-review pending rows: {report.dual_review_pending_total}",
        f"- Active-learning pending rows: {report.active_learning_pending_total}",
        f"- Clinical validity claimed: {report.clinical_validity_claimed}",
        "",
        "## Task Counts",
        *([f"- {task}: {count}" for task, count in sorted(report.task_counts.items())] or ["- none"]),
        "",
        "## Sparse NER Focus",
        *([f"- {label}: {count}" for label, count in sorted(report.sparse_label_counts.items())] or ["- none"]),
        "",
        "## Soft Densify Gaps (non-blocking)",
    ]
    if report.soft_densify_gaps:
        for gap in report.soft_densify_gaps:
            lines.append(
                f"- {gap.task}/{gap.label}: {gap.count} (soft floor {gap.soft_floor}; need +{gap.delta})"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Hard Promotion Blockers",
            *([f"- {blocker}" for blocker in report.promotion_blockers] or ["- none"]),
            "",
            "## Dual-Review Backlog",
        ]
    )
    if report.dual_review_backlog:
        for item in report.dual_review_backlog:
            lines.append(
                f"- `{item.path}` ({item.queue_kind}): pending={item.pending_rows}/"
                f"{item.total_rows} decided={item.decided_rows}"
                + (f" - {item.note}" if item.note else "")
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Active-Learning Backlog"])
    if report.active_learning_backlog:
        for item in report.active_learning_backlog:
            lines.append(
                f"- `{item.path}`: pending={item.pending_rows}/{item.total_rows} decided={item.decided_rows}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Actions",
            *([f"- {action}" for action in report.next_actions] or ["- none"]),
            "",
            "## Notes",
            *([f"- {note}" for note in report.notes] or ["- none"]),
            "",
            "## Label Counts",
        ]
    )
    for task, counts in sorted(report.label_counts.items()):
        lines.append(f"### {task}")
        lines.extend([f"- {label}: {count}" for label, count in sorted(counts.items())] or ["- none"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_ops_status_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report gold-pack ops health (counts, soft densify gaps, dual-review/AL backlog, next actions). "
            "Research-use only; not clinical validation."
        )
    )
    parser.add_argument("--gold-pack-report", type=Path, default=Path("reports/training/gold_pack/gold_training_pack.json"))
    parser.add_argument("--threshold-config", type=Path, default=Path("configs/training/gold_pack_promotion_thresholds.json"))
    parser.add_argument("--review-batch-root", type=Path, default=DEFAULT_REVIEW_BATCH_ROOT)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/training/gold_pack/gold_pack_ops_status.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/training/gold_pack/gold_pack_ops_status.md"),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def build_sparse_batch_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a pending sparse-NER dual-review densify batch for human adjudication. "
            "Does not invent labels. Research-use only."
        )
    )
    parser.add_argument("--round", type=int, default=33)
    parser.add_argument("--entities-glob", default=DEFAULT_ENTITY_GLOB)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-spans-per-label", type=int, default=12)
    parser.add_argument("--reviewer-r1", default="")
    parser.add_argument("--reviewer-r2", default="")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/training/gold_pack/sparse_densify_batch_round33.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/training/gold_pack/sparse_densify_batch_round33.md"),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def ops_status_main(argv: list[str] | None = None) -> int:
    args = build_ops_status_arg_parser().parse_args(argv)
    report = build_gold_pack_ops_status(
        gold_pack_report=args.gold_pack_report,
        threshold_config=args.threshold_config,
        review_batch_root=args.review_batch_root,
    )
    save_gold_pack_ops_status_json(report, args.json_output)
    save_gold_pack_ops_status_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_gold_pack_ops_status_markdown(report))
    return 0


def sparse_densify_batch_main(argv: list[str] | None = None) -> int:
    args = build_sparse_batch_arg_parser().parse_args(argv)
    report = export_sparse_densify_dual_review_batch(
        round_id=args.round,
        entities_glob=args.entities_glob,
        output_dir=args.output_dir,
        max_spans_per_label=args.max_spans_per_label,
        reviewer_r1=args.reviewer_r1,
        reviewer_r2=args.reviewer_r2,
    )
    json_path = Path(args.json_output)
    md_path = Path(args.markdown_output)
    if args.round != 33:
        json_path = json_path.with_name(f"sparse_densify_batch_round{args.round}.json")
        md_path = md_path.with_name(f"sparse_densify_batch_round{args.round}.md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_sparse_batch_report_markdown(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(_format_sparse_batch_report_markdown(report))
    return 0


def main(argv: list[str] | None = None) -> int:
    return ops_status_main(argv)


def _soft_densify_gaps(
    label_counts: dict[str, dict[str, int]],
    floors: dict[str, dict[str, int]],
) -> list[SoftDensifyGap]:
    gaps: list[SoftDensifyGap] = []
    for task, task_floors in sorted(floors.items()):
        counts = label_counts.get(task) or {}
        for label, floor in sorted(task_floors.items()):
            count = int(counts.get(label, 0))
            if count < int(floor):
                gaps.append(
                    SoftDensifyGap(
                        task=task,
                        label=label,
                        count=count,
                        soft_floor=int(floor),
                        delta=max(0, int(floor) - count),
                    )
                )
    return gaps


def _scan_review_backlog(root: Path) -> list[BacklogQueue]:
    if not root.exists():
        return []
    backlog: list[BacklogQueue] = []
    for path in sorted(root.rglob("*.jsonl")):
        name = path.name.lower()
        if not any(hint in name for hint in ACTIVE_QUEUE_NAME_HINTS):
            continue
        if "consensus" in name or "adjudication" in name:
            continue
        total, pending, decided = _count_review_statuses(path)
        if pending <= 0:
            continue
        kind = "entity_span" if "span" in name else "reviewed_queue"
        note = ""
        if "round28" in str(path).lower() and pending == total:
            note = "legacy unfinished span queue; prefer latest sparse densify round"
        backlog.append(
            BacklogQueue(
                path=str(path),
                queue_kind=kind,
                total_rows=total,
                pending_rows=pending,
                decided_rows=decided,
                note=note,
            )
        )
    backlog.sort(
        key=lambda item: (
            1 if item.note.startswith("legacy") else 0,
            -item.pending_rows,
            item.path,
        )
    )
    return backlog[:40]


def _scan_active_learning_backlog(paths: list[Path]) -> list[BacklogQueue]:
    backlog: list[BacklogQueue] = []
    seen: set[str] = set()
    for path in paths:
        resolved = str(path)
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        total, pending, decided = _count_review_statuses(path)
        if total <= 0:
            continue
        backlog.append(
            BacklogQueue(
                path=str(path),
                queue_kind="active_learning_batch",
                total_rows=total,
                pending_rows=pending,
                decided_rows=decided,
                note="export CSV / adjudicate before import" if pending else "",
            )
        )
    return backlog


def _count_review_statuses(path: Path) -> tuple[int, int, int]:
    total = pending = decided = 0
    for row in _read_jsonl(path):
        total += 1
        status = str(row.get("review_status") or row.get("status") or "").strip().lower()
        if status in PENDING_STATUSES:
            pending += 1
        else:
            decided += 1
    return total, pending, decided


def _next_actions(
    *,
    promotable: bool,
    blockers: list[str],
    soft_gaps: list[SoftDensifyGap],
    dual_pending: int,
    al_pending: int,
    dual_backlog: list[BacklogQueue],
    al_backlog: list[BacklogQueue],
) -> list[str]:
    actions: list[str] = []
    if blockers:
        actions.append("Clear hard promotion blockers (see promotion_blockers), then re-run ops status.")
    elif promotable:
        actions.append(
            "Hard promotion floors met - deepen quality via soft densify / dual-review (not lit-mining scale)."
        )
    if soft_gaps:
        top = ", ".join(f"{gap.task}/{gap.label}(+{gap.delta})" for gap in soft_gaps[:6])
        actions.append(f"Prioritize soft densify gaps: {top}.")
    if dual_pending:
        latest = dual_backlog[0].path if dual_backlog else "review_batches"
        actions.append(
            f"Adjudicate dual-review backlog ({dual_pending} pending). Start with `{latest}`."
        )
    if al_pending:
        latest_al = al_backlog[0].path if al_backlog else "active_learning_batches"
        actions.append(
            f"Clear active-learning pending rows ({al_pending}). Queue: `{latest_al}`."
        )
    actions.append("After human decisions: finalize/promote curated round -> `gbmbert-rebuild-curated-rounds`.")
    actions.append("Keep preferred research checkpoints (evidence v9 / relation v3 / BIO NER v6) until freeze-split compare.")
    actions.append("Do not claim clinical validation; promotable != patient-ready model.")
    return actions


def _select_sparse_spans(
    *,
    entities_glob: str,
    target_labels: tuple[str, ...] | list[str],
    max_spans_per_label: int,
    root: str | Path = ".",
) -> list[dict[str, Any]]:
    label_set = set(target_labels)
    buckets: dict[str, list[dict[str, Any]]] = {label: [] for label in target_labels}
    for path in sorted(Path(root).glob(entities_glob)):
        for doc in _read_jsonl(path):
            pmid = str(doc.get("pmid") or doc.get("source_pmid") or "").strip()
            context = str(doc.get("text") or "")
            if not pmid or not context:
                continue
            for entity in doc.get("entities") or []:
                if not isinstance(entity, dict):
                    continue
                label = str(entity.get("label") or "").strip()
                if label not in label_set:
                    continue
                if len(buckets[label]) >= max_spans_per_label:
                    continue
                start = int(entity.get("start", -1))
                end = int(entity.get("end", -1))
                mention = str(entity.get("text") or "")
                if start < 0 or end <= start or not mention:
                    continue
                buckets[label].append(
                    {
                        "source_file": str(path),
                        "source_pmid": pmid,
                        "label": label,
                        "text": mention,
                        "context_text": context,
                        "start": start,
                        "end": end,
                        "confidence": entity.get("confidence"),
                        "normalized_text": entity.get("normalized_text"),
                    }
                )
    selected: list[dict[str, Any]] = []
    for label in target_labels:
        selected.extend(buckets.get(label) or [])
    return selected


def _format_sparse_batch_instructions(
    *,
    round_id: int,
    labels: tuple[str, ...] | list[str],
    span_count: int,
    document_count: int,
    label_counts: dict[str, int],
    r1_path: Path,
    r2_path: Path,
    csv_path: Path,
) -> str:
    label_lines = [f"- {label}: {count}" for label, count in sorted(label_counts.items())]
    return "\n".join(
        [
            f"# Round {round_id} - Sparse NER densify dual-review",
            "",
            RESEARCH_WARNING,
            "",
            "## Goal",
            "",
            "Human dual-review of sparse NER spans for research gold-pack deepening "
            f"({', '.join(labels)}). Prefer quality multi-token PATHWAY phrases; avoid bare gene-symbol PATHWAY.",
            "",
            f"- Pending spans: **{span_count}** across **{document_count}** PMID(s)",
            *label_lines,
            "",
            "## Queues (all pending - do not auto-accept)",
            "",
            f"- Reviewer 1: `{r1_path}`",
            f"- Reviewer 2: `{r2_path}`",
            f"- Shared CSV: `{csv_path}`",
            "",
            "## Human steps",
            "",
            "1. Independently set each row `review_status` to accepted / corrected / rejected.",
            "2. For corrections, fill `corrected_label` / offsets / text.",
            "3. Run `gbmbert-adjudication-report` on r1 vs r2 JSONL.",
            "4. Write consensus JSONL, then promote accepted spans into "
            f"`data/training/curated_expansion/gold_entities_round{round_id}.jsonl`.",
            "5. Run `gbmbert-rebuild-curated-rounds` and `gbmbert-gold-pack-ops-status`.",
            "",
            "## Boundary",
            "",
            "Research-use only. Not clinical validation. Deepen governance/quality - do not scale lit-mining or claim CDS.",
            "",
        ]
    )


def _format_sparse_batch_report_markdown(report: SparseDensifyBatchReport) -> str:
    lines = [
        f"# Sparse Densify Dual-Review Batch (Round {report.round_id})",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output dir: `{report.output_dir}`",
        f"- R1 JSONL: `{report.r1_jsonl}`",
        f"- R2 JSONL: `{report.r2_jsonl}`",
        f"- CSV: `{report.csv_output}`",
        f"- Instructions: `{report.instructions_path}`",
        f"- Spans: {report.span_count}",
        f"- Documents: {report.document_count}",
        f"- Pending for human: {report.pending_for_human}",
        "",
        "## Label Counts",
        *([f"- {label}: {count}" for label, count in sorted(report.label_counts.items())] or ["- none"]),
        "",
        "## Notes",
        *([f"- {note}" for note in report.notes] or ["- none"]),
        "",
    ]
    return "\n".join(lines)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _write_span_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "item_id",
        "source_pmid",
        "label",
        "text",
        "start",
        "end",
        "review_status",
        "corrected_label",
        "reviewer",
        "review_notes",
        "context_text",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
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


if __name__ == "__main__":
    raise SystemExit(main())
