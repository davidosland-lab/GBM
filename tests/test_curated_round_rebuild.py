import json
import subprocess
from pathlib import Path

from gbmbert.training.curated_round_rebuild import (
    build_rebuild_commands,
    discover_curated_rounds,
    run_curated_round_rebuild,
)


def test_discover_curated_rounds_orders_base_then_numbered(tmp_path: Path) -> None:
    _touch(tmp_path / "evidence_full_label.jsonl")
    _touch(tmp_path / "gold_entities.jsonl")
    _touch(tmp_path / "gold_reviewed_queue.jsonl")
    for n in (2, 3):
        _touch(tmp_path / f"evidence_round{n}.jsonl")
        _touch(tmp_path / f"gold_entities_round{n}.jsonl")
        _touch(tmp_path / f"gold_reviewed_queue_round{n}.jsonl")

    rounds, warnings = discover_curated_rounds(tmp_path)

    assert [r.round_number for r in rounds] == [1, 2, 3]
    assert warnings == []
    assert rounds[0].evidence.endswith("evidence_full_label.jsonl")
    assert rounds[2].reviewed.endswith("gold_reviewed_queue_round3.jsonl")


def test_discover_curated_rounds_warns_on_partial_round(tmp_path: Path) -> None:
    _touch(tmp_path / "evidence_full_label.jsonl")
    _touch(tmp_path / "gold_entities.jsonl")
    _touch(tmp_path / "gold_reviewed_queue.jsonl")
    # Round 2 evidence present but entity/reviewed missing -> partial, excluded.
    _touch(tmp_path / "evidence_round2.jsonl")

    rounds, warnings = discover_curated_rounds(tmp_path)

    assert [r.round_number for r in rounds] == [1]
    assert any("round 2 is missing files" in w for w in warnings)


def test_build_rebuild_commands_spans_every_round_and_stage(tmp_path: Path) -> None:
    _touch(tmp_path / "evidence_full_label.jsonl")
    _touch(tmp_path / "gold_entities.jsonl")
    _touch(tmp_path / "gold_reviewed_queue.jsonl")
    _touch(tmp_path / "evidence_round2.jsonl")
    _touch(tmp_path / "gold_entities_round2.jsonl")
    _touch(tmp_path / "gold_reviewed_queue_round2.jsonl")
    rounds, _ = discover_curated_rounds(tmp_path)

    commands = build_rebuild_commands(rounds, import_dir="data/training/curated_import")
    by_name = {name: cmd for name, cmd in commands}

    # Every expected stage is present and ordered import -> ... -> contract.
    assert [name for name, _ in commands][0] == "curated_fixture_import"
    assert [name for name, _ in commands][-1] == "governance_detail_contract"
    for stage in (
        "gold_seed",
        "gold_training_pack",
        "evidence_training_pack",
        "relation_training_pack",
        "gold_pack_promotion_review",
        "gold_pack_promotion_plan",
        "training_governance_suite",
        "strict_training_governance",
    ):
        assert stage in by_name
    # The import command carries both rounds' fixture flags.
    import_cmd = by_name["curated_fixture_import"]
    assert import_cmd.count("--evidence-jsonl") == 2
    assert import_cmd.count("--reviewed-queue-jsonl") == 2
    assert "--no-copy" in import_cmd


def test_run_curated_round_rebuild_uses_injected_runner(tmp_path: Path) -> None:
    _touch(tmp_path / "evidence_full_label.jsonl")
    _touch(tmp_path / "gold_entities.jsonl")
    _touch(tmp_path / "gold_reviewed_queue.jsonl")
    seen: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    report = run_curated_round_rebuild(curated_dir=tmp_path, runner=runner)

    assert report.passed is True
    assert report.round_count == 1
    assert report.step_count == len(seen) == 20
    assert report.failed_step_count == 0


def test_run_curated_round_rebuild_marks_failure(tmp_path: Path) -> None:
    _touch(tmp_path / "evidence_full_label.jsonl")
    _touch(tmp_path / "gold_entities.jsonl")
    _touch(tmp_path / "gold_reviewed_queue.jsonl")

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        rc = 1 if "gbmbert-build-gold-training-pack" in command[0] else 0
        return subprocess.CompletedProcess(command, rc, stdout="boom", stderr="")

    report = run_curated_round_rebuild(curated_dir=tmp_path, runner=runner)

    assert report.passed is False
    assert report.failed_step_count == 1
    assert any("gold_training_pack failed" in w for w in report.warnings)


def test_run_curated_round_rebuild_no_rounds_is_not_passed(tmp_path: Path) -> None:
    report = run_curated_round_rebuild(curated_dir=tmp_path, runner=lambda c: subprocess.CompletedProcess(c, 0, "", ""))

    assert report.passed is False
    assert report.round_count == 0
    assert report.step_count == 0
    assert any("no complete curated rounds" in w for w in report.warnings)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
