import json
from pathlib import Path

from gbmbert.ingest.query_packs import (
    PubMedQueryPack,
    annotate_records_with_query_pack,
    list_query_packs,
    load_query_pack,
    search_query_pack,
    unique_pmids,
)


def test_load_query_pack_reads_curated_pack() -> None:
    pack = load_query_pack("pubmed_gbm_v1")

    assert pack.name == "pubmed_gbm_v1"
    assert "glioblastoma MGMT methylation" in pack.queries


def test_list_query_packs_returns_available_pack_names() -> None:
    packs = list_query_packs()

    assert "pubmed_gbm_v1" in packs
    assert "pubmed_gbm_v2" in packs
    assert "pubmed_spinal_fusion_neuropathy_v1" in packs
    assert "pubmed_gallbladder_v1" in packs


def test_spinal_fusion_neuropathy_pack_is_research_scoped() -> None:
    pack = load_query_pack("pubmed_spinal_fusion_neuropathy_v1")

    assert "Research-use only" in pack.description
    assert pack.source == "docs/SPINAL_FUSION_NEUROPATHY_REVIEW.md"
    assert any("neuropath" in query.lower() for query in pack.queries)
    assert any("spinal fusion" in query.lower() for query in pack.queries)


def test_gallbladder_pack_is_research_scoped() -> None:
    pack = load_query_pack("pubmed_gallbladder_v1")

    assert "Research-use only" in pack.description
    assert pack.source == "docs/GALLBLADDER_REVIEW.md"
    assert any("gallstone" in query.lower() for query in pack.queries)
    assert any("cholecystectomy" in query.lower() for query in pack.queries)


def test_gallbladder_pack_covers_removal_and_recovery() -> None:
    queries = [query.lower() for query in load_query_pack("pubmed_gallbladder_v1").queries]

    assert any("cholecystectomy" in query and "complication" in query for query in queries)
    assert any("recovery" in query for query in queries)
    assert any("post-cholecystectomy" in query for query in queries)
    assert any("conservative management" in query or "guideline" in query for query in queries)


def test_search_query_pack_uses_supplied_search_function() -> None:
    pack = PubMedQueryPack(name="test", queries=["MGMT", "EGFR"])
    calls: list[tuple[str, int, str]] = []

    def fake_search(query: str, retmax: int, sort: str) -> list[str]:
        calls.append((query, retmax, sort))
        return ["1", "2"] if query == "MGMT" else ["2", "3"]

    results = search_query_pack(pack, retmax_per_query=5, sort="date", search_fn=fake_search)

    assert calls == [("MGMT", 5, "date"), ("EGFR", 5, "date")]
    assert unique_pmids(results) == ["1", "2", "3"]


def test_annotate_records_with_query_pack_preserves_matched_queries() -> None:
    pack = PubMedQueryPack(name="test", source="unit", queries=["MGMT", "EGFR"])
    records = [{"pmid": "1", "title": "A"}, {"pmid": "2", "title": "B"}]

    annotated = annotate_records_with_query_pack(
        records,
        pack=pack,
        search_results={"MGMT": ["1", "2"], "EGFR": ["2"]},
    )

    assert annotated[0]["query_pack"] == "test"
    assert annotated[0]["matched_queries"] == ["MGMT"]
    assert annotated[1]["matched_queries"] == ["EGFR", "MGMT"]


def test_load_query_pack_accepts_direct_path(tmp_path: Path) -> None:
    path = tmp_path / "custom.json"
    path.write_text(json.dumps({"name": "custom", "queries": ["glioblastoma"]}), encoding="utf-8")

    pack = load_query_pack(str(path))

    assert pack.name == "custom"
