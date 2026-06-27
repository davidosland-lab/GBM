from pathlib import Path
from urllib.parse import parse_qs

from gbmbert.knowledge_graph.explorer import (
    DEFAULT_BASELINE_DATA,
    EXPLORER_HTML,
    GraphExplorerService,
    build_arg_parser,
    graph_artifacts_from_index,
    _neighborhood_params,
    load_graph_records,
    resolve_graph_artifact,
)
from gbmbert.knowledge_graph.schema import EvidenceTier, GraphRelation, KnowledgeGraphRecord, NodeLabel, RelationType
from gbmbert.knowledge_graph.schema import GraphNode
from gbmbert.knowledge_graph.trials import ClinicalTrialGraphRecord, TrialGraphRelation


SAMPLE_PATH = Path("data/examples/graph_records_sample.jsonl")


def test_load_graph_records_reads_sample_fixture() -> None:
    records = load_graph_records(SAMPLE_PATH)

    assert len(records) == 2
    assert records[0].pmid == "29097493"


def test_load_graph_records_reads_trial_graph_fixture(tmp_path: Path) -> None:
    trial_path = tmp_path / "trial_graph_records.jsonl"
    trial = GraphNode(label=NodeLabel.TRIAL, key_value="NCT12345678")
    disease = GraphNode(label=NodeLabel.DISEASE, key_value="Glioblastoma")
    record = ClinicalTrialGraphRecord(
        nct_id="NCT12345678",
        trial_properties=trial.keyed_properties(),
        nodes=[disease],
        relations=[
            TrialGraphRelation(
                head=trial,
                relation=RelationType.ASSOCIATED_WITH,
                tail=disease,
                source_id="NCT12345678",
                properties={
                    "source_url": "https://clinicaltrials.gov/study/NCT12345678",
                    "registry_field": "condition",
                },
            )
        ],
    )
    trial_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    service = GraphExplorerService.from_jsonl(trial_path)
    inspection = service.inspection()
    graph = service.neighborhood(relation_types=[RelationType.ASSOCIATED_WITH])

    assert inspection["counts"]["labels"]["Trial"] == 1
    assert inspection["counts"]["relationships"] == 1
    assert graph["edges"][0]["source_ids"] == ["NCT12345678"]


def test_explorer_parser_supports_baseline_data_mode() -> None:
    args = build_arg_parser().parse_args(["--baseline-data"])

    assert args.baseline_data is True
    assert DEFAULT_BASELINE_DATA.as_posix().endswith("ncbi_env_smoke_pipeline/graph_records.jsonl")


def test_graph_artifacts_from_index_selects_graph_jsonl(tmp_path: Path) -> None:
    graph_path = tmp_path / "trial_graph_records.jsonl"
    index_path = tmp_path / "artifact_index.json"
    graph_path.write_text("", encoding="utf-8")
    index_path.write_text(
        """
        {
          "artifacts": [
            {"path": "%s", "artifact_type": "trial_graph_records", "category": "processed"},
            {"path": "data/processed/evidence_overlay_graph_records.jsonl", "artifact_type": "evidence_overlay_graph_records", "category": "processed"},
            {"path": "reports/graph/quality.md", "artifact_type": "graph_quality_report", "category": "graph_report"}
          ]
        }
        """
        % str(graph_path).replace("\\", "\\\\"),
        encoding="utf-8",
    )

    artifacts = graph_artifacts_from_index(index_path)
    resolved = resolve_graph_artifact(index_path, "trial_graph_records")

    assert artifacts[0]["artifact_type"] == "trial_graph_records"
    assert any(item["artifact_type"] == "evidence_overlay_graph_records" for item in artifacts)
    assert resolved == graph_path


def test_sample_inspection_returns_counts_for_dashboard() -> None:
    service = GraphExplorerService.from_jsonl(SAMPLE_PATH)

    inspection = service.inspection()

    assert inspection["counts"]["nodes"] == 6
    assert inspection["counts"]["relationships"] == 6
    assert inspection["counts"]["labels"]["Paper"] == 2
    assert inspection["counts"]["relation_types"]["MENTIONS"] == 4
    assert inspection["evidence_tiers"] == [
        {"tier": 0, "count": 4},
        {"tier": 1, "count": 1},
        {"tier": 3, "count": 1},
    ]


def test_sample_metadata_returns_schema_options_with_active_counts() -> None:
    service = GraphExplorerService.from_jsonl(SAMPLE_PATH)

    metadata = service.metadata()

    biomarker = next(item for item in metadata["node_labels"] if item["value"] == "Biomarker")
    mentions = next(item for item in metadata["relation_types"] if item["value"] == "MENTIONS")
    hypothesis = next(item for item in metadata["evidence_tiers"] if item["value"] == 0)
    assert biomarker["count"] == 1
    assert mentions["count"] == 4
    assert hypothesis["count"] == 4
    assert "Research-use only" in metadata["warning"]


def test_sample_neighborhood_filters_by_search_and_relation_type() -> None:
    service = GraphExplorerService.from_jsonl(SAMPLE_PATH)

    graph = service.neighborhood(
        search="focused ultrasound",
        relation_types=[RelationType.ENHANCES_DELIVERY_OF],
        min_evidence_tier=EvidenceTier.IN_VITRO,
    )

    assert len(graph["edges"]) == 1
    assert graph["edges"][0]["type"] == "ENHANCES_DELIVERY_OF"
    assert graph["edges"][0]["evidence_tier"] == 1
    assert graph["edges"][0]["properties"]["sentence"].startswith("Focused ultrasound")
    assert {node["label"] for node in graph["nodes"]} == {"focused ultrasound", "temozolomide"}


