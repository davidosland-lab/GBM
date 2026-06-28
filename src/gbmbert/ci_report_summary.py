"""Compact CI summary for GBM-AI verification artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


REQUIRED_REPORTS = {
    "local verification": Path("reports/platform_regression/local_verification.json"),
    "artifact policy": Path("reports/platform_regression/artifact_policy.json"),
    "launcher menu": Path("reports/platform_regression/launcher_menu_check.json"),
    "default governance": Path("reports/training/governance/training_governance_suite.json"),
    "strict governance": Path("reports/training/governance_strict/training_governance_suite.json"),
    "gold-pack promotion": Path("reports/training/gold_pack/gold_pack_promotion_review.json"),
}

# Optional reports are surfaced when present but never block summary generation, so a
# missing report file stays visible as a review signal without implying readiness.
OPTIONAL_REPORTS = {
    "governance detail contract": Path("reports/training/governance_detail_contract.json"),
}


class CIReportInputError(RuntimeError):
    """Raised when the CI summary cannot read a required report."""


@dataclass(frozen=True)
class CIReportContract:
    summary_path: str
    valid: bool
    required_families: list[str]
    referenced_families: list[str]
    missing_families: list[str]
    audit_signal_note_present: bool
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_ci_report_summary(root: str | Path = ".") -> str:
    root_path = Path(root)
    payloads = _read_required_reports(root_path)
    optional = _read_optional_reports(root_path)
    local = payloads["local verification"]
    policy = payloads["artifact policy"]
    launcher = payloads["launcher menu"]
    governance = payloads["default governance"]
    strict = payloads["strict governance"]
    promotion = payloads["gold-pack promotion"]
    detail_contract = optional["governance detail contract"]
    detail_present = detail_contract is not None
    detail_missing_rows = len((detail_contract or {}).get("missing_required_rows") or [])
    detail_detail = f"{detail_missing_rows} missing row(s)" if detail_present else "report missing"
    lines = [
        "# GBM-AI CI Verification Summary",
        "",
        RESEARCH_WARNING,
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
        _row("Local verification", bool(local.get("passed")), f"{local.get('passed_step_count', 0)}/{local.get('step_count', 0)} steps"),
        _row("Artifact policy", bool(policy.get("safe")), f"{policy.get('finding_count', 0)} findings"),
        _row("Launcher menu", bool(launcher.get("safe")), f"{launcher.get('warning_count', 0)} warnings"),
        _row("Default governance", bool(governance.get("passed")), f"{len(governance.get('warnings') or [])} warnings"),
        _row("Strict governance audit", not bool(strict.get("passed")), f"{len(strict.get('warnings') or [])} expected audit warning(s)"),
        _row("Gold-pack promotion", bool(promotion.get("promotable")), f"{len(promotion.get('blockers') or [])} blocker(s)"),
        _row("Governance detail contract", detail_present and bool(detail_contract.get("valid")), detail_detail),
        "",
        "Strict governance and gold-pack promotion are audit signals. A non-promotable gold pack is expected until reviewed data volume thresholds are met.",
        "The governance detail contract is a visibility signal; missing detail rows stay listed and do not imply model or clinical readiness.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def validate_ci_report_summary_contract(
    summary_path: str | Path = Path("reports/platform_regression/ci_report_summary.md"),
) -> CIReportContract:
    """Validate that the generated CI summary still references required report families."""

    path = Path(summary_path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required_families = [
        "Local verification",
        "Artifact policy",
        "Launcher menu",
        "Default governance",
        "Strict governance audit",
        "Gold-pack promotion",
        "Governance detail contract",
    ]
    referenced_families = [family for family in required_families if family in text]
    missing_families = [family for family in required_families if family not in text]
    audit_signal_note_present = "Strict governance and gold-pack promotion are audit signals" in text
    return CIReportContract(
        summary_path=str(path),
        valid=path.exists() and not missing_families and audit_signal_note_present and RESEARCH_WARNING in text,
        required_families=required_families,
        referenced_families=referenced_families,
        missing_families=missing_families,
        audit_signal_note_present=audit_signal_note_present,
    )


def save_ci_report_contract_json(report: CIReportContract, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_ci_report_contract_markdown(report: CIReportContract, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_ci_report_contract_markdown(report), encoding="utf-8")
    return output


def format_ci_report_contract_markdown(report: CIReportContract) -> str:
    lines = [
        "# CI Summary Artifact Contract",
        "",
        RESEARCH_WARNING,
        "",
        f"- Summary: `{report.summary_path}`",
        f"- Valid: {report.valid}",
        f"- Audit-signal note present: {report.audit_signal_note_present}",
        "",
        "## Required Families",
        *[f"- {family}" for family in report.required_families],
        "",
        "## Missing Families",
        *([f"- {family}" for family in report.missing_families] if report.missing_families else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a compact Markdown summary from verification reports.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("reports/platform_regression/ci_report_summary.md"))
    return parser


def build_contract_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the generated CI summary artifact contract.")
    parser.add_argument("--summary", type=Path, default=Path("reports/platform_regression/ci_report_summary.md"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/platform_regression/ci_summary_contract.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/platform_regression/ci_summary_contract.md"))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        summary = build_ci_report_summary(args.root)
    except CIReportInputError as exc:
        print(f"CI summary input error: {exc}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")
    print(summary)
    return 0


def contract_main(argv: list[str] | None = None) -> int:
    args = build_contract_arg_parser().parse_args(argv)
    report = validate_ci_report_summary_contract(args.summary)
    save_ci_report_contract_json(report, args.json_output)
    save_ci_report_contract_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_ci_report_contract_markdown(report))
    return 0 if report.valid else 1


def _read_required_reports(root_path: Path) -> dict[str, dict[str, Any]]:
    return {name: _read_json(root_path / path) for name, path in REQUIRED_REPORTS.items()}


def _read_optional_reports(root_path: Path) -> dict[str, dict[str, Any] | None]:
    return {name: _read_optional_json(root_path / path) for name, path in OPTIONAL_REPORTS.items()}


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CIReportInputError(f"required report not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CIReportInputError(f"required report is invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise CIReportInputError(f"required report must be a JSON object: {path}")
    return payload


def _row(name: str, passed: bool, detail: str) -> str:
    return f"| {name} | {'pass' if passed else 'review'} | {detail} |"


if __name__ == "__main__":
    raise SystemExit(main())
