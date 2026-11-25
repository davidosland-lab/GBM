"""Tests for MedBERT / biomedical-NLP inspired dashboard visual helpers."""

from __future__ import annotations

from gbmbert.dashboard.visuals import (
    ENTITY_TYPE_HEX,
    collect_span_labels,
    entity_legend_html,
    entity_type_color,
    evidence_chips_html,
    highlight_spans_html,
    normalize_entity_type,
    paper_card_header_html,
    pmid_badge_html,
    relation_triple_html,
    score_bar_html,
    score_level,
)


def test_entity_type_normalization_and_colors() -> None:
    assert normalize_entity_type("EntityType.GENE") == "GENE"
    assert normalize_entity_type("chemical") == "DRUG"
    assert normalize_entity_type(None) == "UNKNOWN"
    assert entity_type_color("GENE", as_hex=True) == ENTITY_TYPE_HEX["GENE"]
    assert entity_type_color("not-a-type", as_hex=True) == ENTITY_TYPE_HEX["UNKNOWN"]


def test_highlight_spans_html_colors_and_escapes() -> None:
    text = "MGMT predicts temozolomide in <glioblastoma>."
    gene = "MGMT"
    drug = "temozolomide"
    disease = "<glioblastoma>"
    spans = [
        {"start": text.index(gene), "end": text.index(gene) + len(gene), "label": "GENE"},
        {"start": text.index(drug), "end": text.index(drug) + len(drug), "label": "DRUG"},
        {
            "start": text.index(disease),
            "end": text.index(disease) + len(disease),
            "label": "DISEASE",
        },
    ]
    html = highlight_spans_html(text, spans)
    assert 'class="gbm-ent"' in html
    assert ENTITY_TYPE_HEX["GENE"] in html
    assert ENTITY_TYPE_HEX["DRUG"] in html
    assert "MGMT" in html
    assert "&lt;glioblastoma&gt;" in html
    assert "GENE" in html
    legend = entity_legend_html(collect_span_labels(spans))
    assert "GENE" in legend and "DRUG" in legend
    assert ENTITY_TYPE_HEX["GENE"] in legend


def test_highlight_skips_overlaps_and_empty() -> None:
    text = "ABCDEF"
    spans = [
        {"start": 0, "end": 4, "label": "GENE"},
        {"start": 2, "end": 5, "label": "DRUG"},  # overlap — skipped
    ]
    html = highlight_spans_html(text, spans)
    assert html.count('class="gbm-ent"') == 1
    empty = highlight_spans_html("", [])
    assert "(empty)" in empty or 'gbm-highlight-panel">' in empty


def test_score_bar_and_chips() -> None:
    assert score_level(0.9) == "high"
    assert score_level(0.5) == "mid"
    assert score_level(0.1) == "low"
    bar = score_bar_html(0.82, label="conf")
    assert "gbm-score-bar" in bar
    assert "0.82" in bar
    assert score_bar_html(None) == ""
    chips = evidence_chips_html(pmid="29097493", entity_type="GENE", evidence_tier=3, score=0.7)
    assert "PMID 29097493" in chips
    assert "GENE" in chips
    assert "tier 3" in chips
    assert pmid_badge_html("123") == '<span class="gbm-chip gbm-chip-pmid">PMID 123</span>'


def test_relation_triple_and_paper_card_header() -> None:
    triple = relation_triple_html("MGMT", "PREDICTS", "temozolomide response", meta="tier 3", score=0.9)
    assert "gbm-triple" in triple
    assert "MGMT" in triple
    assert "PREDICTS" in triple
    assert "temozolomide response" in triple
    header = paper_card_header_html(
        title="Demo paper",
        citation="Author A · 2018 · Journal",
        pmid="29097493",
        evidence_tier=4,
        score=0.55,
    )
    assert "Demo paper" in header
    assert "PMID 29097493" in header
    assert "tier 4" in header
