import json
from pathlib import Path

from gbmbert.adjudication import build_adjudication_report


def test_adjudication_compares_entity_span_label_fields(tmp_path: Path) -> None:
    r1 = tmp_path / "r1.jsonl"
    r2 = tmp_path / "r2.jsonl"
    shared = {
        "item_id": "entity_span:1:0:0:11",
        "source_pmid": "1",
        "text": "mesenchymal",
        "label": "CELL_STATE",
        "start": 0,
        "end": 11,
        "review_status": "accepted",
    }
    r1.write_text(json.dumps(shared) + "\n", encoding="utf-8")
    divergent = {
        **shared,
        "review_status": "corrected",
        "corrected_label": "UNKNOWN",
        "corrected_start": 0,
        "corrected_end": 11,
    }
    r2.write_text(json.dumps(divergent) + "\n", encoding="utf-8")

    report = build_adjudication_report([r1, r2])
    assert report.compared_item_count == 1
    assert report.conflicted_item_count == 1
    fields = {conflict.field for conflict in report.conflicts}
    # accepted vs corrected surfaces on review_status; corrected_* only conflicts when both sides set it
    assert "review_status" in fields
