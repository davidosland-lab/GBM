"""PubMed ingestion through NCBI E-utilities."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared for normal installs.
    load_dotenv = None

from gbmbert.preprocess.clean_text import clean_text, join_abstract_sections

LOGGER = logging.getLogger(__name__)

EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_TOOL_NAME = "gbm-ai-platform"
DEFAULT_JSONL_PATH = Path("data/raw/pubmed_records.jsonl")
_ENV_LOADED = False


class PubMedIngestionError(RuntimeError):
    """Raised when a PubMed request or response cannot be processed."""


def _load_environment() -> None:
    global _ENV_LOADED
    if _ENV_LOADED or load_dotenv is None:
        return

    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            load_dotenv(dotenv_path=env_path, encoding="utf-8")
        except UnicodeDecodeError:
            LOGGER.warning("Could not read %s as UTF-8; retrying as UTF-16.", env_path)
            load_dotenv(dotenv_path=env_path, encoding="utf-16")
    _ENV_LOADED = True


def _ncbi_config() -> dict[str, str | None]:
    _load_environment()
    return {
        "email": os.getenv("NCBI_EMAIL"),
        "api_key": os.getenv("NCBI_API_KEY"),
        "tool": os.getenv("NCBI_TOOL", DEFAULT_TOOL_NAME),
    }


def _rate_limit_delay(api_key: str | None) -> float:
    return 0.11 if api_key else 0.34


def _request_json(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    content = _request(endpoint, {**params, "retmode": "json"})
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise PubMedIngestionError("NCBI returned invalid JSON") from exc


def _request_xml(endpoint: str, params: dict[str, Any]) -> ET.Element:
    content = _request(endpoint, {**params, "retmode": "xml"})
    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        raise PubMedIngestionError("NCBI returned invalid XML") from exc


def _request(endpoint: str, params: dict[str, Any]) -> str:
    config = _ncbi_config()
    request_params = {
        "tool": config["tool"],
        **params,
    }
    if config["email"]:
        request_params["email"] = config["email"]
    else:
        LOGGER.warning("NCBI_EMAIL is not set; NCBI asks clients to provide a contact email.")
    if config["api_key"]:
        request_params["api_key"] = config["api_key"]

    encoded = urllib.parse.urlencode(request_params, doseq=True)
    url = f"{EUTILS_BASE_URL}/{endpoint}?{encoded}"
    time.sleep(_rate_limit_delay(config["api_key"]))

    LOGGER.debug("Requesting NCBI E-utilities endpoint %s", endpoint)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")
    except OSError as exc:
        raise PubMedIngestionError(f"NCBI request failed for {endpoint}") from exc


def search_pubmed(query: str, retmax: int = 100, sort: str = "relevance") -> list[str]:
    """Search PubMed and return PMIDs matching a query."""

    if not query.strip():
        raise ValueError("query must not be empty")
    if retmax < 1:
        raise ValueError("retmax must be at least 1")

    payload = _request_json(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "sort": sort,
        },
    )
    pmids = payload.get("esearchresult", {}).get("idlist", [])
    return [str(pmid) for pmid in pmids]


def fetch_pubmed_records(pmids: Sequence[str], batch_size: int = 100) -> list[dict[str, Any]]:
    """Fetch PubMed records by PMID and return JSON-serializable dictionaries."""

    normalized_pmids = [str(pmid).strip() for pmid in pmids if str(pmid).strip()]
    if not normalized_pmids:
        return []
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    records: list[dict[str, Any]] = []
    for start in range(0, len(normalized_pmids), batch_size):
        batch = normalized_pmids[start : start + batch_size]
        root = _request_xml(
            "efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(batch),
            },
        )
        records.extend(_parse_pubmed_xml(root))
    return records


def save_jsonl(
    records: Iterable[dict[str, Any]],
    path: str | Path = DEFAULT_JSONL_PATH,
) -> Path:
    """Save PubMed records to newline-delimited JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    LOGGER.info("Saved PubMed JSONL records to %s", output_path)
    return output_path


def _parse_pubmed_xml(root: ET.Element) -> list[dict[str, Any]]:
    records = []
    for article in root.findall(".//PubmedArticle"):
        pmid = _find_text(article, ".//MedlineCitation/PMID")
        if not pmid:
            continue
        records.append(
            {
                "pmid": pmid,
                "title": _article_title(article),
                "abstract": _abstract(article),
                "journal": _journal(article),
                "publication_date": _publication_date(article),
                "mesh_terms": _mesh_terms(article),
            }
        )
    return records


def _find_text(element: ET.Element, path: str) -> str:
    node = element.find(path)
    if node is None:
        return ""
    return clean_text("".join(node.itertext()))


def _article_title(article: ET.Element) -> str:
    return _find_text(article, ".//Article/ArticleTitle")


def _abstract(article: ET.Element) -> str:
    sections = [
        clean_text("".join(node.itertext()))
        for node in article.findall(".//Article/Abstract/AbstractText")
    ]
    return join_abstract_sections(sections)


def _journal(article: ET.Element) -> str:
    return _find_text(article, ".//Article/Journal/Title")


def _publication_date(article: ET.Element) -> str:
    pub_date = article.find(".//Article/Journal/JournalIssue/PubDate")
    if pub_date is None:
        return ""

    medline_date = _find_text(pub_date, "MedlineDate")
    if medline_date:
        return medline_date

    year = _find_text(pub_date, "Year")
    month = _find_text(pub_date, "Month")
    day = _find_text(pub_date, "Day")
    return "-".join(part for part in [year, month, day] if part)


def _mesh_terms(article: ET.Element) -> list[str]:
    terms = []
    for descriptor in article.findall(".//MeshHeading/DescriptorName"):
        term = clean_text("".join(descriptor.itertext()))
        if term:
            terms.append(term)
    return terms
