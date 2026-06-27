"""Import and validate reviewed curated training fixtures."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


REVIEW_METADATA_FIELDS = ("review_status", "reviewer", "review_notes")


@dataclass(frozen=True)
class CuratedFixtureImportReport:
    output_dir: str
    evidence_path: str
    entity_path: str
    reviewed_queue_path: str
    evidence_paths: list[str]
    entity_paths: list[str]
    reviewed_queue_paths: list[str]
    copied_files: dict[str, str]
    combined_files: dict[str, str]
    evidence_rows: int
    entity_rows: int
    reviewed_queue_rows: int
    pmid_count: int
    reviewed_item_types: dict[str, int]
    missing_pmid_count: int
    missing_review_metadata_count: int
    warning_count: int
    safe: bool
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def import_curated_training_fixture(
    *,
    evidence_jsonl: str | Path | list[str | Path],
    entity_jsonl: str | Path | list[str | Path],
    reviewed_queue_jsonl: str | Path | list[str | Path],
    output_dir: str | Path,
    copy_files: bool = True,
) -> CuratedFixtureImportReport:
    """Validate and optionally copy a curated evidence/NER/relation fixture batch."""

    evidence_paths = _paths(evidence_jsonl)
    entity_paths = _paths(entity_jsonl)
    reviewed_paths = _paths(reviewed_queue_jsonl)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    evidence_rows = _read_jsonl_many(evidence_paths)
    entity_rows = _read_jsonl_many(entity_paths)
    reviewed_rows = _read_jsonl_many(reviewed_paths)
    warnings: list[str] = []
    pmids: set[str] = set()
    missing_pmid_count = 0
    missing_review_metadata_count = 0

    for source_name, rows in (("evidence", evidence_rows), ("entities", entity_rows), ("reviewed_queue", reviewed_rows)):
        for index, row in enumerate(rows, start=1):
            pmid = _row_pmid(row)
            if pmid:
                pmids.add(pmid)
            else:
                missing_pmid_count += 1
                warnings.append(f"{source_name} row {index} is missing source PMID")

    for source_name, rows in (("evidence", evidence_rows), ("reviewed_queue", reviewed_rows)):
        for index, row in enumerate(rows, start=1):
            missing = [field for field in REVIEW_METADATA_FIELDS if not str(row.get(field) or "").strip()]
            if missing:
                missing_review_metadata_count += 1
                warnings.append(f"{source_name} row {index} is missing review metadata: {', '.join(missing)}")

    for source_name, paths in (("evidence", evidence_paths), ("entities", entity_paths), ("reviewed_queue", reviewed_paths)):
        if not paths:
            warnings.append(f"{source_name} source file list is empty")
        for path in paths:
            if not path.exists():
                warnings.append(f"{source_name} source file not found: {path}")

    copied_files: dict[str, str] = {}
    if copy_files:
        for key, paths in (("evidence", evidence_paths), ("entities", entity_paths), ("reviewed_queue", reviewed_paths)):
            for source in paths:
                if source.exists():
                    target = output_root / _unique_target_name(output_root, source.name)
                    shutil.copy2(source, target)
                    copied_files[f"{key}:{source.name}"] = str(target)

    combined_files = {
        "evidence": str(_write_jsonl(output_root / "combined_evidence.jsonl", evidence_rows)),
        "entities": str(_write_jsonl(output_root / "combined_entities.jsonl", entity_rows)),
        "reviewed_queue": str(_write_jsonl(output_root / "combined_reviewed_queue.jsonl", reviewed_rows)),
    }

    report = CuratedFixtureImportReport(
        output_dir=str(output_root),
        evidence_path=str(evidence_paths[0]) if evidence_paths else "",
        entity_path=str(entity_paths[0]) if entity_paths else "",
        reviewed_queue_path=str(reviewed_paths[0]) if reviewed_paths else "",
        evidence_paths=[str(path) for path in evidence_paths],
        entity_paths=[str(path) for path in entity_paths],
        reviewed_queue_paths=[str(path) for path in reviewed_paths],
        copied_files=copied_files,
        combined_files=combined_files,
        evidence_rows=len(evidence_rows),
        entity_rows=sum(len(row.get("entities") or []) for row in entity_rows),
        reviewed_queue_rows=len(reviewed_rows),
        pmid_count=len(pmids),
        reviewed_item_types=dict(sorted(Counter(str(row.get("item_type") or "unknown") for row in reviewed_rows).items())),
        missing_pmid_count=missing_pmid_count,
        missing_review_metadata_count=missing_review_metadata_count,
        warning_count=len(warnings),
        safe=not warnings,
        warnings=warnings,
    )
    return report


def save_curated_fixture_import_json(report: CuratedFixtureImportReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_curated_fixture_import_markdown(report: CuratedFixtureImportReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_curated_fixture_import_markdown(report), encoding="utf-8")
    return output


def format_curated_fixture_import_markdown(report: CuratedFixtureImportReport) -> str:
    lines = [
        "# Curated Training Fixture Import",
        "",
        RESEARCH_WARNING,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- Safe: {report.safe}",
        f"- Evidence rows: {report.evidence_rows}",
        f"- Entity rows: {report.entity_rows}",
        f"- Reviewed queue rows: {report.reviewed_queue_rows}",
        f"- Source PMIDs: {report.pmid_count}",
        f"- Missing PMID rows: {report.missing_pmid_count}",
        f"- Missing review metadata rows: {report.missing_review_metadata_count}",
        f"- Warnings: {report.warning_count}",
        "",
        "## Reviewed Item Types",
        *([f"- {name}: {count}" for name, count in report.reviewed_item_types.items()] or ["- none"]),
        "",
        "## Copied Files",
        *([f"- {name}: `{path}`" for name, path in sorted(report.copied_files.items())] or ["- none"]),
        "",
        "## Combined Files",
        *([f"- {name}: `{path}`" for name, path in sorted(report.combined_files.items())] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import and validate a curated training fixture batch.")
    parser.add_argument("--evidence-jsonl", type=Path, action="append", required=True)
    parser.add_argument("--entity-jsonl", type=Path, action="append", required=True)
    parser.add_argument("--reviewed-queue-jsonl", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/training/curated_import"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/curated_fixture_import.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/curated_fixture_import.md"))
    parser.add_argument("--no-copy", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-warnings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = import_curated_training_fixture(
        evidence_jsonl=args.evidence_jsonl,
        entity_jsonl=args.entity_jsonl,
        reviewed_queue_jsonl=args.reviewed_queue_jsonl,
        output_dir=args.output_dir,
        copy_files=not args.no_copy,
    )
    save_curated_fixture_import_json(report, args.json_output)
    save_curated_fixture_import_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_curated_fixture_import_markdown(report))
    return 0 if report.safe or args.allow_warnings else 1


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _read_jsonl_many(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_read_jsonl(path))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def _paths(value: str | Path | list[str | Path]) -> list[Path]:
    if isinstance(value, list):
        return [Path(item) for item in value]
    return [Path(value)]


def _unique_target_name(output_root: Path, name: str) -> str:
    target = output_root / name
    if not target.exists():
        return name
    stem = target.stem
    suffix = target.suffix
    index = 2
    while (output_root / f"{stem}_{index}{suffix}").exists():
        index += 1
    return f"{stem}_{index}{suffix}"


def _row_pmid(row: dict[str, Any]) -> str:
    return str(row.get("source_pmid") or row.get("pmid") or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
