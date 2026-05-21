# Port Configuration

This document describes the port assignments for all services in the Azure Function Auto-Fix Pipeline demo.

## Service Port Assignments

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **Mock ICA Service** | 5000 | http://localhost:5000 | Simulates the Intelligent Code Analyzer API |
| **Cron Job Dashboard** | 5001 | http://localhost:5001 | Displays cron job monitoring (legacy) |
| **Unified Dashboard** | 5002 | http://localhost:5002 | **Main dashboard** - combines all features |
| **Web Dashboard** | 3000 | http://localhost:3000 | Alternative web interface (legacy) |
| **Diagnostics Webhook** | 8080 | http://localhost:8080 | Receives failure notifications |

## Important Notes

### Main Dashboard
The **Unified Dashboard** on port **5002** is the primary interface you should use. It provides:
- Mock cron job scenarios
- Automated fix analysis
- Real automation pipeline trigger
- PR creation and deployment
- End-to-end demonstration

### Port Conflicts
If you encounter port conflicts:
1. Check if another service is using the port: `netstat -ano | findstr :<port>`
2. Stop the conflicting service or change the port in the configuration
3. For the Unified Dashboard, use: `python unified_dashboard.py --port <new_port>`

### Starting Services

**Quick Start (All Services):**
```batch
START_ALL_DEMOS.bat
```
This automatically starts all services on their assigned ports.

**Individual Services:**
```batch
# Mock ICA Service (port 5000)
python examples\mock_ica_service.py

# Unified Dashboard (port 5002)
python unified_dashboard.py --port 5002

# Diagnostics Webhook (port 8080)
python main.py webhook --host 0.0.0.0 --port 8080
```

## Troubleshooting

### "Port already in use" Error
If you see this error, another process is using the port. To find and stop it:

**Windows:**
```batch
# Find process using port 5002
netstat -ano | findstr :5002

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

**Linux/Mac:**
```bash
# Find process using port 5002
lsof -i :5002

# Kill the process
kill -9 <PID>
```

### Services Not Starting
1. Check the log files in the `logs/` directory
2. Ensure Python dependencies are installed: `pip install -r requirements.txt`
3. Verify no other services are using the required ports

## Configuration Files

Port settings can be found in:
- `START_ALL_DEMOS.bat` - Batch file that starts all services
- `unified_dashboard.py` - Main dashboard (default port: 5002)
- `examples/mock_ica_service.py` - Mock ICA service (default port: 5000)
- `main.py` - Webhook service (default port: 8080)

## Recent Changes

**2026-05-18:** Fixed port conflict between Mock ICA Service and Unified Dashboard
- Mock ICA Service remains on port 5000
- Unified Dashboard moved from port 5000 to port 5002
- This resolves the conflict that prevented the dashboard from being accessible