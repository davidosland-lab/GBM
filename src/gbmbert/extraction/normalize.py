"""Entity text normalization for common glioblastoma aliases."""

from __future__ import annotations

import re

ALIASES: dict[str, str] = {
    "gbm": "glioblastoma",
    "glioblastoma multiforme": "glioblastoma",
    "tmz": "temozolomide",
    "pd1": "PD-1",
    "pd-1": "PD-1",
    "pdl1": "PD-L1",
    "pd-l1": "PD-L1",
    "egfr": "EGFR",
    "mgmt": "MGMT",
    "idh1": "IDH1",
    "idh2": "IDH2",
}

_WHITESPACE_RE = re.compile(r"\s+")


def canonical_key(text: str) -> str:
    """Return a case-insensitive lookup key with normalized whitespace."""

    return _WHITESPACE_RE.sub(" ", text.strip().lower())


def normalize_text(text: str) -> str:
    """Normalize a biomedical mention using known aliases."""

    stripped = _WHITESPACE_RE.sub(" ", text.strip())
    if not stripped:
        return ""
    return ALIASES.get(canonical_key(stripped), stripped)


def normalize_many(texts: list[str]) -> list[str]:
    """Normalize a list of entity mentions."""

    return [normalize_text(text) for text in texts]
