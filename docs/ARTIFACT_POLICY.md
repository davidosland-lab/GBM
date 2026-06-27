# Artifact Policy

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This project tracks small, deterministic report artifacts that explain the current research scaffold and make handoff review possible without rerunning every command first.

## Tracked Artifacts

- Governance and readiness reports under `reports/training/` when they describe the current checked-in datasets, configs, or handoff state.
- Planning reports that define acceptance criteria for future curation work, such as gold-pack expansion and evidence-label coverage plans.
- Platform and artifact-index reports that summarize project state after a verification run.
- Tiny smoke fixtures and label maps that are required for tests or current governance checks.

## Regenerated Artifacts

- Reports that include timestamps may change after verification runs and should be refreshed before a handoff commit.
- The artifact index should be regenerated after adding, removing, or renaming report files.
- Strict governance reports are tracked as audit evidence even when the strict profile intentionally reports scaffold findings.

## Not Tracked By Default

- Large model checkpoints, downloaded model weights, caches, virtual environments, and local notebook scratch outputs.
- Full external corpora or private annotation batches unless they are intentionally reduced to a small research fixture.
- Any artifact that would imply a validated trained GBM-BERT model exists before the model is actually trained, evaluated, and reviewed.

