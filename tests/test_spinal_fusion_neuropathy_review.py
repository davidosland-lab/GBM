import json
from pathlib import Path

from gbmbert.extraction.entities import normalize_label

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "configs" / "extraction" / "spinal_fusion_neuropathy_review_schema.json"
LEXICON = ROOT / "configs" / "extraction" / "lexicon_spinal_fusion_neuropathy_v1.json"
RUNBOOK = ROOT / "docs" / "SPINAL_FUSION_NEUROPATHY_REVIEW.md"


def test_spinal_fusion_review_schema_blocks_clinical_claims() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["research_use_only"] is True
    assert schema["clinical_validity_claimed"] is False
    assert "diagnosis" in schema["excluded_uses"]
    assert "patient-specific treatment advice" in schema["excluded_uses"]
    assert schema["promotion_gate"]["requires_patient_specific_claim_audit"] is True


def test_spinal_fusion_review_schema_projects_to_supported_labels() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    for project_label in schema["project_label_projection"].values():
        normalize_label(project_label)

    assert schema["project_label_projection"]["SURGERY_TYPE"] == "TREATMENT"
    assert "NEUROPATHIC_SYMPTOM" in schema["domain_entities"]


def test_spinal_fusion_lexicon_uses_supported_project_labels() -> None:
    lexicon = json.loads(LEXICON.read_text(encoding="utf-8"))

    assert lexicon["name"] == "lexicon_spinal_fusion_neuropathy_v1"
    assert any(entry["term"] == "spinal fusion" for entry in lexicon["entries"])
    assert any(entry["term"] == "neuropathic pain" for entry in lexicon["entries"])
    for entry in lexicon["entries"]:
        assert normalize_label(entry["label"]).value != "UNKNOWN"


def test_spinal_fusion_runbook_links_operational_artifacts() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "gbmbert-search-pubmed --query-pack pubmed_spinal_fusion_neuropathy_v1" in text
    assert "Not medical advice" in text
    assert "visual dashboard" in text.lower()
