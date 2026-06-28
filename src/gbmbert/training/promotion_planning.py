"""Scaffold-only planning report from gold-pack promotion deltas."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from math import ceil
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


DEFAULT_EXAMPLES_PER_BATCH = 24
DEFAULT_LABELS_PER_BATCH = 3
DEFAULT_PMIDS_PER_BATCH = 6


@dataclass(frozen=True)
class PromotionPlanningBatch:
    batch_id: str
    batch_type: str
    task: str
    suggested_examples: int
    suggested_new_pmids: int
    labels: list[dict[str, int]]
    note: str
    task_volume_delta: int = 0
    counts_toward_task_volume: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GoldPackPromotionPlanningReport:
    promotion_review_path: str
    scaffold_only: bool
    promotable_now: bool
    source_pmid_delta: int
    task_example_deltas: dict[str, int]
    label_example_deltas: dict[str, dict[str, int]]
    task_remaining_examples: dict[str, int]
    label_remaining_examples: dict[str, dict[str, int]]
    source_pmid_batches: list[dict[str, int | str]]
    label_balance_relationship: dict[str, dict[str, int]]
    batch_count: int
    batches: list[PromotionPlanningBatch]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_gold_pack_promotion_planning_report(
    *,
    promotion_review: str | Path = Path("reports/training/gold_pack/gold_pack_promotion_review.json"),
    examples_per_batch: int = DEFAULT_EXAMPLES_PER_BATCH,
    labels_per_batch: int = DEFAULT_LABELS_PER_BATCH,
    pmids_per_batch: int = DEFAULT_PMIDS_PER_BATCH,
) -> GoldPackPromotionPlanningReport:
    """Group promotion deltas into future curation batches without promoting anything."""

    review_path = Path(promotion_review)
    payload = _read_json(review_path)
    task_deltas = {str(task): int(delta) for task, delta in (payload.get("task_example_deltas") or {}).items()}
    label_deltas = {
        str(task): {str(label): int(delta) for label, delta in (labels or {}).items() if int(delta) > 0}
        for task, labels in (payload.get("label_example_deltas") or {}).items()
    }
    source_pmid_delta = int(payload.get("source_pmid_delta") or 0)
    batches: list[PromotionPlanningBatch] = []
    source_pmid_batches: list[dict[str, int | str]] = []
    label_balance_relationship: dict[str, dict[str, int]] = {}

    for task in sorted(task_deltas):
        low_labels = [
            {"label": label, "additional_examples_needed": delta}
            for label, delta in sorted(label_deltas.get(task, {}).items())
            if delta > 0
        ]
        label_delta_total = sum(item["additional_examples_needed"] for item in low_labels)
        task_example_delta = int(task_deltas[task])
        remaining_task_delta = max(0, task_example_delta - label_delta_total)
        # Surface how the label-balance batches relate to the task-volume delta:
        # label-floor examples are a subset of the task-volume delta, so the
        # remaining volume after label balancing is task_example_delta minus the
        # label-floor total (clamped at zero).
        label_balance_relationship[task] = {
            "task_example_delta": task_example_delta,
            "label_delta_total": label_delta_total,
            "remaining_task_volume_after_labels": remaining_task_delta,
        }
        for index, chunk in enumerate(_chunks(low_labels, max(1, labels_per_batch)), start=1):
            batches.append(
                PromotionPlanningBatch(
                    batch_id=f"{task}-label-balance-{index:03d}",
                    batch_type="label_balance",
                    task=task,
                    suggested_examples=sum(item["additional_examples_needed"] for item in chunk),
                    suggested_new_pmids=0,
                    labels=chunk,
                    note="Prioritize labels still below the configured per-label floor; these examples also count toward the task-volume delta.",
                    task_volume_delta=task_example_delta,
                    counts_toward_task_volume=True,
                )
            )
        for index in range(ceil(remaining_task_delta / max(1, examples_per_batch))):
            suggested = min(max(1, examples_per_batch), remaining_task_delta - index * max(1, examples_per_batch))
            batches.append(
                PromotionPlanningBatch(
                    batch_id=f"{task}-volume-{index + 1:03d}",
                    batch_type="task_volume",
                    task=task,
                    suggested_examples=suggested,
                    suggested_new_pmids=0,
                    labels=[],
                    note="Add balanced reviewed examples for the task-volume delta remaining after label-floor batches.",
                    task_volume_delta=task_example_delta,
                    counts_toward_task_volume=True,
                )
            )

    for index in range(ceil(source_pmid_delta / max(1, pmids_per_batch))):
        suggested_pmids = min(max(1, pmids_per_batch), source_pmid_delta - index * max(1, pmids_per_batch))
        batch_id = f"source-pmid-expansion-{index + 1:03d}"
        source_pmid_batches.append({"batch_id": batch_id, "suggested_new_pmids": suggested_pmids})
        batches.append(
            PromotionPlanningBatch(
                batch_id=batch_id,
                batch_type="source_pmid_expansion",
                task="all",
                suggested_examples=0,
                suggested_new_pmids=suggested_pmids,
                labels=[],
                note="Select additional source PMIDs for future reviewed curation batches.",
            )
        )

    return GoldPackPromotionPlanningReport(
        promotion_review_path=str(review_path),
        scaffold_only=True,
        promotable_now=bool(payload.get("promotable")),
        source_pmid_delta=source_pmid_delta,
        task_example_deltas=task_deltas,
        label_example_deltas=label_deltas,
        task_remaining_examples=dict(sorted(task_deltas.items())),
        label_remaining_examples={task: dict(sorted(labels.items())) for task, labels in sorted(label_deltas.items())},
        source_pmid_batches=source_pmid_batches,
        label_balance_relationship=dict(sorted(label_balance_relationship.items())),
        batch_count=len(batches),
        batches=batches,
    )


def save_gold_pack_promotion_planning_json(report: GoldPackPromotionPlanningReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_gold_pack_promotion_planning_markdown(report: GoldPackPromotionPlanningReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_gold_pack_promotion_planning_markdown(report), encoding="utf-8")
    return output


def format_gold_pack_promotion_planning_markdown(report: GoldPackPromotionPlanningReport) -> str:
    lines = [
        "# Gold Pack Promotion Planning Report",
        "",
        RESEARCH_WARNING,
        "",
        "This is a scaffold-only curation planning report. It does not promote a dataset, validate a trained GBM-BERT model, or support clinical decision-making.",
        "",
        f"- Promotion review: `{report.promotion_review_path}`",
        f"- Scaffold only: {report.scaffold_only}",
        f"- Promotable now: {report.promotable_now}",
        f"- Source PMIDs still needed: {report.source_pmid_delta}",
        f"- Suggested future batches: {report.batch_count}",
        "",
        "## Compact Summary",
        "### Task Remaining Examples",
        *([f"- {task}: {delta}" for task, delta in sorted(report.task_remaining_examples.items())] or ["- none"]),
        "",
        "### Label Remaining Examples",
    ]
    for task, labels in sorted(report.label_remaining_examples.items()):
        lines.append(f"- {task}: " + (", ".join(f"{label}={delta}" for label, delta in sorted(labels.items())) or "none"))
    lines.extend(
        [
            "",
            "### Label Balance vs Task Volume",
        ]
    )
    if report.label_balance_relationship:
        for task, relationship in sorted(report.label_balance_relationship.items()):
            lines.append(
                f"- {task}: label-floor {relationship['label_delta_total']} of {relationship['task_example_delta']} "
                f"task-volume example(s); {relationship['remaining_task_volume_after_labels']} remaining after label balancing"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "### Source PMID Batches",
            *(
                [
                    f"- `{batch['batch_id']}`: {batch['suggested_new_pmids']} new PMID(s)"
                    for batch in report.source_pmid_batches
                ]
                or ["- none"]
            ),
            "",
        ]
    )
    lines.extend(
        [
        "## Task Deltas",
        *([f"- {task}: {delta} example(s)" for task, delta in sorted(report.task_example_deltas.items())] or ["- none"]),
        "",
        "## Suggested Batches",
        ]
    )
    for batch in report.batches:
        label_text = ", ".join(f"{item['label']} +{item['additional_examples_needed']}" for item in batch.labels) or "balanced/general"
        lines.append(
            f"- `{batch.batch_id}` ({batch.batch_type}, {batch.task}): "
            f"{batch.suggested_examples} example(s), {batch.suggested_new_pmids} new PMID(s); {label_text}. {batch.note}"
        )
    if not report.batches:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan scaffold-only future curation batches from promotion deltas.")
    parser.add_argument("--promotion-review", type=Path, default=Path("reports/training/gold_pack/gold_pack_promotion_review.json"))
    parser.add_argument("--examples-per-batch", type=int, default=DEFAULT_EXAMPLES_PER_BATCH)
    parser.add_argument("--labels-per-batch", type=int, default=DEFAULT_LABELS_PER_BATCH)
    parser.add_argument("--pmids-per-batch", type=int, default=DEFAULT_PMIDS_PER_BATCH)
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/gold_pack/gold_pack_promotion_plan.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/gold_pack/gold_pack_promotion_plan.md"))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_gold_pack_promotion_planning_report(
        promotion_review=args.promotion_review,
        examples_per_batch=args.examples_per_batch,
        labels_per_batch=args.labels_per_batch,
        pmids_per_batch=args.pmids_per_batch,
    )
    save_gold_pack_promotion_planning_json(report, args.json_output)
    save_gold_pack_promotion_planning_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_gold_pack_promotion_planning_markdown(report))
    return 0


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"promotion review JSON must be an object: {path}")
    return payload


def _chunks(items: list[dict[str, int]], size: int) -> list[list[dict[str, int]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


if __name__ == "__main__":
    raise SystemExit(main())