def test_sample_neighborhood_surfaces_evidence_overlay_metadata(tmp_path: Path) -> None:
    graph_path = tmp_path / "overlay_graph_records.jsonl"
    drug = GraphNode(label=NodeLabel.DRUG, key_value="temozolomide")
    outcome = GraphNode(label=NodeLabel.OUTCOME, key_value="response")
    record = KnowledgeGraphRecord(
        pmid="12345678",
        nodes=[drug, outcome],
        relations=[
            GraphRelation(
                head=drug,
                relation=RelationType.IMPROVES,
                tail=outcome,
                source_pmid="12345678",
                evidence_tier=EvidenceTier.RETROSPECTIVE_HUMAN,
                properties={
                    "evidence_overlay_source": "curated_gbmbert_prediction",
                    "evidence_overlay_original_tier": 1,
                    "evidence_overlay_tier": 3,
                    "evidence_overlay_item_id": "prediction:12345678:1",
                    "evidence_overlay_checkpoint": "gbmbert_evidence_v1",
                    "evidence_overlay_review_status": "accepted",
                },
            )
        ],
    )
    graph_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")
    service = GraphExplorerService.from_jsonl(graph_path)

    graph = service.neighborhood(relation_types=[RelationType.IMPROVES])
    overlay_graph = service.neighborhood(relation_types=[RelationType.IMPROVES], overlay_only=True, tier_changed_only=True)
    summary = service.node_summary(NodeLabel.DRUG, "temozolomide")

    assert graph["edges"][0]["evidence_overlay"]["original_tier"] == 1
    assert graph["edges"][0]["evidence_overlay"]["overlaid_tier"] == 3
    assert graph["edges"][0]["evidence_overlay"]["tier_changed"] is True
    assert graph["edges"][0]["curation_links"][0]["value"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    assert any(link["value"] == "prediction:12345678:1" for link in graph["edges"][0]["curation_links"])
    assert len(overlay_graph["edges"]) == 1
    assert graph["edges"][0]["evidence_overlay"]["checkpoint"] == "gbmbert_evidence_v1"
    assert summary["relations"][0]["evidence_overlay"]["review_status"] == "accepted"
    assert summary["relations"][0]["curation_links"][0]["label"] == "PubMed 12345678"


def test_sample_neighborhood_includes_paper_mention_edges() -> None:
    service = GraphExplorerService.from_jsonl(SAMPLE_PATH)

    graph = service.neighborhood(search="MGMT", relation_types=[RelationType.MENTIONS])

    assert len(graph["edges"]) == 2
    assert {edge["type"] for edge in graph["edges"]} == {"MENTIONS"}
    assert {edge["source_pmids"][0] for edge in graph["edges"]} == {"29097493"}


def test_sample_node_summary_returns_relations_and_pmids() -> None:
    service = GraphExplorerService.from_jsonl(SAMPLE_PATH)

    summary = service.node_summary(NodeLabel.BIOMARKER, "MGMT methylation")

    assert summary["node"]["name"] == "MGMT methylation"
    assert summary["relations"][0]["relation"] == "PREDICTS"
    assert summary["relations"][0]["source_pmids"] == ["29097493"]


def test_neighborhood_params_parse_query_strings() -> None:
    params = parse_qs(
        "search=MGMT&node_label=Biomarker&relation_type=PREDICTS"
        "&min_evidence_tier=3&depth=2&min_citations=1&limit=50&overlay_only=true&tier_changed_only=1"
    )

    parsed = _neighborhood_params(params)

    assert parsed["search"] == "MGMT"
    assert parsed["node_labels"] == [NodeLabel.BIOMARKER]
    assert parsed["relation_types"] == [RelationType.PREDICTS]
    assert parsed["min_evidence_tier"] == EvidenceTier.RETROSPECTIVE_HUMAN
    assert parsed["depth"] == 2
    assert parsed["limit"] == 50
    assert parsed["overlay_only"] is True
    assert parsed["tier_changed_only"] is True


def test_explorer_html_contains_required_mount_points() -> None:
    assert "GBM-AI Knowledge Graph Explorer" in EXPLORER_HTML
    assert 'id="graph"' in EXPLORER_HTML
    assert 'id="evidence-legend"' in EXPLORER_HTML
    assert "/api/metadata" in EXPLORER_HTML
    assert "/api/neighborhood" in EXPLORER_HTML


def test_explorer_html_styles_edges_by_evidence_tier() -> None:
    assert "evidenceTierStyles" in EXPLORER_HTML
    assert "stroke-dasharray" in EXPLORER_HTML
    assert "evidenceTierStyle(edge.evidence_tier)" in EXPLORER_HTML
    assert "tier ${item.value}" in EXPLORER_HTML


def test_explorer_html_supports_edge_provenance_drilldown() -> None:
    assert "data-edge-index" in EXPLORER_HTML
    assert "renderEdgeDetails(edge)" in EXPLORER_HTML
    assert "Edge Provenance" in EXPLORER_HTML
    assert "Source Sentence" in EXPLORER_HTML
    assert "evidence_overlay" in EXPLORER_HTML
    assert "Overlay Checkpoint" in EXPLORER_HTML
    assert "Curation Links" in EXPLORER_HTML
    assert 'id="overlay-only"' in EXPLORER_HTML
    assert 'id="tier-changed-only"' in EXPLORER_HTML
    assert "Tier Changed" in EXPLORER_HTML
