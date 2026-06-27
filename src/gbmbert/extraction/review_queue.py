"""Human-review queue export for uncertain evidence and relation extraction outputs."""

from __future__ import annotations

import argparse
import csv
import json
import logging
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gbmbert.annotation.schema import EvidenceClaim, EvidenceLevel
from gbmbert.extraction.evidence import load_evidence_claims_jsonl
from gbmbert.knowledge_graph.schema import EvidenceTier, KnowledgeGraphRecord, RelationType

LOGGER = logging.getLogger(__name__)


class ReviewQueueItem(BaseModel):
    """One extraction item that should be reviewed before downstream use."""

    model_config = ConfigDict(str_strip_whitespace=True)

    item_id: str
    item_type: Literal["evidence_claim", "graph_relation"]
    source_pmid: str
    evidence_tier: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    text: str = ""
    relation_type: str = ""
    head: str = ""
    tail: str = ""
    reasons: list[str] = Field(default_factory=list)
    source_file: str = ""
    review_status: Literal["pending", "accepted", "corrected", "rejected"] = "pending"
    reviewer: str = ""
    review_notes: str = ""
    corrected_relation_type: str = ""
    corrected_evidence_tier: int | None = None

    @model_validator(mode="after")
    def curation_fields_must_be_consistent(self) -> "ReviewQueueItem":
        if self.corrected_relation_type:
            try:
                RelationType(self.corrected_relation_type)
            except ValueError as exc:
                raise ValueError("corrected_relation_type must be a known graph relation type") from exc
        if self.corrected_evidence_tier is not None:
            try:
                EvidenceTier(self.corrected_evidence_tier)
            except ValueError as exc:
                raise ValueError("corrected_evidence_tier must be a known evidence tier") from exc
        if self.review_status == "corrected":
            if not self.review_notes.strip():
                raise ValueError("corrected items require review_notes")
            if not self.corrected_relation_type and self.corrected_evidence_tier is None:
                raise ValueError("corrected items require a corrected relation type or evidence tier")
        if self.review_status == "rejected" and not self.review_notes.strip():
            raise ValueError("rejected items require review_notes")
        if self.review_status == "accepted" and (self.corrected_relation_type or self.corrected_evidence_tier is not None):
            raise ValueError("accepted items must not include correction fields")
        return self


@dataclass(frozen=True)
class ReviewCount:
    key: str
    count: int


@dataclass(frozen=True)
class ReviewQueueSummary:
    source_path: str
    item_count: int
    item_type_counts: list[ReviewCount]
    reason_counts: list[ReviewCount]
    evidence_tier_counts: list[ReviewCount]
    relation_type_counts: list[ReviewCount]
    top_pmids: list[ReviewCount]
    sample_items: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewedQueueSummary:
    source_path: str
    item_count: int
    status_counts: list[ReviewCount]
    item_type_counts: list[ReviewCount]
    corrected_relation_type_counts: list[ReviewCount]
    corrected_evidence_tier_counts: list[ReviewCount]
    pending_count: int
    warning_count: int
    warnings: list[str]
    sample_items: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_review_queue(
    *,
    evidence_jsonl: str | Path | None = None,
    graph_jsonl: str | Path | None = None,
    max_confidence: float = 0.65,
    include_hypothesis: bool = True,
) -> list[ReviewQueueItem]:
    """Collect low-confidence claims and uncertain graph relations for review."""

    if evidence_jsonl is None and graph_jsonl is None:
        raise ValueError("evidence_jsonl or graph_jsonl is required")
    if max_confidence < 0.0 or max_confidence > 1.0:
        raise ValueError("max_confidence must be between 0.0 and 1.0")

    items: list[ReviewQueueItem] = []
    if evidence_jsonl is not None:
        items.extend(
            evidence_claims_to_review_items(
                load_evidence_claims_jsonl(evidence_jsonl),
                source_file=str(evidence_jsonl),
                max_confidence=max_confidence,
                include_hypothesis=include_hypothesis,
            )
        )
    if graph_jsonl is not None:
        items.extend(
            graph_relations_to_review_items(
                load_graph_records_jsonl(graph_jsonl),
                source_file=str(graph_jsonl),
                max_confidence=max_confidence,
                include_hypothesis=include_hypothesis,
            )
        )
    return items


