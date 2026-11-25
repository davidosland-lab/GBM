"""Paper / PMID open helpers for the Phase 7 research dashboard.

Research-use only. PubMed and DOI URLs open in the user's browser; they do not
require the dashboard process itself to have network access.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov"
DOI_BASE = "https://doi.org"

_PMID_RE = re.compile(r"^\d{1,12}$")
_DOI_PREFIX_RE = re.compile(r"^https?://(dx\.)?doi\.org/", re.IGNORECASE)


def normalize_pmid(value: object) -> str:
    """Return a digits-only PMID string, or empty if invalid."""

    if value is None:
        return ""
    text = str(value).strip()
    if text.lower().startswith("pmid:"):
        text = text.split(":", 1)[1].strip()
    text = text.strip().rstrip("/")
    if text.isdigit() and _PMID_RE.match(text):
        return text
    return ""


def pmid_url(pmid: object) -> str | None:
    """Return a PubMed abstract URL for a PMID, or None if invalid."""

    cleaned = normalize_pmid(pmid)
    if not cleaned:
        return None
    return f"{PUBMED_BASE}/{cleaned}/"


def pmid_markdown_link(pmid: object, *, label: str | None = None) -> str:
    """Markdown link for a PMID (falls back to plain text when invalid)."""

    cleaned = normalize_pmid(pmid)
    if not cleaned:
        return str(pmid or "")
    url = pmid_url(cleaned)
    display = label or cleaned
    return f"[{display}]({url})"


def normalize_doi(value: object) -> str:
    """Normalize a DOI or DOI URL to a bare DOI string."""

    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = _DOI_PREFIX_RE.sub("", text)
    if text.lower().startswith("doi:"):
        text = text.split(":", 1)[1].strip()
    return text.strip().strip("/")


def doi_url(doi: object) -> str | None:
    """Return a doi.org URL, or None if DOI is empty/invalid."""

    cleaned = normalize_doi(doi)
    if not cleaned or "/" not in cleaned:
        return None
    return f"{DOI_BASE}/{cleaned}"


def _first_nonempty(record: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def full_text_url(record: dict[str, Any]) -> str | None:
    """Prefer an explicit full-text / PMC / landing URL when present."""

    raw = _first_nonempty(
        record,
        (
            "full_text_url",
            "fulltext_url",
            "pmc_url",
            "url",
            "landing_url",
        ),
    )
    if not raw:
        pmcid = _first_nonempty(record, ("pmcid", "PMCID"))
        if pmcid:
            token = pmcid.upper()
            if not token.startswith("PMC"):
                token = f"PMC{token}"
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{token}/"
        return None
    if raw.lower().startswith(("http://", "https://")):
        return raw
    return None


def local_pdf_path(record: dict[str, Any], *, base_dir: str | Path = ".") -> Path | None:
    """Return a resolved local PDF/path when metadata points at an existing file."""

    raw = _first_nonempty(
        record,
        (
            "local_pdf",
            "pdf_path",
            "local_path",
            "pdf",
            "file_path",
        ),
    )
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (Path(base_dir) / candidate).resolve()
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def publication_year(record: dict[str, Any]) -> str:
    """Best-effort year from publication_date / year fields."""

    explicit = _first_nonempty(record, ("year", "publication_year"))
    if explicit and re.search(r"\d{4}", explicit):
        match = re.search(r"\d{4}", explicit)
        return match.group(0) if match else explicit
    pub_date = _first_nonempty(record, ("publication_date", "pub_date", "date"))
    if pub_date:
        match = re.search(r"\d{4}", pub_date)
        if match:
            return match.group(0)
    return ""


def format_authors(record: dict[str, Any], *, max_authors: int = 3) -> str:
    """Format author list from common PubMed-ish record shapes."""

    authors = record.get("authors")
    if authors is None:
        authors = record.get("author_list")
    if isinstance(authors, str) and authors.strip():
        return authors.strip()
    if isinstance(authors, list) and authors:
        names: list[str] = []
        for item in authors:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
            elif isinstance(item, dict):
                collective = str(item.get("collective_name") or "").strip()
                if collective:
                    names.append(collective)
                    continue
                last = str(item.get("last_name") or item.get("LastName") or "").strip()
                initials = str(
                    item.get("initials") or item.get("Initials") or item.get("fore_name") or ""
                ).strip()
                if last and initials:
                    names.append(f"{last} {initials}")
                elif last:
                    names.append(last)
        if not names:
            return ""
        if len(names) > max_authors:
            return ", ".join(names[:max_authors]) + " et al."
        return ", ".join(names)
    return ""


def format_citation_line(record: dict[str, Any]) -> str:
    """Compact authors · year · journal line for literature cards."""

    parts = [
        format_authors(record),
        publication_year(record),
        str(record.get("journal") or "").strip(),
    ]
    return " · ".join(part for part in parts if part)


def paper_link_bundle(
    record: dict[str, Any] | str | int | None,
    *,
    base_dir: str | Path = ".",
) -> dict[str, Any]:
    """Normalize a paper record or bare PMID into openable link fields."""

    if record is None:
        payload: dict[str, Any] = {}
    elif isinstance(record, (str, int)):
        payload = {"pmid": record}
    else:
        payload = dict(record)

    pmid = normalize_pmid(
        payload.get("pmid")
        or payload.get("source_pmid")
        or payload.get("PMID")
        or payload.get("id")
    )
    doi = normalize_doi(payload.get("doi") or payload.get("DOI"))
    local = local_pdf_path(payload, base_dir=base_dir)
    return {
        "pmid": pmid,
        "title": str(payload.get("title") or "").strip(),
        "citation": format_citation_line(payload),
        "abstract": str(payload.get("abstract") or "").strip(),
        "journal": str(payload.get("journal") or "").strip(),
        "year": publication_year(payload),
        "authors": format_authors(payload),
        "doi": doi,
        "pubmed_url": pmid_url(pmid),
        "doi_url": doi_url(doi),
        "full_text_url": full_text_url(payload),
        "local_pdf": str(local) if local else "",
        "note": str(payload.get("note") or "").strip(),
    }


def collect_pmids(*sources: object) -> list[str]:
    """Collect unique PMIDs from strings, lists, dicts, and nested payloads."""

    found: list[str] = []
    seen: set[str] = set()

    def _add(value: object) -> None:
        cleaned = normalize_pmid(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            found.append(cleaned)

    def _walk(value: object) -> None:
        if value is None:
            return
        if isinstance(value, (str, int)):
            text = str(value).strip()
            if "," in text and not text.isdigit():
                for part in text.split(","):
                    _add(part.strip())
            else:
                _add(text)
            return
        if isinstance(value, dict):
            for key in ("pmid", "source_pmid", "PMID"):
                if key in value:
                    _add(value.get(key))
            for key in (
                "pmids",
                "source_pmids",
                "source_pmid_list",
                "literature_anchors",
                "feature_rows",
                "features",
                "graph_features",
                "graph_modulation",
                "rows",
            ):
                if key in value:
                    _walk(value.get(key))
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                _walk(item)

    for source in sources:
        _walk(source)
    return found


def open_local_path(path: str | Path) -> bool:
    """Best-effort open/reveal a local file in the OS file browser / default app."""

    target = Path(path)
    if not target.exists():
        return False
    try:
        if sys.platform == "win32":
            os.startfile(str(target))  # type: ignore[attr-defined]
            return True
        if sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
            return True
        subprocess.run(["xdg-open", str(target)], check=False)
        return True
    except OSError:
        return False


def with_pubmed_link_column(
    rows: list[dict[str, Any]],
    *,
    pmid_key: str = "pmid",
    url_key: str = "pubmed_url",
) -> list[dict[str, Any]]:
    """Copy table rows and add a PubMed URL column derived from a PMID field."""

    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        url = pmid_url(item.get(pmid_key))
        item[url_key] = url or ""
        enriched.append(item)
    return enriched


def render_paper_open_buttons(
    st: object,
    record: dict[str, Any] | str | int | None,
    *,
    key_prefix: str,
    base_dir: str | Path = ".",
) -> dict[str, Any]:
    """Render PubMed / DOI / full-text / local-PDF open controls for one paper."""

    bundle = paper_link_bundle(record, base_dir=base_dir)
    buttons: list[tuple[str, str | None, str]] = [
        ("PubMed", bundle["pubmed_url"], "pubmed"),
        ("DOI", bundle["doi_url"], "doi"),
        ("Full text", bundle["full_text_url"], "fulltext"),
    ]
    available = [(label, url, suffix) for label, url, suffix in buttons if url]
    if not available and not bundle["local_pdf"]:
        st.caption("No openable paper link for this row.")
        return bundle

    cols = st.columns(max(len(available) + (1 if bundle["local_pdf"] else 0), 1))
    for idx, (label, url, suffix) in enumerate(available):
        with cols[idx]:
            st.link_button(label, url, use_container_width=True)
    if bundle["local_pdf"]:
        with cols[len(available)]:
            if st.button("Open local PDF", key=f"{key_prefix}_local_pdf", use_container_width=True):
                if open_local_path(bundle["local_pdf"]):
                    st.caption(f"Opened `{bundle['local_pdf']}`")
                else:
                    st.warning(f"Could not open `{bundle['local_pdf']}`")
    return bundle


def render_paper_row(
    st: object,
    record: dict[str, Any] | str | int | None,
    *,
    key_prefix: str,
    expanded: bool = False,
    base_dir: str | Path = ".",
    show_abstract: bool = True,
    entity_type: object = None,
    evidence_tier: object = None,
    score: object = None,
    spans: list[dict[str, Any]] | None = None,
    highlight_text: str | None = None,
) -> dict[str, Any]:
    """Render a literature-style card with title, citation, badges, and open buttons.

    Optional ``spans`` / ``highlight_text`` enable PubTator-style inline entity
    highlighting inside the abstract expander when offsets are available.
    """

    from gbmbert.dashboard.visuals import paper_card_header_html, render_highlighted_text

    bundle = paper_link_bundle(record, base_dir=base_dir)
    payload = dict(record) if isinstance(record, dict) else {}
    title = bundle["title"] or (f"PMID {bundle['pmid']}" if bundle["pmid"] else "Untitled paper")
    tier = evidence_tier if evidence_tier is not None else payload.get("evidence_tier")
    if tier is None:
        tier = payload.get("predicted_evidence_tier")
    type_value = entity_type if entity_type is not None else payload.get("entity_type") or payload.get("label")
    score_value = score if score is not None else payload.get("confidence") or payload.get("score")
    with st.container():
        st.markdown(
            paper_card_header_html(
                title=title,
                citation=bundle["citation"],
                pmid=bundle["pmid"] or None,
                entity_type=type_value,
                evidence_tier=tier,
                score=score_value,
                note=bundle["note"],
            ),
            unsafe_allow_html=True,
        )
        render_paper_open_buttons(st, bundle, key_prefix=key_prefix, base_dir=base_dir)
        abstract_text = highlight_text if highlight_text is not None else bundle["abstract"]
        entity_spans = spans if spans is not None else payload.get("entities") or payload.get("spans")
        if show_abstract and abstract_text:
            with st.expander("Abstract", expanded=expanded):
                if isinstance(entity_spans, list) and entity_spans:
                    render_highlighted_text(st, str(abstract_text), entity_spans)
                else:
                    st.write(abstract_text)
        st.divider()
    return bundle


def render_pmid_open_list(
    st: object,
    pmids: Iterable[object],
    *,
    key_prefix: str,
    title: str = "Referenced papers",
    empty_message: str = "No paper PMIDs in this result.",
) -> list[str]:
    """Render a compact list of PMIDs with PubMed open buttons."""

    cleaned = collect_pmids(list(pmids))
    if title:
        st.subheader(title)
    if not cleaned:
        if empty_message:
            st.info(empty_message)
        return []
    # Markdown links avoid Streamlit widget-key collisions on long PMID lists.
    _ = key_prefix
    for pmid in cleaned:
        url = pmid_url(pmid)
        if url:
            st.markdown(f"- **PMID {pmid}** — [Open PubMed]({url})")
        else:
            st.markdown(f"- PMID {pmid}")
    return cleaned


def counts_to_chart_rows(counts: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Convert a label→count mapping into rows for Streamlit bar charts."""

    if not counts:
        return []
    rows: list[dict[str, Any]] = []
    for label, value in counts.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        rows.append({"label": str(label), "count": numeric})
    return rows
