import json
from pathlib import Path

from gbmbert.annotation.schema import EvidenceLevel, Paper
from gbmbert.extraction.evidence import (
    RuleBasedEvidenceClassifier,
    classify_paper_evidence,
    classify_pubmed_jsonl,
)


def test_rule_based_evidence_classifier_detects_randomized_evidence() -> None:
    classifier = RuleBasedEvidenceClassifier()

    result = classifier.classify("A randomized phase III trial in glioblastoma.")

    assert result.evidence_level is EvidenceLevel.RANDOMIZED_EVIDENCE
    assert "randomized" in [cue.casefold() for cue in result.matched_cues]
    assert result.method == "rule_based_placeholder_v1"


def test_rule_based_evidence_classifier_detects_preclinical_tiers() -> None:
    classifier = RuleBasedEvidenceClassifier()

    assert classifier.classify("Murine xenograft model.").evidence_level is EvidenceLevel.ANIMAL
    assert classifier.classify("In vitro glioblastoma cell line assay.").evidence_level is EvidenceLevel.IN_VITRO


def test_classify_paper_evidence_preserves_method_and_cues() -> None:
    paper = Paper(
        pmid="12345678",
        title="Phase II glioblastoma study",
        abstract="Clinical trial of a research intervention.",
    )

    claim = classify_paper_evidence(paper)

    assert claim.source_pmid == "12345678"
    assert claim.evidence_level is EvidenceLevel.PHASE_I_II
    assert claim.classification_method == "rule_based_placeholder_v1"
    assert claim.evidence_cues


def test_classify_pubmed_jsonl_writes_evidence_claims(tmp_path: Path) -> None:
    input_path = tmp_path / "pubmed.jsonl"
    output_path = tmp_path / "evidence.jsonl"
    input_path.write_text(
        json.dumps(
            {
                "pmid": "12345678",
                "title": "Retrospective glioblastoma cohort",
                "abstract": "Patient records were reviewed.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    classify_pubmed_jsonl(input_path, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["evidence_level"] == 3
    assert payload["classification_method"] == "rule_based_placeholder_v1"
