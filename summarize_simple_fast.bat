@echo off
REM Simple Fast Article Summarizer - Reliable High Performance Version

echo.
echo ========================================
echo   Simple Fast Article Summarizer
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting RELIABLE fast article summarization...
echo Optimizations:
echo   - Small batch processing (no hanging)
echo   - Parallel file I/O
echo   - Progress indicators
echo   - Automatic fallbacks
echo.

REM Run the simple fast summarization script
python summarize_articles_simple_fast.py --batch-size 4 --workers 4

REM Check if summarization was successful
if errorlevel 1 (
    echo.
    echo ERROR: Simple fast summarization failed!
    echo Try the regular version: python summarize_articles.py
    pause
    exit /b 1
) else (
    echo.
    echo SUCCESS: Fast summarization complete!
    echo Check the 'summary' folder for your summaries.
    echo.
)

pause
