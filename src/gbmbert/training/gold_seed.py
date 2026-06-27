"""Gold seed dataset builder from reviewed GBM-AI curation artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.extraction.io import load_entity_jsonl
from gbmbert.extraction.review_queue import ReviewQueueItem, load_review_queue_jsonl
from gbmbert.training.prediction_curation import PredictionReviewItem, load_prediction_review_queue_jsonl


@dataclass(frozen=True)
class GoldSeedReport:
    output_dir: str
    reviewed_queue_path: str
    prediction_reviewed_queue_path: str
    entity_jsonl_path: str
    ner_count: int
    evidence_count: int
    relation_count: int
    skipped_pending_count: int
    skipped_rejected_count: int
    files: dict[str, str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_gold_seed_dataset(
    *,
    output_dir: str | Path,
    reviewed_queue_jsonl: str | Path | None = None,
    prediction_reviewed_queue_jsonl: str | Path | None = None,
    entity_jsonl: str | Path | None = None,
) -> GoldSeedReport:
    """Build conservative gold-seed JSONL files from accepted/corrected review decisions."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    files = {
        "ner": str(output_path / "gold_ner.jsonl"),
        "evidence": str(output_path / "gold_evidence.jsonl"),
        "relation": str(output_path / "gold_relations.jsonl"),
        "manifest": str(output_path / "gold_seed_manifest.json"),
        "markdown": str(output_path / "gold_seed_manifest.md"),
    }
    warnings: list[str] = []
    skipped_pending = 0
    skipped_rejected = 0
    ner_rows = _ner_rows(entity_jsonl) if entity_jsonl else []
    evidence_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []

    if reviewed_queue_jsonl:
        items = load_review_queue_jsonl(reviewed_queue_jsonl)
        for item in items:
            if item.review_status == "pending":
                skipped_pending += 1
                continue
            if item.review_status == "rejected":
                skipped_rejected += 1
                continue
            if item.item_type == "evidence_claim":
                evidence_rows.append(_evidence_row_from_review_item(item))
            elif item.item_type == "graph_relation":
                relation_rows.append(_relation_row_from_review_item(item))
    if prediction_reviewed_queue_jsonl:
        predictions = load_prediction_review_queue_jsonl(prediction_reviewed_queue_jsonl)
        for item in predictions:
            if item.review_status == "pending":
                skipped_pending += 1
                continue
            if item.review_status == "rejected":
                skipped_rejected += 1
                continue
            evidence_rows.append(_evidence_row_from_prediction_item(item))
    if not any((reviewed_queue_jsonl, prediction_reviewed_queue_jsonl, entity_jsonl)):
        warnings.append("No source artifacts were provided")

    _write_jsonl(ner_rows, files["ner"])
    _write_jsonl(evidence_rows, files["evidence"])
    _write_jsonl(relation_rows, files["relation"])
    report = GoldSeedReport(
        output_dir=str(output_path),
        reviewed_queue_path=str(reviewed_queue_jsonl or ""),
        prediction_reviewed_queue_path=str(prediction_reviewed_queue_jsonl or ""),
        entity_jsonl_path=str(entity_jsonl or ""),
        ner_count=len(ner_rows),
        evidence_count=len(evidence_rows),
        relation_count=len(relation_rows),
        skipped_pending_count=skipped_pending,
        skipped_rejected_count=skipped_rejected,
        files=files,
        warnings=warnings,
    )
    Path(files["manifest"]).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    Path(files["markdown"]).write_text(format_gold_seed_markdown(report), encoding="utf-8")
    return report


def format_gold_seed_markdown(report: GoldSeedReport) -> str:
    lines = [
        "# GBM-AI Gold Seed Dataset",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- NER examples: {report.ner_count}",
        f"- Evidence examples: {report.evidence_count}",
        f"- Relation examples: {report.relation_count}",
        f"- Skipped pending: {report.skipped_pending_count}",
        f"- Skipped rejected: {report.skipped_rejected_count}",
        "",
        "## Files",
        *[f"- {key}: `{value}`" for key, value in sorted(report.files.items())],
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a conservative GBM-BERT gold seed dataset from reviewed queues.")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--reviewed-queue-jsonl", type=Path)
    parser.add_argument("--prediction-reviewed-queue-jsonl", type=Path)
    parser.add_argument("--entity-jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_gold_seed_dataset(
        output_dir=args.output_dir,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        prediction_reviewed_queue_jsonl=args.prediction_reviewed_queue_jsonl,
        entity_jsonl=args.entity_jsonl,
    )
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(format_gold_seed_markdown(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_gold_seed_markdown(report))
    return 0


def _evidence_row_from_review_item(item: ReviewQueueItem) -> dict[str, Any]:
    tier = item.corrected_evidence_tier if item.corrected_evidence_tier is not None else item.evidence_tier
    return {
        "task": "evidence",
        "item_id": item.item_id,
        "source_pmid": item.source_pmid,
        "text": item.text,
        "label": int(tier),
        "review_status": item.review_status,
        "reviewer": item.reviewer,
        "review_notes": item.review_notes,
        "warning": RESEARCH_WARNING,
    }


def _evidence_row_from_prediction_item(item: PredictionReviewItem) -> dict[str, Any]:
    tier = item.corrected_evidence_tier if item.corrected_evidence_tier is not None else item.predicted_evidence_tier
    return {
        "task": "evidence",
        "item_id": item.item_id,
        "source_pmid": item.source_pmid,
        "text": item.text,
        "label": int(tier) if tier is not None else None,
        "review_status": item.review_status,
        "reviewer": item.reviewer or item.reviewer_id,
        "review_notes": item.review_notes,
        "checkpoint_name": item.checkpoint_name,
        "warning": RESEARCH_WARNING,
    }


def _relation_row_from_review_item(item: ReviewQueueItem) -> dict[str, Any]:
    tier = item.corrected_evidence_tier if item.corrected_evidence_tier is not None else item.evidence_tier
    label = item.corrected_relation_type or item.relation_type
    source_type = "curated_no_relation" if label == "NO_RELATION" else "human_or_curated_positive"
    return {
        "task": "relation",
        "item_id": item.item_id,
        "source_pmid": item.source_pmid,
        "text": item.text,
        "sentence": item.text,
        "head": item.head,
        "tail": item.tail,
        "label": label,
        "evidence_tier": int(tier),
        "review_status": item.review_status,
        "reviewer": item.reviewer,
        "review_notes": item.review_notes,
        "relation_pack_source_path": item.source_file,
        "relation_pack_source_type": source_type,
        "relation_pack_synthetic": False,
        "warning": RESEARCH_WARNING,
    }


def _ner_rows(entity_jsonl: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in load_entity_jsonl(entity_jsonl):
        for entity in result.entities:
            rows.append(
                {
                    "task": "ner",
                    "source_pmid": result.pmid,
                    "text": entity.text,
                    "label": entity.label.value,
                    "start": entity.start,
                    "end": entity.end,
                    "confidence": entity.confidence,
                    "normalized_text": entity.normalized_text,
                    "warning": RESEARCH_WARNING,
                }
            )
    return rows


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
