"""Artifact policy checks for tracked GBM-AI handoff outputs."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


REQUIRED_ARTIFACTS = (
    Path("CHANGELOG.md"),
    Path("PROJECT_HANDOFF.md"),
    Path("docs/ARTIFACT_POLICY.md"),
    Path("docs/PROJECT_SCOPE.json"),
    Path("reports/artifact_index.json"),
    Path("reports/artifact_index.md"),
    Path("reports/platform_regression/local_verification.json"),
    Path("reports/platform_regression/local_verification.md"),
    Path("reports/training/training_config_suite_review.json"),
    Path("reports/training/training_config_suite_review.md"),
    Path("reports/training/governance/training_governance_suite.json"),
    Path("reports/training/governance/training_governance_suite.md"),
    Path("reports/training/governance_strict/training_governance_suite.json"),
    Path("reports/training/governance_strict/training_governance_suite.md"),
    Path("reports/training/evidence_pack/full_label_coverage_plan.json"),
    Path("reports/training/evidence_pack/full_label_coverage_plan.md"),
    Path("reports/training/gold_pack/gold_pack_expansion_plan.json"),
    Path("reports/training/gold_pack/gold_pack_expansion_plan.md"),
)
FORBIDDEN_TRACKED_PARTS = {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
FORBIDDEN_MODEL_SUFFIXES = {".bin", ".ckpt", ".h5", ".onnx", ".pt", ".pth", ".safetensors"}
DEFAULT_MAX_TRACKED_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ArtifactPolicyFinding:
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class ArtifactPolicyReport:
    root: str
    safe: bool
    required_count: int
    missing_required_count: int
    tracked_count: int
    finding_count: int
    findings: list[ArtifactPolicyFinding]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_artifact_policy(
    *,
    root: str | Path = ".",
    required_paths: tuple[Path, ...] | list[Path] = REQUIRED_ARTIFACTS,
    tracked_paths: list[str | Path] | None = None,
    max_tracked_bytes: int = DEFAULT_MAX_TRACKED_BYTES,
) -> ArtifactPolicyReport:
    """Check that required handoff artifacts exist and heavy byproducts are not tracked."""

    root_path = Path(root)
    tracked = [Path(path) for path in (tracked_paths if tracked_paths is not None else _git_tracked_paths(root_path))]
    findings: list[ArtifactPolicyFinding] = []

    for required in required_paths:
        if not (root_path / required).exists():
            findings.append(ArtifactPolicyFinding("error", str(required), "required handoff artifact is missing"))

    for path in sorted(set(tracked)):
        lowered_parts = {part.casefold() for part in path.parts}
        if lowered_parts & FORBIDDEN_TRACKED_PARTS:
            findings.append(ArtifactPolicyFinding("error", str(path), "local cache or virtual-environment path is tracked"))
            continue
        full_path = root_path / path
        suffix = path.suffix.casefold()
        if suffix in FORBIDDEN_MODEL_SUFFIXES:
            findings.append(ArtifactPolicyFinding("error", str(path), "large model/checkpoint-style binary should not be tracked"))
        if full_path.exists() and full_path.is_file() and full_path.stat().st_size > max_tracked_bytes:
            findings.append(ArtifactPolicyFinding("error", str(path), f"tracked file exceeds {max_tracked_bytes} bytes"))

    error_count = sum(1 for finding in findings if finding.severity == "error")
    return ArtifactPolicyReport(
        root=str(root_path),
        safe=error_count == 0,
        required_count=len(required_paths),
        missing_required_count=sum(1 for finding in findings if finding.message == "required handoff artifact is missing"),
        tracked_count=len(tracked),
        finding_count=len(findings),
        findings=findings,
    )


def save_artifact_policy_json(report: ArtifactPolicyReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_artifact_policy_markdown(report: ArtifactPolicyReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_artifact_policy_markdown(report), encoding="utf-8")
    return output


def format_artifact_policy_markdown(report: ArtifactPolicyReport) -> str:
    lines = [
        "# GBM-AI Artifact Policy Check",
        "",
        RESEARCH_WARNING,
        "",
        f"- Root: `{report.root}`",
        f"- Safe: {report.safe}",
        f"- Required artifacts: {report.required_count}",
        f"- Missing required artifacts: {report.missing_required_count}",
        f"- Tracked paths checked: {report.tracked_count}",
        f"- Findings: {report.finding_count}",
        "",
        "## Findings",
        *([f"- [{finding.severity}] `{finding.path}`: {finding.message}" for finding in report.findings] if report.findings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check tracked artifact policy for GBM-AI handoff outputs.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--max-tracked-bytes", type=int, default=DEFAULT_MAX_TRACKED_BYTES)
    parser.add_argument("--json-output", type=Path, default=Path("reports/platform_regression/artifact_policy.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/platform_regression/artifact_policy.md"))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = check_artifact_policy(root=args.root, max_tracked_bytes=args.max_tracked_bytes)
    save_artifact_policy_json(report, args.json_output)
    save_artifact_policy_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_artifact_policy_markdown(report))
    return 0 if report.safe else 1


def _git_tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return [path.relative_to(root) for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
