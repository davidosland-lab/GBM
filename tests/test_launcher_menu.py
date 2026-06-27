from pathlib import Path


def test_launcher_menu_lists_operational_commands() -> None:
    text = Path("launcher_menu.bat").read_text(encoding="utf-8")

    assert "Run full PubMed pipeline" in text
    assert "Build graph quality report" in text
    assert "Export review queue" in text
    assert "Initialize reviewed queue scaffold" in text
    assert "Summarize reviewed queue" in text
    assert "gbmbert-init-reviewed-queue.exe" in text
    assert "gbmbert-reviewed-queue-summary.exe" in text
    assert "--report-markdown-output" in text
    assert "gbmbert-audit-graph-provenance.exe" in text
    assert "gbmbert-export-curated-graph.exe" in text
    assert "gbmbert-curation-diff.exe" in text
    assert "gbmbert-export-annotation-dataset.exe" in text
    assert "gbmbert-annotation-dataset-quality.exe" in text
    assert "gbmbert-split-annotation-dataset.exe" in text
    assert "gbmbert-build-label-maps.exe" in text
    assert "gbmbert-build-dataset-card.exe" in text
    assert "gbmbert-baseline-report.exe" in text
    assert "gbmbert-build-experiment-manifest.exe" in text
    assert "gbmbert-register-checkpoint.exe" in text
    assert "gbmbert-train.exe" in text
    assert "gbmbert-score-evidence.exe" in text
    assert "gbmbert-build-model-card.exe" in text
    assert "gbmbert-run-training-smoke.exe" in text
    assert "gbmbert-export-prediction-review-queue.exe" in text
    assert "gbmbert-init-reviewed-prediction-queue.exe" in text
    assert "gbmbert-prediction-review-summary.exe" in text
    assert "gbmbert-import-prediction-review-csv.exe" in text
    assert "gbmbert-prediction-quality-report.exe" in text
    assert "gbmbert-audit-curated-evidence.exe" in text
    assert "gbmbert-export-curated-evidence.exe" in text
    assert "gbmbert-apply-evidence-overlay.exe" in text
    assert "gbmbert-export-active-learning-candidates.exe" in text
    assert "gbmbert-overlay-diff.exe" in text
    assert "gbmbert-overlay-load-guard.exe" in text
    assert "gbmbert-run-curation-smoke-workflow.exe" in text
    assert "gbmbert-build-curation-handoff.exe" in text
    assert "gbmbert-validate-curation-handoff.exe" in text
    assert "gbmbert-register-curation-run.exe" in text
    assert "gbmbert-search-curated-evidence.exe" in text
    assert "gbmbert-plan-active-learning-batches.exe" in text
    assert "gbmbert-revert-evidence-overlay.exe" in text
    assert "gbmbert-run-curation-regression-pack.exe" in text
    assert "gbmbert-browse-curation-runs.exe" in text
    assert "gbmbert-artifact-detail.exe" in text
    assert "gbmbert-active-learning-batch-status.exe" in text
    assert "gbmbert-export-active-learning-batch-csv.exe" in text
    assert "gbmbert-import-active-learning-batch-csv.exe" in text
    assert "gbmbert-promote-evidence-overlay.exe" in text
    assert "gbmbert-relation-extraction-audit.exe" in text
    assert "gbmbert-scope-drift-monitor.exe" in text
    assert "gbmbert-platform-regression.exe" in text
    assert "gbmbert-verify-local.exe" in text
    assert "gbmbert-build-gold-seed-dataset.exe" in text
    assert "gbmbert-adjudication-report.exe" in text
    assert "gbmbert-normalize-graph-entities.exe" in text
    assert "gbmbert-enrich-relation-qualifiers.exe" in text
    assert "gbmbert-training-readiness-report.exe" in text
    assert "gbmbert-split-by-pmid.exe" in text
    assert "gbmbert-repair-evidence-labels.exe" in text
    assert "gbmbert-build-gold-training-pack.exe" in text
    assert "gbmbert-build-relation-negatives.exe" in text
    assert "gbmbert-relation-dataset-quality.exe" in text
    assert "gbmbert-merge-relation-pack.exe" in text
    assert "gbmbert-build-relation-training-pack.exe" in text
    assert "gbmbert-build-evidence-training-pack.exe" in text
    assert "gbmbert-review-training-config.exe" in text
    assert "gbmbert-compare-training-packs.exe" in text
    assert "gbmbert-audit-model-registry.exe" in text
    assert "gbmbert-run-training-governance-suite.exe" in text
    assert "gbmbert-run-strict-training-governance.exe" in text
    assert "gbmbert-run-smoke-baseline.exe" in text
    assert "--artifact-index" in text
    assert "--baseline-data" in text
    assert "Build artifact index" in text
    assert "Run preflight checks" in text
