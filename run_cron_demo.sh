#!/bin/bash
# Quick Start Script for Cron Job Auto-Fix Demo (Linux/Mac)

echo "========================================"
echo " Cron Job Auto-Fix Demo - Quick Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.7+ from https://www.python.org/"
    exit 1
fi

echo "[1/3] Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask not found. Installing..."
    pip3 install flask
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install Flask"
        exit 1
    fi
else
    echo "Flask is already installed"
fi

echo ""
echo "[2/3] Starting Cron Job Dashboard..."
echo ""
echo "Dashboard will be available at: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the dashboard
python3 cron_job_dashboard.py

# Made with Bob
