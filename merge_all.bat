@echo off
title Merge All Leads Into One File
cd /d "%~dp0"
color 0B

echo.
echo ============================================================
echo   MERGE ALL DATA INTO ONE UPLOAD FILE
echo   Creates: data\ALL_LEADS_COMBINED.csv
echo            data\ALL_LEADS_COMBINED.xlsx
echo   Close Excel files first!
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

python -m scraper.merge_all
echo.
pause
