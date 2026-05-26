@echo off
REM ============================================================================
REM Upload Historical Failures to Context Studio via MCP API
REM ============================================================================

echo.
echo ============================================================================
echo   Upload Historical Failures to Context Studio
echo ============================================================================
echo.
echo This script will upload 15 historical failure records to Context Studio
echo via the MCP API for vector search demonstration.
echo.
echo What will be uploaded:
echo   - 15 realistic failure scenarios
echo   - Error types, messages, and stack traces
echo   - Resolutions and fixes applied
echo   - Metadata (severity, category, confidence)
echo.
echo Prerequisites:
echo   - MCP Context Studio connection configured in .bob/mcp.json
echo   - File: historical_failures_for_context_studio.jsonl exists
echo   - Python dependencies installed (aiohttp)
echo.
pause

echo.
echo [1/3] Checking prerequisites...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)
echo [OK] Python detected

REM Check if file exists
if not exist "historical_failures_for_context_studio.jsonl" (
    echo [ERROR] File not found: historical_failures_for_context_studio.jsonl
    echo Please ensure the file exists in the current directory
    pause
    exit /b 1
)
echo [OK] Data file found

REM Check if logs directory exists
if not exist "logs" mkdir logs
echo [OK] Logs directory ready

echo.
echo [2/3] Installing/Checking dependencies...
echo.

REM Install required packages
pip install aiohttp pyyaml --quiet
if errorlevel 1 (
    echo [WARNING] Some packages may not have installed correctly
    echo Continuing anyway...
)
echo [OK] Dependencies ready

echo.
echo [3/3] Starting upload to Context Studio...
echo.

REM Run the upload script
python upload_to_context_studio.py

if errorlevel 1 (
    echo.
    echo ============================================================================
    echo   Upload Failed
    echo ============================================================================
    echo.
    echo Please check:
    echo   1. MCP connection settings in .bob/mcp.json
    echo   2. Bearer token is valid
    echo   3. Context ID is correct (ctx_7c3822579dfd)
    echo   4. Network connectivity to Context Studio
    echo.
    echo Check logs/context_studio_upload.log for detailed error information
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   Upload Completed Successfully!
echo ============================================================================
echo.
echo What happens next:
echo   1. Context Studio will index the data (5-10 minutes)
echo   2. Vector search will be able to find similar failures
echo   3. Dashboard will show real MCP results
echo.
echo To test the vector search:
echo   1. Run: START_ALL_DEMOS.bat
echo   2. Open: http://localhost:5002
echo   3. Click "Run Job" on any card
echo   4. Click "Search Similar Failures"
echo   5. See real MCP results from uploaded data!
echo.
echo Log file: logs/context_studio_upload.log
echo.
pause

REM Made with Bob

@REM Made with Bob
