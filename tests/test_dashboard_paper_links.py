"""Tests for dashboard paper / PMID open helpers."""

from __future__ import annotations

from pathlib import Path

from gbmbert.dashboard.paper_links import (
    collect_pmids,
    counts_to_chart_rows,
    doi_url,
    format_authors,
    format_citation_line,
    full_text_url,
    local_pdf_path,
    normalize_doi,
    normalize_pmid,
    paper_link_bundle,
    pmid_markdown_link,
    pmid_url,
    with_pubmed_link_column,
)


def test_pmid_and_doi_urls() -> None:
    assert normalize_pmid("PMID:29097493") == "29097493"
    assert pmid_url("29097493") == "https://pubmed.ncbi.nlm.nih.gov/29097493/"
    assert pmid_url("not-a-pmid") is None
    assert normalize_doi("https://doi.org/10.1000/xyz") == "10.1000/xyz"
    assert doi_url("10.1000/xyz") == "https://doi.org/10.1000/xyz"
    assert doi_url("") is None
    assert "29097493" in pmid_markdown_link("29097493")


def test_paper_link_bundle_and_citation(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    record = {
        "pmid": "29097493",
        "title": "MGMT methylation predicts temozolomide response",
        "authors": [{"last_name": "Example", "initials": "A"}, {"last_name": "Other", "initials": "B"}],
        "publication_date": "2018-Jun-01",
        "journal": "Example Research",
        "doi": "10.1000/gbm.example",
        "full_text_url": "https://example.org/full",
        "local_pdf": str(pdf),
    }
    bundle = paper_link_bundle(record, base_dir=tmp_path)
    assert bundle["pubmed_url"].endswith("/29097493/")
    assert bundle["doi_url"] == "https://doi.org/10.1000/gbm.example"
    assert bundle["full_text_url"] == "https://example.org/full"
    assert bundle["local_pdf"] == str(pdf)
    assert "Example A" in format_authors(record)
    assert "2018" in format_citation_line(record)
    assert local_pdf_path(record, base_dir=tmp_path) == pdf
    assert full_text_url({"pmcid": "PMC123"}) == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123/"


def test_collect_pmids_and_table_enrichment() -> None:
    pmids = collect_pmids(
        {"pmid": "111"},
        ["222", "pmid:333"],
        {"literature_anchors": [{"pmid": "444", "note": "x"}]},
        {"source_pmids": "555, 666"},
        {"graph_features": {"feature_rows": [{"source_pmid": "29097493"}]}},
    )
    assert pmids == ["111", "222", "333", "444", "555", "666", "29097493"]
    rows = with_pubmed_link_column([{"pmid": "29097493", "title": "t"}], pmid_key="pmid")
    assert rows[0]["pubmed_url"] == "https://pubmed.ncbi.nlm.nih.gov/29097493/"
    assert counts_to_chart_rows({"GENE": 3, "DRUG": 1}) == [
        {"label": "GENE", "count": 3.0},
        {"label": "DRUG", "count": 1.0},
    ]


def test_literature_runner_passes_optional_paper_fields(tmp_path: Path) -> None:
    from gbmbert.dashboard.runners import run_literature_search_live

    jsonl = tmp_path / "papers.jsonl"
    jsonl.write_text(
        (
            '{"pmid":"12345","title":"Demo","abstract":"glioblastoma demo",'
            '"journal":"J","publication_date":"2020","doi":"10.1/x",'
            '"authors":["Alpha A","Beta B"],"full_text_url":"https://example.org/ft"}\n'
        ),
        encoding="utf-8",
    )
    result = run_literature_search_live(
        query="glioblastoma",
        retmax=5,
        offline=True,
        local_jsonl=jsonl,
        write_reports=False,
        base_dir=tmp_path,
    )
    assert result.payload["pmid_count"] == 1
    row = result.payload["records"][0]
    assert row["doi"] == "10.1/x"
    assert row["full_text_url"] == "https://example.org/ft"
    assert paper_link_bundle(row)["pubmed_url"].endswith("/12345/")
