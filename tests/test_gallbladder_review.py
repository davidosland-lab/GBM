import json
from pathlib import Path

from gbmbert.extraction.entities import normalize_label

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "configs" / "extraction" / "gallbladder_review_schema.json"
LEXICON = ROOT / "configs" / "extraction" / "lexicon_gallbladder_v1.json"
RUNBOOK = ROOT / "docs" / "GALLBLADDER_REVIEW.md"


def test_gallbladder_review_schema_blocks_clinical_claims() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["research_use_only"] is True
    assert schema["clinical_validity_claimed"] is False
    assert "diagnosis" in schema["excluded_uses"]
    assert "patient-specific treatment advice" in schema["excluded_uses"]
    assert "post-operative care instruction" in schema["excluded_uses"]
    assert "dietary prescription after cholecystectomy" in schema["excluded_uses"]
    assert schema["promotion_gate"]["requires_patient_specific_claim_audit"] is True


def test_gallbladder_review_schema_projects_to_supported_labels() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    for project_label in schema["project_label_projection"].values():
        normalize_label(project_label)

    assert schema["project_label_projection"]["PROCEDURE"] == "TREATMENT"
    assert schema["project_label_projection"]["COMPLICATION"] == "DISEASE"
    assert schema["project_label_projection"]["RECOVERY_OUTCOME"] == "OUTCOME"
    assert "RECOVERY_OUTCOME" in schema["domain_entities"]


def test_gallbladder_review_schema_keeps_comparator_evidence_field() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert "comparator" in schema["evidence_fields"]
    assert "excluded_patient_advice" in schema["review_status_values"]


def test_gallbladder_lexicon_uses_supported_project_labels() -> None:
    lexicon = json.loads(LEXICON.read_text(encoding="utf-8"))

    assert lexicon["name"] == "lexicon_gallbladder_v1"
    terms = {entry["term"] for entry in lexicon["entries"]}
    assert {"gallstones", "cholecystectomy", "laparoscopic cholecystectomy"}.issubset(terms)
    assert "post-cholecystectomy syndrome" in terms
    for entry in lexicon["entries"]:
        assert normalize_label(entry["label"]).value != "UNKNOWN"


def test_gallbladder_lexicon_covers_the_four_review_areas() -> None:
    lexicon = json.loads(LEXICON.read_text(encoding="utf-8"))
    labels = {entry["label"] for entry in lexicon["entries"]}

    assert {"DISEASE", "TREATMENT", "DRUG", "OUTCOME"}.issubset(labels)


def test_gallbladder_runbook_links_operational_artifacts() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "gbmbert-search-pubmed --query-pack pubmed_gallbladder_v1" in text
    assert "configs/extraction/lexicon_gallbladder_v1.json" in text
    assert "Not medical advice" in text
    assert "visual dashboard" in text.lower()
