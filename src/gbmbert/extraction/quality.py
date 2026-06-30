"""Quality reports for biomedical entity extraction output."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.annotation.schema import EntityType
from gbmbert.datasets import RESEARCH_WARNING
from gbmbert.extraction.entities import EntityExtractionResult, ExtractedEntity
from gbmbert.extraction.io import load_entity_jsonl, load_pubmed_jsonl
from gbmbert.extraction.pipeline import paper_to_source_text

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountItem:
    key: str
    count: int


@dataclass(frozen=True)
class OffsetIssue:
    pmid: str
    text: str
    start: int
    end: int
    reason: str


@dataclass(frozen=True)
class EntityQualityReport:
    entity_jsonl_path: str
    pubmed_jsonl_path: str | None
    paper_count: int
    source_paper_count: int | None
    entity_count: int
    empty_paper_count: int
    unknown_entity_count: int
    unknown_entity_rate: float
    average_entities_per_paper: float
    low_confidence_count: int
    short_entity_count: int
    invalid_offset_count: int
    text_mismatch_count: int
    missing_source_pmid_count: int
    label_counts: list[CountItem]
    confidence_bucket_counts: list[CountItem]
    top_normalized_entities: list[CountItem]
    top_unknown_entities: list[CountItem]
    offset_issues: list[OffsetIssue]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_entity_quality_report(
    entity_jsonl: str | Path,
    *,
    pubmed_jsonl: str | Path | None = None,
    low_confidence_threshold: float = 0.5,
    top_limit: int = 10,
    sample_limit: int = 10,
) -> EntityQualityReport:
    """Summarize entity extraction output and optional source-text offset validity."""

    if not 0.0 <= low_confidence_threshold <= 1.0:
        raise ValueError("low_confidence_threshold must be between 0.0 and 1.0")
    if top_limit < 0:
        raise ValueError("top_limit must be non-negative")
    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")

    entity_path = Path(entity_jsonl)
    results = list(load_entity_jsonl(entity_path))
    source_texts = _load_source_texts(pubmed_jsonl)

    label_counts: Counter[str] = Counter()
    confidence_bucket_counts: Counter[str] = Counter()
    normalized_counts: Counter[str] = Counter()
    unknown_counts: Counter[str] = Counter()
    offset_issues: list[OffsetIssue] = []

    entity_count = 0
    empty_paper_count = 0
    unknown_entity_count = 0
    low_confidence_count = 0
    short_entity_count = 0
    invalid_offset_count = 0
    text_mismatch_count = 0
    missing_source_pmid_count = 0

    for result in results:
        if not result.entities:
            empty_paper_count += 1
        if source_texts is not None and result.pmid not in source_texts:
            missing_source_pmid_count += 1
        for entity in result.entities:
            entity_count += 1
            label = entity.label.value
            label_counts[label] += 1
            confidence_bucket_counts[_confidence_bucket(entity.confidence)] += 1
            normalized_counts[entity.normalized_text] += 1
            if entity.label is EntityType.UNKNOWN:
                unknown_entity_count += 1
                unknown_counts[entity.normalized_text] += 1
            if entity.confidence < low_confidence_threshold:
                low_confidence_count += 1
            if len(entity.text.strip()) <= 2:
                short_entity_count += 1

            issue = _offset_issue(result, entity, source_texts)
            if issue is None:
                continue
            offset_issues.append(issue)
            if issue.reason == "invalid span":
                invalid_offset_count += 1
            elif issue.reason == "text mismatch":
                text_mismatch_count += 1

    warnings = _quality_warnings(
        entity_count=entity_count,
        unknown_entity_count=unknown_entity_count,
        empty_paper_count=empty_paper_count,
        invalid_offset_count=invalid_offset_count,
        text_mismatch_count=text_mismatch_count,
        missing_source_pmid_count=missing_source_pmid_count,
        has_source_texts=source_texts is not None,
    )

    return EntityQualityReport(
        entity_jsonl_path=str(entity_path),
        pubmed_jsonl_path=str(pubmed_jsonl) if pubmed_jsonl is not None else None,
        paper_count=len(results),
        source_paper_count=len(source_texts) if source_texts is not None else None,
        entity_count=entity_count,
        empty_paper_count=empty_paper_count,
        unknown_entity_count=unknown_entity_count,
        unknown_entity_rate=_rate(unknown_entity_count, entity_count),
        average_entities_per_paper=_rate(entity_count, len(results)),
        low_confidence_count=low_confidence_count,
        short_entity_count=short_entity_count,
        invalid_offset_count=invalid_offset_count,
        text_mismatch_count=text_mismatch_count,
        missing_source_pmid_count=missing_source_pmid_count,
        label_counts=_count_items(label_counts, limit=top_limit),
        confidence_bucket_counts=_count_items(confidence_bucket_counts, limit=top_limit),
        top_normalized_entities=_count_items(normalized_counts, limit=top_limit),
        top_unknown_entities=_count_items(unknown_counts, limit=top_limit),
        offset_issues=offset_issues[:sample_limit],
        warnings=warnings,
    )


def format_entity_quality_markdown(report: EntityQualityReport) -> str:
    warning_lines = [f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]
    source_line = report.pubmed_jsonl_path or "not provided"
    lines = [
        "# GBM-AI Entity Extraction Quality Report",
        "",
        RESEARCH_WARNING,
        "",
        f"- Entity JSONL: `{report.entity_jsonl_path}`",
        f"- PubMed JSONL: `{source_line}`",
        f"- Papers: {report.paper_count}",
        f"- Entities: {report.entity_count}",
        f"- Empty papers: {report.empty_paper_count}",
        f"- Average entities per paper: {report.average_entities_per_paper:.2f}",
        f"- UNKNOWN entities: {report.unknown_entity_count} ({report.unknown_entity_rate:.1%})",
        f"- Low-confidence entities: {report.low_confidence_count}",
        f"- Short entities: {report.short_entity_count}",
        f"- Invalid offsets: {report.invalid_offset_count}",
        f"- Text mismatches: {report.text_mismatch_count}",
        f"- Missing source PMIDs: {report.missing_source_pmid_count}",
        "",
        "## Labels",
        *_format_counts(report.label_counts),
        "",
        "## Confidence Buckets",
        *_format_counts(report.confidence_bucket_counts),
        "",
        "## Top Normalized Entities",
        *_format_counts(report.top_normalized_entities),
        "",
        "## Top UNKNOWN Entities",
        *_format_counts(report.top_unknown_entities),
        "",
        "## Offset Issue Samples",
        *_format_offset_issues(report.offset_issues),
        "",
        "## Warnings",
        *warning_lines,
    ]
    return "\n".join(lines).rstrip() + "\n"


def save_entity_quality_json(report: EntityQualityReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    LOGGER.info("Saved entity quality JSON to %s", output_path)
    return output_path


def save_entity_quality_markdown(report: EntityQualityReport, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_entity_quality_markdown(report), encoding="utf-8")
    LOGGER.info("Saved entity quality Markdown to %s", output_path)
    return output_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize GBM-AI entity extraction quality.")
    parser.add_argument("entity_jsonl", type=Path)
    parser.add_argument("--pubmed-jsonl", type=Path, help="Optional source PubMed JSONL for offset checks.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.5)
    parser.add_argument("--top-limit", type=int, default=10)
    parser.add_argument("--sample-limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of Markdown.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    report = build_entity_quality_report(
        args.entity_jsonl,
        pubmed_jsonl=args.pubmed_jsonl,
        low_confidence_threshold=args.low_confidence_threshold,
        top_limit=args.top_limit,
        sample_limit=args.sample_limit,
    )
    if args.json_output:
        save_entity_quality_json(report, args.json_output)
    if args.markdown_output:
        save_entity_quality_markdown(report, args.markdown_output)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_entity_quality_markdown(report))
    return 0


def _load_source_texts(pubmed_jsonl: str | Path | None) -> dict[str, str] | None:
    if pubmed_jsonl is None:
        return None
    return {paper.pmid: paper_to_source_text(paper) for paper in load_pubmed_jsonl(pubmed_jsonl)}


def _offset_issue(
    result: EntityExtractionResult,
    entity: ExtractedEntity,
    source_texts: dict[str, str] | None,
) -> OffsetIssue | None:
    if source_texts is None:
        return None
    source_text = source_texts.get(result.pmid)
    if source_text is None:
        return None
    if entity.start < 0 or entity.end < entity.start or entity.end > len(source_text):
        return OffsetIssue(
            pmid=result.pmid,
            text=entity.text,
            start=entity.start,
            end=entity.end,
            reason="invalid span",
        )
    if source_text[entity.start : entity.end].strip() != entity.text:
        return OffsetIssue(
            pmid=result.pmid,
            text=entity.text,
            start=entity.start,
            end=entity.end,
            reason="text mismatch",
        )
    return None


def _quality_warnings(
    *,
    entity_count: int,
    unknown_entity_count: int,
    empty_paper_count: int,
    invalid_offset_count: int,
    text_mismatch_count: int,
    missing_source_pmid_count: int,
    has_source_texts: bool,
) -> list[str]:
    warnings: list[str] = []
    if entity_count == 0:
        warnings.append("no entities extracted")
    elif _rate(unknown_entity_count, entity_count) >= 0.25:
        warnings.append("UNKNOWN entity rate is at least 25%")
    if empty_paper_count:
        warnings.append(f"{empty_paper_count} paper(s) have no extracted entities")
    if not has_source_texts:
        warnings.append("PubMed source JSONL not provided; offset text validation skipped")
    if invalid_offset_count:
        warnings.append(f"{invalid_offset_count} entity offset(s) are outside source text")
    if text_mismatch_count:
        warnings.append(f"{text_mismatch_count} entity span(s) do not match source text")
    if missing_source_pmid_count:
        warnings.append(f"{missing_source_pmid_count} extracted PMID(s) are missing from source JSONL")
    return warnings


def _confidence_bucket(confidence: float) -> str:
    if confidence < 0.5:
        return "<0.50"
    if confidence < 0.75:
        return "0.50-0.74"
    if confidence < 0.9:
        return "0.75-0.89"
    return "0.90-1.00"


def _count_items(counter: Counter[str], *, limit: int) -> list[CountItem]:
    return [CountItem(key=key, count=count) for key, count in counter.most_common(limit)]


def _format_counts(items: list[CountItem]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item.key}: {item.count}" for item in items]


def _format_offset_issues(issues: list[OffsetIssue]) -> list[str]:
    if not issues:
        return ["- none"]
    return [
        f"- PMID {issue.pmid} `{issue.text}` [{issue.start}, {issue.end}]: {issue.reason}"
        for issue in issues
    ]


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


if __name__ == "__main__":
    raise SystemExit(main())
