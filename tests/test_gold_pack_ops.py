"""Tests for gold-pack ops status and sparse densify batch export."""

from __future__ import annotations

import json
from pathlib import Path

from gbmbert.training.gold_pack_ops import (
    build_gold_pack_ops_status,
    export_sparse_densify_dual_review_batch,
    format_gold_pack_ops_status_markdown,
    ops_status_main,
    sparse_densify_batch_main,
)


def test_gold_pack_ops_status_reports_soft_gaps_and_backlog(tmp_path: Path) -> None:
    split_dir = tmp_path / "splits"
    split_dir.mkdir(parents=True)
    _write_jsonl(
        split_dir / "evidence_train.jsonl",
        [{"label": "0", "source_pmid": "1", "text": "a"} for _ in range(5)]
        + [{"label": "1", "source_pmid": "2", "text": "b"} for _ in range(5)],
    )
    _write_jsonl(
        split_dir / "ner_train.jsonl",
        [{"label": "PATHWAY", "source_pmid": "1", "text": "mapk"} for _ in range(3)]
        + [{"label": "CELL_STATE", "source_pmid": "2", "text": "mesenchymal"} for _ in range(2)]
        + [{"label": "DISEASE", "source_pmid": "3", "text": "gbm"} for _ in range(30)],
    )
    _write_jsonl(
        split_dir / "relation_train.jsonl",
        [{"label": "IMPROVES", "source_pmid": "1", "text": "x"} for _ in range(6)]
        + [{"label": "NO_RELATION", "source_pmid": "2", "text": "y"} for _ in range(6)],
    )
    pack_report = tmp_path / "gold_training_pack.json"
    pack_report.write_text(
        json.dumps({"ready": True, "split_dir": str(split_dir)}),
        encoding="utf-8",
    )
    thresholds = tmp_path / "thresholds.json"
    thresholds.write_text(
        json.dumps(
            {
                "min_examples_per_task": 10,
                "min_examples_per_label": 2,
                "min_source_pmids": 2,
            }
        ),
        encoding="utf-8",
    )
    review_root = tmp_path / "review_batches" / "round33"
    review_root.mkdir(parents=True)
    _write_jsonl(
        review_root / "span_review_r1_round33.jsonl",
        [
            {"item_id": "1", "review_status": "pending", "label": "PATHWAY"},
            {"item_id": "2", "review_status": "accepted", "label": "PATHWAY"},
        ],
    )
    al_path = tmp_path / "active_learning_batches.jsonl"
    _write_jsonl(
        al_path,
        [
            {"item_id": "al1", "review_status": "pending"},
            {"item_id": "al2", "status": "accepted"},
        ],
    )

    report = build_gold_pack_ops_status(
        gold_pack_report=pack_report,
        threshold_config=thresholds,
        review_batch_root=tmp_path / "review_batches",
        active_learning_batch_paths=[al_path],
        soft_densify_floors={
            "ner": {"PATHWAY": 10, "CELL_STATE": 10},
            "relation": {"IMPROVES": 10},
        },
    )
    markdown = format_gold_pack_ops_status_markdown(report)

    assert report.pack_ready is True
    assert report.promotable is True
    assert report.task_counts["evidence"] == 10
    assert report.dual_review_pending_total == 1
    assert report.active_learning_pending_total == 1
    assert any(gap.label == "PATHWAY" and gap.delta == 7 for gap in report.soft_densify_gaps)
    assert any("soft densify" in action.lower() for action in report.next_actions)
    assert "Research-use only" in markdown
    assert "clinical decision-making" in markdown.lower()
    assert report.clinical_validity_claimed is False


