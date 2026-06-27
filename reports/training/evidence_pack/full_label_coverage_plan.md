# Full Evidence Label Coverage Plan

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Current evidence smoke labels: `0`, `1`
- Expanded local evidence labels: `0`, `1`, `2`, `3`, `4`, `5`
- Current full-label gap: none in the checked-in minimal curated fixture
- Current local fixture: 12 accepted evidence rows, with two rows for each label

## Acceptance Criteria

- Done: source-backed examples now cover labels `0` through `5`.
- Done: the evidence pack was rebuilt with PMID-safe train, validation, and test splits.
- Done: the full evidence config points at the rebuilt local evidence pack.
- Still required before promotion: expand beyond the minimal fixture and review whether `governance_profile=scaffold` can become `current`.
- Preserve PMID provenance and the research-use warning on all generated rows.

## Promotion Rule

Do not promote the full evidence config from `governance_profile=scaffold` to `governance_profile=current` based only on the minimal fixture. Promotion requires additional curated rows, governance review, and no training-readiness findings.

