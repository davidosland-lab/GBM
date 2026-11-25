"""Review-topic registry for the research operations console.

Each topic bundles the artifacts a literature review extension needs: a PubMed
query pack, an offline lexicon, a review schema, a runbook, and the local corpus
and graph paths the live runners default to.

Research-use only. Topics describe which literature is being organized. They do
not describe a clinical domain the platform is validated for.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewTopic:
    """A literature review extension the console can be pointed at."""

    key: str
    label: str
    console_title: str
    query_pack: str
    pubmed_jsonl: str
    processed_dir: str
    lexicon_path: str
    schema_path: str
    runbook_path: str
    sample_query: str
    sample_text: str
    sample_pmid: str

    @property
    def graph_jsonl(self) -> str:
        return f"{self.processed_dir}/graph_records.jsonl"


GALLBLADDER_TOPIC = ReviewTopic(
    key="gallbladder",
    label="Gallbladder and gallstone review",
    console_title="Gallbladder and Gallstone Research Review",
    query_pack="pubmed_gallbladder_v1",
    pubmed_jsonl="data/raw/pubmed_gallbladder_v1_2026-09-08.jsonl",
    processed_dir="data/processed/gallbladder_v1",
    lexicon_path="configs/extraction/lexicon_gallbladder_v1.json",
    schema_path="configs/extraction/gallbladder_review_schema.json",
    runbook_path="docs/GALLBLADDER_REVIEW.md",
    sample_query="laparoscopic cholecystectomy outcomes complications",
    sample_text=(
        "Laparoscopic cholecystectomy for acute cholecystitis is compared with delayed "
        "surgery, with reported outcomes including postoperative pain, length of stay, "
        "conversion to open surgery, bile duct injury, and post-cholecystectomy diarrhoea."
    ),
    sample_pmid="23989961",
)

SPINAL_FUSION_TOPIC = ReviewTopic(
    key="spinal_fusion_neuropathy",
    label="Spinal fusion neuropathy review",
    console_title="Spinal Fusion Neuropathy Research Review",
    query_pack="pubmed_spinal_fusion_neuropathy_v1",
    pubmed_jsonl="data/raw/pubmed_spinal_fusion_neuropathy_v1_2026-07-24.jsonl",
    processed_dir="data/processed/spinal_fusion_neuropathy_v1",
    lexicon_path="configs/extraction/lexicon_spinal_fusion_neuropathy_v1.json",
    schema_path="configs/extraction/spinal_fusion_neuropathy_review_schema.json",
    runbook_path="docs/SPINAL_FUSION_NEUROPATHY_REVIEW.md",
    sample_query="spinal fusion postoperative neuropathy",
    sample_text=(
        "Spinal fusion studies report postoperative radiculopathy, neuropathic pain, "
        "numbness, weakness, decompression, and revision surgery outcomes."
    ),
    sample_pmid="29097493",
)

REVIEW_TOPICS: tuple[ReviewTopic, ...] = (GALLBLADDER_TOPIC, SPINAL_FUSION_TOPIC)
DEFAULT_REVIEW_TOPIC: ReviewTopic = GALLBLADDER_TOPIC


def review_topic_keys() -> list[str]:
    """Return the registered review-topic keys in console order."""

    return [topic.key for topic in REVIEW_TOPICS]


def review_topic_labels() -> list[str]:
    """Return the registered review-topic labels in console order."""

    return [topic.label for topic in REVIEW_TOPICS]


def get_review_topic(key: str | None) -> ReviewTopic:
    """Look up a topic by key, falling back to the default topic."""

    for topic in REVIEW_TOPICS:
        if topic.key == key:
            return topic
    return DEFAULT_REVIEW_TOPIC


def review_topic_from_label(label: str | None) -> ReviewTopic:
    """Look up a topic by sidebar label, falling back to the default topic."""

    for topic in REVIEW_TOPICS:
        if topic.label == label:
            return topic
    return DEFAULT_REVIEW_TOPIC


def review_topic_for_query_pack(query_pack: str | None) -> ReviewTopic | None:
    """Return the topic that owns a query pack, or None for unowned packs."""

    for topic in REVIEW_TOPICS:
        if topic.query_pack == query_pack:
            return topic
    return None


def active_review_topic(st: object) -> ReviewTopic:
    """Resolve the topic currently selected in the Streamlit session.

    The topic radio's own widget state is checked first so the page title and
    defaults update on the same rerun as the selection, not the one after it.
    """

    session_state = getattr(st, "session_state", None)
    if session_state is None:
        return DEFAULT_REVIEW_TOPIC
    label = _session_value(session_state, "review_topic_label")
    for topic in REVIEW_TOPICS:
        if topic.label == label:
            return topic
    return get_review_topic(_session_value(session_state, "review_topic_key"))


def _session_value(session_state: object, key: str) -> object | None:
    try:
        return session_state.get(key)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - non-mapping session state
        return getattr(session_state, key, None)
