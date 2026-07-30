@echo off
title USA Google Maps Scraper - Setup
cd /d "%~dp0"

echo.
echo ============================================================
echo   SETTING UP GOOGLE MAPS SCRAPER
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo Installing Playwright browser (Chromium)...
python -m playwright install chromium
if errorlevel 1 (
    echo ERROR: Failed to install Playwright browser.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo   Double-click start.bat to begin scraping.
echo ============================================================
pause
