# Changelog

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Unreleased

- Added a task-delta coverage view to the gold-pack promotion planning report: per-task label-floor coverage vs. remaining raw task volume, plus an overall coverage percentage. Scaffold-only and research-use-only.
- Added a seventh curated local curation round (six new source PMIDs) and rebuilt every report via the one-command orchestrator; the gold pack is now 48 evidence / 96 NER / 48 relation across 42 source PMIDs, still correctly below promotion thresholds.
- Added `gbmbert-rebuild-curated-rounds` (launcher `16BS`): a single observe-only command that discovers every curated expansion round and regenerates the full report chain (import, provenance diff, gold seed/pack, evidence/relation packs, governance, promotion review/planning, governance detail).
- Added a launcher path (`16BR`) for the full multi-batch curated import across every expansion round, matching the provenance-diff fixed file set.
- Surfaced the governance detail contract state in the compact CI Markdown summary and CI summary contract, keeping missing detail rows visible without implying readiness.
- Refined gold-pack promotion planning so label-balance batches report how they relate to the task-volume delta (label-floor total vs. remaining task volume).
- Added a sixth curated local curation round and rebuilt combined import, provenance, evidence, NER, relation, promotion, planning, CI, and governance reports from all six rounds.
- Added a fifth curated local curation round and rebuilt combined import, provenance, evidence, NER, relation, promotion, and governance reports from all five rounds.
- Added compact promotion-planning summary fields for remaining task examples, label examples, and source-PMID batches.
- Added a governance detail contract check that keeps required governance rows visible even when reports are missing.
- Added launcher shortcuts for promotion planning, governance detail export, and CI summary contract checks.
- Added a fourth curated local curation round and rebuilt combined import, provenance, evidence, NER, relation, promotion, and governance reports from all four rounds.
- Added a standalone dashboard governance detail export report for Markdown/JSON handoff review.
- Added a CI summary artifact contract check to keep required verification, governance, and promotion report families visible.
- Added a scaffold-only gold-pack promotion planning report that groups promotion deltas into future curation batches.
- Added promotion-review delta fields showing exact examples and source PMIDs still needed before any scaffold promotion review.
- Hardened the CI Markdown summary so missing or invalid required verification/governance reports fail the summary command.
- Added dashboard governance detail rows for training report paths, existence, and report status.
- Added a third curated local curation round and rebuilt combined import, evidence, NER, relation, promotion, and governance reports from all three rounds.
- Added a curated multi-batch provenance diff report that compares source files, PMIDs, tasks, labels, reviewers, and review statuses before training-pack rebuilds.
- Aligned strict label-drift checks to config-specific governance datasets so smoke configs are not compared against scaffold packs.
- Added a curated training fixture import validator for larger reviewed evidence, NER, and relation batches.
- Extended curated training fixture import to accept repeated evidence, entity, and reviewed-queue JSONL inputs and write combined JSONL outputs.
- Added reviewable gold-pack promotion thresholds in `configs/training/gold_pack_promotion_thresholds.json`.
- Added a compact CI Markdown summary report for local verification, artifact policy, launcher, governance, and promotion-review state.
- Refreshed the dashboard training context with label-drift, launcher, curated-import, and promotion-review governance status.
- Added a second curated local curation round and rebuilt evidence, NER, and relation gold-pack reports from the combined import.
- Added CI report upload for verification and governance artifacts.
- Added a non-interactive launcher menu structure check and wired it into local verification.
- Added a gold-pack promotion review with explicit thresholds that keep the minimal fixture scaffold-only.
- Expanded the curated local training fixtures to cover all evidence labels, broad NER labels, and relation labels across PMID-safe splits.
- Added tracked artifact policy enforcement and wired it into canonical local verification.
- Simplified `launcher_menu.bat` into workflow groups while preserving legacy command shortcuts, with a new launcher guide in `docs/LAUNCHER_MENU.md`.
- Added a canonical local verification command, `gbmbert-verify-local`, that runs pytest, pip check, scope drift, training governance, platform regression, and artifact indexing in one ordered path.
- Added `gbmbert-run-strict-training-governance` for audit runs that treat scaffold training gaps as findings under `reports/training/governance_strict`.
- Added a current NER smoke config aligned to the populated local NER smoke splits while retaining the broader NER config as a scaffold.
- Added tracked planning artifacts for gold-pack expansion and full evidence-label coverage.
- Added an artifact policy describing which generated outputs are tracked and which remain reproducible local byproducts.
