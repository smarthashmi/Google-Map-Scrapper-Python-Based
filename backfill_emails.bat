@echo off
title Backfill Emails from Websites
cd /d "%~dp0"
color 0E

echo.
echo ============================================================
echo   BACKFILL EMAILS
echo   Finds emails from business websites for existing leads
echo   Close Excel / all_results.csv first!
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

python -m scraper.backfill_emails
echo.
pause
