"""Research-scope drift monitor for GBM-AI user-facing artifacts."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING

DEFAULT_SCOPE_PATHS = [
    Path("README.md"),
    Path("docs/ANNOTATION_GUIDELINES.md"),
    Path("docs/PROJECT_SCOPE.json"),
    Path("docs/RESEARCH_SCOPE_V2.md"),
    Path("reports/wireframes/kg_explorer.md"),
    Path("src/gbmbert/dashboard/app.py"),
    Path("src/gbmbert/knowledge_graph/explorer.py"),
]

PROHIBITED_ASSERTION_PATTERNS = (
    re.compile(r"\bis intended for diagnosis\b", re.IGNORECASE),
    re.compile(r"\bis intended for treatment selection\b", re.IGNORECASE),
    re.compile(r"\bclinical decision support system\b", re.IGNORECASE),
    re.compile(r"\bvalidated clinical accuracy\b", re.IGNORECASE),
    re.compile(r"\btreatment recommendation\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ScopeDriftFinding:
    path: str
    finding_type: str
    detail: str


@dataclass(frozen=True)
class ScopeDriftReport:
    checked_paths: list[str]
    finding_count: int
    missing_warning_count: int
    prohibited_assertion_count: int
    safe: bool
    findings: list[ScopeDriftFinding]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def monitor_scope_drift(paths: list[str | Path] | None = None) -> ScopeDriftReport:
    """Check core user-facing files for safety-boundary drift."""

    checked = [Path(path) for path in (paths or DEFAULT_SCOPE_PATHS)]
    findings: list[ScopeDriftFinding] = []
    for path in checked:
        if not path.exists():
            findings.append(ScopeDriftFinding(str(path), "missing_file", "Expected scope file does not exist"))
            continue
        text = path.read_text(encoding="utf-8")
        if not _contains_research_warning(text):
            findings.append(ScopeDriftFinding(str(path), "missing_research_warning", "Required research-use warning not found"))
        for pattern in PROHIBITED_ASSERTION_PATTERNS:
            for match in pattern.finditer(text):
                if _is_negated_context(text, match.start()):
                    continue
                findings.append(
                    ScopeDriftFinding(
                        str(path),
                        "prohibited_assertion",
                        f"Potential scope drift phrase: {match.group(0)}",
                    )
                )
    missing_warning_count = sum(1 for finding in findings if finding.finding_type == "missing_research_warning")
    prohibited_count = sum(1 for finding in findings if finding.finding_type == "prohibited_assertion")
    return ScopeDriftReport(
        checked_paths=[str(path) for path in checked],
        finding_count=len(findings),
        missing_warning_count=missing_warning_count,
        prohibited_assertion_count=prohibited_count,
        safe=not findings,
        findings=findings,
    )


def save_scope_drift_json(report: ScopeDriftReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_scope_drift_markdown(report: ScopeDriftReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_scope_drift_markdown(report), encoding="utf-8")
    return output_path


def format_scope_drift_markdown(report: ScopeDriftReport) -> str:
    lines = [
        "# GBM-AI Scope Drift Monitor",
        "",
        RESEARCH_WARNING,
        "",
        f"- Checked paths: {len(report.checked_paths)}",
        f"- Safe: {report.safe}",
        f"- Findings: {report.finding_count}",
        f"- Missing warnings: {report.missing_warning_count}",
        f"- Prohibited assertions: {report.prohibited_assertion_count}",
        "",
        "## Findings",
    ]
    if report.findings:
        lines.extend(f"- `{finding.path}` {finding.finding_type}: {finding.detail}" for finding in report.findings)
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check GBM-AI files for research-scope drift.")
    parser.add_argument("--path", type=Path, action="append", default=[], help="Path to check. Repeat for multiple paths.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = monitor_scope_drift(args.path or None)
    if args.json_output:
        save_scope_drift_json(report, args.json_output)
    if args.markdown_output:
        save_scope_drift_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_scope_drift_markdown(report))
    return 0 if report.safe else 1


def _is_negated_context(text: str, start: int) -> bool:
    window = text[max(0, start - 80) : start].casefold()
    return any(marker in window for marker in ("not ", "must not ", "never ", "out of scope", "prohibited"))


def _contains_research_warning(text: str) -> bool:
    return _compact_boundary_text(RESEARCH_WARNING) in _compact_boundary_text(text)


def _compact_boundary_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


if __name__ == "__main__":
    raise SystemExit(main())
