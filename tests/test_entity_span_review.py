import json
from pathlib import Path

from gbmbert.training.entity_span_review import (
    apply_entity_span_reviews,
    export_entity_span_review_queue,
)
from gbmbert.training.gold_seed import _ner_rows


def test_entity_span_export_and_apply_roundtrip(tmp_path: Path) -> None:
    entities = tmp_path / "entities.jsonl"
    entities.write_text(
        json.dumps(
            {
                "pmid": "123",
                "text": "mesenchymal GBM invasion",
                "entities": [
                    {"text": "mesenchymal", "label": "CELL_STATE", "start": 0, "end": 11, "confidence": 0.8},
                    {"text": "invasion", "label": "CELL_STATE", "start": 16, "end": 24, "confidence": 0.7},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    review_jsonl = tmp_path / "span_review.jsonl"
    report = export_entity_span_review_queue(
        entities_jsonl=entities,
        jsonl_output=review_jsonl,
        csv_output=tmp_path / "span_review.csv",
        reviewer="tester",
    )
    assert report.span_count == 2
    assert report.document_count == 1
    assert (tmp_path / "span_review.csv").exists()

    rows = [json.loads(line) for line in review_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows[0]["review_status"] = "accepted"
    rows[1]["review_status"] = "corrected"
    rows[1]["corrected_label"] = "UNKNOWN"
    rows[1]["corrected_text"] = "invasion"
    rows[1]["corrected_start"] = 16
    rows[1]["corrected_end"] = 24
    review_jsonl.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    out = tmp_path / "applied.jsonl"
    applied = apply_entity_span_reviews(review_jsonl=review_jsonl, entities_output=out)
    assert applied.ready is True
    assert applied.accepted_span_count == 2
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(docs) == 1
    labels = {entity["label"] for entity in docs[0]["entities"]}
    assert labels == {"CELL_STATE", "UNKNOWN"}


def test_entity_span_apply_blocks_pending(tmp_path: Path) -> None:
    review = tmp_path / "pending.jsonl"
    review.write_text(
        json.dumps(
            {
                "item_id": "entity_span:1:0:0:5",
                "source_pmid": "1",
                "text": "hello",
                "label": "UNKNOWN",
                "start": 0,
                "end": 5,
                "context_text": "hello world",
                "review_status": "pending",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "entities.jsonl"
    report = apply_entity_span_reviews(review_jsonl=review, entities_output=out, require_complete=True)
    assert report.ready is False
    assert report.pending_span_count == 1
    assert not out.exists()


def test_ner_rows_dedupe_identical_spans(tmp_path: Path) -> None:
    path = tmp_path / "dup_entities.jsonl"
    entity = {
        "text": "PI3K",
        "label": "PATHWAY",
        "start": 10,
        "end": 14,
        "confidence": 0.9,
        "normalized_text": "pi3k",
    }
    doc = {"pmid": "999", "entities": [entity, {**entity, "confidence": 0.8}]}
    path.write_text(json.dumps(doc) + "\n" + json.dumps(doc) + "\n", encoding="utf-8")
    rows = _ner_rows(path)
    assert len(rows) == 1
    assert rows[0]["label"] == "PATHWAY"