def evidence_claims_to_review_items(
    claims: Iterable[EvidenceClaim],
    *,
    source_file: str,
    max_confidence: float,
    include_hypothesis: bool,
) -> list[ReviewQueueItem]:
    items = []
    for claim in claims:
        reasons = review_reasons(
            confidence=claim.confidence,
            tier=int(claim.evidence_level.value),
            max_confidence=max_confidence,
            include_hypothesis=include_hypothesis,
        )
        if not reasons:
            continue
        items.append(
            ReviewQueueItem(
                item_id=f"evidence:{claim.source_pmid}",
                item_type="evidence_claim",
                source_pmid=claim.source_pmid,
                evidence_tier=int(claim.evidence_level.value),
                confidence=claim.confidence,
                text=claim.claim,
                reasons=reasons,
                source_file=source_file,
            )
        )
    return items


def graph_relations_to_review_items(
    records: Iterable[KnowledgeGraphRecord],
    *,
    source_file: str,
    max_confidence: float,
    include_hypothesis: bool,
) -> list[ReviewQueueItem]:
    items = []
    for record in records:
        for index, relation in enumerate(record.relations, start=1):
            reasons = review_reasons(
                confidence=relation.confidence,
                tier=int(relation.evidence_tier),
                max_confidence=max_confidence,
                include_hypothesis=include_hypothesis,
            )
            if not reasons:
                continue
            sentence = str(relation.properties.get("sentence", ""))
            items.append(
                ReviewQueueItem(
                    item_id=f"relation:{record.pmid}:{index}",
                    item_type="graph_relation",
                    source_pmid=record.pmid,
                    evidence_tier=int(relation.evidence_tier),
                    confidence=relation.confidence,
                    text=sentence,
                    relation_type=relation.relation.value,
                    head=f"{relation.head.label.value}:{relation.head.key_value}",
                    tail=f"{relation.tail.label.value}:{relation.tail.key_value}",
                    reasons=reasons,
                    source_file=source_file,
                )
            )
    return items


def review_reasons(
    *,
    confidence: float,
    tier: int,
    max_confidence: float,
    include_hypothesis: bool,
) -> list[str]:
    reasons = []
    if confidence <= max_confidence:
        reasons.append(f"confidence <= {max_confidence}")
    if include_hypothesis and tier == int(EvidenceLevel.HYPOTHESIS.value):
        reasons.append("hypothesis-tier evidence")
    return reasons


