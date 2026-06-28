# GBM-AI Local Verification

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Created UTC: 2026-06-28T09:06:41.580332+00:00
- Passed: True
- Steps: 8/8 passed

## Ordered Steps
### pytest
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\python.exe -m pytest -q`
- Detail: ........................................................................ [ 63%] | ........................................................................ [ 94%] | ............                                                             [100%] | 228 passed in 17.09s

### pip_check
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\python.exe -m pip check`
- Detail: No broken requirements found.

### scope_drift_monitor
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-scope-drift-monitor.exe --markdown-output reports\platform_regression\scope_drift.md --json-output reports\platform_regression\scope_drift.json`
- Detail: - Missing warnings: 0 | - Prohibited assertions: 0 | ## Findings | - none

### training_governance_suite
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-run-training-governance-suite.exe --output-dir reports\training\governance`
- Detail: - registry_audit: `reports\training\governance\model_registry_audit.json` | - registry_remediation: `reports\training\governance\model_registry_remediation_plan.json` | ## Warnings | - none

### platform_regression
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-platform-regression.exe --skip-tests --skip-pip-check --reports-dir reports\platform_regression`
- Detail: - scope_drift_monitor: pass (findings=0) | - artifact_index: pass (artifacts=497) | ## Warnings | - none

### launcher_menu_check
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-check-launcher-menu.exe --markdown-output reports\platform_regression\launcher_menu_check.md --json-output reports\platform_regression\launcher_menu_check.json`
- Detail: ## Missing Goto Targets | - none | ## Warnings | - none

### artifact_policy
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-check-artifact-policy.exe --markdown-output reports\platform_regression\artifact_policy.md --json-output reports\platform_regression\artifact_policy.json`
- Detail: - Tracked paths checked: 619 | - Findings: 0 | ## Findings | - none

### artifact_index
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports/artifact_index.md --json-output reports/artifact_index.json`
- Detail: - `reports\training\training_readiness_snapshot.json` (training_readiness_snapshot, training, 476 bytes, lines=13, SHA256 `91C32A0A311D1DBC8BC023910FCDE370A515C9D428D535490476E6ED6EE27B05`) | - `reports\training\training_readiness_snapshot.md` (training_readiness_snapshot, training, 423 bytes, lines=15, SHA256 `DD6041B3112E05E43560BE74FF27C327577EC4A5DB2EF6734E7A2C2FA25A183D`) | - `reports\wireframes\kg_explorer.md` (markdown_report, wireframe, 1641 bytes, lines=26, SHA256 `26027595F9F6B93AECC86EA2CA288C26A0F19D9AF48390C46D93E774E4C2491E`) | - `models\checkpoint_registry.json` (checkpoint_registry, model, 956 bytes, lines=17, SHA256 `72DA040F8AEC0F33607F8703892D2DB1339951CFD28BD29C75F5EAA21E39CED4`)

## Warnings
- none
