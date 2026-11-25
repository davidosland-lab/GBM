"""MedBERT / biomedical-NLP inspired visual helpers for the research dashboard.

Research-use only. Patterns are adapted from PubTator Central (type-colored
inline spans + legend), Gradio HighlightedText / scispaCy displaCy (span
highlighting), and pubmedKB (relation evidence rows + KPI chrome). Palette is
clinical-slate with teal accents — not a generic purple AI theme.

Not clinical decision support. Colors do not imply validated entity types.
"""

from __future__ import annotations

import html
import re
from typing import Any, Iterable, Mapping, Sequence

# Clinical-slate / teal tokens (PubTator-like distinct type pastels on slate UI).
# Documented choice: slate surfaces + teal chrome (pubmedKB / research tooling),
# type colors echo PubTator Central concept highlighting (gene=green, disease=
# warm, chemical/drug=cyan-blue) rather than Gradio default purple.
CSS_VARIABLES = """
:root {
  --gbm-bg: #f4f6f8;
  --gbm-surface: #ffffff;
  --gbm-border: #d7dde5;
  --gbm-text: #1f2933;
  --gbm-muted: #4a5563;
  --gbm-accent: #0f766e;
  --gbm-accent-soft: #ccfbf1;
  --gbm-pmid: #134e4a;
  --gbm-ent-gene: #b7e4c7;
  --gbm-ent-drug: #a5d8ff;
  --gbm-ent-disease: #ffd8a8;
  --gbm-ent-pathway: #c3fae8;
  --gbm-ent-biomarker: #96f2d7;
  --gbm-ent-cell-type: #ffe8cc;
  --gbm-ent-cell-state: #fff3bf;
  --gbm-ent-treatment: #d8f5a2;
  --gbm-ent-delivery: #bac8ff;
  --gbm-ent-outcome: #ffc9c9;
  --gbm-ent-trial: #e9ecef;
  --gbm-ent-unknown: #dee2e6;
  --gbm-score-high: #0f766e;
  --gbm-score-mid: #b45309;
  --gbm-score-low: #64748b;
}
"""

ENTITY_TYPE_COLORS: dict[str, str] = {
    "GENE": "var(--gbm-ent-gene)",
    "DRUG": "var(--gbm-ent-drug)",
    "DISEASE": "var(--gbm-ent-disease)",
    "PATHWAY": "var(--gbm-ent-pathway)",
    "BIOMARKER": "var(--gbm-ent-biomarker)",
    "CELL_TYPE": "var(--gbm-ent-cell-type)",
    "CELL_STATE": "var(--gbm-ent-cell-state)",
    "TREATMENT": "var(--gbm-ent-treatment)",
    "DELIVERY_MODIFIER": "var(--gbm-ent-delivery)",
    "OUTCOME": "var(--gbm-ent-outcome)",
    "TRIAL_PHASE": "var(--gbm-ent-trial)",
    "UNKNOWN": "var(--gbm-ent-unknown)",
}

# Fallback hex when CSS variables are unavailable (e.g. tests asserting style attrs).
ENTITY_TYPE_HEX: dict[str, str] = {
    "GENE": "#b7e4c7",
    "DRUG": "#a5d8ff",
    "DISEASE": "#ffd8a8",
    "PATHWAY": "#c3fae8",
    "BIOMARKER": "#96f2d7",
    "CELL_TYPE": "#ffe8cc",
    "CELL_STATE": "#fff3bf",
    "TREATMENT": "#d8f5a2",
    "DELIVERY_MODIFIER": "#bac8ff",
    "OUTCOME": "#ffc9c9",
    "TRIAL_PHASE": "#e9ecef",
    "UNKNOWN": "#dee2e6",
}

