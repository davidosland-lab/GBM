@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "DASHBOARD_EXE=%VENV_DIR%\Scripts\gbmbert-dashboard.exe"
set "HOST=127.0.0.1"
set "PORT=8501"

if defined GBM_DASHBOARD_HOST set "HOST=%GBM_DASHBOARD_HOST%"
if defined GBM_DASHBOARD_PORT set "PORT=%GBM_DASHBOARD_PORT%"
if not "%~1"=="" set "PORT=%~1"
set "URL=http://%HOST%:%PORT%/"

echo ============================================================
echo GBM-AI Phase 7 Research Operations Console
echo ============================================================
echo.
echo Project folder:
echo %CD%
echo.
echo Research-use only. Not medical advice. Not intended for
echo diagnosis, treatment selection, or clinical decision-making.
echo.

if not exist "%PYTHON_EXE%" (
    echo ERROR: Local virtual environment not found at:
    echo   %VENV_DIR%
    echo.
    echo Create it with launcher_menu.bat ^(option 1^), install the
    echo package ^(option 3^), then install the dashboard extra:
    echo   "%PYTHON_EXE%" -m pip install -e ".[dashboard]"
    echo.
    pause
    exit /b 1
)

netstat -ano 2>nul | findstr ":%PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo Port %PORT% appears to be in use already.
    echo.
    echo If the dashboard is already running, open:
    echo   %URL%
    echo.
    echo Or stop the other process, or use a different port:
    echo   start_dashboard.bat 8502
    echo.
    set /p "OPEN_EXISTING=Open browser to that URL anyway? [Y/N]: "
    if /I "!OPEN_EXISTING!"=="Y" start "" "%URL%"
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
set "PATH=%VENV_DIR%\Scripts;%PATH%"
REM Prefer our delayed browser open over Streamlit's auto-open.
set "STREAMLIT_SERVER_HEADLESS=true"

echo Starting Streamlit dashboard at %URL%
echo Same entry point as launcher menu item 16CA / gbmbert-dashboard.
echo Close this window to stop the server.
echo.

start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 3; Start-Process '%URL%'"

if exist "%DASHBOARD_EXE%" (
    "%DASHBOARD_EXE%" --host "%HOST%" --port %PORT%
) else (
    "%PYTHON_EXE%" -m gbmbert.dashboard.cli --host "%HOST%" --port %PORT%
)

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Dashboard exited with an error ^(code %EXIT_CODE%^).
    echo If Streamlit is missing, install with:
    echo   "%PYTHON_EXE%" -m pip install -e ".[dashboard]"
    echo Or use launcher_menu.bat option 16CA after setup.
    echo.
)

pause
exit /b %EXIT_CODE%
