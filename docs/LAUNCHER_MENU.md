# Launcher Menu Guide

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

`launcher_menu.bat` is a local convenience wrapper for common GBM-AI commands. The first screen is intentionally short: choose the workflow family first, then pick the specific command. Existing legacy shortcuts, such as `16BI`, still work from the main prompt.

## Main Groups

| Group | Use it for | Typical commands |
| --- | --- | --- |
| Setup and environment | Creating `.venv`, installing dependencies, opening an activated shell, and checking installed packages. | `1`, `1R`, `2`, `3`, `5`, `6` |
| Verify, reports, and handoff checks | Running tests, preflight, scope drift, platform regression, artifact index, local verification, and artifact policy checks. | `4`, `15`, `16`, `16AO`, `16AP`, `16BI`, `16BJ` |
| Literature and graph pipeline | Building source-derived PubMed, ClinicalTrials.gov, corpus, entity, and graph artifacts. | `7`, `8`, `9`, `12`, `13`, `14`, `14A`, `16B` |
| Review and curation workflow | Creating review queues, reviewed queues, curated graph outputs, curation bundles, overlays, and regression packs. | `10`, `11`, `11R`, `11S`, `11C`, `11D`, `16O`, `16P`, `16R`, `16S`, `16Z` |
| Training data and governance | Building annotation packs, gold/evidence/relation training packs, readiness reports, and governance audits. | `16C`, `16D`, `16AQ`, `16AX`, `16BA`, `16AZ`, `16BE`, `16BB`, `16BG`, `16BH` |
| Knowledge Graph Explorer | Starting the local browser explorer with sample, baseline, artifact-index-selected, or Neo4j-backed data. | `17`, `17A`, `17B`, `18` |
| Advanced command index | A compact map of the legacy flat menu for people who already know the old shortcut. | All legacy shortcuts |

## Recommended Paths

For a fresh checkout:

```powershell
launcher_menu.bat
# A -> 1
# A -> 3
# B -> 16BI
```

For a normal handoff check:

```powershell
launcher_menu.bat
# B -> 16BI
```

For training-data governance work:

```powershell
launcher_menu.bat
# E -> 16AX
# E -> 16BA
# E -> 16BE
# E -> 16BG
# E -> 16BH
```

For local graph inspection:

```powershell
launcher_menu.bat
# F -> 17B
```

## What Changed

The previous launcher showed every command on the first screen, which made normal use harder as the project grew. The simplified launcher keeps all commands available but groups them by the question a user is usually asking:

- "Is my environment ready?"
- "Is the project safe to hand off?"
- "Do I need to build literature or graph artifacts?"
- "Do I need review or curation tools?"
- "Do I need training data/governance tools?"
- "Do I want to inspect a graph in the browser?"
