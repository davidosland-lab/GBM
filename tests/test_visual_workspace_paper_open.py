"""Opening papers selected on the knowledge graph.

Research-use only. These checks cover link plumbing, not clinical content.
"""

from gbmbert.dashboard.paper_links import pmid_url
from gbmbert.dashboard.visual_workspace import (
    _graph_pmids,
    _paper_option_label,
    _visible_papers,
    visual_workspace_context,
    visual_workspace_html,
)

SAMPLE_GRAPH = "data/examples/graph_records_sample.jsonl"


class _FakeRecord:
    def __init__(self, pmid: str, **properties: object) -> None:
        self.pmid = pmid
        self.paper_properties = properties
        self.nodes: list[object] = []


def test_graph_pmids_reads_paper_nodes_claims_and_edges() -> None:
    payload = {
        "nodes": [
            {"labels": ["Paper"], "key_value": "111", "properties": {"pmid": "111"}},
            {"labels": ["Disease"], "key_value": "Gallstone", "properties": {}},
            {"labels": ["Claim"], "key_value": "Claim:333:0", "properties": {"source_id": "333"}},
        ],
        "edges": [
            {"source": "Paper:111", "target": "Disease:Gallstone", "source_pmids": ["222"], "properties": {}},
            {"source": "Paper:111", "target": "Disease:Gallstone", "properties": {"source_id": "111"}},
        ],
    }

    assert _graph_pmids(payload) == ["111", "333", "222"]


def test_graph_pmids_rejects_non_pmid_identifiers() -> None:
    payload = {
        "nodes": [{"labels": ["Trial"], "key_value": "NCT01234567", "properties": {}}],
        "edges": [{"source": "a", "target": "b", "source_pmids": ["", None, "not-a-pmid"], "properties": {}}],
    }

    assert _graph_pmids(payload) == []


def test_visible_papers_enrich_pmids_from_local_records() -> None:
    payload = {"nodes": [{"labels": ["Paper"], "key_value": "111", "properties": {"pmid": "111"}}], "edges": []}
    records = [_FakeRecord("111", title="Gallstone review", journal="Gut", publication_date="2021-Jul")]

    papers = _visible_papers(payload, records)

    assert len(papers) == 1
    assert papers[0]["title"] == "Gallstone review"
    assert papers[0]["publication_date"] == "2021-Jul"
    assert pmid_url(papers[0]["pmid"]) == "https://pubmed.ncbi.nlm.nih.gov/111/"


def test_visible_papers_keep_graph_only_pmids_without_a_local_record() -> None:
    payload = {"nodes": [{"labels": ["Paper"], "key_value": "999", "properties": {}}], "edges": []}

    papers = _visible_papers(payload, [])

    assert [item["pmid"] for item in papers] == ["999"]
    assert papers[0]["title"] == ""


def test_paper_option_label_leads_with_the_pmid() -> None:
    label = _paper_option_label({"pmid": "111", "title": "Gallstone review", "publication_date": "2021-Jul"})

    assert label.startswith("PMID 111")
    assert "2021" in label
    assert "Gallstone review" in label


def test_paper_option_label_survives_a_missing_local_title() -> None:
    label = _paper_option_label({"pmid": "111", "title": "", "publication_date": ""})

    assert label.startswith("PMID 111")
    assert "no title" in label


def test_workspace_context_exposes_papers_for_the_current_view() -> None:
    context = visual_workspace_context(graph_path=SAMPLE_GRAPH)

    assert context["papers"]
    assert all(item["pmid"].isdigit() for item in context["papers"])


def test_workspace_html_offers_pubmed_open_links_on_selection() -> None:
    html = visual_workspace_html(visual_workspace_context(graph_path=SAMPLE_GRAPH))

    assert "https://pubmed.ncbi.nlm.nih.gov/" in html
    assert "openTargets" in html
    assert "nodeSources" in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "dblclick" in html
    assert "Open in PubMed" in html


def test_paper_title_index_shortens_long_titles() -> None:
    from gbmbert.dashboard.visual_workspace import _paper_title_index

    index = _paper_title_index([{"pmid": "111", "title": "G" * 200}], max_chars=20)

    assert index["111"].endswith("...")
    assert len(index["111"]) == 20


def test_workspace_html_opens_every_source_paper_of_a_shared_entity() -> None:
    html = visual_workspace_html(visual_workspace_context(graph_path=SAMPLE_GRAPH))

    assert "paper_titles" in html
    assert "Open all " in html
    assert "?term=" in html


def test_stacked_workspace_puts_the_graph_before_the_rails() -> None:
    """A narrow embed must not push the 3D graph below the fold."""

    html = visual_workspace_html(visual_workspace_context(graph_path=SAMPLE_GRAPH))
    stacked = html.split("@media (max-width: 980px)", 1)[1].split("}\n  </style>", 1)[0]

    assert ".canvas-wrap { order: -2; }" in stacked
    assert ".detail { order: -1; }" in stacked
    assert ".rail { order: 0; }" in stacked
