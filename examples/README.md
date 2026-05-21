# Demo Examples and Showcase

This directory contains runnable examples and demo scripts to showcase the Azure Function Auto-Diagnose and Auto-Fix Pipeline.

## 🎯 Quick Start

### Windows
```bash
# Run the complete demo environment
examples\run_demo.bat

# Then in another terminal, run the interactive demo
python examples\demo_pipeline.py
```

### Linux/Mac
```bash
# Make script executable
chmod +x examples/run_demo.sh

# Run the complete demo environment
./examples/run_demo.sh

# Then in another terminal, run the interactive demo
python examples/demo_pipeline.py
```

## 📁 Available Examples

### 1. Mock ICA Service (`mock_ica_service.py`)

A fully functional mock Intelligent Code Analyzer service that simulates real ICA behavior.

**Features:**
- Realistic failure analysis
- Multiple failure patterns (NullReference, Timeout, OutOfMemory, etc.)
- Generates code, configuration, and infrastructure fixes
- Risk assessment and recommendations

**Run standalone:**
```bash
python examples/mock_ica_service.py
```

**Endpoints:**
- `GET /health` - Health check
- `POST /analyze` - Analyze failure and generate fixes
- `GET /status/<id>` - Get analysis status

**Test it:**
```bash
curl http://localhost:5000/health

curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "diagnostic_data": {
      "error": {
        "message": "NullReferenceException in ProcessRequest"
      }
    }
  }'
```

### 2. Interactive Pipeline Demo (`demo_pipeline.py`)

A complete, interactive demonstration of the entire pipeline workflow.

**Features:**
- Step-by-step pipeline execution
- Mock components (no Azure resources needed)
- Visual progress indicators
- Detailed output at each stage

**Run:**
```bash
python examples/demo_pipeline.py
```

**What it demonstrates:**
1. **Monitoring** - Failure detection
2. **Diagnostics** - Information collection
3. **Analysis** - ICA root cause analysis
4. **Automation** - BOB fix application
5. **Validation** - Post-deployment verification

**Sample Output:**
```
======================================================================
  Azure Function Auto-Diagnose and Auto-Fix Pipeline - DEMO
======================================================================

This demo showcases the complete automation workflow:
1. Monitoring - Detect failures
2. Diagnostics - Collect failure information
3. Analysis - ICA analyzes root cause
4. Automation - BOB applies fixes and creates PR
5. Validation - Verify deployment

Press Enter to start the demo...

======================================================================
  Initializing Pipeline Components
======================================================================

[INFO] Mock Azure Monitor initialized
[INFO] Mock ICA Client initialized
[INFO] Mock BOB Automation initialized

✓ All components initialized successfully
...
```

### 3. Failure Simulator (`simulate_failure.py`)

Interactive tool to simulate Azure Function failures and send them to the webhook.

**Features:**
- Multiple failure scenarios
- Single or batch simulation
- Continuous failure generation
- Webhook health testing

**Run:**
```bash
python examples/simulate_failure.py
```

**Menu Options:**
1. Test webhook health
2. Simulate single failure
3. Simulate multiple failures
4. Simulate continuous failures
5. Exit

**Failure Scenarios:**
- Null Reference Exception
- Timeout Exception
- Out of Memory
- Database Connection Error

**Usage Example:**
```bash
# Start webhook first
python main.py webhook

# In another terminal, run simulator
python examples/simulate_failure.py

# Select option 2 for single failure
# Select option 3 for batch (e.g., 5 failures with 2s interval)
```

### 4. Demo Runner Scripts

Automated scripts to set up the complete demo environment.

#### Windows (`run_demo.bat`)
```bash
examples\run_demo.bat
```

#### Linux/Mac (`run_demo.sh`)
```bash
chmod +x examples/run_demo.sh
./examples/run_demo.sh
```

**What they do:**
1. Create/activate virtual environment
2. Install dependencies
3. Start Mock ICA Service (port 5000)
4. Start Diagnostics Webhook (port 8080)
5. Configure environment variables
6. Display status and next steps

## 🎬 Complete Demo Workflow

### Scenario 1: Interactive Demo (No Azure Required)

```bash
# Terminal 1: Run the interactive demo
python examples/demo_pipeline.py

# Follow the prompts to see each stage
# Press Enter to advance through stages
```

### Scenario 2: End-to-End with Mock Services

