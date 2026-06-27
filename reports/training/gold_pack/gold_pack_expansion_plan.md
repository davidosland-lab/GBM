# Gold Pack Expansion Plan

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Current status: minimal local fixture ready
- Evidence rows: 12
- NER rows: 24 entities across 12 source PMIDs
- Relation rows: 12, with positive relation examples and `NO_RELATION` examples
- Target use: broaden the local gold pack enough to support stable governance checks before any full training claim is made.

## Minimum Acceptance Targets

- Done: evidence examples cover all intended evidence labels in the local fixture.
- Done: NER examples cover the broad local labels represented in the checked-in gold pack.
- Done: relation examples include positive relation labels and `NO_RELATION`.
- Done: splits preserve PMID separation between train, validation, and test.
- Done: relation rows preserve source PMID, source type, and the research-use warning.

## Remaining Work

1. Expand beyond the minimal fixture with more reviewed rows per task and label.
2. Keep provenance audits clean as relation rows are added.
3. Re-run training readiness, pack comparison, default governance, strict governance, and local verification after each expansion.
4. Promote scaffold configs only after readiness reports support the change without relying on scaffold exemptions.

## Promotion Rule

The gold pack remains a research scaffold until larger reviewed data volumes are available, readiness reports show stable non-empty task splits, label maps match current configs, and governance passes without relying on scaffold exemptions.

