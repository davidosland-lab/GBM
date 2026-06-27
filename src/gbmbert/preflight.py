"""Local environment preflight checks for GBM-AI."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from gbmbert.extraction.pipeline import DEFAULT_MODEL_NAME
from gbmbert.paths import standard_paths


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class PreflightReport:
    checks: list[PreflightCheck]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": [asdict(check) for check in self.checks]}


def run_preflight(*, model_name: str = DEFAULT_MODEL_NAME) -> PreflightReport:
    """Run read-only local checks without exposing secrets."""

    _load_environment()
    paths = standard_paths()
    checks = [
        _python_check(),
        _venv_check(),
        _path_check("data/raw", paths.raw_dir),
        _path_check("data/processed", paths.processed_dir),
        _path_check("data/review", paths.review_dir),
        _path_check("reports/corpus", paths.corpus_reports_dir),
        _path_check("reports/graph", paths.graph_reports_dir),
        _path_check("reports/review", paths.review_reports_dir),
        _env_check("NCBI_EMAIL"),
        _env_check("NCBI_API_KEY"),
        _optional_env_check("NEO4J_URI"),
        _optional_env_check("NEO4J_USER"),
        _optional_env_check("NEO4J_PASSWORD"),
        _model_cache_check(model_name),
    ]
    return PreflightReport(checks=checks)


def save_preflight_json(report: PreflightReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_preflight_markdown(report: PreflightReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_preflight_markdown(report), encoding="utf-8")
    return output_path


def format_preflight_markdown(report: PreflightReport) -> str:
    lines = [
        "# GBM-AI Preflight Report",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Overall: {'pass' if report.ok else 'attention needed'}",
        "",
        "## Checks",
    ]
    lines.extend(
        f"- {'PASS' if check.ok else 'WARN'} `{check.name}`: {check.detail}"
        for check in report.checks
    )
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local GBM-AI environment preflight checks.")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    report = run_preflight(model_name=args.model)
    if args.json_output:
        save_preflight_json(report, args.json_output)
    if args.markdown_output:
        save_preflight_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_preflight_markdown(report))
    if args.fail_on_warn and not report.ok:
        return 1
    return 0


def _load_environment() -> None:
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            load_dotenv(dotenv_path=env_path, encoding="utf-8")
        except UnicodeDecodeError:
            load_dotenv(dotenv_path=env_path, encoding="utf-16")


def _python_check() -> PreflightCheck:
    ok = sys.version_info[:2] in ((3, 11), (3, 12)) and platform.architecture()[0] == "64bit"
    return PreflightCheck(
        name="python",
        ok=ok,
        detail=f"{platform.python_version()} {platform.architecture()[0]}",
    )


def _venv_check() -> PreflightCheck:
    ok = Path(sys.prefix).name.casefold() == ".venv"
    return PreflightCheck(name="local_venv", ok=ok, detail=sys.prefix)


def _path_check(name: str, path: Path) -> PreflightCheck:
    return PreflightCheck(name=name, ok=path.exists(), detail=str(path))


def _env_check(name: str) -> PreflightCheck:
    return PreflightCheck(
        name=name,
        ok=bool(os.getenv(name)),
        detail="configured" if os.getenv(name) else "not configured",
    )


def _optional_env_check(name: str) -> PreflightCheck:
    return PreflightCheck(
        name=name,
        ok=True,
        detail="configured" if os.getenv(name) else "not configured",
    )


def _model_cache_check(model_name: str) -> PreflightCheck:
    try:
        from transformers import AutoConfig

        AutoConfig.from_pretrained(model_name, local_files_only=True)
    except Exception as exc:  # noqa: BLE001 - preflight should report, not fail.
        return PreflightCheck(
            name="hf_model_cache",
            ok=False,
            detail=f"{model_name} not available locally ({exc.__class__.__name__})",
        )
    return PreflightCheck(name="hf_model_cache", ok=True, detail=f"{model_name} available locally")


if __name__ == "__main__":
    raise SystemExit(main())
