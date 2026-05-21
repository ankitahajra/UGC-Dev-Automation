@echo off
REM ============================================================================
REM Azure Function Auto-Fix Pipeline - Web Dashboard Demo
REM Launches all services and opens the web dashboard
REM ============================================================================

echo.
echo ============================================================================
echo   Azure Function Auto-Fix Pipeline - Web Dashboard
echo ============================================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    pause
    exit /b 1
)

REM Create directories
if not exist "logs" mkdir logs
if not exist "templates" mkdir templates

REM Install dependencies
echo [1/4] Installing dependencies...
pip install flask flask-cors pyyaml python-dotenv requests --quiet

REM Set environment variables for demo
set ICA_API_ENDPOINT=http://localhost:5000
set ICA_API_KEY=demo-key
set AZURE_SUBSCRIPTION_ID=demo-subscription
set AZURE_TENANT_ID=demo-tenant
set AZURE_CLIENT_ID=demo-client
set AZURE_CLIENT_SECRET=demo-secret
set AZURE_RESOURCE_GROUP=demo-rg
set AZURE_FUNCTION_NAME=demo-function
set APP_INSIGHTS_KEY=demo-key
set APP_INSIGHTS_CONNECTION_STRING=demo-connection
set LOG_ANALYTICS_WORKSPACE_ID=demo-workspace
set LOG_ANALYTICS_WORKSPACE_KEY=demo-key

echo [2/4] Starting Mock ICA Service...
start "Mock ICA Service" /MIN python examples\mock_ica_service.py
timeout /t 4 /nobreak >nul

echo [3/4] Starting Diagnostics Webhook...
start "Diagnostics Webhook" /MIN python main.py webhook --host 0.0.0.0 --port 8080
timeout /t 4 /nobreak >nul

echo [4/4] Starting Web Dashboard...
echo.
echo ============================================================================
echo   Services Started!
echo ============================================================================
echo.
echo   Mock ICA Service:      http://localhost:5000
echo   Diagnostics Webhook:   http://localhost:8080
echo   Web Dashboard:         http://localhost:3000
echo.
echo ============================================================================
echo.
echo Opening dashboard in your browser...
echo.

REM Wait a moment then open browser
timeout /t 2 /nobreak >nul
start http://localhost:3000

REM Start dashboard (this will block)
python web_dashboard.py

REM Cleanup on exit
taskkill /F /FI "WINDOWTITLE eq Mock ICA*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080') do taskkill /F /PID %%a >nul 2>&1

@REM Made with Bob
