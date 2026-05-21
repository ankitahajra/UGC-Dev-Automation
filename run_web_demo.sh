#!/bin/bash
# ============================================================================
# Azure Function Auto-Fix Pipeline - Web Dashboard Demo
# Launches all services and opens the web dashboard
# ============================================================================

echo ""
echo "============================================================================"
echo "  Azure Function Auto-Fix Pipeline - Web Dashboard"
echo "============================================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    exit 1
fi

# Create directories
mkdir -p logs templates

# Install dependencies
echo "[1/4] Installing dependencies..."
pip install flask flask-cors pyyaml python-dotenv requests --quiet

# Set environment variables for demo
export ICA_API_ENDPOINT="http://localhost:5000"
export ICA_API_KEY="demo-key"
export AZURE_SUBSCRIPTION_ID="demo-subscription"
export AZURE_TENANT_ID="demo-tenant"
export AZURE_CLIENT_ID="demo-client"
export AZURE_CLIENT_SECRET="demo-secret"
export AZURE_RESOURCE_GROUP="demo-rg"
export AZURE_FUNCTION_NAME="demo-function"
export APP_INSIGHTS_KEY="demo-key"
export APP_INSIGHTS_CONNECTION_STRING="demo-connection"
export LOG_ANALYTICS_WORKSPACE_ID="demo-workspace"
export LOG_ANALYTICS_WORKSPACE_KEY="demo-key"

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $MOCK_ICA_PID 2>/dev/null || true
    kill $WEBHOOK_PID 2>/dev/null || true
    kill $DASHBOARD_PID 2>/dev/null || true
    echo "Services stopped."
    exit 0
}

trap cleanup EXIT INT TERM

echo "[2/4] Starting Mock ICA Service..."
python3 examples/mock_ica_service.py > logs/mock_ica.log 2>&1 &
MOCK_ICA_PID=$!
sleep 3

echo "[3/4] Starting Diagnostics Webhook..."
python3 main.py webhook --host 0.0.0.0 --port 8080 > logs/webhook.log 2>&1 &
WEBHOOK_PID=$!
sleep 3

echo "[4/4] Starting Web Dashboard..."
echo ""
echo "============================================================================"
echo "  Services Started!"
echo "============================================================================"
echo ""
echo "  Mock ICA Service:      http://localhost:5000"
echo "  Diagnostics Webhook:   http://localhost:8080"
echo "  Web Dashboard:         http://localhost:3000"
echo ""
echo "============================================================================"
echo ""
echo "Opening dashboard in your browser..."
echo "Press Ctrl+C to stop all services"
echo ""

# Wait a moment then open browser
sleep 2

# Try to open browser (works on most systems)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &
fi

# Start dashboard (this will block)
python3 web_dashboard.py

# Made with Bob
