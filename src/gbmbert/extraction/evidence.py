"""Evidence classification interface and conservative rule-based placeholder."""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from gbmbert.annotation.schema import EvidenceClaim, EvidenceLevel, Paper
from gbmbert.extraction.io import load_pubmed_jsonl

LOGGER = logging.getLogger(__name__)


class EvidenceClassification(BaseModel):
    """Evidence-tier prediction with transparent cue provenance."""

    model_config = ConfigDict(str_strip_whitespace=True)

    evidence_level: EvidenceLevel = EvidenceLevel.HYPOTHESIS
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    matched_cues: list[str] = Field(default_factory=list)
    method: str = "rule_based_placeholder_v1"


class EvidenceClassifier(Protocol):
    """Interface for future GBM-BERT evidence classifiers."""

    def classify(self, text: str) -> EvidenceClassification: ...


class RuleBasedEvidenceClassifier:
    """Conservative placeholder until model-based evidence classification exists."""

    RULES: tuple[tuple[EvidenceLevel, float, tuple[re.Pattern[str], ...]], ...] = (
        (
            EvidenceLevel.RANDOMIZED_EVIDENCE,
            0.82,
            (
                re.compile(r"\brandomi[sz]ed\b", re.IGNORECASE),
                re.compile(r"\bphase\s*(iii|3)\b", re.IGNORECASE),
            ),
        ),
        (
            EvidenceLevel.PHASE_I_II,
            0.76,
            (
                re.compile(r"\bphase\s*(i/ii|1/2|ii|2|i|1)\b", re.IGNORECASE),
                re.compile(r"\bclinical trial\b", re.IGNORECASE),
            ),
        ),
        (
            EvidenceLevel.RETROSPECTIVE_HUMAN,
            0.68,
            (
                re.compile(r"\bretrospective\b", re.IGNORECASE),
                re.compile(r"\bcohort\b", re.IGNORECASE),
                re.compile(r"\bpatient[s]?\b", re.IGNORECASE),
            ),
        ),
        (
            EvidenceLevel.ANIMAL,
            0.62,
            (
                re.compile(r"\bmouse\b", re.IGNORECASE),
                re.compile(r"\bmurine\b", re.IGNORECASE),
                re.compile(r"\bxenograft\b", re.IGNORECASE),
            ),
        ),
        (
            EvidenceLevel.IN_VITRO,
            0.58,
            (
                re.compile(r"\bin vitro\b", re.IGNORECASE),
                re.compile(r"\bcell line[s]?\b", re.IGNORECASE),
                re.compile(r"\borganoid[s]?\b", re.IGNORECASE),
            ),
        ),
    )

    def classify(self, text: str) -> EvidenceClassification:
        if not text.strip():
            return EvidenceClassification()
        for level, confidence, patterns in self.RULES:
            cues = [match.group(0) for pattern in patterns for match in pattern.finditer(text)]
            if cues:
                return EvidenceClassification(
                    evidence_level=level,
                    confidence=confidence,
                    matched_cues=sorted(set(cues), key=str.casefold),
                )
        return EvidenceClassification(matched_cues=[])


def classify_paper_evidence(
    paper: Paper,
    classifier: EvidenceClassifier | None = None,
) -> EvidenceClaim:
    """Create one evidence claim for a PubMed paper without clinical interpretation."""

    active_classifier = classifier or RuleBasedEvidenceClassifier()
    text = " ".join(part for part in [paper.title, paper.abstract] if part)
    classification = active_classifier.classify(text)
    return EvidenceClaim(
        claim=paper.title or f"PubMed record {paper.pmid}",
        source_pmid=paper.pmid,
        evidence_level=classification.evidence_level,
        confidence=classification.confidence,
        classification_method=classification.method,
        evidence_cues=classification.matched_cues,
    )


def classify_pubmed_records(
    papers: Iterable[Paper],
    classifier: EvidenceClassifier | None = None,
) -> list[EvidenceClaim]:
    """Classify evidence level for PubMed records using a transparent placeholder."""

    active_classifier = classifier or RuleBasedEvidenceClassifier()
    return [classify_paper_evidence(paper, active_classifier) for paper in papers]


def save_evidence_claims_jsonl(claims: Iterable[EvidenceClaim], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for claim in claims:
            handle.write(claim.model_dump_json())
            handle.write("\n")
    LOGGER.info("Saved evidence classification JSONL to %s", output_path)
    return output_path


def load_evidence_claims_jsonl(path: str | Path) -> list[EvidenceClaim]:
    """Load evidence-claim JSONL output."""

    input_path = Path(path)
    claims: list[EvidenceClaim] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                claims.append(EvidenceClaim.model_validate(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
    return claims


def classify_pubmed_jsonl(input_path: str | Path, output_path: str | Path) -> Path:
    papers = list(load_pubmed_jsonl(input_path))
    return save_evidence_claims_jsonl(classify_pubmed_records(papers), output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify PubMed records into evidence tiers using a transparent placeholder."
    )
    parser.add_argument("input", type=Path, help="Input PubMed JSONL path.")
    parser.add_argument("output", type=Path, help="Output evidence-claim JSONL path.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    classify_pubmed_jsonl(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
