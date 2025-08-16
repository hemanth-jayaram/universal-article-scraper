@echo off
REM Launch Scraper GUI

echo.
echo ========================================
echo   Article Scraper & Summarizer GUI
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please make sure you have a virtual environment set up in the 'venv' directory.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in virtual environment!
    echo.
    pause
    exit /b 1
)

REM Launch GUI
echo.
echo Launching Scraper GUI...
echo.
python scraper_gui.py

REM Handle exit
if errorlevel 1 (
    echo.
    echo GUI exited with error!
    echo.
    pause
    exit /b 1
)

echo.
echo GUI closed successfully.
echo.
