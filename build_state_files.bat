@echo off
title Build State Master CSV Files
cd /d "%~dp0"
color 0B

echo.
echo ============================================================
echo   BUILD ONE CSV PER STATE
echo   Output: data\by_state\CA.csv , TX.csv , ...
echo   Also:   data\ALL_STATES_COMBINED.csv / .xlsx
echo   Close Excel files first!
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

python -m scraper.build_state_files
echo.
pause
