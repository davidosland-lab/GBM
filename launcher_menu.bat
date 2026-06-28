@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"

:menu
cls
echo ============================================================
echo GBM-AI Platform Local Launcher
echo ============================================================
echo.
echo Project folder:
echo %CD%
echo.
echo This launcher uses a local virtual environment at:
echo %VENV_DIR%
echo.
echo Research-use only. Not medical advice. Not intended for
echo diagnosis, treatment selection, or clinical decision-making.
echo.
echo A. Setup and environment
echo B. Verify, reports, and handoff checks
echo C. Literature and graph pipeline
echo D. Review and curation workflow
echo E. Training data and governance
echo F. Knowledge Graph Explorer
echo G. Advanced command index
echo Q. Exit
echo.
echo Tip: old shortcuts such as 16BI still work.
echo.
set /p "choice=Choose an option: "

if /I "%choice%"=="A" goto setup_menu
if /I "%choice%"=="B" goto verify_menu
if /I "%choice%"=="C" goto pipeline_menu
if /I "%choice%"=="D" goto curation_menu
if /I "%choice%"=="E" goto training_menu
if /I "%choice%"=="F" goto explorer_menu
if /I "%choice%"=="G" goto advanced_menu
if /I "%choice%"=="Q" goto end
if "%choice%"=="1" goto create_venv
if /I "%choice%"=="1R" goto recreate_venv
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto install_editable
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto show_versions
if "%choice%"=="6" goto open_shell
if "%choice%"=="7" goto run_extraction
if "%choice%"=="8" goto run_pipeline
if "%choice%"=="9" goto graph_quality
if "%choice%"=="10" goto export_review_queue
if "%choice%"=="11" goto summarize_review_queue
if /I "%choice%"=="11R" goto initialize_reviewed_queue
if /I "%choice%"=="11S" goto summarize_reviewed_queue
if /I "%choice%"=="11C" goto export_curated_graph
if /I "%choice%"=="11D" goto curation_diff
if "%choice%"=="12" goto build_manifest
if "%choice%"=="13" goto build_trial_graph
if "%choice%"=="14" goto dry_run_load
if /I "%choice%"=="14A" goto audit_graph_provenance
if "%choice%"=="15" goto preflight
if "%choice%"=="16" goto artifact_index
if /I "%choice%"=="16B" goto smoke_baseline
if /I "%choice%"=="16C" goto export_annotation_dataset
if /I "%choice%"=="16D" goto annotation_dataset_quality
if /I "%choice%"=="16E" goto split_annotation_dataset
if /I "%choice%"=="16F" goto build_label_maps
if /I "%choice%"=="16G" goto build_dataset_card
if /I "%choice%"=="16H" goto build_baseline_report
if /I "%choice%"=="16I" goto build_experiment_manifest
if /I "%choice%"=="16J" goto register_checkpoint
if /I "%choice%"=="16K" goto validate_training_gate
if /I "%choice%"=="16L" goto score_evidence
if /I "%choice%"=="16M" goto build_model_card
if /I "%choice%"=="16N" goto run_training_smoke
if /I "%choice%"=="16O" goto export_prediction_review_queue
if /I "%choice%"=="16P" goto initialize_prediction_queue
if /I "%choice%"=="16Q" goto prediction_quality_report
if /I "%choice%"=="16R" goto export_curated_evidence
if /I "%choice%"=="16S" goto apply_evidence_overlay
if /I "%choice%"=="16T" goto prediction_review_summary
if /I "%choice%"=="16U" goto import_prediction_review_csv
if /I "%choice%"=="16V" goto audit_curated_evidence
if /I "%choice%"=="16W" goto export_active_learning_candidates
if /I "%choice%"=="16X" goto overlay_diff
if /I "%choice%"=="16Y" goto overlay_load_guard
if /I "%choice%"=="16Z" goto curation_smoke_workflow
if /I "%choice%"=="16AA" goto curation_handoff_bundle
if /I "%choice%"=="16AB" goto validate_curation_handoff
if /I "%choice%"=="16AC" goto register_curation_run
if /I "%choice%"=="16AD" goto search_curated_evidence
if /I "%choice%"=="16AE" goto plan_active_learning_batches
if /I "%choice%"=="16AF" goto revert_evidence_overlay
if /I "%choice%"=="16AG" goto curation_regression_pack
if /I "%choice%"=="16AH" goto browse_curation_runs
if /I "%choice%"=="16AI" goto artifact_detail
if /I "%choice%"=="16AJ" goto active_learning_batch_status
if /I "%choice%"=="16AK" goto export_active_learning_batch_csv
if /I "%choice%"=="16AL" goto import_active_learning_batch_csv
if /I "%choice%"=="16AM" goto promote_evidence_overlay
if /I "%choice%"=="16AN" goto relation_extraction_audit
if /I "%choice%"=="16AO" goto scope_drift_monitor
if /I "%choice%"=="16AP" goto platform_regression
if /I "%choice%"=="16AQ" goto build_gold_seed_dataset
if /I "%choice%"=="16AR" goto adjudication_report
if /I "%choice%"=="16AS" goto normalize_graph_entities
if /I "%choice%"=="16AT" goto enrich_relation_qualifiers
if /I "%choice%"=="16AU" goto training_readiness_report
if /I "%choice%"=="16AV" goto split_by_pmid
if /I "%choice%"=="16AW" goto repair_evidence_labels
if /I "%choice%"=="16AX" goto gold_training_pack
if /I "%choice%"=="16AY" goto build_relation_negatives
if /I "%choice%"=="16AZ" goto relation_dataset_quality
if /I "%choice%"=="16BA" goto evidence_training_pack
if /I "%choice%"=="16BB" goto review_training_config
if /I "%choice%"=="16BC" goto merge_relation_pack
if /I "%choice%"=="16BD" goto relation_training_pack
if /I "%choice%"=="16BE" goto compare_training_packs
if /I "%choice%"=="16BF" goto audit_model_registry
if /I "%choice%"=="16BG" goto training_governance_suite
if /I "%choice%"=="16BH" goto strict_training_governance
if /I "%choice%"=="16BI" goto local_verification
if /I "%choice%"=="16BJ" goto artifact_policy_check
if /I "%choice%"=="16BK" goto launcher_menu_check
if /I "%choice%"=="16BL" goto curated_fixture_import
if /I "%choice%"=="16BM" goto gold_pack_promotion_review
if /I "%choice%"=="16BN" goto curated_provenance_diff
if /I "%choice%"=="16BO" goto promotion_planning_report
if /I "%choice%"=="16BP" goto governance_detail_export
if /I "%choice%"=="16BQ" goto ci_summary_contract
if /I "%choice%"=="16BR" goto curated_fixture_import_multibatch
if /I "%choice%"=="16BS" goto curated_round_rebuild
if "%choice%"=="17" goto run_explorer_sample
if /I "%choice%"=="17A" goto run_explorer_artifact
if /I "%choice%"=="17B" goto run_explorer_baseline
if "%choice%"=="18" goto run_explorer_neo4j
if "%choice%"=="19" goto end

echo.
echo Invalid choice.
pause
goto menu

:setup_menu
cls
echo ============================================================
echo Setup and Environment
echo ============================================================
echo.
echo Use these first when the project is new, dependencies changed,
echo or you want an activated shell.
echo.
echo 1. Create local virtual environment
echo 1R. Recreate local virtual environment with Python 3.12 64-bit
echo 2. Install project dependencies into local virtual environment
echo 3. Install/update project in editable dev mode
echo 5. Show installed dependency versions
echo 6. Open activated PowerShell in this project
echo M. Main menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if "%choice%"=="1" goto create_venv
if /I "%choice%"=="1R" goto recreate_venv
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto install_editable
if "%choice%"=="5" goto show_versions
if "%choice%"=="6" goto open_shell
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto setup_menu

:verify_menu
cls
echo ============================================================
echo Verify, Reports, and Handoff Checks
echo ============================================================
echo.
echo Use these before handing work off or after larger changes.
echo.
echo 4. Run tests
echo 15. Run preflight checks
echo 16. Build artifact index
echo 16AO. Run scope drift monitor
echo 16AP. Run platform regression
echo 16BI. Run canonical local verification
echo 16BJ. Check tracked artifact policy
echo 16BK. Check launcher menu structure
echo M. Main menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if "%choice%"=="4" goto run_tests
if "%choice%"=="15" goto preflight
if "%choice%"=="16" goto artifact_index
if /I "%choice%"=="16AO" goto scope_drift_monitor
if /I "%choice%"=="16AP" goto platform_regression
if /I "%choice%"=="16BI" goto local_verification
if /I "%choice%"=="16BJ" goto artifact_policy_check
if /I "%choice%"=="16BK" goto launcher_menu_check
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto verify_menu

:pipeline_menu
cls
echo ============================================================
echo Literature and Graph Pipeline
echo ============================================================
echo.
echo Use these to build source-derived literature and graph artifacts.
echo.
echo 7. Run PubMed to entity extraction CLI
echo 8. Run full PubMed pipeline
echo 9. Build graph quality report
echo 12. Build corpus manifest
echo 13. Build trial graph records
echo 14. Dry-run graph load
echo 14A. Audit graph provenance
echo 16B. Run offline smoke baseline rebuild
echo 16AS. Normalize graph entities
echo 16AT. Enrich relation qualifiers
echo M. Main menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if "%choice%"=="7" goto run_extraction
if "%choice%"=="8" goto run_pipeline
if "%choice%"=="9" goto graph_quality
if "%choice%"=="12" goto build_manifest
if "%choice%"=="13" goto build_trial_graph
if "%choice%"=="14" goto dry_run_load
if /I "%choice%"=="14A" goto audit_graph_provenance
if /I "%choice%"=="16B" goto smoke_baseline
if /I "%choice%"=="16AS" goto normalize_graph_entities
if /I "%choice%"=="16AT" goto enrich_relation_qualifiers
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto pipeline_menu

:curation_menu
cls
echo ============================================================
echo Review and Curation Workflow
echo ============================================================
echo.
echo Use these to move from raw queues to reviewed, auditable
echo curation artifacts and graph overlays.
echo.
echo 10. Export review queue
echo 11. Summarize review queue
echo 11R. Initialize reviewed queue scaffold
echo 11S. Summarize reviewed queue
echo 11C. Export curated graph records
echo 11D. Build curation diff report
echo 16O. Export GBM-BERT prediction review queue
echo 16P. Initialize reviewed prediction queue
echo 16R. Export curated GBM-BERT evidence
echo 16S. Apply curated evidence overlay to graph
echo 16Z. Run curation smoke workflow
echo 16AA. Build curation handoff bundle
echo 16AG. Run curation regression pack
echo M. Main menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if "%choice%"=="10" goto export_review_queue
if "%choice%"=="11" goto summarize_review_queue
if /I "%choice%"=="11R" goto initialize_reviewed_queue
if /I "%choice%"=="11S" goto summarize_reviewed_queue
if /I "%choice%"=="11C" goto export_curated_graph
if /I "%choice%"=="11D" goto curation_diff
if /I "%choice%"=="16O" goto export_prediction_review_queue
if /I "%choice%"=="16P" goto initialize_prediction_queue
if /I "%choice%"=="16R" goto export_curated_evidence
if /I "%choice%"=="16S" goto apply_evidence_overlay
if /I "%choice%"=="16Z" goto curation_smoke_workflow
if /I "%choice%"=="16AA" goto curation_handoff_bundle
if /I "%choice%"=="16AG" goto curation_regression_pack
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto curation_menu

