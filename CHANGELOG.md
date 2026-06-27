# Changelog

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Unreleased

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
