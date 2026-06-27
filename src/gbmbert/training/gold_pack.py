"""Gold training pack workflow for GBM-BERT dataset preparation."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.gold_seed import build_gold_seed_dataset
from gbmbert.training.preparation import (
    build_baseline_report,
    build_dataset_card,
    build_label_maps,
    format_baseline_report_markdown,
    format_dataset_card_markdown,
    format_evidence_label_repair_markdown,
    format_pmid_split_markdown,
    repair_evidence_labels,
    save_baseline_report,
    save_dataset_card,
    split_annotation_dataset_by_pmid,
)
from gbmbert.training.readiness import (
    build_training_readiness_report,
    format_training_readiness_markdown,
    save_training_readiness_json,
    save_training_readiness_markdown,
)


@dataclass(frozen=True)
class GoldTrainingPackReport:
    output_dir: str
    reports_dir: str
    gold_seed_dir: str
    dataset_dir: str
    repaired_dataset_dir: str
    split_dir: str
    label_map_dir: str
    ready: bool
    warnings: list[str]
    artifacts: dict[str, str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_gold_training_pack(
    *,
    output_dir: str | Path,
    reports_dir: str | Path,
    reviewed_queue_jsonl: str | Path | None = None,
    prediction_reviewed_queue_jsonl: str | Path | None = None,
    entity_jsonl: str | Path | None = None,
    min_examples_per_task: int = 10,
    min_examples_per_label: int = 2,
) -> GoldTrainingPackReport:
    """Build a repeatable local gold training pack from curated review artifacts."""

    output_root = Path(output_dir)
    report_root = Path(reports_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)
    gold_seed_dir = output_root / "gold_seed"
    dataset_dir = output_root / "annotation_dataset"
    repaired_dir = output_root / "annotation_dataset_repaired"
    split_dir = output_root / "annotation_splits"
    label_map_dir = output_root / "label_maps"
    artifacts: dict[str, str] = {}
    warnings: list[str] = []

    seed_report = build_gold_seed_dataset(
        output_dir=gold_seed_dir,
        reviewed_queue_jsonl=reviewed_queue_jsonl,
        prediction_reviewed_queue_jsonl=prediction_reviewed_queue_jsonl,
        entity_jsonl=entity_jsonl,
    )
    artifacts["gold_seed_manifest"] = str(report_root / "gold_seed_manifest.json")
    Path(artifacts["gold_seed_manifest"]).write_text(json.dumps(seed_report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    dataset_dir.mkdir(parents=True, exist_ok=True)
    _copy_gold_seed_to_annotation_dataset(gold_seed_dir, dataset_dir)

    repair_report = repair_evidence_labels(dataset_dir, repaired_dir)
    artifacts["evidence_label_repair_json"] = str(report_root / "evidence_label_repair.json")
    artifacts["evidence_label_repair_md"] = str(report_root / "evidence_label_repair.md")
    Path(artifacts["evidence_label_repair_json"]).write_text(json.dumps(repair_report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    Path(artifacts["evidence_label_repair_md"]).write_text(format_evidence_label_repair_markdown(repair_report), encoding="utf-8")

    split_manifest = split_annotation_dataset_by_pmid(repaired_dir, split_dir)
    artifacts["pmid_split_manifest_json"] = str(report_root / "pmid_split_manifest.json")
    artifacts["pmid_split_manifest_md"] = str(report_root / "pmid_split_manifest.md")
    Path(artifacts["pmid_split_manifest_json"]).write_text(json.dumps(split_manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    Path(artifacts["pmid_split_manifest_md"]).write_text(format_pmid_split_markdown(split_manifest), encoding="utf-8")

    label_summary = build_label_maps(split_dir, label_map_dir)
    artifacts["label_maps_manifest"] = str(label_map_dir / "label_maps_manifest.json")

    dataset_card = build_dataset_card(split_dir)
    artifacts["dataset_card_json"] = str(report_root / "dataset_card.json")
    artifacts["dataset_card_md"] = str(report_root / "dataset_card.md")
    save_dataset_card(dataset_card, json_output=artifacts["dataset_card_json"], markdown_output=artifacts["dataset_card_md"])

    baseline = build_baseline_report(split_dir)
    artifacts["baseline_json"] = str(report_root / "baseline_report.json")
    artifacts["baseline_md"] = str(report_root / "baseline_report.md")
    save_baseline_report(baseline, json_output=artifacts["baseline_json"], markdown_output=artifacts["baseline_md"])

    readiness = build_training_readiness_report(
        split_dir,
        min_examples_per_task=min_examples_per_task,
        min_examples_per_label=min_examples_per_label,
    )
    artifacts["training_readiness_json"] = str(report_root / "training_readiness.json")
    artifacts["training_readiness_md"] = str(report_root / "training_readiness.md")
    save_training_readiness_json(readiness, artifacts["training_readiness_json"])
    save_training_readiness_markdown(readiness, artifacts["training_readiness_md"])

    warnings.extend(seed_report.warnings)
    warnings.extend(repair_report.warnings)
    warnings.extend(split_manifest.leakage_warnings)
    warnings.extend(readiness.warnings)
    report = GoldTrainingPackReport(
        output_dir=str(output_root),
        reports_dir=str(report_root),
        gold_seed_dir=str(gold_seed_dir),
        dataset_dir=str(dataset_dir),
        repaired_dataset_dir=str(repaired_dir),
        split_dir=str(split_dir),
        label_map_dir=str(label_map_dir),
        ready=readiness.ready,
        warnings=warnings,
        artifacts=artifacts,
    )
    (report_root / "gold_training_pack.json").write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    (report_root / "gold_training_pack.md").write_text(format_gold_training_pack_markdown(report), encoding="utf-8")
    return report


def format_gold_training_pack_markdown(report: GoldTrainingPackReport) -> str:
    return "\n".join(
        [
            "# GBM-BERT Gold Training Pack",
            "",
            RESEARCH_WARNING,
            "",
            f"- Output directory: `{report.output_dir}`",
            f"- Reports directory: `{report.reports_dir}`",
            f"- Ready: {report.ready}",
            f"- Warnings: {len(report.warnings)}",
            "",
            "## Artifacts",
            *[f"- {key}: `{value}`" for key, value in sorted(report.artifacts.items())],
            "",
            "## Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
        ]
    ).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a GBM-BERT gold training pack from reviewed curation artifacts.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/training/gold_pack"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/training/gold_pack"))
    parser.add_argument("--reviewed-queue-jsonl", type=Path)
    parser.add_argument("--prediction-reviewed-queue-jsonl", type=Path)
    parser.add_argument("--entity-jsonl", type=Path)
    parser.add_argument("--min-examples-per-task", type=int, default=10)
    parser.add_argument("--min-examples-per-label", type=int, default=2)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-not-ready", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_gold_training_pack(
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        prediction_reviewed_queue_jsonl=args.prediction_reviewed_queue_jsonl,
        entity_jsonl=args.entity_jsonl,
        min_examples_per_task=args.min_examples_per_task,
        min_examples_per_label=args.min_examples_per_label,
    )
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(format_gold_training_pack_markdown(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_gold_training_pack_markdown(report))
    return 0 if report.ready or args.allow_not_ready else 1


def _copy_gold_seed_to_annotation_dataset(gold_seed_dir: Path, dataset_dir: Path) -> None:
    mapping = {
        "gold_ner.jsonl": "ner.jsonl",
        "gold_evidence.jsonl": "evidence.jsonl",
        "gold_relations.jsonl": "relations.jsonl",
    }
    for source_name, target_name in mapping.items():
        source = gold_seed_dir / source_name
        target = dataset_dir / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.copyfile(source, target)
        else:
            target.write_text("", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