def test_export_sparse_densify_batch_leaves_rows_pending(tmp_path: Path) -> None:
    entities = tmp_path / "data" / "training" / "curated_expansion" / "gold_entities_roundX.jsonl"
    entities.parent.mkdir(parents=True)
    docs = [
        {
            "pmid": "1001",
            "text": "MAPK pathway drives mesenchymal GBM.",
            "entities": [
                {"label": "PATHWAY", "text": "MAPK pathway", "start": 0, "end": 12},
                {"label": "CELL_STATE", "text": "mesenchymal", "start": 20, "end": 31},
            ],
        },
        {
            "pmid": "1002",
            "text": "Phase II trial of unknown agent.",
            "entities": [
                {"label": "TRIAL_PHASE", "text": "Phase II", "start": 0, "end": 8},
                {"label": "UNKNOWN", "text": "unknown agent", "start": 18, "end": 31},
            ],
        },
    ]
    _write_jsonl(entities, docs)

    report = export_sparse_densify_dual_review_batch(
        round_id=99,
        entities_glob="data/training/curated_expansion/gold_entities*.jsonl",
        output_dir=tmp_path / "data/research/review_batches/round99",
        max_spans_per_label=5,
        root=tmp_path,
    )
    r1_rows = _read_jsonl(Path(report.r1_jsonl))
    r2_rows = _read_jsonl(Path(report.r2_jsonl))

    assert report.span_count == 4
    assert report.pending_for_human is True
    assert all(row["review_status"] == "pending" for row in r1_rows)
    assert all(row["review_status"] == "pending" for row in r2_rows)
    assert Path(report.instructions_path).exists()
    assert "do not auto-accept" in Path(report.instructions_path).read_text(encoding="utf-8").lower()


def test_ops_status_cli_writes_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    split_dir = tmp_path / "splits"
    split_dir.mkdir()
    for task, label in (("evidence", "0"), ("ner", "GENE"), ("relation", "PREDICTS")):
        _write_jsonl(
            split_dir / f"{task}_train.jsonl",
            [{"label": label, "source_pmid": str(i), "text": "t"} for i in range(12)],
        )
    reports = tmp_path / "reports" / "training" / "gold_pack"
    reports.mkdir(parents=True)
    (reports / "gold_training_pack.json").write_text(
        json.dumps({"ready": True, "split_dir": str(split_dir)}),
        encoding="utf-8",
    )
    cfg = tmp_path / "thresholds.json"
    cfg.write_text(
        json.dumps(
            {"min_examples_per_task": 10, "min_examples_per_label": 2, "min_source_pmids": 2}
        ),
        encoding="utf-8",
    )
    out_json = reports / "gold_pack_ops_status.json"
    out_md = reports / "gold_pack_ops_status.md"
    code = ops_status_main(
        [
            "--gold-pack-report",
            str(reports / "gold_training_pack.json"),
            "--threshold-config",
            str(cfg),
            "--review-batch-root",
            str(tmp_path / "missing"),
            "--json-output",
            str(out_json),
            "--markdown-output",
            str(out_md),
        ]
    )
    assert code == 0
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert payload["task_counts"]["ner"] == 12
    assert out_md.exists()


def test_sparse_batch_cli_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    entities = tmp_path / "data" / "training" / "curated_expansion" / "gold_entities.jsonl"
    entities.parent.mkdir(parents=True)
    _write_jsonl(
        entities,
        [
            {
                "pmid": "9",
                "text": "EGFR pathway",
                "entities": [{"label": "PATHWAY", "text": "EGFR pathway", "start": 0, "end": 12}],
            }
        ],
    )
    code = sparse_densify_batch_main(
        [
            "--round",
            "77",
            "--max-spans-per-label",
            "3",
            "--json-output",
            str(tmp_path / "reports/training/gold_pack/sparse_densify_batch_round77.json"),
            "--markdown-output",
            str(tmp_path / "reports/training/gold_pack/sparse_densify_batch_round77.md"),
        ]
    )
    assert code == 0
    queue = tmp_path / "data/research/review_batches/round77/span_review_r1_round77.jsonl"
    assert queue.exists()
    assert all(row["review_status"] == "pending" for row in _read_jsonl(queue))


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
