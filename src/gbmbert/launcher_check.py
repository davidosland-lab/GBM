"""Non-interactive checks for the Windows launcher menu."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


REQUIRED_MENU_TEXT = (
    "Setup and environment",
    "Verify, reports, and handoff checks",
    "Literature and graph pipeline",
    "Review and curation workflow",
    "Training data and governance",
    "Knowledge Graph Explorer",
    "Advanced command index",
)
REQUIRED_SHORTCUTS = ("16BI", "16BJ", "16BK", "16BL", "16BM")


@dataclass(frozen=True)
class LauncherMenuCheckReport:
    launcher_path: str
    safe: bool
    label_count: int
    goto_count: int
    missing_required_text: list[str]
    missing_shortcuts: list[str]
    missing_goto_targets: list[str]
    warning_count: int
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_launcher_menu(path: str | Path = "launcher_menu.bat") -> LauncherMenuCheckReport:
    launcher_path = Path(path)
    text = launcher_path.read_text(encoding="utf-8")
    labels = set(re.findall(r"(?im)^:([A-Za-z0-9_]+)\s*$", text))
    goto_targets = re.findall(r"(?i)\bgoto\s+([A-Za-z0-9_]+)", text)
    missing_targets = sorted({target for target in goto_targets if target not in labels and target.lower() not in {"eof"}})
    missing_text = [item for item in REQUIRED_MENU_TEXT if item not in text]
    missing_shortcuts = [shortcut for shortcut in REQUIRED_SHORTCUTS if shortcut not in text]
    warnings = []
    warnings.extend(f"missing required menu text: {item}" for item in missing_text)
    warnings.extend(f"missing required shortcut: {item}" for item in missing_shortcuts)
    warnings.extend(f"goto target has no label: {item}" for item in missing_targets)
    return LauncherMenuCheckReport(
        launcher_path=str(launcher_path),
        safe=not warnings,
        label_count=len(labels),
        goto_count=len(goto_targets),
        missing_required_text=missing_text,
        missing_shortcuts=missing_shortcuts,
        missing_goto_targets=missing_targets,
        warning_count=len(warnings),
        warnings=warnings,
    )


def save_launcher_menu_check_json(report: LauncherMenuCheckReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_launcher_menu_check_markdown(report: LauncherMenuCheckReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_launcher_menu_check_markdown(report), encoding="utf-8")
    return output


def format_launcher_menu_check_markdown(report: LauncherMenuCheckReport) -> str:
    lines = [
        "# Launcher Menu Check",
        "",
        RESEARCH_WARNING,
        "",
        f"- Launcher: `{report.launcher_path}`",
        f"- Safe: {report.safe}",
        f"- Labels: {report.label_count}",
        f"- Goto commands: {report.goto_count}",
        f"- Warnings: {report.warning_count}",
        "",
        "## Missing Required Text",
        *([f"- {item}" for item in report.missing_required_text] if report.missing_required_text else ["- none"]),
        "",
        "## Missing Shortcuts",
        *([f"- {item}" for item in report.missing_shortcuts] if report.missing_shortcuts else ["- none"]),
        "",
        "## Missing Goto Targets",
        *([f"- {item}" for item in report.missing_goto_targets] if report.missing_goto_targets else ["- none"]),
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check launcher menu structure without running it.")
    parser.add_argument("--launcher", type=Path, default=Path("launcher_menu.bat"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/platform_regression/launcher_menu_check.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/platform_regression/launcher_menu_check.md"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-warnings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = check_launcher_menu(args.launcher)
    save_launcher_menu_check_json(report, args.json_output)
    save_launcher_menu_check_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_launcher_menu_check_markdown(report))
    return 0 if report.safe or args.allow_warnings else 1


if __name__ == "__main__":
    raise SystemExit(main())
