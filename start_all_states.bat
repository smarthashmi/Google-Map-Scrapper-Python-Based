@echo off
title USA Scraper - ALL 50 STATES
cd /d "%~dp0"
color 0A

echo.
echo ============================================================
echo   ALL 50 STATES MODE
echo   - Every county + city in all US states
echo   - No manual state typing needed
echo   - Auto repair keyword pack included
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Run setup.bat first.
    pause
    exit /b 1
)

python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo Playwright not installed. Running setup first...
    call setup.bat
)

echo Close all_results.csv / Excel files before starting.
echo.
python -m scraper.main all-states

echo.
pause
