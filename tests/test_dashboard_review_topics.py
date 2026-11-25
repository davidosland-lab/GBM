import json
from pathlib import Path

from gbmbert.dashboard.review_topics import (
    DEFAULT_REVIEW_TOPIC,
    REVIEW_TOPICS,
    active_review_topic,
    get_review_topic,
    review_topic_for_query_pack,
    review_topic_from_label,
    review_topic_keys,
)
from gbmbert.ingest.query_packs import list_query_packs

ROOT = Path(__file__).resolve().parents[1]


class _FakeStreamlit:
    def __init__(self, **state: object) -> None:
        self.session_state = dict(state)


def test_registry_defaults_to_the_gallbladder_review() -> None:
    assert DEFAULT_REVIEW_TOPIC.key == "gallbladder"
    assert DEFAULT_REVIEW_TOPIC.console_title == "Gallbladder and Gallstone Research Review"


def test_registry_keeps_the_spinal_fusion_review_available() -> None:
    assert "spinal_fusion_neuropathy" in review_topic_keys()
    assert get_review_topic("spinal_fusion_neuropathy").query_pack == "pubmed_spinal_fusion_neuropathy_v1"


def test_unknown_topic_keys_and_labels_fall_back_to_the_default() -> None:
    assert get_review_topic("not-a-topic") is DEFAULT_REVIEW_TOPIC
    assert get_review_topic(None) is DEFAULT_REVIEW_TOPIC
    assert review_topic_from_label("Not a label") is DEFAULT_REVIEW_TOPIC


def test_active_review_topic_reads_session_state() -> None:
    assert active_review_topic(_FakeStreamlit()) is DEFAULT_REVIEW_TOPIC
    selected = active_review_topic(_FakeStreamlit(review_topic_key="spinal_fusion_neuropathy"))
    assert selected.key == "spinal_fusion_neuropathy"


def test_review_topic_for_query_pack_only_claims_owned_packs() -> None:
    assert review_topic_for_query_pack("pubmed_gallbladder_v1") is DEFAULT_REVIEW_TOPIC
    assert review_topic_for_query_pack("pubmed_gbm_v1") is None


def test_every_topic_points_at_artifacts_that_exist() -> None:
    packs = set(list_query_packs())
    for topic in REVIEW_TOPICS:
        assert topic.query_pack in packs, topic.key
        for relative in (topic.lexicon_path, topic.schema_path, topic.runbook_path):
            assert (ROOT / relative).exists(), f"{topic.key}: {relative}"
        assert topic.graph_jsonl.startswith(topic.processed_dir)


def test_every_topic_review_schema_is_research_use_only() -> None:
    for topic in REVIEW_TOPICS:
        schema = json.loads((ROOT / topic.schema_path).read_text(encoding="utf-8"))
        assert schema["research_use_only"] is True
        assert schema["clinical_validity_claimed"] is False


def test_topic_radio_label_wins_over_stale_topic_key() -> None:
    st = _FakeStreamlit(
        review_topic_label="Spinal fusion neuropathy review",
        review_topic_key="gallbladder",
    )

    assert active_review_topic(st).key == "spinal_fusion_neuropathy"
