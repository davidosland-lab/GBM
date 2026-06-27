# Changelog

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Unreleased

- Added a canonical local verification command, `gbmbert-verify-local`, that runs pytest, pip check, scope drift, training governance, platform regression, and artifact indexing in one ordered path.
- Added `gbmbert-run-strict-training-governance` for audit runs that treat scaffold training gaps as findings under `reports/training/governance_strict`.
- Added a current NER smoke config aligned to the populated local NER smoke splits while retaining the broader NER config as a scaffold.
- Added tracked planning artifacts for gold-pack expansion and full evidence-label coverage.
- Added an artifact policy describing which generated outputs are tracked and which remain reproducible local byproducts.

