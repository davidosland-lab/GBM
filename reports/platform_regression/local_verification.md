# GBM-AI Local Verification

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Created UTC: 2026-06-27T09:17:19.176528+00:00
- Passed: True
- Steps: 7/7 passed

## Ordered Steps
### pytest
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\python.exe -m pytest -q`
- Detail: ........................................................................ [ 34%] | ........................................................................ [ 69%] | ................................................................         [100%] | 208 passed in 11.52s

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
- Detail: - scope_drift_monitor: pass (findings=0) | - artifact_index: pass (artifacts=461) | ## Warnings | - none

### artifact_policy
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-check-artifact-policy.exe --markdown-output reports\platform_regression\artifact_policy.md --json-output reports\platform_regression\artifact_policy.json`
- Detail: - Tracked paths checked: 600 | - Findings: 0 | ## Findings | - none

### artifact_index
- Status: pass
- Return code: 0
- Command: `C:\Users\david\GBM\.venv\Scripts\gbmbert-artifact-index.exe --markdown-output reports/artifact_index.md --json-output reports/artifact_index.json`
- Detail: - `reports\training\training_readiness_snapshot.json` (training_readiness_snapshot, training, 416 bytes, lines=12, SHA256 `AE8A3312E9E1C3E272C1138A9BBF47B083FCB0615ED4F281C161E4D51A0E8F52`) | - `reports\training\training_readiness_snapshot.md` (training_readiness_snapshot, training, 373 bytes, lines=12, SHA256 `75B0FD6DA4D8BA5044C76AF2AE72960BF6E78BBF9549832826027DB0D7A120B2`) | - `reports\wireframes\kg_explorer.md` (markdown_report, wireframe, 1641 bytes, lines=26, SHA256 `26027595F9F6B93AECC86EA2CA288C26A0F19D9AF48390C46D93E774E4C2491E`) | - `models\checkpoint_registry.json` (checkpoint_registry, model, 956 bytes, lines=17, SHA256 `72DA040F8AEC0F33607F8703892D2DB1339951CFD28BD29C75F5EAA21E39CED4`)

## Warnings
- none