def load_graph_records_jsonl(path: str | Path) -> list[KnowledgeGraphRecord]:
    input_path = Path(path)
    records: list[KnowledgeGraphRecord] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(KnowledgeGraphRecord.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return records


def save_review_queue_jsonl(items: Iterable[ReviewQueueItem], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(item.model_dump_json())
            handle.write("\n")
    LOGGER.info("Saved review queue JSONL to %s", output_path)
    return output_path


def save_review_queue_csv(items: Iterable[ReviewQueueItem], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [item.model_dump() for item in items]
    fieldnames = list(ReviewQueueItem.model_fields)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row["reasons"] = "; ".join(row["reasons"])
            writer.writerow(row)
    LOGGER.info("Saved review queue CSV to %s", output_path)
    return output_path


def load_review_queue_jsonl(path: str | Path) -> list[ReviewQueueItem]:
    input_path = Path(path)
    items: list[ReviewQueueItem] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                items.append(ReviewQueueItem.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return items


def initialize_reviewed_queue(
    input_jsonl: str | Path,
    output_jsonl: str | Path,
    *,
    reviewer: str = "",
    overwrite: bool = False,
    csv_output: str | Path | None = None,
) -> list[ReviewQueueItem]:
    """Create a separate reviewed queue scaffold without modifying the raw queue."""

    output_path = Path(output_jsonl)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} already exists; pass overwrite=True to replace it")
    items = [
        item.model_copy(update={"review_status": "pending", "reviewer": reviewer})
        for item in load_review_queue_jsonl(input_jsonl)
    ]
    save_review_queue_jsonl(items, output_path)
    if csv_output:
        save_review_queue_csv(items, csv_output)
    return items


def summarize_review_queue(
    path: str | Path,
    *,
    sample_limit: int = 5,
) -> ReviewQueueSummary:
    """Summarize a review queue JSONL file for curation planning."""

    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")
    items = load_review_queue_jsonl(path)
    item_type_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    evidence_tier_counts: Counter[str] = Counter()
    relation_type_counts: Counter[str] = Counter()
    pmid_counts: Counter[str] = Counter()
    for item in items:
        item_type_counts[item.item_type] += 1
        evidence_tier_counts[str(item.evidence_tier)] += 1
        pmid_counts[item.source_pmid] += 1
        if item.relation_type:
            relation_type_counts[item.relation_type] += 1
        for reason in item.reasons:
            reason_counts[reason] += 1

    return ReviewQueueSummary(
        source_path=str(path),
        item_count=len(items),
        item_type_counts=_review_counts(item_type_counts),
        reason_counts=_review_counts(reason_counts),
        evidence_tier_counts=_review_counts(evidence_tier_counts),
        relation_type_counts=_review_counts(relation_type_counts),
        top_pmids=_review_counts(pmid_counts),
        sample_items=[item.model_dump() for item in items[:sample_limit]],
    )


def summarize_reviewed_queue(
    path: str | Path,
    *,
    sample_limit: int = 5,
) -> ReviewedQueueSummary:
    """Summarize manual curation status for a reviewed queue scaffold."""

    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")
    items = load_review_queue_jsonl(path)
    status_counts: Counter[str] = Counter()
    item_type_counts: Counter[str] = Counter()
    corrected_relation_type_counts: Counter[str] = Counter()
    corrected_evidence_tier_counts: Counter[str] = Counter()
    for item in items:
        status_counts[item.review_status] += 1
        item_type_counts[item.item_type] += 1
        if item.corrected_relation_type:
            corrected_relation_type_counts[item.corrected_relation_type] += 1
        if item.corrected_evidence_tier is not None:
            corrected_evidence_tier_counts[str(item.corrected_evidence_tier)] += 1
    pending_count = status_counts.get("pending", 0)
    warnings = []
    if pending_count:
        warnings.append(f"{pending_count} item(s) still pending review")
    return ReviewedQueueSummary(
        source_path=str(path),
        item_count=len(items),
        status_counts=_review_counts(status_counts),
        item_type_counts=_review_counts(item_type_counts),
        corrected_relation_type_counts=_review_counts(corrected_relation_type_counts),
        corrected_evidence_tier_counts=_review_counts(corrected_evidence_tier_counts),
        pending_count=pending_count,
        warning_count=len(warnings),
        warnings=warnings,
        sample_items=[item.model_dump() for item in items[:sample_limit]],
    )


def save_review_queue_summary_json(summary: ReviewQueueSummary, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    LOGGER.info("Saved review queue summary JSON to %s", output_path)
    return output_path


def save_review_queue_summary_markdown(summary: ReviewQueueSummary, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_review_queue_summary_markdown(summary), encoding="utf-8")
    LOGGER.info("Saved review queue summary Markdown to %s", output_path)
    return output_path


def save_reviewed_queue_summary_json(summary: ReviewedQueueSummary, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    LOGGER.info("Saved reviewed queue summary JSON to %s", output_path)
    return output_path


def save_reviewed_queue_summary_markdown(summary: ReviewedQueueSummary, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_reviewed_queue_summary_markdown(summary), encoding="utf-8")
    LOGGER.info("Saved reviewed queue summary Markdown to %s", output_path)
    return output_path


def format_review_queue_summary_markdown(summary: ReviewQueueSummary) -> str:
    lines = [
        "# GBM-AI Review Queue Summary",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Source: `{summary.source_path}`",
        f"- Items: {summary.item_count}",
        "",
        "## Item Types",
        *_format_review_counts(summary.item_type_counts),
        "",
        "## Reasons",
        *_format_review_counts(summary.reason_counts),
        "",
        "## Evidence Tiers",
        *_format_review_counts(summary.evidence_tier_counts, prefix="tier "),
        "",
        "## Relation Types",
        *_format_review_counts(summary.relation_type_counts),
        "",
        "## Top PMIDs",
        *_format_review_counts(summary.top_pmids),
        "",
        "## Sample Items",
        *_format_sample_items(summary.sample_items),
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_reviewed_queue_summary_markdown(summary: ReviewedQueueSummary) -> str:
    warning_lines = [f"- {warning}" for warning in summary.warnings] if summary.warnings else ["- none"]
    lines = [
        "# GBM-AI Reviewed Queue Summary",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Source: `{summary.source_path}`",
        f"- Items: {summary.item_count}",
        f"- Pending: {summary.pending_count}",
        f"- Warnings: {summary.warning_count}",
        "",
        "## Review Status",
        *_format_review_counts(summary.status_counts),
        "",
        "## Item Types",
        *_format_review_counts(summary.item_type_counts),
        "",
        "## Corrected Relation Types",
        *_format_review_counts(summary.corrected_relation_type_counts),
        "",
        "## Corrected Evidence Tiers",
        *_format_review_counts(summary.corrected_evidence_tier_counts, prefix="tier "),
        "",
        "## Warnings",
        *warning_lines,
        "",
        "## Sample Items",
        *_format_sample_items(summary.sample_items),
    ]
    return "\n".join(lines).rstrip() + "\n"


def export_review_queue(
    *,
    output_jsonl: str | Path,
    evidence_jsonl: str | Path | None = None,
    graph_jsonl: str | Path | None = None,
    csv_output: str | Path | None = None,
    max_confidence: float = 0.65,
    include_hypothesis: bool = True,
) -> list[ReviewQueueItem]:
    items = build_review_queue(
        evidence_jsonl=evidence_jsonl,
        graph_jsonl=graph_jsonl,
        max_confidence=max_confidence,
        include_hypothesis=include_hypothesis,
    )
    save_review_queue_jsonl(items, output_jsonl)
    if csv_output:
        save_review_queue_csv(items, csv_output)
    return items


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export low-confidence evidence and relation extraction items for review."
    )
    parser.add_argument("--evidence-jsonl", type=Path)
    parser.add_argument("--graph-jsonl", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Output review queue JSONL path.")
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--max-confidence", type=float, default=0.65)
    parser.add_argument(
        "--exclude-hypothesis",
        action="store_true",
        help="Do not automatically queue tier-0 hypothesis items.",
    )
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_summary_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a GBM-AI review queue JSONL file.")
    parser.add_argument("review_queue_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--sample-limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of Markdown.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_reviewed_summary_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a GBM-AI reviewed queue JSONL file.")
    parser.add_argument("reviewed_queue_jsonl", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--sample-limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of Markdown.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def build_initialize_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a separate reviewed queue scaffold.")
    parser.add_argument("input_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    if args.evidence_jsonl is None and args.graph_jsonl is None:
        parser.error("--evidence-jsonl or --graph-jsonl is required")
    items = export_review_queue(
        evidence_jsonl=args.evidence_jsonl,
        graph_jsonl=args.graph_jsonl,
        output_jsonl=args.output,
        csv_output=args.csv_output,
        max_confidence=args.max_confidence,
        include_hypothesis=not args.exclude_hypothesis,
    )
    LOGGER.info("Queued %d item(s) for review", len(items))
    return 0


def summary_main(argv: list[str] | None = None) -> int:
    parser = build_summary_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    summary = summarize_review_queue(args.review_queue_jsonl, sample_limit=args.sample_limit)
    if args.json_output:
        save_review_queue_summary_json(summary, args.json_output)
    if args.markdown_output:
        save_review_queue_summary_markdown(summary, args.markdown_output)
    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_review_queue_summary_markdown(summary))
    return 0


def reviewed_summary_main(argv: list[str] | None = None) -> int:
    parser = build_reviewed_summary_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    summary = summarize_reviewed_queue(args.reviewed_queue_jsonl, sample_limit=args.sample_limit)
    if args.json_output:
        save_reviewed_queue_summary_json(summary, args.json_output)
    if args.markdown_output:
        save_reviewed_queue_summary_markdown(summary, args.markdown_output)
    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_reviewed_queue_summary_markdown(summary))
    return 0


def initialize_main(argv: list[str] | None = None) -> int:
    parser = build_initialize_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        items = initialize_reviewed_queue(
            args.input_jsonl,
            args.output_jsonl,
            reviewer=args.reviewer,
            overwrite=args.overwrite,
            csv_output=args.csv_output,
        )
    except FileExistsError as exc:
        parser.error(str(exc))
    LOGGER.info("Initialized %d reviewed queue item(s)", len(items))
    return 0


def _review_counts(counter: Counter[str]) -> list[ReviewCount]:
    return [ReviewCount(key=key, count=count) for key, count in counter.most_common()]


def _format_review_counts(items: list[ReviewCount], prefix: str = "") -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {prefix}{item.key}: {item.count}" for item in items]


def _format_sample_items(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["- none"]
    return [
        (
            f"- `{item.get('item_id')}` PMID {item.get('source_pmid')}: "
            f"{item.get('item_type')} confidence={item.get('confidence')}"
        )
        for item in items
    ]


if __name__ == "__main__":
    raise SystemExit(main())
