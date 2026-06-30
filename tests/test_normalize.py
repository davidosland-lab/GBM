from gbmbert.extraction.normalize import canonical_key, normalize_many, normalize_text


def test_normalize_text_applies_gbm_aliases_case_insensitively() -> None:
    assert normalize_text("GBM") == "glioblastoma"
    assert normalize_text("glioblastoma multiforme") == "glioblastoma"
    assert normalize_text("  TMZ ") == "temozolomide"
    assert normalize_text("egfr") == "EGFR"
    assert normalize_text("PDL1") == "PD-L1"


def test_normalize_text_preserves_unknown_terms() -> None:
    assert normalize_text("neuron-glioma synapses") == "neuron-glioma synapses"


def test_normalize_many_normalizes_multiple_mentions() -> None:
    assert normalize_many(["gbm", "mgmt", "idh1"]) == ["glioblastoma", "MGMT", "IDH1"]


def test_canonical_key_normalizes_case_and_whitespace() -> None:
    assert canonical_key("  Glioblastoma   Multiforme ") == "glioblastoma multiforme"
