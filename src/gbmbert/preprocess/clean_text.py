"""Text cleaning helpers for biomedical abstracts."""

from __future__ import annotations

import html
import re

_WHITESPACE_RE = re.compile(r"\s+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str | None) -> str:
    """Normalize HTML entities, control characters, and whitespace."""

    if not text:
        return ""
    cleaned = html.unescape(text)
    cleaned = _CONTROL_RE.sub(" ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    return cleaned.strip()


def join_abstract_sections(sections: list[str]) -> str:
    """Join PubMed abstract sections into a single cleaned abstract."""

    return clean_text(" ".join(section for section in sections if section))
