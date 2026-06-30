@echo off
setlocal EnableExtensions

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
echo 1. Create local virtual environment
echo 2. Install project dependencies into local virtual environment
echo 3. Install/update project in editable dev mode
echo 4. Run tests
echo 5. Show installed dependency versions
echo 6. Open activated PowerShell in this project
echo 7. Run PubMed to entity extraction CLI
echo 8. Exit
echo.
set /p "choice=Choose an option: "

if "%choice%"=="1" goto create_venv
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto install_editable
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto show_versions
if "%choice%"=="6" goto open_shell
if "%choice%"=="7" goto run_extraction
if "%choice%"=="8" goto end

echo.
echo Invalid choice.
pause
goto menu

:create_venv
echo.
if exist "%PYTHON_EXE%" (
    echo Local virtual environment already exists.
) else (
    echo Creating local virtual environment...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed using py launcher. Trying python...
        python -m venv "%VENV_DIR%"
    )
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

:install_deps
call :ensure_venv
if errorlevel 1 goto menu
echo.
echo Upgrading pip inside local virtual environment...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto command_failed
echo.
echo Installing project dependencies from pyproject.toml...
"%PYTHON_EXE%" -m pip install -e .
if errorlevel 1 goto command_failed
echo.
echo Dependencies installed locally.
pause
goto menu

:install_editable
call :ensure_venv
if errorlevel 1 goto menu
echo.
echo Installing project in editable mode with dev dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto command_failed
"%PYTHON_EXE%" -m pip install -e ".[dev]"
if errorlevel 1 goto command_failed
echo.
echo Editable dev install complete.
pause
goto menu

:run_tests
call :ensure_venv
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
"%PYTHON_EXE%" -m pip show pydantic python-dotenv tqdm transformers torch datasets accelerate spacy scispacy pytest
echo.
pause
goto menu

:open_shell
call :ensure_venv
if errorlevel 1 goto menu
echo.
echo Opening PowerShell with the local virtual environment activated...
start "GBM Local Environment" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%CD%'; . '.\.venv\Scripts\Activate.ps1'; Write-Host 'GBM local virtual environment activated.'"
goto menu

:run_extraction
call :ensure_venv
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

:ensure_venv
if exist "%PYTHON_EXE%" exit /b 0
echo.
echo Local virtual environment does not exist yet.
echo Choose option 1 first, then return to this option.
pause
exit /b 1

:command_failed
echo.
echo Command failed. Review the output above.
pause
goto menu

:end
endlocal
