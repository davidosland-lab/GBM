"""Promotion review thresholds for GBM-BERT gold-pack scaffolds."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


DEFAULT_MIN_EXAMPLES_PER_TASK = 100
DEFAULT_MIN_EXAMPLES_PER_LABEL = 10
DEFAULT_MIN_SOURCE_PMIDS = 50
DEFAULT_REQUIRED_TASKS = ("evidence", "ner", "relation")


@dataclass(frozen=True)
class GoldPackPromotionReview:
    gold_pack_report: str
    threshold_config: str
    pack_ready: bool
    promotable: bool
    min_examples_per_task: int
    min_examples_per_label: int
    min_source_pmids: int
    task_counts: dict[str, int]
    label_counts: dict[str, dict[str, int]]
    source_pmid_count: int
    task_example_deltas: dict[str, int]
    label_example_deltas: dict[str, dict[str, int]]
    source_pmid_delta: int
    blockers: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def review_gold_pack_promotion(
    *,
    gold_pack_report: str | Path = Path("reports/training/gold_pack/gold_training_pack.json"),
    threshold_config: str | Path | None = Path("configs/training/gold_pack_promotion_thresholds.json"),
    min_examples_per_task: int = DEFAULT_MIN_EXAMPLES_PER_TASK,
    min_examples_per_label: int = DEFAULT_MIN_EXAMPLES_PER_LABEL,
    min_source_pmids: int = DEFAULT_MIN_SOURCE_PMIDS,
) -> GoldPackPromotionReview:
    """Review whether the gold pack is large enough to consider scaffold promotion."""

    report_path = Path(gold_pack_report)
    threshold_path = Path(threshold_config) if threshold_config else None
    if threshold_path and threshold_path.exists():
        thresholds = _read_json(threshold_path)
        min_examples_per_task = int(thresholds.get("min_examples_per_task") or min_examples_per_task)
        min_examples_per_label = int(thresholds.get("min_examples_per_label") or min_examples_per_label)
        min_source_pmids = int(thresholds.get("min_source_pmids") or min_source_pmids)
    payload = _read_json(report_path)
    split_dir = Path(str(payload.get("split_dir") or payload.get("split_dataset_dir") or ""))
    pack_ready = bool(payload.get("ready"))
    task_counts: dict[str, int] = {}
    label_counts: dict[str, dict[str, int]] = {}
    task_example_deltas: dict[str, int] = {}
    label_example_deltas: dict[str, dict[str, int]] = {}
    source_pmids: set[str] = set()
    blockers: list[str] = []

    if not pack_ready:
        blockers.append("gold pack readiness report is not ready")
    if not split_dir.exists():
        blockers.append(f"gold pack split directory not found: {split_dir}")

    for task in DEFAULT_REQUIRED_TASKS:
        rows = _read_task_rows(split_dir, task)
        task_counts[task] = len(rows)
        task_example_deltas[task] = max(0, min_examples_per_task - len(rows))
        labels: dict[str, int] = {}
        for row in rows:
            raw_label = row.get("label")
            label = str(raw_label).strip() if raw_label is not None else ""
            if label:
                labels[label] = labels.get(label, 0) + 1
            pmid = str(row.get("source_pmid") or row.get("pmid") or "").strip()
            if pmid:
                source_pmids.add(pmid)
        label_counts[task] = dict(sorted(labels.items()))
        label_example_deltas[task] = {
            label: max(0, min_examples_per_label - count)
            for label, count in sorted(labels.items())
            if count < min_examples_per_label
        }
        if len(rows) < min_examples_per_task:
            blockers.append(f"{task} has {len(rows)} examples; needs at least {min_examples_per_task}")
        low_labels = [f"{label}={count}" for label, count in sorted(labels.items()) if count < min_examples_per_label]
        if low_labels:
            blockers.append(f"{task} labels below {min_examples_per_label} examples: {', '.join(low_labels)}")
        if not labels:
            blockers.append(f"{task} has no labels")

    if len(source_pmids) < min_source_pmids:
        blockers.append(f"source PMID count is {len(source_pmids)}; needs at least {min_source_pmids}")
    source_pmid_delta = max(0, min_source_pmids - len(source_pmids))

    return GoldPackPromotionReview(
        gold_pack_report=str(report_path),
        threshold_config=str(threshold_path) if threshold_path else "",
        pack_ready=pack_ready,
        promotable=not blockers,
        min_examples_per_task=min_examples_per_task,
        min_examples_per_label=min_examples_per_label,
        min_source_pmids=min_source_pmids,
        task_counts=task_counts,
        label_counts=label_counts,
        source_pmid_count=len(source_pmids),
        task_example_deltas=task_example_deltas,
        label_example_deltas=label_example_deltas,
        source_pmid_delta=source_pmid_delta,
        blockers=blockers,
    )


def save_gold_pack_promotion_review_json(report: GoldPackPromotionReview, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_gold_pack_promotion_review_markdown(report: GoldPackPromotionReview, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_gold_pack_promotion_review_markdown(report), encoding="utf-8")
    return output


def format_gold_pack_promotion_review_markdown(report: GoldPackPromotionReview) -> str:
    lines = [
        "# Gold Pack Promotion Review",
        "",
        RESEARCH_WARNING,
        "",
        f"- Gold pack report: `{report.gold_pack_report}`",
        f"- Threshold config: `{report.threshold_config or 'not provided'}`",
        f"- Pack ready: {report.pack_ready}",
        f"- Promotable: {report.promotable}",
        f"- Minimum examples per task: {report.min_examples_per_task}",
        f"- Minimum examples per label: {report.min_examples_per_label}",
        f"- Minimum source PMIDs: {report.min_source_pmids}",
        f"- Observed source PMIDs: {report.source_pmid_count}",
        f"- Additional source PMIDs needed: {report.source_pmid_delta}",
        "",
        "## Task Counts",
        *([f"- {task}: {count}" for task, count in sorted(report.task_counts.items())] or ["- none"]),
        "",
        "## Promotion Deltas",
        *(
            [
                f"- {task}: {delta} additional example(s) needed"
                for task, delta in sorted(report.task_example_deltas.items())
            ]
            or ["- none"]
        ),
        "",
        "## Label Counts",
    ]
    for task, counts in sorted(report.label_counts.items()):
        lines.append(f"### {task}")
        lines.extend([f"- {label}: {count}" for label, count in sorted(counts.items())] or ["- none"])
        lines.append("")
    lines.append("## Label Deltas")
    for task, counts in sorted(report.label_example_deltas.items()):
        lines.append(f"### {task}")
        lines.extend([f"- {label}: {delta} additional example(s) needed" for label, delta in sorted(counts.items())] or ["- none"])
        lines.append("")
    lines.extend(["## Blockers", *([f"- {blocker}" for blocker in report.blockers] if report.blockers else ["- none"])])
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review whether the local gold pack can be considered for scaffold promotion.")
    parser.add_argument("--gold-pack-report", type=Path, default=Path("reports/training/gold_pack/gold_training_pack.json"))
    parser.add_argument("--threshold-config", type=Path, default=Path("configs/training/gold_pack_promotion_thresholds.json"))
    parser.add_argument("--min-examples-per-task", type=int, default=DEFAULT_MIN_EXAMPLES_PER_TASK)
    parser.add_argument("--min-examples-per-label", type=int, default=DEFAULT_MIN_EXAMPLES_PER_LABEL)
    parser.add_argument("--min-source-pmids", type=int, default=DEFAULT_MIN_SOURCE_PMIDS)
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/gold_pack/gold_pack_promotion_review.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/gold_pack/gold_pack_promotion_review.md"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-blockers", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = review_gold_pack_promotion(
        gold_pack_report=args.gold_pack_report,
        threshold_config=args.threshold_config,
        min_examples_per_task=args.min_examples_per_task,
        min_examples_per_label=args.min_examples_per_label,
        min_source_pmids=args.min_source_pmids,
    )
    save_gold_pack_promotion_review_json(report, args.json_output)
    save_gold_pack_promotion_review_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_gold_pack_promotion_review_markdown(report))
    return 0 if report.promotable or args.allow_blockers else 1


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON report must be an object: {path}")
    return payload


def _read_task_rows(split_dir: Path, task: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in ("train", "validation", "test"):
        rows.extend(_read_jsonl(split_dir / f"{task}_{split}.jsonl"))
    return rows


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
