import json
from pathlib import Path

from gbmbert.training.promotion_planning import (
    build_gold_pack_promotion_planning_report,
    format_gold_pack_promotion_planning_markdown,
)


def _review(tmp_path: Path) -> Path:
    review_path = tmp_path / "promotion.json"
    review_path.write_text(
        json.dumps(
            {
                "promotable": False,
                "source_pmid_delta": 7,
                "task_example_deltas": {"evidence": 20, "ner": 8, "relation": 0},
                "label_example_deltas": {
                    "evidence": {"0": 3, "1": 2, "2": 1},
                    "ner": {"GENE": 4},
                    "relation": {},
                },
            }
        ),
        encoding="utf-8",
    )
    return review_path


def test_promotion_planning_reports_task_delta_coverage(tmp_path: Path) -> None:
    report = build_gold_pack_promotion_planning_report(promotion_review=_review(tmp_path))

    # evidence: label-floor 6 of 20 -> 30% covered, 70% remaining raw volume.
    assert report.task_coverage["evidence"]["label_floor_coverage_pct"] == 30.0
    assert report.task_coverage["evidence"]["task_volume_remaining_pct"] == 70.0
    # ner: label-floor 4 of 8 -> 50%.
    assert report.task_coverage["ner"]["label_floor_coverage_pct"] == 50.0
    # relation: zero delta -> treated as fully covered, nothing remaining.
    assert report.task_coverage["relation"]["label_floor_coverage_pct"] == 100.0
    assert report.task_coverage["relation"]["task_volume_remaining_pct"] == 0.0


def test_promotion_planning_overall_coverage_ignores_zero_delta_tasks(tmp_path: Path) -> None:
    report = build_gold_pack_promotion_planning_report(promotion_review=_review(tmp_path))

    # numerator = min(6,20)+min(4,8)+min(0,0) = 10; denominator = 20+8+0 = 28.
    assert report.overall_label_floor_coverage_pct == round(10 / 28 * 100, 1)


def test_promotion_planning_markdown_surfaces_coverage(tmp_path: Path) -> None:
    report = build_gold_pack_promotion_planning_report(promotion_review=_review(tmp_path))

    markdown = format_gold_pack_promotion_planning_markdown(report)

    assert "Overall label-floor coverage of task deltas:" in markdown
    assert "### Task Delta Coverage" in markdown
    assert "covered by label-floor batches" in markdown
