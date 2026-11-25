"""Evaluation reports for GBM-BERT research training runs."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING


@dataclass(frozen=True)
class LabelMetrics:
    label: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass(frozen=True)
class EvaluationReport:
    task: str
    examples: int
    accuracy: float
    macro_f1: float
    labels: list[LabelMetrics]
    confusion_matrix: dict[str, dict[str, int]]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_predictions(
    *,
    task: str,
    true_labels: list[str],
    predicted_labels: list[str],
    label_set: list[str],
) -> EvaluationReport:
    """Compute simple classification metrics without optional sklearn dependency."""

    if len(true_labels) != len(predicted_labels):
        raise ValueError("true_labels and predicted_labels must have the same length")
    labels = sorted(set(label_set) | set(true_labels) | set(predicted_labels))
    confusion: dict[str, dict[str, int]] = {label: {pred: 0 for pred in labels} for label in labels}
    for true, predicted in zip(true_labels, predicted_labels, strict=False):
        confusion[true][predicted] += 1
    correct = sum(1 for true, predicted in zip(true_labels, predicted_labels, strict=False) if true == predicted)
    label_metrics: list[LabelMetrics] = []
    for label in labels:
        true_positive = confusion[label][label]
        false_positive = sum(confusion[other][label] for other in labels if other != label)
        false_negative = sum(confusion[label][other] for other in labels if other != label)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        support = sum(confusion[label].values())
        label_metrics.append(LabelMetrics(label=label, precision=precision, recall=recall, f1=f1, support=support))
    warnings: list[str] = []
    if len(true_labels) < 10:
        warnings.append("fewer than 10 evaluation examples")
    missing_labels = [label for label in label_set if Counter(true_labels)[label] == 0]
    if missing_labels:
        warnings.append(f"label(s) absent from evaluation set: {', '.join(missing_labels)}")
    return EvaluationReport(
        task=task,
        examples=len(true_labels),
        accuracy=correct / len(true_labels) if true_labels else 0.0,
        macro_f1=sum(item.f1 for item in label_metrics) / len(label_metrics) if label_metrics else 0.0,
        labels=label_metrics,
        confusion_matrix=confusion,
        warnings=warnings,
    )


def evaluate_bio_spans(
    *,
    task: str,
    true_spans_by_doc: list[list[tuple[int, int, str]]],
    predicted_spans_by_doc: list[list[tuple[int, int, str]]],
    entity_types: list[str],
) -> EvaluationReport:
    """Exact token-span match metrics for BIO NER (start, end, type)."""

    if len(true_spans_by_doc) != len(predicted_spans_by_doc):
        raise ValueError("true/predicted span docs must have the same length")
    types = sorted(set(entity_types) | {span[2] for doc in true_spans_by_doc for span in doc} | {span[2] for doc in predicted_spans_by_doc for span in doc})
    tp = Counter()
    fp = Counter()
    fn = Counter()
    matched_total = 0
    gold_total = 0
    pred_total = 0
    for true_spans, pred_spans in zip(true_spans_by_doc, predicted_spans_by_doc, strict=False):
        gold_total += len(true_spans)
        pred_total += len(pred_spans)
        remaining = Counter(pred_spans)
        for span in true_spans:
            if remaining[span] > 0:
                remaining[span] -= 1
                tp[span[2]] += 1
                matched_total += 1
            else:
                fn[span[2]] += 1
        for span, count in remaining.items():
            fp[span[2]] += count
    label_metrics: list[LabelMetrics] = []
    for label in types:
        precision = tp[label] / (tp[label] + fp[label]) if tp[label] + fp[label] else 0.0
        recall = tp[label] / (tp[label] + fn[label]) if tp[label] + fn[label] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        label_metrics.append(
            LabelMetrics(
                label=label,
                precision=precision,
                recall=recall,
                f1=f1,
                support=tp[label] + fn[label],
            )
        )
    confusion = {
        label: {other: (tp[label] if other == label else 0) for other in types}
        for label in types
    }
    for label in types:
        # Represent FN as gold->MISS and FP as MISS->pred via off-diagonal buckets when possible.
        if "__MISS__" not in confusion:
            for row in confusion.values():
                row["__MISS__"] = 0
            confusion["__MISS__"] = {other: 0 for other in [*types, "__MISS__"]}
        confusion[label]["__MISS__"] = fn[label]
        confusion["__MISS__"][label] = fp[label]
    warnings = ["BIO exact-span metrics (token indices); research scaffold only"]
    if gold_total < 10:
        warnings.append("fewer than 10 gold entity spans in evaluation set")
    return EvaluationReport(
        task=task,
        examples=gold_total,
        accuracy=matched_total / gold_total if gold_total else 0.0,
        macro_f1=sum(item.f1 for item in label_metrics) / len(label_metrics) if label_metrics else 0.0,
        labels=label_metrics,
        confusion_matrix=confusion,
        warnings=warnings,
    )


def save_evaluation_report_json(report: EvaluationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_evaluation_report_markdown(report: EvaluationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_evaluation_report_markdown(report), encoding="utf-8")
    return output


def format_evaluation_report_markdown(report: EvaluationReport) -> str:
    warnings = [f"- {warning}" for warning in report.warnings] if report.warnings else ["- none"]
    lines = [
        "# GBM-BERT Evaluation Report",
        "",
        report.warning,
        "",
        f"- Task: {report.task}",
        f"- Examples: {report.examples}",
        f"- Accuracy: {report.accuracy:.3f}",
        f"- Macro F1: {report.macro_f1:.3f}",
        "",
        "## Labels",
    ]
    for item in report.labels:
        lines.append(
            f"- {item.label}: precision={item.precision:.3f}, recall={item.recall:.3f}, "
            f"f1={item.f1:.3f}, support={item.support}"
        )
    lines.extend(["", "## Warnings", *warnings])
    return "\n".join(lines).rstrip() + "\n"
