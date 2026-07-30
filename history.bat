@echo off
title Scraper History and Stats
cd /d "%~dp0"
color 0B

echo.
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Run setup.bat first.
    pause
    exit /b 1
)

python -m scraper.main history

echo.
echo Press any key to view data file locations...
pause >nul
python -m scraper.main files
echo.
pause
