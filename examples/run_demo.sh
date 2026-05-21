#!/bin/bash

# Demo Runner Script
# Runs the complete demo with all components

set -e

echo "======================================================================"
echo "  Azure Function Auto-Diagnose and Auto-Fix Pipeline - Demo Setup"
echo "======================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "======================================================================"
echo "  Starting Demo Components"
echo "======================================================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    kill $MOCK_ICA_PID 2>/dev/null || true
    kill $WEBHOOK_PID 2>/dev/null || true
    echo "Demo stopped"
}

trap cleanup EXIT

# Start Mock ICA Service
echo "1. Starting Mock ICA Service on port 5000..."
python3 examples/mock_ica_service.py > logs/mock_ica.log 2>&1 &
MOCK_ICA_PID=$!
sleep 2

# Check if Mock ICA is running
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo "Error: Mock ICA Service failed to start"
    exit 1
fi
echo "   ✓ Mock ICA Service running (PID: $MOCK_ICA_PID)"

# Update config to use mock ICA
echo ""
echo "2. Configuring pipeline to use Mock ICA Service..."
export ICA_API_ENDPOINT="http://localhost:5000"
export ICA_API_KEY="demo-key"
echo "   ✓ Configuration updated"

# Start Webhook Server
echo ""
echo "3. Starting Diagnostics Webhook on port 8080..."
python3 main.py webhook --host 0.0.0.0 --port 8080 > logs/webhook.log 2>&1 &
WEBHOOK_PID=$!
sleep 2

# Check if Webhook is running
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "Error: Webhook Server failed to start"
    exit 1
fi
echo "   ✓ Webhook Server running (PID: $WEBHOOK_PID)"

echo ""
echo "======================================================================"
echo "  Demo Environment Ready!"
echo "======================================================================"
echo ""
echo "Services running:"
echo "  - Mock ICA Service: http://localhost:5000"
echo "  - Diagnostics Webhook: http://localhost:8080"
echo ""
echo "Available demos:"
echo "  1. Interactive Pipeline Demo: python3 examples/demo_pipeline.py"
echo "  2. Simulate Failures: python3 examples/simulate_failure.py"
echo ""
echo "Logs available in:"
echo "  - logs/mock_ica.log"
echo "  - logs/webhook.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================================================"
echo ""

# Keep script running
wait

# Made with Bob