:training_menu
cls
echo ============================================================
echo Training Data and Governance
echo ============================================================
echo.
echo Use these to build annotation packs, inspect training readiness,
echo and run governance checks. These do not claim a validated model.
echo.
echo 16C. Export annotation datasets
echo 16D. Build annotation dataset quality report
echo 16AQ. Build gold seed dataset
echo 16AX. Build gold training pack
echo 16BA. Build evidence-only training pack
echo 16AZ. Build relation dataset quality report
echo 16BE. Compare training packs
echo 16BB. Review training config gate
echo 16BG. Run training governance suite
echo 16BH. Run strict training governance audit
echo 16BI. Run canonical local verification
echo 16BL. Import curated training fixture
echo 16BM. Review gold-pack promotion thresholds
echo 16BN. Diff curated batch provenance
echo 16BO. Plan gold-pack promotion curation batches
echo 16BP. Export governance detail links
echo 16BQ. Check CI summary artifact contract
echo 16BR. Import all curated rounds (multi-batch)
echo 16BS. Rebuild all curated-round reports (one command)
echo T. Advanced training commands
echo M. Main menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if /I "%choice%"=="16C" goto export_annotation_dataset
if /I "%choice%"=="16D" goto annotation_dataset_quality
if /I "%choice%"=="16AQ" goto build_gold_seed_dataset
if /I "%choice%"=="16AX" goto gold_training_pack
if /I "%choice%"=="16BA" goto evidence_training_pack
if /I "%choice%"=="16AZ" goto relation_dataset_quality
if /I "%choice%"=="16BE" goto compare_training_packs
if /I "%choice%"=="16BB" goto review_training_config
if /I "%choice%"=="16BG" goto training_governance_suite
if /I "%choice%"=="16BH" goto strict_training_governance
if /I "%choice%"=="16BI" goto local_verification
if /I "%choice%"=="16BL" goto curated_fixture_import
if /I "%choice%"=="16BM" goto gold_pack_promotion_review
if /I "%choice%"=="16BN" goto curated_provenance_diff
if /I "%choice%"=="16BO" goto promotion_planning_report
if /I "%choice%"=="16BP" goto governance_detail_export
if /I "%choice%"=="16BQ" goto ci_summary_contract
if /I "%choice%"=="16BR" goto curated_fixture_import_multibatch
if /I "%choice%"=="16BS" goto curated_round_rebuild
if /I "%choice%"=="T" goto advanced_training_menu
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto training_menu

:advanced_training_menu
cls
echo ============================================================
echo Advanced Training Commands
echo ============================================================
echo.
echo These are lower-level steps that are usually covered by the
echo pack builders or governance commands.
echo.
echo 16E. Split annotation datasets
echo 16F. Build GBM-BERT label maps
echo 16G. Build GBM-BERT dataset card
echo 16H. Build GBM-BERT baseline report
echo 16I. Build GBM-BERT experiment manifest
echo 16J. Register GBM-BERT checkpoint metadata
echo 16K. Validate GBM-BERT training gate
echo 16L. Score evidence rows with GBM-BERT checkpoint
echo 16M. Build GBM-BERT model card
echo 16N. Run GBM-BERT training smoke fixture
echo 16AY. Build relation negative examples
echo 16BC. Merge relation training pack
echo 16BD. Build relation-only training pack
echo 16BF. Audit model registry
echo M. Main menu
echo B. Back to training menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if /I "%choice%"=="16E" goto split_annotation_dataset
if /I "%choice%"=="16F" goto build_label_maps
if /I "%choice%"=="16G" goto build_dataset_card
if /I "%choice%"=="16H" goto build_baseline_report
if /I "%choice%"=="16I" goto build_experiment_manifest
if /I "%choice%"=="16J" goto register_checkpoint
if /I "%choice%"=="16K" goto validate_training_gate
if /I "%choice%"=="16L" goto score_evidence
if /I "%choice%"=="16M" goto build_model_card
if /I "%choice%"=="16N" goto run_training_smoke
if /I "%choice%"=="16AY" goto build_relation_negatives
if /I "%choice%"=="16BC" goto merge_relation_pack
if /I "%choice%"=="16BD" goto relation_training_pack
if /I "%choice%"=="16BF" goto audit_model_registry
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="B" goto training_menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto advanced_training_menu

:explorer_menu
cls
echo ============================================================
echo Knowledge Graph Explorer
echo ============================================================
echo.
echo Use these to inspect graph artifacts locally in a browser.
echo.
echo 17. Start Knowledge Graph Explorer with sample data
echo 17A. Start Knowledge Graph Explorer with artifact index selection
echo 17B. Start Knowledge Graph Explorer with baseline smoke data
echo 18. Start Knowledge Graph Explorer with Neo4j
echo M. Main menu
echo Q. Exit
echo.
set /p "choice=Choose an option: "
if "%choice%"=="17" goto run_explorer_sample
if /I "%choice%"=="17A" goto run_explorer_artifact
if /I "%choice%"=="17B" goto run_explorer_baseline
if "%choice%"=="18" goto run_explorer_neo4j
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Invalid choice.
pause
goto explorer_menu

:advanced_menu
cls
echo ============================================================
echo Advanced Command Index
echo ============================================================
echo.
echo This is the legacy flat list. Use it when you already know the
echo exact command shortcut.
echo.
echo Setup: 1, 1R, 2, 3, 4, 5, 6
echo Pipeline: 7, 8, 9, 12, 13, 14, 14A, 16B, 16AS, 16AT
echo Review: 10, 11, 11R, 11S, 11C, 11D
echo Curation: 16O-16AG, plus 16AH-16AM for run/batch operations
echo Training: 16C-16N and 16AQ-16BQ
echo Verification: 15, 16, 16AO, 16AP, 16BI, 16BJ, 16BK
echo Explorer: 17, 17A, 17B, 18
echo.
echo Old shortcuts still work from the main menu prompt.
echo Press M to return to the main menu.
echo.
set /p "choice=Choose an option: "
if /I "%choice%"=="M" goto menu
if /I "%choice%"=="Q" goto end
echo.
echo Returning to main menu.
pause
goto menu

:create_venv
echo.
if exist "%PYTHON_EXE%" (
    echo Local virtual environment already exists.
    call :check_venv
    if errorlevel 1 (
        echo.
        echo Use option 1R to recreate it with a supported Python.
    )
) else (
    call :create_supported_venv
)
if not exist "%PYTHON_EXE%" (
    echo.
    echo Could not create %VENV_DIR%.
    pause
    goto menu
)
echo.
echo Local virtual environment ready.
pause
goto menu

:recreate_venv
echo.
echo Recreating local virtual environment...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$root = (Resolve-Path -LiteralPath '%CD%').Path; $venv = Join-Path $root '.venv'; if (Test-Path -LiteralPath $venv) { $resolved = (Resolve-Path -LiteralPath $venv).Path; if ($resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) { Remove-Item -LiteralPath $resolved -Recurse -Force } else { throw 'Refusing to remove a path outside the project.' } }"
if errorlevel 1 goto command_failed
call :create_supported_venv
if errorlevel 1 goto command_failed
echo.
echo Local virtual environment recreated.
pause
goto menu

:install_deps
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Keeping bundled virtual-environment pip to avoid Windows self-upgrade issues.
echo.
echo Installing project dependencies from pyproject.toml...
"%PYTHON_EXE%" -m pip install --disable-pip-version-check --no-build-isolation --no-compile -e .
if errorlevel 1 goto command_failed
echo.
echo Dependencies installed locally.
pause
goto menu

:install_editable
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Installing project in editable mode with dev dependencies...
"%PYTHON_EXE%" -m pip install --disable-pip-version-check --no-build-isolation --no-compile -e ".[dev]"
if errorlevel 1 goto command_failed
echo.
echo Editable dev install complete.
pause
goto menu

:run_tests
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Running tests with local virtual environment...
"%PYTHON_EXE%" -m pytest
if errorlevel 1 goto command_failed
echo.
echo Tests passed.
pause
goto menu

:show_versions
call :ensure_venv
if errorlevel 1 goto menu
echo.
"%PYTHON_EXE%" --version
"%PYTHON_EXE%" -m pip --version
echo.
"%PYTHON_EXE%" -m pip show pydantic python-dotenv tqdm transformers torch datasets accelerate spacy scispacy neo4j pytest
echo.
pause
goto menu

:open_shell
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Opening PowerShell with the local virtual environment activated...
start "GBM Local Environment" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%CD%'; . '.\.venv\Scripts\Activate.ps1'; Write-Host 'GBM local virtual environment activated.'"
goto menu

:run_extraction
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "input_path=Input PubMed JSONL path: "
set /p "output_path=Output entity JSONL path: "
if "%input_path%"=="" (
    echo Input path is required.
    pause
    goto menu
)
if "%output_path%"=="" (
    echo Output path is required.
    pause
    goto menu
)
echo.
"%PYTHON_EXE%" -m gbmbert.extraction.pipeline "%input_path%" "%output_path%"
if errorlevel 1 goto command_failed
echo.
echo Entity extraction complete.
pause
goto menu

:run_pipeline
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "input_path=Input PubMed JSONL path: "
set /p "output_dir=Output pipeline directory [data\processed\literature_pipeline]: "
set /p "entity_mode=Entity mode model or lexicon [lexicon]: "
set /p "lexicon_path=Lexicon path for lexicon mode [configs\extraction\lexicon_gbm_v1.json]: "
if "%input_path%"=="" (
    echo Input path is required.
    pause
    goto menu
)
if "%output_dir%"=="" set "output_dir=data\processed\literature_pipeline"
if "%entity_mode%"=="" set "entity_mode=lexicon"
if "%lexicon_path%"=="" set "lexicon_path=configs\extraction\lexicon_gbm_v1.json"
"%PYTHON_EXE%" -m gbmbert.pipeline "%input_path%" --output-dir "%output_dir%" --entity-mode "%entity_mode%" --lexicon "%lexicon_path%"
if errorlevel 1 goto command_failed
echo.
echo Pipeline complete.
pause
goto menu

