"""Compare GBM-BERT training packs side by side."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


@dataclass(frozen=True)
class TrainingPackComparisonRow:
    name: str
    pack_report_path: str
    dataset_dir: str | None
    split_dir: str | None
    label_map_dir: str | None
    ready: bool | None
    row_counts: dict[str, int]
    label_counts: dict[str, dict[str, int]]
    leakage_warnings: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class TrainingPackComparisonReport:
    packs: list[TrainingPackComparisonRow]
    ready_count: int
    warning_count: int
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compare_training_packs(
    *,
    evidence_pack_report: str | Path | None = None,
    relation_pack_report: str | Path | None = None,
    gold_pack_report: str | Path | None = None,
) -> TrainingPackComparisonReport:
    """Build a compact comparison across evidence, relation, and gold training packs."""

    rows: list[TrainingPackComparisonRow] = []
    for name, path in (
        ("evidence", evidence_pack_report),
        ("relation", relation_pack_report),
        ("gold", gold_pack_report),
    ):
        if path is None:
            continue
        rows.append(_summarize_pack(name, Path(path)))
    return TrainingPackComparisonReport(
        packs=rows,
        ready_count=sum(1 for row in rows if row.ready is True),
        warning_count=sum(len(row.warnings) + len(row.leakage_warnings) for row in rows),
    )


def save_training_pack_comparison_json(report: TrainingPackComparisonReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_training_pack_comparison_markdown(report: TrainingPackComparisonReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_training_pack_comparison_markdown(report), encoding="utf-8")
    return output


def format_training_pack_comparison_markdown(report: TrainingPackComparisonReport) -> str:
    lines = [
        "# GBM-BERT Training Pack Comparison",
        "",
        RESEARCH_WARNING,
        "",
        f"- Packs compared: {len(report.packs)}",
        f"- Ready packs: {report.ready_count}",
        f"- Warnings: {report.warning_count}",
        "",
        "## Packs",
    ]
    for pack in report.packs:
        lines.extend(
            [
                f"### {pack.name}",
                f"- Report: `{pack.pack_report_path}`",
                f"- Dataset: `{pack.dataset_dir or 'n/a'}`",
                f"- Splits: `{pack.split_dir or 'n/a'}`",
                f"- Label maps: `{pack.label_map_dir or 'n/a'}`",
                f"- Ready: {pack.ready}",
                "- Row counts:",
                *_format_counts(pack.row_counts),
                "- Label coverage:",
                *_format_nested_counts(pack.label_counts),
                "- Leakage:",
                *([f"- {warning}" for warning in pack.leakage_warnings] if pack.leakage_warnings else ["- none"]),
                "- Warnings:",
                *([f"- {warning}" for warning in pack.warnings] if pack.warnings else ["- none"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare GBM-BERT training packs.")
    parser.add_argument("--evidence-pack-report", type=Path, default=Path("reports/training/evidence_pack/evidence_training_pack.json"))
    parser.add_argument("--relation-pack-report", type=Path, default=Path("reports/training/relation_pack/relation_training_pack.json"))
    parser.add_argument("--gold-pack-report", type=Path, default=Path("reports/training/gold_pack/gold_training_pack.json"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = compare_training_packs(
        evidence_pack_report=args.evidence_pack_report if args.evidence_pack_report.exists() else None,
        relation_pack_report=args.relation_pack_report if args.relation_pack_report.exists() else None,
        gold_pack_report=args.gold_pack_report if args.gold_pack_report.exists() else None,
    )
    if args.json_output:
        save_training_pack_comparison_json(report, args.json_output)
    if args.markdown_output:
        save_training_pack_comparison_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_training_pack_comparison_markdown(report))
    return 0


def _summarize_pack(name: str, report_path: Path) -> TrainingPackComparisonRow:
    payload = _read_json(report_path)
    split_dir = payload.get("split_dataset_dir") or payload.get("split_dir")
    dataset_dir = payload.get("annotation_dataset_dir") or payload.get("dataset_dir")
    label_map_dir = payload.get("label_map_dir")
    row_counts, label_counts = _summarize_split_dir(Path(split_dir)) if split_dir else ({}, {})
    readiness_path = _readiness_path(name, payload, report_path)
    leakage_warnings: list[str] = []
    warnings = [str(item) for item in payload.get("warnings", [])]
    if readiness_path and readiness_path.exists():
        readiness = _read_json(readiness_path)
        leakage_warnings = [str(item) for item in readiness.get("leakage_warnings", [])]
        warnings.extend(str(item) for item in readiness.get("warnings", []) if str(item) not in warnings)
    return TrainingPackComparisonRow(
        name=name,
        pack_report_path=str(report_path),
        dataset_dir=str(dataset_dir) if dataset_dir else None,
        split_dir=str(split_dir) if split_dir else None,
        label_map_dir=str(label_map_dir) if label_map_dir else None,
        ready=payload.get("ready") if isinstance(payload.get("ready"), bool) else None,
        row_counts=row_counts,
        label_counts=label_counts,
        leakage_warnings=leakage_warnings,
        warnings=warnings,
    )


def _readiness_path(name: str, payload: dict[str, Any], report_path: Path) -> Path | None:
    artifacts = payload.get("artifacts")
    if isinstance(artifacts, dict) and artifacts.get("training_readiness_json"):
        return Path(str(artifacts["training_readiness_json"]))
    reports_dir = payload.get("reports_dir")
    if not reports_dir:
        return None
    filename = {
        "evidence": "evidence_training_pack_readiness.json",
        "relation": "relation_training_pack_readiness.json",
        "gold": "training_readiness.json",
    }.get(name)
    return Path(str(reports_dir)) / filename if filename else report_path.with_name("training_readiness.json")


def _summarize_split_dir(split_dir: Path) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    row_counts: dict[str, int] = {}
    label_counts: dict[str, dict[str, int]] = {}
    if not split_dir.exists():
        return row_counts, label_counts
    for task in ("evidence", "ner", "relation"):
        rows: list[dict[str, Any]] = []
        for path in sorted(split_dir.glob(f"{task}_*.jsonl")):
            rows.extend(_read_jsonl(path))
        row_counts[task] = len(rows)
        label_counts[task] = dict(sorted(Counter(_label_text(row) for row in rows if _label_text(row)).items()))
    return row_counts, label_counts


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON report must be an object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


def _label_text(row: dict[str, Any]) -> str:
    value = row.get("label")
    if value is None:
        return ""
    return str(value).strip()


def _format_counts(counts: dict[str, int]) -> list[str]:
    return [f"- {name}: {count}" for name, count in sorted(counts.items())] if counts else ["- none"]


def _format_nested_counts(counts: dict[str, dict[str, int]]) -> list[str]:
    if not counts:
        return ["- none"]
    lines: list[str] = []
    for task, task_counts in sorted(counts.items()):
        formatted = ", ".join(f"{label}={count}" for label, count in sorted(task_counts.items())) or "none"
        lines.append(f"- {task}: {formatted}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