DASHBOARD_VISUAL_CSS = f"""
<style>
{CSS_VARIABLES}
.gbm-highlight-panel {{
  background: var(--gbm-surface);
  border: 1px solid var(--gbm-border);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  line-height: 1.55;
  color: var(--gbm-text);
  font-size: 0.95rem;
}}
.gbm-ent {{
  border-radius: 3px;
  padding: 0.05em 0.2em;
  border-bottom: 2px solid rgba(15, 118, 110, 0.35);
  white-space: baseline;
}}
.gbm-ent-label {{
  font-size: 0.68em;
  font-weight: 700;
  letter-spacing: 0.03em;
  margin-left: 0.25em;
  color: var(--gbm-muted);
  text-transform: uppercase;
  vertical-align: super;
}}
.gbm-legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.75rem;
  margin: 0.35rem 0 0.75rem 0;
  font-size: 0.82rem;
  color: var(--gbm-muted);
}}
.gbm-legend-item {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}}
.gbm-legend-swatch {{
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 3px;
  border: 1px solid var(--gbm-border);
  display: inline-block;
}}
.gbm-chip {{
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border-radius: 999px;
  padding: 0.12rem 0.55rem;
  font-size: 0.78rem;
  font-weight: 600;
  border: 1px solid var(--gbm-border);
  background: var(--gbm-bg);
  color: var(--gbm-text);
  margin-right: 0.35rem;
  margin-bottom: 0.25rem;
}}
.gbm-chip-pmid {{
  background: var(--gbm-accent-soft);
  border-color: #99f6e4;
  color: var(--gbm-pmid);
}}
.gbm-chip-type {{
  background: #ecfeff;
  border-color: #a5f3fc;
  color: #155e75;
}}
.gbm-chip-tier {{
  background: #fff7ed;
  border-color: #fed7aa;
  color: #9a3412;
}}
.gbm-score {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  vertical-align: middle;
}}
.gbm-score-bar {{
  width: 52px;
  height: 7px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
  display: inline-block;
}}
.gbm-score-fill {{
  height: 100%;
  border-radius: 999px;
}}
.gbm-score-label {{
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--gbm-muted);
}}
.gbm-triple {{
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) auto minmax(0, 1.2fr) auto;
  gap: 0.45rem 0.65rem;
  align-items: center;
  border: 1px solid var(--gbm-border);
  border-radius: 8px;
  padding: 0.55rem 0.75rem;
  margin-bottom: 0.45rem;
  background: var(--gbm-surface);
}}
.gbm-triple-node {{
  border-radius: 6px;
  padding: 0.35rem 0.55rem;
  background: var(--gbm-bg);
  border: 1px solid var(--gbm-border);
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}}
.gbm-triple-pred {{
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--gbm-accent);
  text-align: center;
  white-space: nowrap;
}}
.gbm-triple-meta {{
  font-size: 0.78rem;
  color: var(--gbm-muted);
  justify-self: end;
}}
.gbm-paper-card {{
  border: 1px solid var(--gbm-border);
  border-radius: 8px;
  padding: 0.75rem 0.9rem 0.35rem 0.9rem;
  margin-bottom: 0.65rem;
  background: var(--gbm-surface);
}}
.gbm-paper-title {{
  font-weight: 650;
  color: var(--gbm-text);
  margin-bottom: 0.2rem;
}}
.gbm-paper-meta {{
  color: var(--gbm-muted);
  font-size: 0.85rem;
  margin-bottom: 0.35rem;
}}
.gbm-section-note {{ color: var(--gbm-muted); font-size: 0.92rem; }}
</style>
"""

_FLOAT_RE = re.compile(r"^-?\d+(\.\d+)?$")


def normalize_entity_type(value: object) -> str:
    """Normalize EntityType / NodeLabel / plain strings to an uppercase token."""

    if value is None:
        return "UNKNOWN"
    if hasattr(value, "value"):
        text = str(getattr(value, "value"))
    else:
        text = str(value).strip()
    if not text:
        return "UNKNOWN"
    if "." in text and text.split(".", 1)[0] in {"EntityType", "NodeLabel", "RelationType"}:
        text = text.split(".", 1)[-1]
    token = text.strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "GENE_OR_GENE_PRODUCT": "GENE",
        "CHEMICAL": "DRUG",
        "DRUG_OR_CHEMICAL": "DRUG",
        "CANCER": "DISEASE",
        "CELL": "CELL_TYPE",
        "CELLLINE": "CELL_TYPE",
        "CELL_LINE": "CELL_TYPE",
    }
    token = aliases.get(token, token)
    return token if token in ENTITY_TYPE_COLORS else (token if token else "UNKNOWN")


def entity_type_color(label: object, *, as_hex: bool = False) -> str:
    """Return CSS color for an entity type (variable or hex)."""

    token = normalize_entity_type(label)
    if as_hex:
        return ENTITY_TYPE_HEX.get(token, ENTITY_TYPE_HEX["UNKNOWN"])
    return ENTITY_TYPE_COLORS.get(token, ENTITY_TYPE_COLORS["UNKNOWN"])


