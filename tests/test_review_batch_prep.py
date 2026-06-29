import json
import subprocess
from pathlib import Path

from gbmbert.training.review_batch_prep import (
    PENDING_STATUS,
    build_prep_commands,
    finalize_review_batch,
    run_review_batch_prep,
)


def test_build_prep_commands_offline_lexicon_chain(tmp_path: Path) -> None:
    commands = build_prep_commands(
        round_number=8,
        pubmed_jsonl=tmp_path / "pubmed.jsonl",
        staging_dir=tmp_path / "stage",
        reviewer="david",
    )
    names = [name for name, _ in commands]

    # No query pack -> no search step; lexicon entity mode is used.
    assert names == ["literature_pipeline_lexicon", "export_review_queue", "init_reviewed_queue"]
    pipeline_cmd = dict(commands)["literature_pipeline_lexicon"]
    assert "--entity-mode" in pipeline_cmd and "lexicon" in pipeline_cmd
    init_cmd = dict(commands)["init_reviewed_queue"]
    assert init_cmd[-2:] == ["--reviewer", "david"]


def test_build_prep_commands_includes_search_when_query_pack(tmp_path: Path) -> None:
    commands = build_prep_commands(
        round_number=8,
        pubmed_jsonl=tmp_path / "pubmed.jsonl",
        staging_dir=tmp_path / "stage",
        reviewer="david",
        query_pack="pubmed_gbm_v1",
    )
    assert [name for name, _ in commands][0] == "search_pubmed"


def test_run_prep_writes_skeleton_and_instructions(tmp_path: Path) -> None:
    staging = tmp_path / "stage"

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        # Emulate the lexicon pipeline writing its entities output.
        if "gbmbert-run-pipeline" in command[0] or command[0] == "gbmbert-run-pipeline":
            (staging / "pipeline").mkdir(parents=True, exist_ok=True)
            (staging / "pipeline" / "entities.jsonl").write_text(
                json.dumps({"pmid": "1", "entities": []}) + "\n", encoding="utf-8"
            )
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    report = run_review_batch_prep(
        round_number=8,
        pubmed_jsonl=tmp_path / "pubmed.jsonl",
        staging_dir=staging,
        reviewer="david",
        runner=runner,
    )

    assert report.passed is True
    assert Path(report.entities_path).exists()
    assert Path(report.instructions_path).exists()
    assert "accepted` or `rejected" in Path(report.instructions_path).read_text(encoding="utf-8")


def test_finalize_blocks_when_rows_still_pending(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    _write_skeleton(
        staging,
        round_number=8,
        rows=[
            _evidence("1", tier=4, status=PENDING_STATUS),
            _evidence("2", tier=2, status="accepted"),
        ],
    )
    curated = tmp_path / "curated"

    report = finalize_review_batch(round_number=8, staging_dir=staging, curated_dir=curated)

    assert report.ready is False
    assert report.promoted is False
    assert report.pending_count == 1
    assert not (curated / "evidence_round8.jsonl").exists()  # nothing promoted


def test_finalize_promotes_when_complete(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    _write_skeleton(
        staging,
        round_number=8,
        rows=[
            _evidence("11", tier=4, status="accepted", notes="RCT primary endpoint"),
            _evidence("12", tier=1, status="rejected"),
            _relation("13", rel="ASSOCIATED_WITH", status="accepted"),
        ],
    )
    curated = tmp_path / "curated"

    report = finalize_review_batch(round_number=8, staging_dir=staging, curated_dir=curated)

    assert report.ready is True
    assert report.promoted is True
    assert report.accepted_evidence == 1
    assert report.accepted_relations == 1
    assert report.rejected_count == 1
    # Only accepted rows enter the corpus; the derived evidence file has the accepted tier.
    evidence = [json.loads(line) for line in (curated / "evidence_round8.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(evidence) == 1
    assert evidence[0]["label"] == 4
    assert evidence[0]["source_pmid"] == "11"
    reviewed = [json.loads(line) for line in (curated / "gold_reviewed_queue_round8.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {r["review_status"] for r in reviewed} == {"accepted"}


def test_finalize_uses_corrected_tier(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    row = _evidence("21", tier=2, status="accepted")
    row["corrected_evidence_tier"] = 5
    _write_skeleton(staging, round_number=9, rows=[row])
    curated = tmp_path / "curated"

    report = finalize_review_batch(round_number=9, staging_dir=staging, curated_dir=curated)

    assert report.promoted is True
    evidence = [json.loads(line) for line in (curated / "evidence_round9.jsonl").read_text(encoding="utf-8").splitlines()]
    assert evidence[0]["label"] == 5  # corrected tier wins over the original


def _evidence(pmid: str, *, tier: int, status: str, notes: str = "note") -> dict:
    return {
        "item_id": f"evidence:{pmid}",
        "item_type": "evidence_claim",
        "source_pmid": pmid,
        "evidence_tier": tier,
        "corrected_evidence_tier": None,
        "text": f"Finding for {pmid}.",
        "relation_type": "",
        "review_status": status,
        "reviewer": "david",
        "review_notes": notes,
    }


def _relation(pmid: str, *, rel: str, status: str) -> dict:
    return {
        "item_id": f"relation:{pmid}",
        "item_type": "graph_relation",
        "source_pmid": pmid,
        "evidence_tier": 0,
        "relation_type": rel,
        "corrected_relation_type": "",
        "head": "a",
        "tail": "b",
        "text": "relation text",
        "review_status": status,
        "reviewer": "david",
        "review_notes": "note",
    }


def _write_skeleton(staging: Path, *, round_number: int, rows: list[dict]) -> None:
    staging.mkdir(parents=True, exist_ok=True)
    (staging / f"gold_reviewed_queue_round{round_number}.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    (staging / f"gold_entities_round{round_number}.jsonl").write_text(
        json.dumps({"pmid": rows[0]["source_pmid"], "entities": []}) + "\n", encoding="utf-8"
    )
