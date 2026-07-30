@echo off
title Organize Lead Data
cd /d "%~dp0"
color 0E

echo.
echo ============================================================
echo   ORGANIZING SCRAPED DATA
echo   - Clean phone numbers
echo   - Split address into street / city / state / zip
echo   - Fix hours columns
echo   - Create leads_organized.csv and leads_organized.xlsx
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

python -m scraper.organize
echo.
pause
