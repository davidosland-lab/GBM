import json
from pathlib import Path

CURATED_DIR = Path("data/training/curated_expansion")
ROUND7_PMIDS = {"27475281", "30113929", "32049286", "34228056", "36099112", "38445703"}


def test_round7_curated_fixtures_extend_pmid_coverage() -> None:
    evidence = _read_jsonl(CURATED_DIR / "evidence_round7.jsonl")
    entities = _read_jsonl(CURATED_DIR / "gold_entities_round7.jsonl")
    reviewed = _read_jsonl(CURATED_DIR / "gold_reviewed_queue_round7.jsonl")

    assert len(evidence) == 6
    assert len(entities) == 6
    assert len(reviewed) == 12  # 6 evidence_claim + 6 graph_relation
    assert {str(row["source_pmid"]) for row in evidence} == ROUND7_PMIDS
    assert {row["item_type"] for row in reviewed} == {"evidence_claim", "graph_relation"}
    # Round 7 must introduce brand-new PMIDs disjoint from every prior round so the
    # gold pack source-PMID count keeps moving toward the promotion threshold.
    prior_pmids: set[str] = set()
    for prior in CURATED_DIR.glob("evidence_*.jsonl"):
        if prior.name == "evidence_round7.jsonl":
            continue
        prior_pmids |= {str(row["source_pmid"]) for row in _read_jsonl(prior)}
    assert ROUND7_PMIDS.isdisjoint(prior_pmids)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