```bash
# Terminal 1: Start mock services
# Windows:
examples\run_demo.bat
# Linux/Mac:
./examples/run_demo.sh

# Terminal 2: Simulate a failure
python examples/simulate_failure.py
# Select option 2 (single failure)
# Choose scenario 1 (Null Reference)

# Terminal 3: Check webhook logs
tail -f logs/webhook.log  # Linux/Mac
type logs\webhook.log     # Windows
```

### Scenario 3: Continuous Monitoring Demo

```bash
# Terminal 1: Start mock ICA
python examples/mock_ica_service.py

# Terminal 2: Start webhook
python main.py webhook

# Terminal 3: Simulate continuous failures
python examples/simulate_failure.py
# Select option 4 (continuous)
# Set interval to 10 seconds

# Watch the pipeline process each failure automatically
```

## 🔧 Configuration for Demos

The demo scripts use these default configurations:

```yaml
# Mock ICA Service
ICA_API_ENDPOINT: http://localhost:5000
ICA_API_KEY: demo-key

# Webhook Server
WEBHOOK_HOST: 0.0.0.0
WEBHOOK_PORT: 8080
```

## 📊 Demo Outputs

### Logs
All demo activities are logged to:
- `logs/mock_ica.log` - Mock ICA service logs
- `logs/webhook.log` - Webhook server logs
- `logs/pipeline.log` - Pipeline execution logs

### Console Output
Each demo provides detailed console output showing:
- Component initialization
- Stage execution
- Success/failure indicators
- Timing information
- Generated artifacts (PR URLs, etc.)

## 🎓 Learning Path

### Beginner
1. Start with `demo_pipeline.py` - See the complete workflow
2. Explore `mock_ica_service.py` - Understand ICA responses
3. Try `simulate_failure.py` - Send test failures

### Intermediate
1. Run the complete demo environment with `run_demo.sh`
2. Simulate multiple failures and observe processing
3. Examine logs to understand data flow

### Advanced
1. Modify mock responses in `mock_ica_service.py`
2. Create custom failure scenarios in `simulate_failure.py`
3. Integrate with real Azure resources (see main README.md)

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
# Linux/Mac:
lsof -i :5000
lsof -i :8080

# Windows:
netstat -ano | findstr :5000
netstat -ano | findstr :8080

# Kill the process or use different ports
```

### Mock ICA Not Responding
```bash
# Check if service is running
curl http://localhost:5000/health

# Check logs
cat logs/mock_ica.log  # Linux/Mac
type logs\mock_ica.log # Windows

# Restart the service
python examples/mock_ica_service.py
```

### Webhook Connection Failed
```bash
# Verify webhook is running
curl http://localhost:8080/health

# Check logs
cat logs/webhook.log  # Linux/Mac
type logs\webhook.log # Windows

# Restart webhook
python main.py webhook
```

## 📝 Customization

### Add New Failure Scenarios

Edit `simulate_failure.py`:
```python
FAILURE_SCENARIOS.append({
    "name": "Custom Error",
    "functionName": "MyFunction",
    "exceptionMessage": "Custom exception message",
    # ... other fields
})
```

### Modify Mock ICA Responses

Edit `mock_ica_service.py`:
```python
FAILURE_PATTERNS['CustomError'] = {
    'category': 'code_error',
    'summary': 'Custom error description',
    # ... other fields
}
```

### Change Demo Timing

Edit `demo_pipeline.py`:
```python
# Adjust sleep times for faster/slower demo
time.sleep(1)  # Change to desired seconds
```

## 🎯 Presentation Tips

When showcasing to stakeholders:

1. **Start with the interactive demo** (`demo_pipeline.py`)
   - Shows the complete workflow clearly
   - Easy to pause and explain each stage

2. **Demonstrate failure simulation** (`simulate_failure.py`)
   - Shows real-time processing
   - Illustrates automation capabilities

3. **Show the logs**
   - Demonstrates observability
   - Shows structured logging

4. **Highlight key features**
   - Automatic root cause analysis
   - Risk assessment
   - PR automation
   - No manual intervention needed

## 📚 Additional Resources

- [Main README](../README.md) - Complete documentation
- [Setup Guide](../SETUP.md) - Production setup instructions
- [Examples Guide](../EXAMPLES.md) - More usage examples

## 🤝 Contributing

To add new demo examples:
1. Create your script in this directory
2. Add documentation to this README
3. Update the main EXAMPLES.md if applicable
4. Test thoroughly before committing

---

**Happy Demoing! 🚀**