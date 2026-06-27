"""Promotion gate for evidence-overlay graph artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


@dataclass(frozen=True)
class PromotionGateCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class EvidenceOverlayPromotionGateReport:
    overlay_graph_path: str
    created_at_utc: str
    safe_to_promote: bool
    check_count: int
    passed_check_count: int
    failed_check_count: int
    checks: list[PromotionGateCheck]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_evidence_overlay_promotion_gate_report(
    *,
    overlay_graph_jsonl: str | Path,
    graph_quality_json: str | Path,
    overlay_diff_json: str | Path,
    overlay_load_guard_json: str | Path,
    handoff_validation_json: str | Path,
    regression_pack_json: str | Path | None = None,
) -> EvidenceOverlayPromotionGateReport:
    """Evaluate whether an evidence-overlay graph is ready for Neo4j loading."""

    checks: list[PromotionGateCheck] = []
    quality = _read_json(graph_quality_json)
    checks.append(
        PromotionGateCheck(
            name="graph_quality",
            passed=int(quality.get("invalid_record_count") or 0) == 0 and not quality.get("warnings", []),
            detail=f"invalid={quality.get('invalid_record_count', 0)}, warnings={len(quality.get('warnings', []))}",
        )
    )
    diff = _read_json(overlay_diff_json)
    checks.append(
        PromotionGateCheck(
            name="overlay_diff",
            passed=int(diff.get("overlay_metadata_count") or 0) > 0 and not diff.get("warnings", []),
            detail=f"overlay_metadata={diff.get('overlay_metadata_count', 0)}, warnings={len(diff.get('warnings', []))}",
        )
    )
    guard = _read_json(overlay_load_guard_json)
    checks.append(
        PromotionGateCheck(
            name="overlay_load_guard",
            passed=bool(guard.get("safe_to_load")) and not guard.get("warnings", []),
            detail=f"safe_to_load={guard.get('safe_to_load')}, warnings={len(guard.get('warnings', []))}",
        )
    )
    validation = _read_json(handoff_validation_json)
    checks.append(
        PromotionGateCheck(
            name="handoff_validation",
            passed=bool(validation.get("valid")) and not validation.get("warnings", []),
            detail=f"valid={validation.get('valid')}, warnings={len(validation.get('warnings', []))}",
        )
    )
    if regression_pack_json:
        regression = _read_json(regression_pack_json)
        checks.append(
            PromotionGateCheck(
                name="curation_regression_pack",
                passed=not regression.get("warnings", []),
                detail=f"warnings={len(regression.get('warnings', []))}",
            )
        )
    warnings = [f"{check.name} failed: {check.detail}" for check in checks if not check.passed]
    return EvidenceOverlayPromotionGateReport(
        overlay_graph_path=str(overlay_graph_jsonl),
        created_at_utc=datetime.now(UTC).isoformat(),
        safe_to_promote=not warnings,
        check_count=len(checks),
        passed_check_count=sum(1 for check in checks if check.passed),
        failed_check_count=sum(1 for check in checks if not check.passed),
        checks=checks,
        warnings=warnings,
    )


def save_promotion_gate_json(report: EvidenceOverlayPromotionGateReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def save_promotion_gate_markdown(report: EvidenceOverlayPromotionGateReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_promotion_gate_markdown(report), encoding="utf-8")
    return output_path


def format_promotion_gate_markdown(report: EvidenceOverlayPromotionGateReport) -> str:
    lines = [
        "# GBM-AI Evidence Overlay Promotion Gate",
        "",
        RESEARCH_WARNING,
        "",
        f"- Overlay graph: `{report.overlay_graph_path}`",
        f"- Created UTC: {report.created_at_utc}",
        f"- Safe to promote: {report.safe_to_promote}",
        f"- Checks: {report.passed_check_count}/{report.check_count} passed",
        "",
        "## Checks",
        *[f"- {check.name}: {'pass' if check.passed else 'fail'} ({check.detail})" for check in report.checks],
        "",
        "## Warnings",
        *([f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gate an evidence-overlay graph before promotion to load-ready status.")
    parser.add_argument("--overlay-graph-jsonl", type=Path, default=Path("data/processed/curation_regression_pack/evidence_overlay_graph_records.jsonl"))
    parser.add_argument("--graph-quality-json", type=Path, default=Path("reports/review/curation_regression_pack/overlay_graph_quality.json"))
    parser.add_argument("--overlay-diff-json", type=Path, default=Path("reports/review/curation_regression_pack/evidence_overlay_diff.json"))
    parser.add_argument("--overlay-load-guard-json", type=Path, default=Path("reports/review/curation_regression_pack/overlay_load_guard.json"))
    parser.add_argument("--handoff-validation-json", type=Path, default=Path("reports/review/curation_regression_pack/curation_handoff_validation.json"))
    parser.add_argument("--regression-pack-json", type=Path, default=Path("reports/review/curation_regression_pack/curation_regression_pack.json"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_evidence_overlay_promotion_gate_report(
        overlay_graph_jsonl=args.overlay_graph_jsonl,
        graph_quality_json=args.graph_quality_json,
        overlay_diff_json=args.overlay_diff_json,
        overlay_load_guard_json=args.overlay_load_guard_json,
        handoff_validation_json=args.handoff_validation_json,
        regression_pack_json=args.regression_pack_json,
    )
    if args.json_output:
        save_promotion_gate_json(report, args.json_output)
    if args.markdown_output:
        save_promotion_gate_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_promotion_gate_markdown(report))
    return 0 if report.safe_to_promote else 1


def _read_json(path: str | Path) -> dict[str, Any]:
    input_path = Path(path)
    return json.loads(input_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