:graph_quality
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Input graph-record JSONL path: "
set /p "trial_path=Optional trial graph-record JSONL path: "
set /p "md_path=Markdown output path [reports\graph\quality.md]: "
set /p "json_path=JSON output path [reports\graph\quality.json]: "
if "%graph_path%"=="" (
    echo Graph path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\graph\quality.md"
if "%json_path%"=="" set "json_path=reports\graph\quality.json"
if "%trial_path%"=="" (
    "%PYTHON_EXE%" -m gbmbert.knowledge_graph.quality "%graph_path%" --markdown-output "%md_path%" --json-output "%json_path%"
) else (
    "%PYTHON_EXE%" -m gbmbert.knowledge_graph.quality "%graph_path%" --trial-jsonl "%trial_path%" --markdown-output "%md_path%" --json-output "%json_path%"
)
if errorlevel 1 goto command_failed
echo.
echo Graph quality report complete.
pause
goto menu

:export_review_queue
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "evidence_path=Evidence claims JSONL path: "
set /p "graph_path=Graph records JSONL path: "
set /p "queue_path=Review queue JSONL output [data\review\evidence_review_queue.jsonl]: "
set /p "csv_path=Review queue CSV output [data\review\evidence_review_queue.csv]: "
if "%queue_path%"=="" set "queue_path=data\review\evidence_review_queue.jsonl"
if "%csv_path%"=="" set "csv_path=data\review\evidence_review_queue.csv"
"%PYTHON_EXE%" -m gbmbert.extraction.review_queue --evidence-jsonl "%evidence_path%" --graph-jsonl "%graph_path%" --output "%queue_path%" --csv-output "%csv_path%"
if errorlevel 1 goto command_failed
echo.
echo Review queue exported.
pause
goto menu

:summarize_review_queue
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "queue_path=Review queue JSONL path: "
set /p "md_path=Markdown summary output [reports\review\evidence_review_summary.md]: "
set /p "json_path=JSON summary output [reports\review\evidence_review_summary.json]: "
if "%queue_path%"=="" (
    echo Review queue path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\review\evidence_review_summary.md"
if "%json_path%"=="" set "json_path=reports\review\evidence_review_summary.json"
"%VENV_DIR%\Scripts\gbmbert-review-queue-summary.exe" "%queue_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Review queue summary complete.
pause
goto menu

:initialize_reviewed_queue
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "queue_path=Raw review queue JSONL path: "
set /p "reviewed_path=Reviewed queue JSONL output [data\review\evidence_reviewed_queue.jsonl]: "
set /p "csv_path=Reviewed queue CSV output [data\review\evidence_reviewed_queue.csv]: "
set /p "reviewer=Reviewer name or initials: "
if "%queue_path%"=="" (
    echo Raw review queue path is required.
    pause
    goto menu
)
if "%reviewed_path%"=="" set "reviewed_path=data\review\evidence_reviewed_queue.jsonl"
if "%csv_path%"=="" set "csv_path=data\review\evidence_reviewed_queue.csv"
"%VENV_DIR%\Scripts\gbmbert-init-reviewed-queue.exe" "%queue_path%" "%reviewed_path%" --csv-output "%csv_path%" --reviewer "%reviewer%"
if errorlevel 1 goto command_failed
echo.
echo Reviewed queue scaffold initialized.
pause
goto menu

:summarize_reviewed_queue
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "reviewed_path=Reviewed queue JSONL path: "
set /p "md_path=Markdown summary output [reports\review\evidence_reviewed_summary.md]: "
set /p "json_path=JSON summary output [reports\review\evidence_reviewed_summary.json]: "
if "%reviewed_path%"=="" (
    echo Reviewed queue path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\review\evidence_reviewed_summary.md"
if "%json_path%"=="" set "json_path=reports\review\evidence_reviewed_summary.json"
"%VENV_DIR%\Scripts\gbmbert-reviewed-queue-summary.exe" "%reviewed_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Reviewed queue summary complete.
pause
goto menu

:export_curated_graph
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Raw graph-record JSONL path: "
set /p "reviewed_path=Reviewed queue JSONL path: "
set /p "curated_path=Curated graph-record JSONL output [data\processed\curated_graph_records.jsonl]: "
set /p "md_path=Curation report Markdown output [reports\review\curation_diff.md]: "
set /p "json_path=Curation report JSON output [reports\review\curation_diff.json]: "
if "%graph_path%"=="" (
    echo Graph path is required.
    pause
    goto menu
)
if "%reviewed_path%"=="" (
    echo Reviewed queue path is required.
    pause
    goto menu
)
if "%curated_path%"=="" set "curated_path=data\processed\curated_graph_records.jsonl"
if "%md_path%"=="" set "md_path=reports\review\curation_diff.md"
if "%json_path%"=="" set "json_path=reports\review\curation_diff.json"
"%VENV_DIR%\Scripts\gbmbert-export-curated-graph.exe" "%graph_path%" "%reviewed_path%" "%curated_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curated graph records exported.
pause
goto menu

:curation_diff
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Raw graph-record JSONL path: "
set /p "curated_path=Curated graph-record JSONL path: "
set /p "reviewed_path=Reviewed queue JSONL path: "
set /p "md_path=Curation diff Markdown output [reports\review\curation_diff.md]: "
set /p "json_path=Curation diff JSON output [reports\review\curation_diff.json]: "
if "%graph_path%"=="" (
    echo Raw graph path is required.
    pause
    goto menu
)
if "%curated_path%"=="" (
    echo Curated graph path is required.
    pause
    goto menu
)
if "%reviewed_path%"=="" (
    echo Reviewed queue path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\review\curation_diff.md"
if "%json_path%"=="" set "json_path=reports\review\curation_diff.json"
"%VENV_DIR%\Scripts\gbmbert-curation-diff.exe" "%graph_path%" "%curated_path%" "%reviewed_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curation diff report complete.
pause
goto menu

:build_manifest
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "artifact_path=Artifact path for manifest: "
set /p "manifest_name=Manifest name: "
set /p "json_path=Manifest JSON output [reports\corpus\manifest.json]: "
set /p "md_path=Manifest Markdown output [reports\corpus\manifest.md]: "
if "%artifact_path%"=="" (
    echo Artifact path is required.
    pause
    goto menu
)
if "%manifest_name%"=="" set "manifest_name=gbm_ai_manifest"
if "%json_path%"=="" set "json_path=reports\corpus\manifest.json"
if "%md_path%"=="" set "md_path=reports\corpus\manifest.md"
"%PYTHON_EXE%" -m gbmbert.ingest.manifest "%artifact_path%" --name "%manifest_name%" --output "%json_path%" --markdown-output "%md_path%"
if errorlevel 1 goto command_failed
echo.
echo Manifest complete.
pause
goto menu

:build_trial_graph
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "trials_path=ClinicalTrials.gov JSONL path: "
set /p "output_path=Trial graph-record JSONL output: "
if "%trials_path%"=="" (
    echo Trials path is required.
    pause
    goto menu
)
if "%output_path%"=="" (
    echo Output path is required.
    pause
    goto menu
)
"%PYTHON_EXE%" -m gbmbert.knowledge_graph.trials "%trials_path%" "%output_path%"
if errorlevel 1 goto command_failed
echo.
echo Trial graph records built.
pause
goto menu

:dry_run_load
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Graph-record JSONL path: "
set /p "record_type=Record type auto, pubmed, or trial [auto]: "
set /p "md_path=Load report Markdown output [reports\graph\load_report.md]: "
set /p "json_path=Load report JSON output [reports\graph\load_report.json]: "
if "%graph_path%"=="" (
    echo Graph path is required.
    pause
    goto menu
)
if "%record_type%"=="" set "record_type=auto"
if "%md_path%"=="" set "md_path=reports\graph\load_report.md"
if "%json_path%"=="" set "json_path=reports\graph\load_report.json"
"%PYTHON_EXE%" -m gbmbert.knowledge_graph.cli "%graph_path%" --record-type "%record_type%" --dry-run --no-constraints --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Dry-run load complete.
pause
goto menu

:audit_graph_provenance
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Graph-record JSONL path: "
set /p "record_type=Record type auto, pubmed, or trial [auto]: "
set /p "md_path=Provenance audit Markdown output [reports\graph\provenance_audit.md]: "
set /p "json_path=Provenance audit JSON output [reports\graph\provenance_audit.json]: "
if "%graph_path%"=="" (
    echo Graph path is required.
    pause
    goto menu
)
if "%record_type%"=="" set "record_type=auto"
if "%md_path%"=="" set "md_path=reports\graph\provenance_audit.md"
if "%json_path%"=="" set "json_path=reports\graph\provenance_audit.json"
"%VENV_DIR%\Scripts\gbmbert-audit-graph-provenance.exe" "%graph_path%" --record-type "%record_type%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Graph provenance audit complete.
pause
goto menu

:preflight
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
"%PYTHON_EXE%" -m gbmbert.preflight --markdown-output reports\preflight.md --json-output reports\preflight.json
if errorlevel 1 goto command_failed
echo.
echo Preflight complete.
pause
goto menu

:artifact_index
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
"%PYTHON_EXE%" -m gbmbert.artifacts --markdown-output reports\artifact_index.md --json-output reports\artifact_index.json
if errorlevel 1 goto command_failed
echo.
echo Artifact index complete.
pause
goto menu

:smoke_baseline
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Rebuilding smoke baseline from existing local raw files...
"%VENV_DIR%\Scripts\gbmbert-run-smoke-baseline.exe" --offline --markdown-output reports\smoke_baseline.md --json-output reports\smoke_baseline.json
if errorlevel 1 goto command_failed
echo.
echo Smoke baseline rebuild complete.
pause
goto menu

:export_annotation_dataset
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "reviewed_path=Reviewed queue JSONL path: "
set /p "output_dir=Annotation dataset output dir [data\training\annotation_dataset]: "
set /p "entity_path=Optional entity JSONL path: "
set /p "summary_path=Dataset summary JSON output [reports\training\annotation_dataset_manifest.json]: "
if "%reviewed_path%"=="" (
    echo Reviewed queue path is required.
    pause
    goto menu
)
if "%output_dir%"=="" set "output_dir=data\training\annotation_dataset"
if "%summary_path%"=="" set "summary_path=reports\training\annotation_dataset_manifest.json"
if "%entity_path%"=="" (
    "%VENV_DIR%\Scripts\gbmbert-export-annotation-dataset.exe" "%reviewed_path%" "%output_dir%" --summary-json-output "%summary_path%"
) else (
    "%VENV_DIR%\Scripts\gbmbert-export-annotation-dataset.exe" "%reviewed_path%" "%output_dir%" --entity-jsonl "%entity_path%" --summary-json-output "%summary_path%"
)
if errorlevel 1 goto command_failed
echo.
echo Annotation datasets exported.
pause
goto menu

:annotation_dataset_quality
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Annotation dataset directory [data\training\annotation_dataset]: "
set /p "md_path=Dataset quality Markdown output [reports\training\annotation_dataset_quality.md]: "
set /p "json_path=Dataset quality JSON output [reports\training\annotation_dataset_quality.json]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_dataset"
if "%md_path%"=="" set "md_path=reports\training\annotation_dataset_quality.md"
if "%json_path%"=="" set "json_path=reports\training\annotation_dataset_quality.json"
"%VENV_DIR%\Scripts\gbmbert-annotation-dataset-quality.exe" "%dataset_dir%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Annotation dataset quality report complete.
pause
goto menu

:split_annotation_dataset
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Annotation dataset directory [data\training\annotation_dataset]: "
set /p "output_dir=Split output directory [data\training\annotation_splits]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_dataset"
if "%output_dir%"=="" set "output_dir=data\training\annotation_splits"
"%VENV_DIR%\Scripts\gbmbert-split-annotation-dataset.exe" "%dataset_dir%" "%output_dir%"
if errorlevel 1 goto command_failed
echo.
echo Annotation dataset splits complete.
pause
goto menu

:build_label_maps
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Dataset or split directory [data\training\annotation_splits]: "
set /p "output_dir=Label map output directory [data\training\label_maps]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_splits"
if "%output_dir%"=="" set "output_dir=data\training\label_maps"
"%VENV_DIR%\Scripts\gbmbert-build-label-maps.exe" "%dataset_dir%" "%output_dir%"
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT label maps complete.
pause
goto menu

:build_dataset_card
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Dataset or split directory [data\training\annotation_splits]: "
set /p "md_path=Dataset card Markdown output [reports\training\dataset_card.md]: "
set /p "json_path=Dataset card JSON output [reports\training\dataset_card.json]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_splits"
if "%md_path%"=="" set "md_path=reports\training\dataset_card.md"
if "%json_path%"=="" set "json_path=reports\training\dataset_card.json"
"%VENV_DIR%\Scripts\gbmbert-build-dataset-card.exe" "%dataset_dir%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT dataset card complete.
pause
goto menu

:build_baseline_report
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Dataset or split directory [data\training\annotation_splits]: "
set /p "md_path=Baseline Markdown output [reports\training\baseline_report.md]: "
set /p "json_path=Baseline JSON output [reports\training\baseline_report.json]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_splits"
if "%md_path%"=="" set "md_path=reports\training\baseline_report.md"
if "%json_path%"=="" set "json_path=reports\training\baseline_report.json"
"%VENV_DIR%\Scripts\gbmbert-baseline-report.exe" "%dataset_dir%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT baseline report complete.
pause
goto menu

:build_experiment_manifest
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "config_path=Training config [configs\training\gbmbert_ner_pubmedbert.json]: "
set /p "dataset_dir=Dataset or split directory [data\training\annotation_splits]: "
set /p "output_path=Experiment manifest output [reports\training\experiment_manifest.json]: "
set /p "label_map_dir=Optional label map directory [data\training\label_maps]: "
if "%config_path%"=="" set "config_path=configs\training\gbmbert_ner_pubmedbert.json"
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_splits"
if "%output_path%"=="" set "output_path=reports\training\experiment_manifest.json"
if "%label_map_dir%"=="" set "label_map_dir=data\training\label_maps"
"%VENV_DIR%\Scripts\gbmbert-build-experiment-manifest.exe" "%config_path%" "%dataset_dir%" "%output_path%" --label-map-dir "%label_map_dir%"
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT experiment manifest complete.
pause
goto menu

:register_checkpoint
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "registry_path=Checkpoint registry path [models\checkpoint_registry.json]: "
set /p "checkpoint_name=Checkpoint name: "
set /p "checkpoint_dir=Checkpoint directory: "
set /p "task=Task [ner]: "
set /p "base_model=Base model [microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext]: "
set /p "status=Status [candidate]: "
if "%registry_path%"=="" set "registry_path=models\checkpoint_registry.json"
if "%checkpoint_name%"=="" (
    echo Checkpoint name is required.
    pause
    goto menu
)
if "%checkpoint_dir%"=="" (
    echo Checkpoint directory is required.
    pause
    goto menu
)
if "%task%"=="" set "task=ner"
if "%base_model%"=="" set "base_model=microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
if "%status%"=="" set "status=candidate"
"%VENV_DIR%\Scripts\gbmbert-register-checkpoint.exe" "%registry_path%" --name "%checkpoint_name%" --checkpoint-dir "%checkpoint_dir%" --task "%task%" --base-model "%base_model%" --status "%status%"
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT checkpoint metadata registered.
pause
goto menu

:validate_training_gate
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "config_path=Training config [configs\training\gbmbert_ner_pubmedbert.json]: "
set /p "dataset_dir=Dataset split directory [data\training\annotation_splits]: "
set /p "label_map_dir=Label map directory [data\training\label_maps]: "
set /p "manifest_path=Experiment manifest output [reports\training\train_gate_experiment_manifest.json]: "
set /p "report_path=Training gate JSON output [reports\training\train_gate.json]: "
set /p "execute_training=Execute training? Type YES to run evidence training [NO]: "
if "%config_path%"=="" set "config_path=configs\training\gbmbert_ner_pubmedbert.json"
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_splits"
if "%label_map_dir%"=="" set "label_map_dir=data\training\label_maps"
if "%manifest_path%"=="" set "manifest_path=reports\training\train_gate_experiment_manifest.json"
if "%report_path%"=="" set "report_path=reports\training\train_gate.json"
if /I "%execute_training%"=="YES" (
    set /p "metrics_path=Metrics JSON output [reports\training\evidence_metrics.json]: "
    set /p "metrics_md_path=Metrics Markdown output [reports\training\evidence_metrics.md]: "
    set /p "run_manifest_path=Run manifest output [reports\training\evidence_run_manifest.json]: "
    set /p "registry_path=Checkpoint registry [models\checkpoint_registry.json]: "
    set /p "checkpoint_name=Checkpoint registry name [gbmbert_evidence_pubmedbert]: "
    if "!metrics_path!"=="" set "metrics_path=reports\training\evidence_metrics.json"
    if "!metrics_md_path!"=="" set "metrics_md_path=reports\training\evidence_metrics.md"
    if "!run_manifest_path!"=="" set "run_manifest_path=reports\training\evidence_run_manifest.json"
    if "!registry_path!"=="" set "registry_path=models\checkpoint_registry.json"
    if "!checkpoint_name!"=="" set "checkpoint_name=gbmbert_evidence_pubmedbert"
    "%VENV_DIR%\Scripts\gbmbert-train.exe" "%config_path%" "%dataset_dir%" "%label_map_dir%" --experiment-manifest "%manifest_path%" --execute-training --metrics-output "!metrics_path!" --evaluation-markdown-output "!metrics_md_path!" --run-manifest-output "!run_manifest_path!" --registry "!registry_path!" --checkpoint-name "!checkpoint_name!" --json-output "%report_path%"
) else (
    "%VENV_DIR%\Scripts\gbmbert-train.exe" "%config_path%" "%dataset_dir%" "%label_map_dir%" --experiment-manifest "%manifest_path%" --json-output "%report_path%"
)
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT training gate validation complete.
pause
goto menu

:score_evidence
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "input_path=Evidence input JSONL path: "
set /p "output_path=Prediction output JSONL [reports\training\evidence_predictions.jsonl]: "
set /p "registry_path=Checkpoint registry [models\checkpoint_registry.json]: "
set /p "checkpoint_name=Checkpoint name: "
if "%input_path%"=="" (
    echo Evidence input JSONL path is required.
    pause
    goto menu
)
if "%checkpoint_name%"=="" (
    echo Checkpoint name is required.
    pause
    goto menu
)
if "%output_path%"=="" set "output_path=reports\training\evidence_predictions.jsonl"
if "%registry_path%"=="" set "registry_path=models\checkpoint_registry.json"
"%VENV_DIR%\Scripts\gbmbert-score-evidence.exe" "%input_path%" "%output_path%" "%registry_path%" --checkpoint-name "%checkpoint_name%"
if errorlevel 1 goto command_failed
echo.
echo Evidence scoring complete.
pause
goto menu

:build_model_card
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "registry_path=Checkpoint registry [models\checkpoint_registry.json]: "
set /p "checkpoint_name=Checkpoint name: "
set /p "dataset_card=Optional dataset card JSON [reports\training\dataset_card.json]: "
set /p "md_path=Model card Markdown output [reports\training\model_card.md]: "
set /p "json_path=Model card JSON output [reports\training\model_card.json]: "
if "%checkpoint_name%"=="" (
    echo Checkpoint name is required.
    pause
    goto menu
)
if "%registry_path%"=="" set "registry_path=models\checkpoint_registry.json"
if "%dataset_card%"=="" set "dataset_card=reports\training\dataset_card.json"
if "%md_path%"=="" set "md_path=reports\training\model_card.md"
if "%json_path%"=="" set "json_path=reports\training\model_card.json"
"%VENV_DIR%\Scripts\gbmbert-build-model-card.exe" "%registry_path%" --checkpoint-name "%checkpoint_name%" --dataset-card-json "%dataset_card%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT model card complete.
pause
goto menu

:run_training_smoke
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "output_dir=Smoke output dir [data\training\evidence_smoke_fixture]: "
set /p "reports_dir=Smoke reports dir [reports\training\evidence_smoke_fixture]: "
set /p "registry_path=Checkpoint registry [models\checkpoint_registry.json]: "
set /p "checkpoint_name=Checkpoint name [gbmbert_evidence_smoke]: "
if "%output_dir%"=="" set "output_dir=data\training\evidence_smoke_fixture"
if "%reports_dir%"=="" set "reports_dir=reports\training\evidence_smoke_fixture"
if "%registry_path%"=="" set "registry_path=models\checkpoint_registry.json"
if "%checkpoint_name%"=="" set "checkpoint_name=gbmbert_evidence_smoke"
"%VENV_DIR%\Scripts\gbmbert-run-training-smoke.exe" --output-dir "%output_dir%" --reports-dir "%reports_dir%" --registry "%registry_path%" --checkpoint-name "%checkpoint_name%" --json
if errorlevel 1 goto command_failed
echo.
echo GBM-BERT training smoke fixture complete.
pause
goto menu

:export_prediction_review_queue
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "predictions_path=Prediction JSONL path: "
set /p "queue_path=Prediction review queue JSONL output [data\review\evidence_prediction_review_queue.jsonl]: "
set /p "csv_path=Prediction review queue CSV output [data\review\evidence_prediction_review_queue.csv]: "
set /p "queue_all=Queue all predictions? Type YES to include high-confidence rows [NO]: "
if "%predictions_path%"=="" (
    echo Prediction JSONL path is required.
    pause
    goto menu
)
if "%queue_path%"=="" set "queue_path=data\review\evidence_prediction_review_queue.jsonl"
if "%csv_path%"=="" set "csv_path=data\review\evidence_prediction_review_queue.csv"
if /I "%queue_all%"=="YES" (
    "%VENV_DIR%\Scripts\gbmbert-export-prediction-review-queue.exe" "%predictions_path%" "%queue_path%" --csv-output "%csv_path%" --queue-all
) else (
    "%VENV_DIR%\Scripts\gbmbert-export-prediction-review-queue.exe" "%predictions_path%" "%queue_path%" --csv-output "%csv_path%"
)
if errorlevel 1 goto command_failed
echo.
echo Prediction review queue exported.
pause
goto menu

:initialize_prediction_queue
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "queue_path=Raw prediction review queue JSONL path: "
set /p "reviewed_path=Reviewed prediction queue JSONL output [data\review\evidence_prediction_reviewed_queue.jsonl]: "
set /p "csv_path=Reviewed prediction queue CSV output [data\review\evidence_prediction_reviewed_queue.csv]: "
set /p "reviewer=Reviewer name or initials: "
if "%queue_path%"=="" (
    echo Raw prediction review queue path is required.
    pause
    goto menu
)
if "%reviewed_path%"=="" set "reviewed_path=data\review\evidence_prediction_reviewed_queue.jsonl"
if "%csv_path%"=="" set "csv_path=data\review\evidence_prediction_reviewed_queue.csv"
"%VENV_DIR%\Scripts\gbmbert-init-reviewed-prediction-queue.exe" "%queue_path%" "%reviewed_path%" --csv-output "%csv_path%" --reviewer "%reviewer%"
if errorlevel 1 goto command_failed
echo.
echo Reviewed prediction queue scaffold initialized.
pause
goto menu

:prediction_quality_report
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "predictions_path=Prediction JSONL path: "
set /p "md_path=Prediction quality Markdown output [reports\training\evidence_prediction_quality.md]: "
set /p "json_path=Prediction quality JSON output [reports\training\evidence_prediction_quality.json]: "
if "%predictions_path%"=="" (
    echo Prediction JSONL path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\training\evidence_prediction_quality.md"
if "%json_path%"=="" set "json_path=reports\training\evidence_prediction_quality.json"
"%VENV_DIR%\Scripts\gbmbert-prediction-quality-report.exe" "%predictions_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Prediction quality report complete.
pause
goto menu

:prediction_review_summary
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "reviewed_path=Reviewed prediction queue JSONL path: "
set /p "md_path=Prediction review summary Markdown output [reports\review\evidence_prediction_review_summary.md]: "
set /p "json_path=Prediction review summary JSON output [reports\review\evidence_prediction_review_summary.json]: "
if "%reviewed_path%"=="" (
    echo Reviewed prediction queue path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\review\evidence_prediction_review_summary.md"
if "%json_path%"=="" set "json_path=reports\review\evidence_prediction_review_summary.json"
"%VENV_DIR%\Scripts\gbmbert-prediction-review-summary.exe" "%reviewed_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Prediction review summary complete.
pause
goto menu

:import_prediction_review_csv
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "csv_path=Reviewed prediction CSV path: "
set /p "reviewed_path=Reviewed prediction JSONL output [data\review\evidence_prediction_reviewed_queue.jsonl]: "
if "%csv_path%"=="" (
    echo Reviewed prediction CSV path is required.
    pause
    goto menu
)
if "%reviewed_path%"=="" set "reviewed_path=data\review\evidence_prediction_reviewed_queue.jsonl"
"%VENV_DIR%\Scripts\gbmbert-import-prediction-review-csv.exe" "%csv_path%" "%reviewed_path%" --overwrite
if errorlevel 1 goto command_failed
echo.
echo Reviewed prediction CSV imported.
pause
goto menu

:export_curated_evidence
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "predictions_path=Prediction JSONL path: "
set /p "reviewed_path=Reviewed prediction queue JSONL path: "
set /p "curated_path=Curated evidence JSONL output [data\processed\curated_evidence_predictions.jsonl]: "
set /p "md_path=Curated evidence report Markdown output [reports\review\curated_evidence_export.md]: "
set /p "json_path=Curated evidence report JSON output [reports\review\curated_evidence_export.json]: "
if "%predictions_path%"=="" (
    echo Prediction JSONL path is required.
    pause
    goto menu
)
if "%reviewed_path%"=="" (
    echo Reviewed prediction queue path is required.
    pause
    goto menu
)
if "%curated_path%"=="" set "curated_path=data\processed\curated_evidence_predictions.jsonl"
if "%md_path%"=="" set "md_path=reports\review\curated_evidence_export.md"
if "%json_path%"=="" set "json_path=reports\review\curated_evidence_export.json"
"%VENV_DIR%\Scripts\gbmbert-export-curated-evidence.exe" "%predictions_path%" "%reviewed_path%" "%curated_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curated evidence exported.
pause
goto menu

:audit_curated_evidence
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "curated_path=Curated evidence JSONL path: "
set /p "md_path=Curated evidence audit Markdown output [reports\review\curated_evidence_audit.md]: "
set /p "json_path=Curated evidence audit JSON output [reports\review\curated_evidence_audit.json]: "
if "%curated_path%"=="" (
    echo Curated evidence path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\review\curated_evidence_audit.md"
if "%json_path%"=="" set "json_path=reports\review\curated_evidence_audit.json"
"%VENV_DIR%\Scripts\gbmbert-audit-curated-evidence.exe" "%curated_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curated evidence audit complete.
pause
goto menu

:export_active_learning_candidates
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "predictions_path=Prediction JSONL path: "
set /p "graph_path=Optional graph-record JSONL path: "
set /p "candidate_path=Active learning candidates JSONL output [data\review\active_learning_candidates.jsonl]: "
set /p "csv_path=Active learning candidates CSV output [data\review\active_learning_candidates.csv]: "
set /p "md_path=Active learning report Markdown output [reports\review\active_learning_candidates.md]: "
set /p "json_path=Active learning report JSON output [reports\review\active_learning_candidates.json]: "
if "%predictions_path%"=="" (
    echo Prediction JSONL path is required.
    pause
    goto menu
)
if "%candidate_path%"=="" set "candidate_path=data\review\active_learning_candidates.jsonl"
if "%csv_path%"=="" set "csv_path=data\review\active_learning_candidates.csv"
if "%md_path%"=="" set "md_path=reports\review\active_learning_candidates.md"
if "%json_path%"=="" set "json_path=reports\review\active_learning_candidates.json"
if "%graph_path%"=="" (
    "%VENV_DIR%\Scripts\gbmbert-export-active-learning-candidates.exe" "%predictions_path%" "%candidate_path%" --csv-output "%csv_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
) else (
    "%VENV_DIR%\Scripts\gbmbert-export-active-learning-candidates.exe" "%predictions_path%" "%candidate_path%" --csv-output "%csv_path%" --graph-jsonl "%graph_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
)
if errorlevel 1 goto command_failed
echo.
echo Active learning candidates exported.
pause
goto menu

:apply_evidence_overlay
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Raw graph-record JSONL path: "
set /p "curated_path=Curated evidence JSONL path: "
set /p "overlay_path=Overlay graph-record JSONL output [data\processed\evidence_overlay_graph_records.jsonl]: "
set /p "md_path=Overlay report Markdown output [reports\graph\evidence_overlay.md]: "
set /p "json_path=Overlay report JSON output [reports\graph\evidence_overlay.json]: "
if "%graph_path%"=="" (
    echo Graph path is required.
    pause
    goto menu
)
if "%curated_path%"=="" (
    echo Curated evidence path is required.
    pause
    goto menu
)
if "%overlay_path%"=="" set "overlay_path=data\processed\evidence_overlay_graph_records.jsonl"
if "%md_path%"=="" set "md_path=reports\graph\evidence_overlay.md"
if "%json_path%"=="" set "json_path=reports\graph\evidence_overlay.json"
"%VENV_DIR%\Scripts\gbmbert-apply-evidence-overlay.exe" "%graph_path%" "%curated_path%" "%overlay_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Evidence overlay graph exported.
pause
goto menu

:overlay_diff
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "raw_graph_path=Raw graph-record JSONL path: "
set /p "overlay_graph_path=Overlay graph-record JSONL path: "
set /p "md_path=Overlay diff Markdown output [reports\graph\evidence_overlay_diff.md]: "
set /p "json_path=Overlay diff JSON output [reports\graph\evidence_overlay_diff.json]: "
if "%raw_graph_path%"=="" (
    echo Raw graph path is required.
    pause
    goto menu
)
if "%overlay_graph_path%"=="" (
    echo Overlay graph path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\graph\evidence_overlay_diff.md"
if "%json_path%"=="" set "json_path=reports\graph\evidence_overlay_diff.json"
"%VENV_DIR%\Scripts\gbmbert-overlay-diff.exe" "%raw_graph_path%" "%overlay_graph_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Evidence overlay diff report complete.
pause
goto menu

:overlay_load_guard
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "overlay_graph_path=Overlay graph-record JSONL path: "
set /p "md_path=Overlay load guard Markdown output [reports\graph\overlay_load_guard.md]: "
set /p "json_path=Overlay load guard JSON output [reports\graph\overlay_load_guard.json]: "
if "%overlay_graph_path%"=="" (
    echo Overlay graph path is required.
    pause
    goto menu
)
if "%md_path%"=="" set "md_path=reports\graph\overlay_load_guard.md"
if "%json_path%"=="" set "json_path=reports\graph\overlay_load_guard.json"
"%VENV_DIR%\Scripts\gbmbert-overlay-load-guard.exe" "%overlay_graph_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Overlay load guard complete.
pause
goto menu

:curation_smoke_workflow
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "predictions_path=Prediction JSONL [reports\training\evidence_smoke_fixture\sample_graph_predictions.jsonl]: "
set /p "graph_path=Graph JSONL [data\examples\graph_records_sample.jsonl]: "
set /p "reviewed_path=Reviewed prediction queue [data\review\sample_graph_prediction_reviewed_queue.jsonl]: "
set /p "output_dir=Workflow output dir [data\processed\curation_smoke_workflow]: "
set /p "reports_dir=Workflow reports dir [reports\review\curation_smoke_workflow]: "
if "%predictions_path%"=="" set "predictions_path=reports\training\evidence_smoke_fixture\sample_graph_predictions.jsonl"
if "%graph_path%"=="" set "graph_path=data\examples\graph_records_sample.jsonl"
if "%reviewed_path%"=="" set "reviewed_path=data\review\sample_graph_prediction_reviewed_queue.jsonl"
if "%output_dir%"=="" set "output_dir=data\processed\curation_smoke_workflow"
if "%reports_dir%"=="" set "reports_dir=reports\review\curation_smoke_workflow"
"%VENV_DIR%\Scripts\gbmbert-run-curation-smoke-workflow.exe" --predictions-jsonl "%predictions_path%" --graph-jsonl "%graph_path%" --reviewed-queue-jsonl "%reviewed_path%" --output-dir "%output_dir%" --reports-dir "%reports_dir%"
if errorlevel 1 goto command_failed
echo.
echo Curation smoke workflow complete.
pause
goto menu

:curation_handoff_bundle
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "bundle_dir=Curation handoff bundle dir [data\processed\curation_handoff_bundle]: "
set /p "md_path=Curation handoff Markdown manifest [data\processed\curation_handoff_bundle\curation_handoff_bundle.md]: "
set /p "json_path=Curation handoff JSON manifest [data\processed\curation_handoff_bundle\curation_handoff_bundle.json]: "
if "%bundle_dir%"=="" set "bundle_dir=data\processed\curation_handoff_bundle"
if "%md_path%"=="" set "md_path=%bundle_dir%\curation_handoff_bundle.md"
if "%json_path%"=="" set "json_path=%bundle_dir%\curation_handoff_bundle.json"
"%VENV_DIR%\Scripts\gbmbert-build-curation-handoff.exe" --output-dir "%bundle_dir%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curation handoff bundle complete.
pause
goto menu

:validate_curation_handoff
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "manifest_path=Curation handoff manifest [data\processed\curation_handoff_bundle\curation_handoff_bundle.json]: "
set /p "md_path=Validation Markdown output [reports\review\curation_handoff_validation.md]: "
set /p "json_path=Validation JSON output [reports\review\curation_handoff_validation.json]: "
if "%manifest_path%"=="" set "manifest_path=data\processed\curation_handoff_bundle\curation_handoff_bundle.json"
if "%md_path%"=="" set "md_path=reports\review\curation_handoff_validation.md"
if "%json_path%"=="" set "json_path=reports\review\curation_handoff_validation.json"
"%VENV_DIR%\Scripts\gbmbert-validate-curation-handoff.exe" "%manifest_path%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curation handoff validation complete.
pause
goto menu

:register_curation_run
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "workflow_path=Workflow report JSON [reports\review\curation_smoke_workflow\curation_smoke_workflow.json]: "
set /p "handoff_path=Handoff manifest JSON [data\processed\curation_handoff_bundle\curation_handoff_bundle.json]: "
set /p "registry_path=Run registry JSON [reports\review\curation_run_registry.json]: "
set /p "md_path=Run registry Markdown output [reports\review\curation_run_registry.md]: "
if "%workflow_path%"=="" set "workflow_path=reports\review\curation_smoke_workflow\curation_smoke_workflow.json"
if "%handoff_path%"=="" set "handoff_path=data\processed\curation_handoff_bundle\curation_handoff_bundle.json"
if "%registry_path%"=="" set "registry_path=reports\review\curation_run_registry.json"
if "%md_path%"=="" set "md_path=reports\review\curation_run_registry.md"
"%VENV_DIR%\Scripts\gbmbert-register-curation-run.exe" "%workflow_path%" --handoff-manifest-json "%handoff_path%" --registry-json "%registry_path%" --report-markdown-output "%md_path%"
if errorlevel 1 goto command_failed
echo.
echo Curation run registered.
pause
goto menu

:search_curated_evidence
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "curated_path=Curated evidence JSONL [data\processed\curation_smoke_workflow\curated_evidence_predictions.jsonl]: "
set /p "search_text=Text contains: "
set /p "review_status=Review status: "
set /p "md_path=Search Markdown output [reports\review\curated_evidence_search.md]: "
set /p "json_path=Search JSON output [reports\review\curated_evidence_search.json]: "
if "%curated_path%"=="" set "curated_path=data\processed\curation_smoke_workflow\curated_evidence_predictions.jsonl"
if "%md_path%"=="" set "md_path=reports\review\curated_evidence_search.md"
if "%json_path%"=="" set "json_path=reports\review\curated_evidence_search.json"
"%VENV_DIR%\Scripts\gbmbert-search-curated-evidence.exe" "%curated_path%" --text "%search_text%" --review-status "%review_status%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curated evidence search complete.
pause
goto menu

:plan_active_learning_batches
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "candidate_path=Active learning candidates JSONL [data\processed\curation_smoke_workflow\active_learning_candidates.jsonl]: "
set /p "batch_path=Batch JSONL output [data\processed\curation_regression_pack\active_learning_batches.jsonl]: "
set /p "csv_path=Batch CSV output [data\processed\curation_regression_pack\active_learning_batches.csv]: "
set /p "md_path=Batch report Markdown [reports\review\curation_regression_pack\active_learning_batches.md]: "
set /p "json_path=Batch report JSON [reports\review\curation_regression_pack\active_learning_batches.json]: "
if "%candidate_path%"=="" set "candidate_path=data\processed\curation_smoke_workflow\active_learning_candidates.jsonl"
if "%batch_path%"=="" set "batch_path=data\processed\curation_regression_pack\active_learning_batches.jsonl"
if "%csv_path%"=="" set "csv_path=data\processed\curation_regression_pack\active_learning_batches.csv"
if "%md_path%"=="" set "md_path=reports\review\curation_regression_pack\active_learning_batches.md"
if "%json_path%"=="" set "json_path=reports\review\curation_regression_pack\active_learning_batches.json"
"%VENV_DIR%\Scripts\gbmbert-plan-active-learning-batches.exe" "%candidate_path%" "%batch_path%" --csv-output "%csv_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Active learning batches planned.
pause
goto menu

:revert_evidence_overlay
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "overlay_path=Overlay graph JSONL [data\processed\curation_smoke_workflow\evidence_overlay_graph_records.jsonl]: "
set /p "reverted_path=Reverted graph JSONL [data\processed\curation_regression_pack\reverted_graph_records.jsonl]: "
set /p "md_path=Revert report Markdown [reports\review\curation_regression_pack\overlay_revert.md]: "
set /p "json_path=Revert report JSON [reports\review\curation_regression_pack\overlay_revert.json]: "
if "%overlay_path%"=="" set "overlay_path=data\processed\curation_smoke_workflow\evidence_overlay_graph_records.jsonl"
if "%reverted_path%"=="" set "reverted_path=data\processed\curation_regression_pack\reverted_graph_records.jsonl"
if "%md_path%"=="" set "md_path=reports\review\curation_regression_pack\overlay_revert.md"
if "%json_path%"=="" set "json_path=reports\review\curation_regression_pack\overlay_revert.json"
"%VENV_DIR%\Scripts\gbmbert-revert-evidence-overlay.exe" "%overlay_path%" "%reverted_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Evidence overlay reverted.
pause
goto menu

:curation_regression_pack
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
"%VENV_DIR%\Scripts\gbmbert-run-curation-regression-pack.exe"
if errorlevel 1 goto command_failed
echo.
echo Curation regression pack complete.
pause
goto menu

:browse_curation_runs
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "registry_path=Curation registry JSON [reports\review\curation_run_registry.json]: "
set /p "md_path=Run browser Markdown [reports\review\curation_run_browser.md]: "
set /p "json_path=Run browser JSON [reports\review\curation_run_browser.json]: "
if "%registry_path%"=="" set "registry_path=reports\review\curation_run_registry.json"
if "%md_path%"=="" set "md_path=reports\review\curation_run_browser.md"
if "%json_path%"=="" set "json_path=reports\review\curation_run_browser.json"
"%VENV_DIR%\Scripts\gbmbert-browse-curation-runs.exe" --registry-json "%registry_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Curation run browser report complete.
pause
goto menu

:artifact_detail
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "artifact_query=Artifact path, type, SHA, or text [active_learning_batches]: "
set /p "artifact_index=Artifact index JSON [reports\artifact_index.json]: "
set /p "md_path=Artifact detail Markdown [reports\artifact_detail.md]: "
set /p "json_path=Artifact detail JSON [reports\artifact_detail.json]: "
if "%artifact_query%"=="" set "artifact_query=active_learning_batches"
if "%artifact_index%"=="" set "artifact_index=reports\artifact_index.json"
if "%md_path%"=="" set "md_path=reports\artifact_detail.md"
if "%json_path%"=="" set "json_path=reports\artifact_detail.json"
"%VENV_DIR%\Scripts\gbmbert-artifact-detail.exe" "%artifact_query%" --index-json "%artifact_index%" --markdown-output "%md_path%" --json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Artifact detail report complete.
pause
goto menu

:active_learning_batch_status
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "batch_path=Batch JSONL [data\processed\curation_regression_pack\active_learning_batches.jsonl]: "
set /p "reviewed_path=Reviewed queue JSONL [data\processed\curation_regression_pack\prediction_reviewed_queue.jsonl]: "
set /p "md_path=Batch status Markdown [reports\review\curation_regression_pack\active_learning_batch_status.md]: "
set /p "json_path=Batch status JSON [reports\review\curation_regression_pack\active_learning_batch_status.json]: "
if "%batch_path%"=="" set "batch_path=data\processed\curation_regression_pack\active_learning_batches.jsonl"
if "%reviewed_path%"=="" set "reviewed_path=data\processed\curation_regression_pack\prediction_reviewed_queue.jsonl"
if "%md_path%"=="" set "md_path=reports\review\curation_regression_pack\active_learning_batch_status.md"
if "%json_path%"=="" set "json_path=reports\review\curation_regression_pack\active_learning_batch_status.json"
"%VENV_DIR%\Scripts\gbmbert-active-learning-batch-status.exe" "%batch_path%" --reviewed-queue-jsonl "%reviewed_path%" --report-markdown-output "%md_path%" --report-json-output "%json_path%"
if errorlevel 1 goto command_failed
echo.
echo Active learning batch status complete.
pause
goto menu

:export_active_learning_batch_csv
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "batch_path=Batch JSONL [data\processed\curation_regression_pack\active_learning_batches.jsonl]: "
set /p "batch_id=Batch ID [ALBATCH-001]: "
set /p "csv_path=Batch CSV output [data\review\active_learning_batch_ALBATCH-001.csv]: "
set /p "reviewer=Assigned reviewer [curator]: "
if "%batch_path%"=="" set "batch_path=data\processed\curation_regression_pack\active_learning_batches.jsonl"
if "%batch_id%"=="" set "batch_id=ALBATCH-001"
if "%csv_path%"=="" set "csv_path=data\review\active_learning_batch_ALBATCH-001.csv"
if "%reviewer%"=="" set "reviewer=curator"
"%VENV_DIR%\Scripts\gbmbert-export-active-learning-batch-csv.exe" "%batch_path%" "%batch_id%" "%csv_path%" --assigned-reviewer "%reviewer%" --report-markdown-output reports\review\active_learning_batch_roundtrip_export.md
if errorlevel 1 goto command_failed
echo.
echo Active learning batch CSV exported.
pause
goto menu

:import_active_learning_batch_csv
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "csv_path=Edited batch CSV [data\review\active_learning_batch_ALBATCH-001.csv]: "
set /p "output_path=Reviewed queue JSONL output [data\review\active_learning_batch_reviewed_queue.jsonl]: "
set /p "reviewed_path=Existing reviewed queue JSONL [data\processed\curation_regression_pack\prediction_reviewed_queue.jsonl]: "
if "%csv_path%"=="" set "csv_path=data\review\active_learning_batch_ALBATCH-001.csv"
if "%output_path%"=="" set "output_path=data\review\active_learning_batch_reviewed_queue.jsonl"
if "%reviewed_path%"=="" set "reviewed_path=data\processed\curation_regression_pack\prediction_reviewed_queue.jsonl"
"%VENV_DIR%\Scripts\gbmbert-import-active-learning-batch-csv.exe" "%csv_path%" "%output_path%" --reviewed-queue-jsonl "%reviewed_path%" --overwrite --report-markdown-output reports\review\active_learning_batch_roundtrip_import.md
if errorlevel 1 goto command_failed
echo.
echo Active learning batch CSV imported.
pause
goto menu

:promote_evidence_overlay
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "overlay_path=Overlay graph JSONL [data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl]: "
if "%overlay_path%"=="" set "overlay_path=data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl"
"%VENV_DIR%\Scripts\gbmbert-graph-quality-report.exe" "%overlay_path%" --markdown-output reports\review\curation_regression_pack\overlay_graph_quality.md --json-output reports\review\curation_regression_pack\overlay_graph_quality.json
if errorlevel 1 goto command_failed
"%VENV_DIR%\Scripts\gbmbert-promote-evidence-overlay.exe" --overlay-graph-jsonl "%overlay_path%" --json-output reports\review\curation_regression_pack\evidence_overlay_promotion_gate.json --markdown-output reports\review\curation_regression_pack\evidence_overlay_promotion_gate.md
if errorlevel 1 goto command_failed
echo.
echo Evidence overlay promotion gate passed.
pause
goto menu

:relation_extraction_audit
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Graph JSONL [data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl]: "
if "%graph_path%"=="" set "graph_path=data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl"
"%VENV_DIR%\Scripts\gbmbert-relation-extraction-audit.exe" "%graph_path%" --markdown-output reports\graph\relation_extraction_audit.md --json-output reports\graph\relation_extraction_audit.json
if errorlevel 1 goto command_failed
echo.
echo Relation extraction audit complete.
pause
goto menu

:scope_drift_monitor
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
"%VENV_DIR%\Scripts\gbmbert-scope-drift-monitor.exe" --markdown-output reports\platform_regression\scope_drift.md --json-output reports\platform_regression\scope_drift.json
if errorlevel 1 goto command_failed
echo.
echo Scope drift monitor passed.
pause
goto menu

:platform_regression
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
"%VENV_DIR%\Scripts\gbmbert-platform-regression.exe"
if errorlevel 1 goto command_failed
echo.
echo Platform regression complete.
pause
goto menu

:build_gold_seed_dataset
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "output_dir=Gold seed output dir [data\training\gold_seed]: "
set /p "reviewed_path=Reviewed graph queue JSONL [data\review\evidence_reviewed_queue.jsonl]: "
set /p "prediction_reviewed_path=Reviewed prediction queue JSONL [data\review\evidence_prediction_reviewed_queue.jsonl]: "
set /p "entity_path=Optional entity JSONL [data\processed\entities.jsonl]: "
if "%output_dir%"=="" set "output_dir=data\training\gold_seed"
if "%reviewed_path%"=="" set "reviewed_path=data\review\evidence_reviewed_queue.jsonl"
if "%prediction_reviewed_path%"=="" set "prediction_reviewed_path=data\review\evidence_prediction_reviewed_queue.jsonl"
if "%entity_path%"=="" set "entity_path=data\processed\entities.jsonl"
"%VENV_DIR%\Scripts\gbmbert-build-gold-seed-dataset.exe" "%output_dir%" --reviewed-queue-jsonl "%reviewed_path%" --prediction-reviewed-queue-jsonl "%prediction_reviewed_path%" --entity-jsonl "%entity_path%" --json-output reports\training\gold_seed_manifest.json --markdown-output reports\training\gold_seed_manifest.md
if errorlevel 1 goto command_failed
echo.
echo Gold seed dataset build complete.
pause
goto menu

:adjudication_report
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "left_path=First reviewed JSONL: "
set /p "right_path=Second reviewed JSONL: "
if "%left_path%"=="" (
    echo First reviewed JSONL is required.
    pause
    goto menu
)
if "%right_path%"=="" (
    echo Second reviewed JSONL is required.
    pause
    goto menu
)
"%VENV_DIR%\Scripts\gbmbert-adjudication-report.exe" "%left_path%" "%right_path%" --markdown-output reports\review\adjudication_report.md --json-output reports\review\adjudication_report.json
if errorlevel 1 goto command_failed
echo.
echo Adjudication report complete.
pause
goto menu

:normalize_graph_entities
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Input graph JSONL [data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl]: "
set /p "output_path=Normalized graph JSONL [data\processed\curation_regression_pack\normalized_graph_records.jsonl]: "
set /p "synonym_path=Synonym table [data\examples\entity_synonyms.json]: "
if "%graph_path%"=="" set "graph_path=data\processed\curation_regression_pack\evidence_overlay_graph_records.jsonl"
if "%output_path%"=="" set "output_path=data\processed\curation_regression_pack\normalized_graph_records.jsonl"
if "%synonym_path%"=="" set "synonym_path=data\examples\entity_synonyms.json"
"%VENV_DIR%\Scripts\gbmbert-normalize-graph-entities.exe" "%graph_path%" "%output_path%" --synonym-table "%synonym_path%" --markdown-output reports\graph\entity_normalization.md --json-output reports\graph\entity_normalization.json
if errorlevel 1 goto command_failed
echo.
echo Graph entity normalization complete.
pause
goto menu

:enrich_relation_qualifiers
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "graph_path=Input graph JSONL [data\processed\curation_regression_pack\normalized_graph_records.jsonl]: "
set /p "output_path=Qualifier-enriched graph JSONL [data\processed\curation_regression_pack\qualifier_enriched_graph_records.jsonl]: "
if "%graph_path%"=="" set "graph_path=data\processed\curation_regression_pack\normalized_graph_records.jsonl"
if "%output_path%"=="" set "output_path=data\processed\curation_regression_pack\qualifier_enriched_graph_records.jsonl"
"%VENV_DIR%\Scripts\gbmbert-enrich-relation-qualifiers.exe" "%graph_path%" "%output_path%" --markdown-output reports\graph\qualifier_enrichment.md --json-output reports\graph\qualifier_enrichment.json
if errorlevel 1 goto command_failed
echo.
echo Relation qualifier enrichment complete.
pause
goto menu

:training_readiness_report
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Dataset or split directory [data\training\annotation_splits]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_splits"
"%VENV_DIR%\Scripts\gbmbert-training-readiness-report.exe" "%dataset_dir%" --markdown-output reports\training\training_readiness.md --json-output reports\training\training_readiness.json --allow-not-ready
if errorlevel 1 goto command_failed
echo.
echo Training readiness report complete.
pause
goto menu

:split_by_pmid
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Annotation dataset directory [data\training\annotation_dataset]: "
set /p "output_dir=PMID-safe split output dir [data\training\annotation_splits_pmid]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_dataset"
if "%output_dir%"=="" set "output_dir=data\training\annotation_splits_pmid"
"%VENV_DIR%\Scripts\gbmbert-split-by-pmid.exe" "%dataset_dir%" "%output_dir%" --markdown-output reports\training\pmid_split_manifest.md --json-output reports\training\pmid_split_manifest.json
if errorlevel 1 goto command_failed
echo.
echo PMID-safe dataset split complete.
pause
goto menu

:repair_evidence_labels
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Dataset directory [data\training\annotation_dataset]: "
set /p "output_dir=Repaired dataset output dir [data\training\annotation_dataset_repaired]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\annotation_dataset"
if "%output_dir%"=="" set "output_dir=data\training\annotation_dataset_repaired"
"%VENV_DIR%\Scripts\gbmbert-repair-evidence-labels.exe" "%dataset_dir%" "%output_dir%" --markdown-output reports\training\evidence_label_repair.md --json-output reports\training\evidence_label_repair.json --allow-unrepaired
if errorlevel 1 goto command_failed
echo.
echo Evidence label repair complete.
pause
goto menu

:gold_training_pack
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "prediction_reviewed_path=Reviewed prediction queue JSONL [data\review\sample_graph_prediction_reviewed_queue.jsonl]: "
set /p "output_dir=Gold pack output dir [data\training\gold_pack]: "
set /p "reports_dir=Gold pack reports dir [reports\training\gold_pack]: "
if "%prediction_reviewed_path%"=="" set "prediction_reviewed_path=data\review\sample_graph_prediction_reviewed_queue.jsonl"
if "%output_dir%"=="" set "output_dir=data\training\gold_pack"
if "%reports_dir%"=="" set "reports_dir=reports\training\gold_pack"
"%VENV_DIR%\Scripts\gbmbert-build-gold-training-pack.exe" --prediction-reviewed-queue-jsonl "%prediction_reviewed_path%" --output-dir "%output_dir%" --reports-dir "%reports_dir%" --allow-not-ready
if errorlevel 1 goto command_failed
echo.
echo Gold training pack complete.
pause
goto menu

:build_relation_negatives
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_path=Relation dataset file or directory [data\training\ncbi_env_smoke_annotation_dataset]: "
set /p "output_path=Negative relation JSONL [data\training\relation_negatives.jsonl]: "
if "%dataset_path%"=="" set "dataset_path=data\training\ncbi_env_smoke_annotation_dataset"
if "%output_path%"=="" set "output_path=data\training\relation_negatives.jsonl"
"%VENV_DIR%\Scripts\gbmbert-build-relation-negatives.exe" "%dataset_path%" "%output_path%" --markdown-output reports\training\relation_negatives.md --json-output reports\training\relation_negatives.json
if errorlevel 1 goto command_failed
echo.
echo Relation negative examples complete.
pause
goto menu

:relation_dataset_quality
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_path=Relation dataset file or directory [data\training\relation_negatives.jsonl]: "
if "%dataset_path%"=="" set "dataset_path=data\training\relation_negatives.jsonl"
"%VENV_DIR%\Scripts\gbmbert-relation-dataset-quality.exe" "%dataset_path%" --markdown-output reports\training\relation_dataset_quality.md --json-output reports\training\relation_dataset_quality.json
if errorlevel 1 goto command_failed
echo.
echo Relation dataset quality report complete.
pause
goto menu

:merge_relation_pack
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "positive_path=Positive relation dataset file or directory [data\training\ncbi_env_smoke_annotation_dataset]: "
set /p "negative_path=Negative relation JSONL [data\training\relation_negatives.jsonl]: "
set /p "output_path=Merged relation training JSONL [data\training\relation_training_pack.jsonl]: "
if "%positive_path%"=="" set "positive_path=data\training\ncbi_env_smoke_annotation_dataset"
if "%negative_path%"=="" set "negative_path=data\training\relation_negatives.jsonl"
if "%output_path%"=="" set "output_path=data\training\relation_training_pack.jsonl"
"%VENV_DIR%\Scripts\gbmbert-merge-relation-pack.exe" "%positive_path%" "%negative_path%" "%output_path%" --markdown-output reports\training\relation_training_pack.md --json-output reports\training\relation_training_pack.json --allow-not-ready
if errorlevel 1 goto command_failed
echo.
echo Relation training pack merge complete.
pause
goto menu

:evidence_training_pack
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "dataset_dir=Annotation dataset directory [data\training\ncbi_env_smoke_annotation_dataset]: "
set /p "output_dir=Evidence pack output dir [data\training\evidence_pack]: "
set /p "reports_dir=Evidence pack reports dir [reports\training\evidence_pack]: "
if "%dataset_dir%"=="" set "dataset_dir=data\training\ncbi_env_smoke_annotation_dataset"
if "%output_dir%"=="" set "output_dir=data\training\evidence_pack"
if "%reports_dir%"=="" set "reports_dir=reports\training\evidence_pack"
"%VENV_DIR%\Scripts\gbmbert-build-evidence-training-pack.exe" "%dataset_dir%" --output-dir "%output_dir%" --reports-dir "%reports_dir%" --min-examples-per-task 1 --min-examples-per-label 1 --allow-not-ready
if errorlevel 1 goto command_failed
echo.
echo Evidence-only training pack complete.
pause
goto menu

:relation_training_pack
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "input_path=Merged relation JSONL or dataset [data\training\relation_training_pack.jsonl]: "
set /p "output_dir=Relation pack output dir [data\training\relation_pack]: "
set /p "reports_dir=Relation pack reports dir [reports\training\relation_pack]: "
if "%input_path%"=="" set "input_path=data\training\relation_training_pack.jsonl"
if "%output_dir%"=="" set "output_dir=data\training\relation_pack"
if "%reports_dir%"=="" set "reports_dir=reports\training\relation_pack"
"%VENV_DIR%\Scripts\gbmbert-build-relation-training-pack.exe" "%input_path%" --output-dir "%output_dir%" --reports-dir "%reports_dir%" --min-examples-per-task 1 --min-examples-per-label 1 --allow-not-ready
if errorlevel 1 goto command_failed
echo.
echo Relation-only training pack complete.
pause
goto menu

:review_training_config
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "config_path=Training config [configs\training\gbmbert_evidence_pubmedbert.json]: "
set /p "dataset_dir=Prepared split directory [data\training\evidence_pack\annotation_splits]: "
set /p "label_map_dir=Label map directory [data\training\evidence_pack\label_maps]: "
if "%config_path%"=="" set "config_path=configs\training\gbmbert_evidence_pubmedbert.json"
if "%dataset_dir%"=="" set "dataset_dir=data\training\evidence_pack\annotation_splits"
if "%label_map_dir%"=="" set "label_map_dir=data\training\evidence_pack\label_maps"
"%VENV_DIR%\Scripts\gbmbert-review-training-config.exe" "%config_path%" "%dataset_dir%" --label-map-dir "%label_map_dir%" --markdown-output reports\training\training_config_review.md --json-output reports\training\training_config_review.json
if errorlevel 1 goto command_failed
echo.
echo Training config review complete.
pause
goto menu

:compare_training_packs
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
"%VENV_DIR%\Scripts\gbmbert-compare-training-packs.exe" --markdown-output reports\training\training_pack_comparison.md --json-output reports\training\training_pack_comparison.json
if errorlevel 1 goto command_failed
echo.
echo Training pack comparison complete.
pause
goto menu

:audit_model_registry
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "registry_path=Checkpoint registry [models\checkpoint_registry.json]: "
if "%registry_path%"=="" set "registry_path=models\checkpoint_registry.json"
"%VENV_DIR%\Scripts\gbmbert-audit-model-registry.exe" "%registry_path%" --markdown-output reports\training\model_registry_audit.md --json-output reports\training\model_registry_audit.json --allow-findings
if errorlevel 1 goto command_failed
echo.
echo Model registry audit complete.
pause
goto menu

:training_governance_suite
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "output_dir=Training governance reports dir [reports\training\governance]: "
if "%output_dir%"=="" set "output_dir=reports\training\governance"
"%VENV_DIR%\Scripts\gbmbert-run-training-governance-suite.exe" --output-dir "%output_dir%" --allow-findings
if errorlevel 1 goto command_failed
echo.
echo Training governance suite complete.
pause
goto menu

:strict_training_governance
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "output_dir=Strict training governance reports dir [reports\training\governance_strict]: "
if "%output_dir%"=="" set "output_dir=reports\training\governance_strict"
"%VENV_DIR%\Scripts\gbmbert-run-strict-training-governance.exe" --output-dir "%output_dir%" --allow-findings
if errorlevel 1 goto command_failed
echo.
echo Strict training governance audit complete.
pause
goto menu

:local_verification
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Running canonical local verification...
"%VENV_DIR%\Scripts\gbmbert-verify-local.exe"
if errorlevel 1 goto command_failed
echo.
echo Local verification complete.
pause
goto menu

:artifact_policy_check
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Checking tracked artifact policy...
"%VENV_DIR%\Scripts\gbmbert-check-artifact-policy.exe" --markdown-output reports\platform_regression\artifact_policy.md --json-output reports\platform_regression\artifact_policy.json
if errorlevel 1 goto command_failed
echo.
echo Artifact policy check complete.
pause
goto menu

:launcher_menu_check
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Checking launcher menu structure...
"%VENV_DIR%\Scripts\gbmbert-check-launcher-menu.exe" --markdown-output reports\platform_regression\launcher_menu_check.md --json-output reports\platform_regression\launcher_menu_check.json
if errorlevel 1 goto command_failed
echo.
echo Launcher menu check complete.
pause
goto menu

:curated_fixture_import
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "evidence_path=Curated evidence JSONL [data\training\curated_expansion\evidence_full_label.jsonl]: "
set /p "entity_path=Curated entity JSONL [data\training\curated_expansion\gold_entities.jsonl]: "
set /p "reviewed_path=Reviewed queue JSONL [data\training\curated_expansion\gold_reviewed_queue.jsonl]: "
set /p "output_dir=Import output dir [data\training\curated_import]: "
if "%evidence_path%"=="" set "evidence_path=data\training\curated_expansion\evidence_full_label.jsonl"
if "%entity_path%"=="" set "entity_path=data\training\curated_expansion\gold_entities.jsonl"
if "%reviewed_path%"=="" set "reviewed_path=data\training\curated_expansion\gold_reviewed_queue.jsonl"
if "%output_dir%"=="" set "output_dir=data\training\curated_import"
"%VENV_DIR%\Scripts\gbmbert-import-curated-training-fixture.exe" --evidence-jsonl "%evidence_path%" --entity-jsonl "%entity_path%" --reviewed-queue-jsonl "%reviewed_path%" --output-dir "%output_dir%" --markdown-output reports\training\curated_fixture_import.md --json-output reports\training\curated_fixture_import.json
if errorlevel 1 goto command_failed
echo.
echo Curated fixture import check complete.
pause
goto menu

:curated_fixture_import_multibatch
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Importing all curated expansion rounds (multi-batch)...
"%VENV_DIR%\Scripts\gbmbert-import-curated-training-fixture.exe" --evidence-jsonl data\training\curated_expansion\evidence_full_label.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round2.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round3.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round4.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round5.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round6.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round7.jsonl --entity-jsonl data\training\curated_expansion\gold_entities.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round2.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round3.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round4.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round5.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round6.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round7.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round2.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round3.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round4.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round5.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round6.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round7.jsonl --output-dir data\training\curated_import --no-copy --markdown-output reports\training\curated_fixture_import.md --json-output reports\training\curated_fixture_import.json
if errorlevel 1 goto command_failed
echo.
echo Multi-batch curated fixture import complete.
pause
goto menu

:curated_round_rebuild
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Rebuilding every curated-round report (import, packs, governance, promotion, planning)...
"%VENV_DIR%\Scripts\gbmbert-rebuild-curated-rounds.exe" --markdown-output reports\training\curated_round_rebuild.md --json-output reports\training\curated_round_rebuild.json
if errorlevel 1 goto command_failed
echo.
echo Curated round rebuild complete. Run 16BI (local verification) next for platform checks.
pause
goto menu

:curated_provenance_diff
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Diffing curated batch provenance...
"%VENV_DIR%\Scripts\gbmbert-curated-provenance-diff.exe" --evidence-jsonl data\training\curated_expansion\evidence_full_label.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round2.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round3.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round4.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round5.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round6.jsonl --evidence-jsonl data\training\curated_expansion\evidence_round7.jsonl --entity-jsonl data\training\curated_expansion\gold_entities.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round2.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round3.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round4.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round5.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round6.jsonl --entity-jsonl data\training\curated_expansion\gold_entities_round7.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round2.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round3.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round4.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round5.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round6.jsonl --reviewed-queue-jsonl data\training\curated_expansion\gold_reviewed_queue_round7.jsonl --markdown-output reports\training\curated_provenance_diff.md --json-output reports\training\curated_provenance_diff.json --allow-findings
if errorlevel 1 goto command_failed
echo.
echo Curated provenance diff complete.
pause
goto menu

:gold_pack_promotion_review
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Reviewing gold-pack promotion thresholds...
"%VENV_DIR%\Scripts\gbmbert-review-gold-pack-promotion.exe" --markdown-output reports\training\gold_pack\gold_pack_promotion_review.md --json-output reports\training\gold_pack\gold_pack_promotion_review.json --allow-blockers
if errorlevel 1 goto command_failed
echo.
echo Gold-pack promotion review complete.
pause
goto menu

:promotion_planning_report
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Planning scaffold-only gold-pack promotion curation batches...
"%VENV_DIR%\Scripts\gbmbert-plan-gold-pack-promotion.exe" --markdown-output reports\training\gold_pack\gold_pack_promotion_plan.md --json-output reports\training\gold_pack\gold_pack_promotion_plan.json
if errorlevel 1 goto command_failed
echo.
echo Promotion planning report complete.
pause
goto menu

:governance_detail_export
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Exporting governance detail links...
"%VENV_DIR%\Scripts\gbmbert-export-governance-detail-links.exe" --markdown-output reports\training\governance_detail_links.md --json-output reports\training\governance_detail_links.json
if errorlevel 1 goto command_failed
echo.
echo Governance detail export complete.
pause
goto menu

:ci_summary_contract
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Checking CI summary artifact contract...
"%VENV_DIR%\Scripts\gbmbert-check-ci-summary-contract.exe" --summary reports\platform_regression\ci_report_summary.md --markdown-output reports\platform_regression\ci_summary_contract.md --json-output reports\platform_regression\ci_summary_contract.json
if errorlevel 1 goto command_failed
echo.
echo CI summary contract check complete.
pause
goto menu

:run_explorer_sample
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Starting Knowledge Graph Explorer with sample data...
echo Browser URL: http://127.0.0.1:8765/
start "GBM Knowledge Graph Explorer" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%CD%'; . '.\.venv\Scripts\Activate.ps1'; python -m gbmbert.knowledge_graph.explorer --sample-data 'data\examples\graph_records_sample.jsonl' --host 127.0.0.1 --port 8765 --open"
pause
goto menu

:run_explorer_artifact
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
set /p "artifact_selector=Graph artifact path, filename, or stem: "
set /p "artifact_index=Artifact index JSON [reports\artifact_index.json]: "
if "%artifact_selector%"=="" (
    echo Graph artifact selector is required.
    pause
    goto menu
)
if "%artifact_index%"=="" set "artifact_index=reports\artifact_index.json"
echo Starting Knowledge Graph Explorer with selected graph artifact...
echo Browser URL: http://127.0.0.1:8765/
start "GBM Knowledge Graph Explorer" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%CD%'; . '.\.venv\Scripts\Activate.ps1'; python -m gbmbert.knowledge_graph.explorer --artifact-index '%artifact_index%' --artifact '%artifact_selector%' --host 127.0.0.1 --port 8765 --open"
pause
goto menu

:run_explorer_baseline
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Starting Knowledge Graph Explorer with baseline smoke data...
echo Browser URL: http://127.0.0.1:8765/
start "GBM Knowledge Graph Explorer" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%CD%'; . '.\.venv\Scripts\Activate.ps1'; python -m gbmbert.knowledge_graph.explorer --baseline-data --host 127.0.0.1 --port 8765 --open"
pause
goto menu

:run_explorer_neo4j
call :ensure_venv
if errorlevel 1 goto menu
call :check_venv
if errorlevel 1 goto menu
echo.
echo Starting Knowledge Graph Explorer with Neo4j...
echo Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env first.
echo Browser URL: http://127.0.0.1:8765/
start "GBM Knowledge Graph Explorer" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%CD%'; . '.\.venv\Scripts\Activate.ps1'; python -m gbmbert.knowledge_graph.explorer --neo4j --host 127.0.0.1 --port 8765 --open"
pause
goto menu

:ensure_venv
if exist "%PYTHON_EXE%" exit /b 0
echo.
echo Local virtual environment does not exist yet.
echo Choose option 1 first, then return to this option.
pause
exit /b 1

:create_supported_venv
echo Creating local virtual environment with Python 3.12 64-bit...
py -3.12-64 -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Failed with py -3.12-64. Trying py -3.12...
    py -3.12 -m venv "%VENV_DIR%"
)
if errorlevel 1 (
    echo Failed with Python 3.12. Trying Python 3.11 64-bit...
    py -3.11-64 -m venv "%VENV_DIR%"
)
if errorlevel 1 exit /b 1
call :check_venv
exit /b %errorlevel%

:check_venv
if not exist "%PYTHON_EXE%" exit /b 1
set "VENV_CHECK_RESULT="
set "VENV_CHECK_DETAIL="
set "VENV_CHECK_FILE=%TEMP%\gbm_venv_check_%RANDOM%_%RANDOM%.txt"
"%PYTHON_EXE%" -c "import platform, sys; ok=sys.version_info[:2] in ((3,11),(3,12)) and platform.architecture()[0]=='64bit'; print(('OK' if ok else 'BAD') + '|' + sys.version.split()[0] + ' ' + platform.architecture()[0])" > "%VENV_CHECK_FILE%"
if errorlevel 1 (
    if exist "%VENV_CHECK_FILE%" del "%VENV_CHECK_FILE%"
    exit /b 1
)
for /f "usebackq tokens=1,* delims=|" %%a in ("%VENV_CHECK_FILE%") do (
    set "VENV_CHECK_RESULT=%%a"
    set "VENV_CHECK_DETAIL=%%b"
)
if exist "%VENV_CHECK_FILE%" del "%VENV_CHECK_FILE%"
if "%VENV_CHECK_RESULT%"=="OK" exit /b 0
echo.
echo Unsupported local virtual environment: %VENV_CHECK_DETAIL%
echo This project needs 64-bit Python 3.11 or 3.12 for spaCy/SciSpaCy wheels.
echo Use option 1R to recreate .venv.
pause
exit /b 1

:command_failed
echo.
echo Command failed. Review the output above.
pause
goto menu

:end
endlocal