def _coerce_score(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or not _FLOAT_RE.match(text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def score_level(score: float | None) -> str:
    """Bucket a 0–1 (or 0–100) score for chip styling."""

    if score is None:
        return "unknown"
    value = score / 100.0 if score > 1.0 else score
    if value >= 0.75:
        return "high"
    if value >= 0.4:
        return "mid"
    return "low"


def score_bar_html(score: object, *, label: str | None = None) -> str:
    """Compact confidence bar + numeric chip (Gradio-style score chrome)."""

    numeric = _coerce_score(score)
    if numeric is None:
        return ""
    display = numeric
    width_pct = max(0.0, min(100.0, numeric if numeric > 1.0 else numeric * 100.0))
    level = score_level(numeric)
    fill = {
        "high": "var(--gbm-score-high)",
        "mid": "var(--gbm-score-mid)",
        "low": "var(--gbm-score-low)",
    }.get(level, "var(--gbm-score-low)")
    text = f"{display:.2f}" if display <= 1.0 else f"{display:.0f}"
    caption = html.escape(label) if label else "score"
    return (
        f'<span class="gbm-score" title="{caption}={text}">'
        f'<span class="gbm-score-bar"><span class="gbm-score-fill" '
        f'style="width:{width_pct:.1f}%;background:{fill}"></span></span>'
        f'<span class="gbm-score-label">{caption} {text}</span></span>'
    )


def chip_html(text: object, *, kind: str = "default") -> str:
    """Small badge/chip used for PMID, type, and tier chrome."""

    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    css = {
        "pmid": "gbm-chip gbm-chip-pmid",
        "type": "gbm-chip gbm-chip-type",
        "tier": "gbm-chip gbm-chip-tier",
        "default": "gbm-chip",
    }.get(kind, "gbm-chip")
    return f'<span class="{css}">{html.escape(cleaned)}</span>'


def pmid_badge_html(pmid: object) -> str:
    cleaned = str(pmid or "").strip()
    if not cleaned:
        return ""
    if cleaned.lower().startswith("pmid"):
        return chip_html(cleaned, kind="pmid")
    return chip_html(f"PMID {cleaned}", kind="pmid")


def entity_legend_html(labels: Iterable[object] | None = None) -> str:
    """PubTator-style entity-type legend (only types present, or defaults)."""

    if labels is None:
        tokens = list(ENTITY_TYPE_COLORS.keys())
    else:
        seen: list[str] = []
        for label in labels:
            token = normalize_entity_type(label)
            if token not in seen:
                seen.append(token)
        tokens = seen or ["UNKNOWN"]
    items: list[str] = []
    for token in tokens:
        color = entity_type_color(token, as_hex=True)
        items.append(
            f'<span class="gbm-legend-item">'
            f'<span class="gbm-legend-swatch" style="background:{color}"></span>'
            f"{html.escape(token)}</span>"
        )
    return f'<div class="gbm-legend">{"".join(items)}</div>'


def _span_bounds(span: Mapping[str, Any]) -> tuple[int, int] | None:
    try:
        start = int(span.get("start"))
        end = int(span.get("end"))
    except (TypeError, ValueError):
        return None
    if start < 0 or end <= start:
        return None
    return start, end


def highlight_spans_html(
    text: str,
    spans: Sequence[Mapping[str, Any]] | None,
    *,
    show_labels: bool = True,
) -> str:
    """Render text with type-colored entity spans (displaCy / Gradio style).

    Spans are ``{start, end, label}`` character offsets into ``text``. Overlaps
    are resolved by keeping earlier, longer spans.
    """

    source = text or ""
    if not spans:
        return f'<div class="gbm-highlight-panel">{html.escape(source) or "(empty)"}</div>'

    candidates: list[tuple[int, int, str]] = []
    for span in spans:
        bounds = _span_bounds(span)
        if bounds is None:
            continue
        start, end = bounds
        if start >= len(source):
            continue
        end = min(end, len(source))
        if end <= start:
            continue
        label = normalize_entity_type(span.get("label") or span.get("entity_group") or span.get("type"))
        candidates.append((start, end, label))

    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    accepted: list[tuple[int, int, str]] = []
    occupied_until = -1
    for start, end, label in candidates:
        if start < occupied_until:
            continue
        accepted.append((start, end, label))
        occupied_until = end
    accepted.sort(key=lambda item: item[0])

    parts: list[str] = []
    cursor = 0
    for start, end, label in accepted:
        if cursor < start:
            parts.append(html.escape(source[cursor:start]))
        color = entity_type_color(label, as_hex=True)
        chunk = html.escape(source[start:end])
        label_bit = (
            f'<span class="gbm-ent-label">{html.escape(label)}</span>' if show_labels else ""
        )
        parts.append(
            f'<mark class="gbm-ent" style="background:{color}">{chunk}{label_bit}</mark>'
        )
        cursor = end
    if cursor < len(source):
        parts.append(html.escape(source[cursor:]))
    return f'<div class="gbm-highlight-panel">{"".join(parts) or "(empty)"}</div>'


def relation_triple_html(
    subject: object,
    predicate: object,
    obj: object,
    *,
    meta: object = "",
    score: object = None,
) -> str:
    """Subject–predicate–object row (pubmedKB-style relation chrome)."""

    subj = html.escape(str(subject or "").strip() or "?")
    pred = html.escape(str(predicate or "").strip() or "RELATED_TO")
    target = html.escape(str(obj or "").strip() or "?")
    meta_bits: list[str] = []
    meta_text = str(meta or "").strip()
    if meta_text:
        meta_bits.append(html.escape(meta_text))
    score_bit = score_bar_html(score, label="conf")
    if score_bit:
        meta_bits.append(score_bit)
    meta_html = " · ".join(meta_bits) if meta_bits else ""
    return (
        f'<div class="gbm-triple">'
        f'<div class="gbm-triple-node">{subj}</div>'
        f'<div class="gbm-triple-pred">{pred}</div>'
        f'<div class="gbm-triple-node">{target}</div>'
        f'<div class="gbm-triple-meta">{meta_html}</div>'
        f"</div>"
    )


def evidence_chips_html(
    *,
    pmid: object = None,
    entity_type: object = None,
    evidence_tier: object = None,
    score: object = None,
    extra: Sequence[object] | None = None,
) -> str:
    """Badge row for evidence/paper cards (PMID + type + tier + score)."""

    bits: list[str] = []
    pmid_chip = pmid_badge_html(pmid)
    if pmid_chip:
        bits.append(pmid_chip)
    if entity_type:
        bits.append(chip_html(normalize_entity_type(entity_type), kind="type"))
    if evidence_tier is not None and str(evidence_tier).strip() != "":
        bits.append(chip_html(f"tier {evidence_tier}", kind="tier"))
    score_bit = score_bar_html(score, label="conf")
    if score_bit:
        bits.append(score_bit)
    for item in extra or ():
        text = str(item or "").strip()
        if text:
            bits.append(chip_html(text, kind="default"))
    if not bits:
        return ""
    return f'<div>{"".join(bits)}</div>'


def paper_card_header_html(
    *,
    title: str,
    citation: str = "",
    pmid: object = None,
    entity_type: object = None,
    evidence_tier: object = None,
    score: object = None,
    note: str = "",
) -> str:
    """HTML header chrome for a literature / evidence card."""

    chips = evidence_chips_html(
        pmid=pmid,
        entity_type=entity_type,
        evidence_tier=evidence_tier,
        score=score,
    )
    note_html = f'<div class="gbm-paper-meta">{html.escape(note)}</div>' if note else ""
    citation_html = (
        f'<div class="gbm-paper-meta">{html.escape(citation)}</div>' if citation else ""
    )
    return (
        f'<div class="gbm-paper-card">'
        f'<div class="gbm-paper-title">{html.escape(title)}</div>'
        f"{citation_html}{chips}{note_html}</div>"
    )


def collect_span_labels(spans: Sequence[Mapping[str, Any]] | None) -> list[str]:
    labels: list[str] = []
    for span in spans or ():
        token = normalize_entity_type(span.get("label") or span.get("entity_group") or span.get("type"))
        if token not in labels:
            labels.append(token)
    return labels


def render_highlighted_text(
    st: object,
    text: str,
    spans: Sequence[Mapping[str, Any]] | None,
    *,
    legend: bool = True,
    show_labels: bool = True,
) -> None:
    """Streamlit helper: legend + inline highlighted panel."""

    if legend:
        st.markdown(entity_legend_html(collect_span_labels(spans)), unsafe_allow_html=True)
    st.markdown(
        highlight_spans_html(text, spans, show_labels=show_labels),
        unsafe_allow_html=True,
    )


def render_relation_triples(
    st: object,
    edges: Sequence[Mapping[str, Any]],
    *,
    limit: int = 40,
) -> int:
    """Render SPO rows for KG / entity relation lists."""

    shown = 0
    for edge in edges:
        if shown >= limit:
            break
        subject = edge.get("source") or edge.get("subject") or edge.get("head")
        predicate = edge.get("type") or edge.get("predicate") or edge.get("relation")
        obj = edge.get("target") or edge.get("object") or edge.get("tail")
        tier = edge.get("evidence_tier")
        meta_parts = []
        if tier is not None and str(tier).strip() != "":
            meta_parts.append(f"tier {tier}")
        pmids = edge.get("source_pmids") or edge.get("pmid")
        if pmids:
            meta_parts.append(f"PMID {pmids}")
        st.markdown(
            relation_triple_html(
                subject,
                predicate,
                obj,
                meta=" · ".join(meta_parts),
                score=edge.get("confidence") or edge.get("score"),
            ),
            unsafe_allow_html=True,
        )
        shown += 1
    return shown
