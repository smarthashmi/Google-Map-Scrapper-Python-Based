@echo off
title Filter Small Businesses - Remove Inc Corp
cd /d "%~dp0"
color 0A

echo.
echo ============================================================
echo   REMOVE INC / CORP BUSINESSES
echo   Keeps small shops that are easier to dial
echo.
echo   Output:
echo     data\by_state_small\CA.csv , TX.csv , ...
echo     data\SMALL_BUSINESSES_DIAL.csv
echo     data\SMALL_BUSINESSES_DIAL.xlsx
echo     data\REMOVED_INC_CORP.csv   (removed list)
echo ============================================================
echo.
echo Close Excel files first!
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

python -m scraper.filter_small
echo.
pause
