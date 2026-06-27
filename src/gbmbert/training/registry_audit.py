"""Audit GBM-BERT checkpoint registry metadata for research-safety gaps."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.training.registry import load_registry

SAFE_STATUSES = {"candidate", "research_candidate", "metadata_only", "dry_run", "smoke", "scaffold"}
UNSAFE_STATUS_TERMS = ("clinical", "production", "validated", "deployed", "approved")
UNSAFE_NOTE_PHRASES = (
    "approved for clinical",
    "clinical decision support",
    "diagnosis",
    "treatment recommendation",
    "validated clinical",
)


@dataclass(frozen=True)
class RegistryAuditEntry:
    name: str
    task: str
    status: str
    checks: dict[str, bool]
    model_card_paths: list[str]
    dataset_card_paths: list[str]
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class RegistryAuditReport:
    registry_path: str
    reports_dir: str
    checkpoint_count: int
    passed: bool
    entries: list[RegistryAuditEntry]
    errors: list[str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_checkpoint_registry(registry_path: str | Path, *, reports_dir: str | Path = "reports/training") -> RegistryAuditReport:
    """Audit registry records for stale paths, missing cards, unsafe statuses, and missing warnings."""

    path = Path(registry_path)
    report_root = Path(reports_dir)
    registry = load_registry(path)
    entries: list[RegistryAuditEntry] = []
    for item in registry.get("checkpoints", []):
        if not isinstance(item, dict):
            continue
        entries.append(_audit_entry(item, report_root))
    errors = [error for entry in entries for error in entry.errors]
    warnings = [warning for entry in entries for warning in entry.warnings]
    if registry.get("warning") != RESEARCH_WARNING:
        errors.append("registry missing required research-use warning")
    return RegistryAuditReport(
        registry_path=str(path),
        reports_dir=str(report_root),
        checkpoint_count=len(entries),
        passed=not errors,
        entries=entries,
        errors=errors,
        warnings=warnings,
    )


def save_registry_audit_json(report: RegistryAuditReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_registry_audit_markdown(report: RegistryAuditReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_registry_audit_markdown(report), encoding="utf-8")
    return output


def format_registry_audit_markdown(report: RegistryAuditReport) -> str:
    lines = [
        "# GBM-BERT Model Registry Audit",
        "",
        RESEARCH_WARNING,
        "",
        f"- Registry: `{report.registry_path}`",
        f"- Reports directory: `{report.reports_dir}`",
        f"- Checkpoints: {report.checkpoint_count}",
        f"- Passed: {report.passed}",
        f"- Errors: {len(report.errors)}",
        f"- Warnings: {len(report.warnings)}",
        "",
        "## Entries",
    ]
    for entry in report.entries:
        lines.extend(
            [
                f"### {entry.name}",
                f"- Task: {entry.task}",
                f"- Status: {entry.status}",
                "- Checks:",
                *[f"- {name}: {value}" for name, value in sorted(entry.checks.items())],
                "- Model cards:",
                *([f"- `{path}`" for path in entry.model_card_paths] if entry.model_card_paths else ["- none"]),
                "- Dataset cards:",
                *([f"- `{path}`" for path in entry.dataset_card_paths] if entry.dataset_card_paths else ["- none"]),
                "- Errors:",
                *([f"- {error}" for error in entry.errors] if entry.errors else ["- none"]),
                "- Warnings:",
                *([f"- {warning}" for warning in entry.warnings] if entry.warnings else ["- none"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Errors",
            *([f"- {error}" for error in report.errors] if report.errors else ["- none"]),
            "",
            "## Warnings",
            *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit GBM-BERT checkpoint registry metadata.")
    parser.add_argument("registry", type=Path)
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/training"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-findings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = audit_checkpoint_registry(args.registry, reports_dir=args.reports_dir)
    if args.json_output:
        save_registry_audit_json(report, args.json_output)
    if args.markdown_output:
        save_registry_audit_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_registry_audit_markdown(report))
    return 0 if report.passed or args.allow_findings else 1


def _audit_entry(item: dict[str, Any], reports_dir: Path) -> RegistryAuditEntry:
    name = str(item.get("name") or "")
    status = str(item.get("status") or "")
    task = str(item.get("task") or "")
    model_cards, dataset_cards = _find_cards(name, reports_dir)
    notes = str(item.get("notes") or "")
    checks = {
        "name_present": bool(name),
        "checkpoint_dir_exists": Path(str(item.get("checkpoint_dir") or "")).exists(),
        "metrics_path_exists_or_empty": not item.get("metrics_path") or Path(str(item.get("metrics_path"))).exists(),
        "manifest_path_exists_or_empty": not item.get("manifest_path") or Path(str(item.get("manifest_path"))).exists(),
        "status_research_safe": status in SAFE_STATUSES and not any(term in status.casefold() for term in UNSAFE_STATUS_TERMS),
        "entry_warning_present": item.get("warning") == RESEARCH_WARNING,
        "model_card_present": bool(model_cards),
        "dataset_card_present": bool(dataset_cards),
        "notes_do_not_overclaim": not _has_unsafe_phrase(notes),
    }
    errors: list[str] = []
    warnings: list[str] = []
    if not checks["name_present"]:
        errors.append("checkpoint entry missing name")
    if not checks["checkpoint_dir_exists"]:
        errors.append(f"{name}: checkpoint_dir does not exist")
    if not checks["metrics_path_exists_or_empty"]:
        errors.append(f"{name}: metrics_path does not exist")
    if not checks["manifest_path_exists_or_empty"]:
        errors.append(f"{name}: manifest_path does not exist")
    if not checks["status_research_safe"]:
        errors.append(f"{name}: status is not research-safe: {status}")
    if not checks["entry_warning_present"]:
        errors.append(f"{name}: missing required research-use warning")
    if not checks["notes_do_not_overclaim"]:
        errors.append(f"{name}: notes contain unsafe clinical or validation language")
    if not checks["model_card_present"]:
        warnings.append(f"{name}: no matching model card found")
    if not checks["dataset_card_present"]:
        warnings.append(f"{name}: no matching dataset card found")
    return RegistryAuditEntry(
        name=name,
        task=task,
        status=status,
        checks=checks,
        model_card_paths=[str(path) for path in model_cards],
        dataset_card_paths=[str(path) for path in dataset_cards],
        errors=errors,
        warnings=warnings,
    )


def _find_cards(checkpoint_name: str, reports_dir: Path) -> tuple[list[Path], list[Path]]:
    model_cards: list[Path] = []
    dataset_cards: list[Path] = []
    if not reports_dir.exists():
        return model_cards, dataset_cards
    for path in reports_dir.rglob("*model_card.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("checkpoint_name") == checkpoint_name:
            model_cards.append(path)
            if isinstance(payload.get("dataset_card"), dict):
                dataset_cards.append(path)
    for path in reports_dir.rglob("*dataset_card.json"):
        if checkpoint_name.casefold() in path.name.casefold():
            dataset_cards.append(path)
    return sorted(set(model_cards)), sorted(set(dataset_cards))


def _has_unsafe_phrase(text: str) -> bool:
    folded = text.casefold()
    return any(phrase in folded and f"not {phrase}" not in folded for phrase in UNSAFE_NOTE_PHRASES)


if __name__ == "__main__":
    raise SystemExit(main())
