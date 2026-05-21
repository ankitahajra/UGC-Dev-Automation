# Run the Automation NOW - Step by Step

Follow these exact steps to see the automation in action in the next 5 minutes!

## ✅ Prerequisites Check

Open a terminal and verify:

```bash
# Check Python (need 3.8 or higher)
python --version
# or
python3 --version

# Check pip
pip --version
```

If Python is not installed, download from: https://www.python.org/downloads/

---

## 🚀 Method 1: Simplest Demo (2 minutes)

This runs a complete interactive demo with NO setup required!

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd cron-job-automation

# Install required packages
pip install flask pyyaml python-dotenv requests
```

### Step 2: Run the Demo

```bash
python examples/demo_pipeline.py
```

### What You'll See:

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
```

**Just press Enter at each stage to see the complete workflow!**

---

## 🎯 Method 2: Full Interactive Demo (5 minutes)

This shows the complete system with mock services.

### Step 1: Install All Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Open THREE Terminal Windows

#### Terminal 1 - Start Mock ICA Service

```bash
python examples/mock_ica_service.py
```

You should see:
```
============================================================
Mock ICA Service Starting
============================================================
Endpoints:
  GET  /health          - Health check
  POST /analyze         - Analyze failure
  GET  /status/<id>     - Get analysis status
============================================================
Running on http://localhost:5000
Press Ctrl+C to stop
============================================================
```

#### Terminal 2 - Start Webhook Server

```bash
# Set environment variables for demo
set ICA_API_ENDPOINT=http://localhost:5000
set ICA_API_KEY=demo-key

# Or on Linux/Mac:
export ICA_API_ENDPOINT=http://localhost:5000
export ICA_API_KEY=demo-key

# Start webhook
python main.py webhook --host 0.0.0.0 --port 8080
```

You should see the webhook starting.

#### Terminal 3 - Simulate Failures

```bash
python examples/simulate_failure.py
```

You'll see a menu:
```
Options:
  1. Test webhook health
  2. Simulate single failure
  3. Simulate multiple failures
  4. Simulate continuous failures
  5. Exit

Select option (1-5):
```

**Select option 2** to simulate a single failure and watch it process!

---

## 🎬 Method 3: Automated Setup (Windows)

### Single Command:

```bash
examples\run_demo.bat
```

This automatically:
1. Creates virtual environment
2. Installs dependencies
3. Starts Mock ICA Service
4. Starts Webhook Server
5. Shows you what to do next

Then open another terminal and run:
```bash
python examples\simulate_failure.py
```

---

## 🎬 Method 3: Automated Setup (Linux/Mac)

### Single Command:

```bash
chmod +x examples/run_demo.sh
./examples/run_demo.sh
```

This automatically:
1. Creates virtual environment
2. Installs dependencies
3. Starts Mock ICA Service
4. Starts Webhook Server
5. Shows you what to do next

Then open another terminal and run:
```bash
python examples/simulate_failure.py
```

---

## 📝 What Each Demo Shows

### Interactive Demo (`demo_pipeline.py`)
- ✅ Complete 5-stage pipeline
- ✅ Failure detection
- ✅ Root cause analysis
- ✅ Automated fix generation
- ✅ PR creation
- ✅ Validation

### Failure Simulator (`simulate_failure.py`)
- ✅ Send test failures to webhook
- ✅ See real-time processing
- ✅ Multiple failure scenarios
- ✅ Batch processing

### Mock ICA Service (`mock_ica_service.py`)
- ✅ Simulates AI analysis
- ✅ Generates realistic fixes
- ✅ Risk assessment
- ✅ Multiple failure patterns

---

## 🐛 Troubleshooting

### Error: "No module named 'flask'"

**Solution:**
```bash
pip install flask pyyaml python-dotenv requests
```

### Error: "Port already in use"

**Solution:**
```bash
# Find and kill the process using the port
# Windows:
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Linux/Mac:
lsof -ti:5000 | xargs kill -9
```

### Error: "Python not found"

**Solution:**
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### Demo not working?

**Try this:**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Run the simplest demo
python examples/demo_pipeline.py
```

---

## 🎯 Quick Test Commands

Test if everything is working:

```bash
# Test 1: Check Python
python --version

# Test 2: Check dependencies
pip list | grep -i flask

# Test 3: Run simple demo
python examples/demo_pipeline.py

# Test 4: Test Mock ICA (in separate terminal)
python examples/mock_ica_service.py
# Then in another terminal:
curl http://localhost:5000/health
```

---

## 📊 Expected Output Examples

### When Mock ICA Starts:
```
[INFO] Mock Azure Monitor initialized
[INFO] Mock ICA Client initialized
[INFO] Mock BOB Automation initialized
✓ All components initialized successfully
```

### When Failure is Detected:
```
[WARNING] Detected 1 failure(s)
[INFO] Creating diagnostic package for operation demo-op-12345
```

### When Analysis Completes:
```
✓ Analysis completed successfully

Root Cause:
  Category: code_error
  Summary: Null reference exception in data processing
  Confidence: 95.5%
```

### When PR is Created:
```
✓ Pull request created: https://github.com/demo-org/demo-repo/pull/42
```

---

## 🎓 Next Steps After Demo

1. **Understand the workflow** - Review what each stage does
2. **Try different scenarios** - Use the failure simulator
3. **Customize** - Edit `examples/mock_ica_service.py` to add your scenarios
4. **Production setup** - Follow SETUP.md for real Azure integration

---

## 💡 Pro Tips

1. **Keep terminals visible** - Arrange them side-by-side to see the flow
2. **Check logs** - Look in `logs/` directory for detailed output
3. **Start simple** - Begin with `demo_pipeline.py`, then try the full setup
4. **Read output** - Each stage explains what it's doing

---

## 🆘 Still Having Issues?

1. Check you're in the correct directory: `cd cron-job-automation`
2. Verify Python version: `python --version` (need 3.8+)
3. Try the simplest demo first: `python examples/demo_pipeline.py`
4. Check the logs: `cat logs/pipeline.log` or `type logs\pipeline.log`

---

## ✨ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Can run `python examples/demo_pipeline.py`
- [ ] Mock ICA service starts on port 5000
- [ ] Webhook starts on port 8080
- [ ] Failure simulator connects successfully

**Once all checked, you're ready to showcase the automation!** 🚀

---

## 📞 Quick Reference

| What | Command |
|------|---------|
| Simplest demo | `python examples/demo_pipeline.py` |
| Start Mock ICA | `python examples/mock_ica_service.py` |
| Start Webhook | `python main.py webhook` |
| Simulate failure | `python examples/simulate_failure.py` |
| Auto setup (Win) | `examples\run_demo.bat` |
| Auto setup (Unix) | `./examples/run_demo.sh` |

---

**Ready? Start with: `python examples/demo_pipeline.py`** 🎬