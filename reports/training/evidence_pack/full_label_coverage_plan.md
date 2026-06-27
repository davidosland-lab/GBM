# Full Evidence Label Coverage Plan

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Current evidence smoke labels: `0`, `1`
- Full evidence scaffold labels: `0`, `1`, `2`, `3`, `4`, `5`
- Current full-label gap: `2`, `3`, `4`, `5`

## Acceptance Criteria

- Curate source-backed examples for labels `2`, `3`, `4`, and `5`.
- Rebuild the evidence pack so train and validation splits include the full label set expected by `configs/training/gbmbert_evidence_pubmedbert.json`.
- Keep the smoke evidence config current until the full evidence config passes the default config suite without scaffold status.
- Preserve PMID provenance and the research-use warning on all generated rows.

## Promotion Rule

Do not promote the full evidence config from `governance_profile=scaffold` to `governance_profile=current` until the local pack label map and split contents cover labels `0` through `5`.

