"""Standalone export for dashboard training governance detail rows."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.dashboard.app import RESEARCH_WARNING, training_artifacts_dashboard_context


REQUIRED_GOVERNANCE_DETAIL_ROWS = (
    "Curated fixture import",
    "Curated provenance diff",
    "Evidence pack",
    "Gold pack",
    "Gold-pack promotion review",
    "Launcher menu check",
    "Model registry audit",
    "Relation pack",
    "Training config suite",
    "Training label drift",
    "Training pack comparison",
)


@dataclass(frozen=True)
class GovernanceDetailExport:
    root: str
    row_count: int
    missing_count: int
    invalid_count: int
    rows: list[dict[str, object]]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GovernanceDetailContract:
    detail_json_path: str
    valid: bool
    required_rows: list[str]
    present_required_rows: list[str]
    missing_required_rows: list[str]
    malformed_required_rows: list[str]
    row_count: int
    warning_present: bool
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_governance_detail_export(root: str | Path = ".") -> GovernanceDetailExport:
    """Build a report from the dashboard's governance detail context."""

    root_path = Path(root)
    context = training_artifacts_dashboard_context(root_path)
    rows = list(context.get("governance_report_details") or [])
    missing_count = sum(1 for row in rows if str(row.get("status") or "") == "missing")
    invalid_count = sum(1 for row in rows if str(row.get("status") or "") == "invalid")
    return GovernanceDetailExport(
        root=str(root_path),
        row_count=len(rows),
        missing_count=missing_count,
        invalid_count=invalid_count,
        rows=rows,
    )


def validate_governance_detail_contract(
    detail_json: str | Path = Path("reports/training/governance_detail_links.json"),
) -> GovernanceDetailContract:
    """Validate that the governance detail export keeps required report rows visible."""

    path = Path(detail_json)
    payload = _read_json_object(path) if path.exists() else {}
    rows = payload.get("rows") if isinstance(payload, dict) else []
    row_list = rows if isinstance(rows, list) else []
    by_title = {str(row.get("title") or ""): row for row in row_list if isinstance(row, dict)}
    required_rows = list(REQUIRED_GOVERNANCE_DETAIL_ROWS)
    present_required = [title for title in required_rows if title in by_title]
    missing_required = [title for title in required_rows if title not in by_title]
    malformed = [
        title
        for title in present_required
        if not _row_has_contract_fields(by_title[title])
    ]
    warning_present = payload.get("warning") == RESEARCH_WARNING if isinstance(payload, dict) else False
    return GovernanceDetailContract(
        detail_json_path=str(path),
        valid=path.exists() and warning_present and not missing_required and not malformed,
        required_rows=required_rows,
        present_required_rows=present_required,
        missing_required_rows=missing_required,
        malformed_required_rows=malformed,
        row_count=len(row_list),
        warning_present=warning_present,
    )


def save_governance_detail_export_json(report: GovernanceDetailExport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_governance_detail_export_markdown(report: GovernanceDetailExport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_governance_detail_export_markdown(report), encoding="utf-8")
    return output


def save_governance_detail_contract_json(report: GovernanceDetailContract, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_governance_detail_contract_markdown(report: GovernanceDetailContract, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_governance_detail_contract_markdown(report), encoding="utf-8")
    return output


def format_governance_detail_export_markdown(report: GovernanceDetailExport) -> str:
    lines = [
        "# Training Governance Detail Links",
        "",
        RESEARCH_WARNING,
        "",
        f"- Root: `{report.root}`",
        f"- Rows: {report.row_count}",
        f"- Missing reports: {report.missing_count}",
        f"- Invalid reports: {report.invalid_count}",
        "",
        "This export mirrors the dashboard training-governance detail rows for handoff review. Missing rows are visibility signals only and do not imply model or clinical readiness.",
        "",
        "| Report | Status | Markdown | Markdown Exists | JSON | JSON Exists |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report.rows:
        lines.append(
            "| {title} | {status} | `{markdown}` | {markdown_exists} | `{json_path}` | {json_exists} |".format(
                title=row.get("title", ""),
                status=row.get("status", ""),
                markdown=row.get("markdown_path", ""),
                markdown_exists=row.get("markdown_exists", False),
                json_path=row.get("json_path", ""),
                json_exists=row.get("json_exists", False),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def format_governance_detail_contract_markdown(report: GovernanceDetailContract) -> str:
    lines = [
        "# Governance Detail Artifact Contract",
        "",
        RESEARCH_WARNING,
        "",
        f"- Detail JSON: `{report.detail_json_path}`",
        f"- Valid: {report.valid}",
        f"- Rows: {report.row_count}",
        f"- Warning present: {report.warning_present}",
        "",
        "This contract checks that required governance rows remain visible. Missing report files inside those rows are review signals only and do not imply model or clinical readiness.",
        "",
        "## Required Rows",
        *[f"- {title}" for title in report.required_rows],
        "",
        "## Missing Required Rows",
        *([f"- {title}" for title in report.missing_required_rows] if report.missing_required_rows else ["- none"]),
        "",
        "## Malformed Required Rows",
        *([f"- {title}" for title in report.malformed_required_rows] if report.malformed_required_rows else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export dashboard training-governance detail rows.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/governance_detail_links.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/governance_detail_links.md"))
    parser.add_argument("--json", action="store_true")
    return parser


def build_contract_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the governance detail export artifact contract.")
    parser.add_argument("--detail-json", type=Path, default=Path("reports/training/governance_detail_links.json"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/training/governance_detail_contract.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/training/governance_detail_contract.md"))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_governance_detail_export(args.root)
    save_governance_detail_export_json(report, args.json_output)
    save_governance_detail_export_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_governance_detail_export_markdown(report))
    return 0


def contract_main(argv: list[str] | None = None) -> int:
    args = build_contract_arg_parser().parse_args(argv)
    report = validate_governance_detail_contract(args.detail_json)
    save_governance_detail_contract_json(report, args.json_output)
    save_governance_detail_contract_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_governance_detail_contract_markdown(report))
    return 0 if report.valid else 1


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"governance detail JSON must be an object: {path}")
    return payload


def _row_has_contract_fields(row: dict[str, object]) -> bool:
    return all(
        key in row
        for key in (
            "title",
            "status",
            "markdown_path",
            "markdown_exists",
            "json_path",
            "json_exists",
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
