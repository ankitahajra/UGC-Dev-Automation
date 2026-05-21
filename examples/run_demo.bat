@echo off
REM Demo Runner Script for Windows
REM Runs the complete demo with all components

echo ======================================================================
echo   Azure Function Auto-Diagnose and Auto-Fix Pipeline - Demo Setup
echo ======================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo ======================================================================
echo   Starting Demo Components
echo ======================================================================
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Start Mock ICA Service
echo 1. Starting Mock ICA Service on port 5000...
start /B python examples\mock_ica_service.py > logs\mock_ica.log 2>&1
timeout /t 3 /nobreak >nul

REM Check if Mock ICA is running
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo Error: Mock ICA Service failed to start
    exit /b 1
)
echo    * Mock ICA Service running

REM Update config to use mock ICA
echo.
echo 2. Configuring pipeline to use Mock ICA Service...
set ICA_API_ENDPOINT=http://localhost:5000
set ICA_API_KEY=demo-key
echo    * Configuration updated

REM Start Webhook Server
echo.
echo 3. Starting Diagnostics Webhook on port 8080...
start /B python main.py webhook --host 0.0.0.0 --port 8080 > logs\webhook.log 2>&1
timeout /t 3 /nobreak >nul

REM Check if Webhook is running
curl -s http://localhost:8080/health >nul 2>&1
if errorlevel 1 (
    echo Error: Webhook Server failed to start
    exit /b 1
)
echo    * Webhook Server running

echo.
echo ======================================================================
echo   Demo Environment Ready!
echo ======================================================================
echo.
echo Services running:
echo   - Mock ICA Service: http://localhost:5000
echo   - Diagnostics Webhook: http://localhost:8080
echo.
echo Available demos:
echo   1. Interactive Pipeline Demo: python examples\demo_pipeline.py
echo   2. Simulate Failures: python examples\simulate_failure.py
echo.
echo Logs available in:
echo   - logs\mock_ica.log
echo   - logs\webhook.log
echo.
echo Press Ctrl+C to stop all services
echo ======================================================================
echo.

REM Keep window open
pause

@REM Made with Bob
