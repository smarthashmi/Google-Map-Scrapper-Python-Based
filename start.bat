@echo off
title USA Google Maps Scraper
cd /d "%~dp0"
color 0A

echo.
echo ============================================================
echo   USA GOOGLE MAPS SCRAPER - Auto Repair Leads
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Run setup.bat first.
    pause
    exit /b 1
)

if not exist "scraper\main.py" (
    echo ERROR: Scraper files missing.
    pause
    exit /b 1
)

REM Quick dependency check
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo Playwright not installed. Running setup first...
    call setup.bat
)

echo Starting interactive scraper...
echo   For ALL 50 states automatically, use start_all_states.bat
echo.
python -m scraper.main

echo.
echo ============================================================
echo   Session ended. Data saved in the data\ folder.
echo   TIP: Close all_results.csv / Excel files while scraping.
echo   Run history.bat to view stats.
echo ============================================================
pause
