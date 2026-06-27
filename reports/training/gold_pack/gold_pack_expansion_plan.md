# Gold Pack Expansion Plan

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Current status: not ready
- Current blockers: NER and relation examples are absent from the checked-in gold pack.
- Target use: broaden the local gold pack enough to support stable governance checks before any full training claim is made.

## Minimum Acceptance Targets

- Evidence: include examples across all intended evidence labels before promoting the full evidence config from scaffold to current.
- NER: include non-empty train, validation, and test rows with every current smoke NER label represented at least once.
- Relation: include positive relation examples and negative `NO_RELATION` examples across train, validation, and test splits.
- Splits: keep PMID separation between train, validation, and test.
- Provenance: preserve source PMID, source type, and the research-use warning on generated training rows.

## Implementation Order

1. Curate additional gold rows for NER and relation tasks.
2. Rebuild label maps and PMID-safe splits.
3. Re-run training readiness, pack comparison, provenance audit, and the default governance suite.
4. Run the strict governance profile to decide which scaffold configs can be promoted.

## Promotion Rule

The gold pack remains a research scaffold until readiness reports show non-empty task splits, label maps match current configs, and governance passes without relying on scaffold exemptions.

