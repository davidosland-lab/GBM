"""Synthetic negative examples for GBM-BERT relation extraction datasets."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.preparation import SPLITS, TASK_FILES

NO_RELATION_LABEL = "NO_RELATION"


@dataclass(frozen=True)
class RelationNegativeReport:
    input_path: str
    output_path: str
    positive_count: int
    negative_count: int
    skipped_count: int
    negative_ratio: float
    label_counts: dict[str, int]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_relation_negatives(
    dataset_path: str | Path,
    output_jsonl: str | Path,
    *,
    negative_ratio: float = 1.0,
    max_negatives: int | None = None,
    seed: int = 13,
) -> RelationNegativeReport:
    """Build deterministic NO_RELATION examples from existing relation endpoints."""

    if negative_ratio < 0:
        raise ValueError("negative_ratio must be non-negative")
    root = Path(dataset_path)
    output_path = Path(output_jsonl)
    positives = [row for row in _relation_rows(root) if _label_text(row) and _label_text(row) != NO_RELATION_LABEL]
    warnings: list[str] = []
    if not positives:
        warnings.append("no positive relation examples found")

    known_pairs = {
        _pair_key(row)
        for row in positives
        if _endpoint_text(row.get("head")) and _endpoint_text(row.get("tail"))
    }
    candidates: dict[str, dict[str, Any]] = {}
    skipped = 0
    rows_by_sentence: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in positives:
        rows_by_sentence[(_pmid(row), _sentence_text(row))].append(row)

    for (pmid, sentence), rows in rows_by_sentence.items():
        endpoints = sorted(
            {
                _endpoint_text(value)
                for row in rows
                for value in (row.get("head"), row.get("tail"))
                if _endpoint_text(value)
            }
        )
        if len(endpoints) < 2:
            skipped += len(rows)
            continue
        template = rows[0]
        for head in endpoints:
            for tail in endpoints:
                if head == tail:
                    continue
                pair = (pmid, sentence, head, tail)
                if pair in known_pairs:
                    continue
                candidate = _negative_row(template, head=head, tail=tail)
                candidates[_negative_key(candidate)] = candidate

    ordered = list(candidates.values())
    rng = random.Random(seed)
    rng.shuffle(ordered)
    target = int(len(positives) * negative_ratio)
    if negative_ratio > 0 and positives and target == 0:
        target = 1
    if max_negatives is not None:
        target = min(target, max_negatives)
    negatives = ordered[:target]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(negatives, output_path)

    if positives and not negatives:
        warnings.append("no synthetic negatives could be generated")
    return RelationNegativeReport(
        input_path=str(root),
        output_path=str(output_path),
        positive_count=len(positives),
        negative_count=len(negatives),
        skipped_count=skipped,
        negative_ratio=negative_ratio,
        label_counts={NO_RELATION_LABEL: len(negatives)},
        warnings=warnings,
    )


def save_relation_negative_report_json(report: RelationNegativeReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_relation_negative_report_markdown(report: RelationNegativeReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_relation_negative_markdown(report), encoding="utf-8")
    return output


def format_relation_negative_markdown(report: RelationNegativeReport) -> str:
    lines = [
        "# GBM-BERT Relation Negative Sampler",
        "",
        RESEARCH_WARNING,
        "",
        f"- Input: `{report.input_path}`",
        f"- Output: `{report.output_path}`",
        f"- Positive relation examples scanned: {report.positive_count}",
        f"- Synthetic negatives written: {report.negative_count}",
        f"- Skipped positives: {report.skipped_count}",
        f"- Requested negative ratio: {report.negative_ratio:.3f}",
        "",
        "## Labels",
        *([f"- {label}: {count}" for label, count in sorted(report.label_counts.items())] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build synthetic NO_RELATION examples for relation extraction.")
    parser.add_argument("dataset_path", type=Path, help="Relation JSONL file or annotation dataset directory.")
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--negative-ratio", type=float, default=1.0)
    parser.add_argument("--max-negatives", type=int)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_relation_negatives(
        args.dataset_path,
        args.output_jsonl,
        negative_ratio=args.negative_ratio,
        max_negatives=args.max_negatives,
        seed=args.seed,
    )
    if args.json_output:
        save_relation_negative_report_json(report, args.json_output)
    if args.markdown_output:
        save_relation_negative_report_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_relation_negative_markdown(report))
    return 0


def _relation_rows(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        return _read_jsonl(path)
    files = []
    base = path / TASK_FILES["relation"]
    if base.exists():
        files.append(base)
    for split in SPLITS:
        split_path = path / f"relation_{split}.jsonl"
        if split_path.exists():
            files.append(split_path)
    rows: list[dict[str, Any]] = []
    for file_path in files:
        rows.extend(_read_jsonl(file_path))
    return rows


def _negative_row(template: dict[str, Any], *, head: str, tail: str) -> dict[str, Any]:
    row = {
        "task": "relation",
        "source_pmid": _pmid(template),
        "text": str(template.get("text") or template.get("sentence") or ""),
        "sentence": _sentence_text(template),
        "head": head,
        "tail": tail,
        "label": NO_RELATION_LABEL,
        "negative_source": "synthetic_entity_pair_v1",
        "warning": RESEARCH_WARNING,
    }
    if template.get("source_title"):
        row["source_title"] = template.get("source_title")
    return row


def _pair_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (_pmid(row), _sentence_text(row), _endpoint_text(row.get("head")), _endpoint_text(row.get("tail")))


def _negative_key(row: dict[str, Any]) -> str:
    return json.dumps((_pair_key(row), row.get("label")), sort_keys=True)


def _pmid(row: dict[str, Any]) -> str:
    return str(row.get("source_pmid") or row.get("pmid") or "").strip()


def _sentence_text(row: dict[str, Any]) -> str:
    return str(row.get("sentence") or row.get("text") or "").strip()


def _label_text(row: dict[str, Any]) -> str:
    return str(row.get("label") or "").strip()


def _endpoint_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("id", "entity_id", "text", "name", "label"):
            if value.get(key):
                return str(value[key]).strip()
        return json.dumps(value, sort_keys=True)
    return str(value).strip()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL record on line {line_number}: {path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    content = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
