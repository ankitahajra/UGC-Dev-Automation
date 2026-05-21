@echo off
REM Quick Start Script for Cron Job Auto-Fix Demo (Windows)

echo ========================================
echo  Cron Job Auto-Fix Demo - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask not found. Installing...
    pip install flask
    if errorlevel 1 (
        echo ERROR: Failed to install Flask
        pause
        exit /b 1
    )
) else (
    echo Flask is already installed
)

echo.
echo [2/3] Starting Cron Job Dashboard...
echo.
echo Dashboard will be available at: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the dashboard
python cron_job_dashboard.py

pause

@REM Made with Bob
