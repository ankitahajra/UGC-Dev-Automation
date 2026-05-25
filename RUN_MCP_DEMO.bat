@echo off
REM MCP Intelligence Demonstration Runner
REM Shows where and how MCP server intelligence is used

echo ============================================================
echo   MCP INTELLIGENCE DEMONSTRATION
echo   Cron Job Automation with Context Studio
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if logs directory exists
if not exist "logs" (
    echo Creating logs directory...
    mkdir logs
)

REM Install dependencies if needed
echo Checking dependencies...
python -c "import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting MCP Intelligence Demonstration...
echo.
echo This will show you:
echo   1. MCP server health check
echo   2. Knowledge schema retrieval
echo   3. Semantic vector search
echo   4. Graph relationship queries
echo   5. Hybrid intelligence queries
echo   6. Confidence boosting
echo   7. Knowledge ingestion
echo   8. Complete workflow comparison
echo.
echo Press Ctrl+C to stop at any time
echo.
pause

REM Run the demonstration
python demo_mcp_intelligence.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   DEMO ENCOUNTERED AN ERROR
    echo ============================================================
    echo.
    echo Please check:
    echo   1. config.yaml exists and is valid
    echo   2. .bob/mcp.json has valid MCP configuration
    echo   3. Network connectivity to MCP server
    echo   4. Bearer token is not expired
    echo.
    echo Check logs/mcp_demo.log for details
    echo.
) else (
    echo.
    echo ============================================================
    echo   DEMO COMPLETED SUCCESSFULLY!
    echo ============================================================
    echo.
    echo Check logs/mcp_demo.log for detailed output
    echo.
)

pause

@REM Made with Bob
