# Quick Start Guide

Get the Azure Function Auto-Diagnose and Auto-Fix Pipeline running in 5 minutes!

## 🚀 For Demo/Testing (No Azure Required)

### Step 1: Install Dependencies (1 minute)

```bash
# Clone or navigate to the project
cd cron-job-automation

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Run the Interactive Demo (2 minutes)

```bash
# Run the complete interactive demo
python examples/demo_pipeline.py
```

**What you'll see:**
- Complete pipeline workflow
- All 5 stages in action
- Mock data (no Azure needed)
- Step-by-step execution

Press Enter at each stage to continue.

### Step 3: Try the Full Demo Environment (2 minutes)

**Windows:**
```bash
examples\run_demo.bat
```

**Linux/Mac:**
```bash
chmod +x examples/run_demo.sh
./examples/run_demo.sh
```

This starts:
- Mock ICA Service (port 5000)
- Diagnostics Webhook (port 8080)

**Then in another terminal:**
```bash
# Simulate failures
python examples/simulate_failure.py
```

**Done!** You've seen the complete automation in action.

---

## 🔧 For Production Setup

### Step 1: Azure Prerequisites (10 minutes)

1. **Create Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "autofix-pipeline-sp" --role Contributor
   ```
   Save the output (appId, password, tenant).

2. **Create Azure Function:**
   ```bash
   az functionapp create \
     --name my-autofix-function \
     --resource-group my-rg \
     --storage-account mystorage \
     --consumption-plan-location eastus
   ```

3. **Enable Application Insights:**
   ```bash
   az monitor app-insights component create \
     --app my-insights \
     --location eastus \
     --resource-group my-rg
   ```

### Step 2: Configure Environment (2 minutes)

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
# Required: AZURE_*, APP_INSIGHTS_*, GIT_*
```

### Step 3: Validate and Run (1 minute)

```bash
# Validate configuration
python main.py validate-config

# Check health
python main.py check-health

# Run pipeline
python main.py run-pipeline
```

**Done!** Your production pipeline is running.

---

## 📚 What's Next?

### Learn More
- [README.md](README.md) - Complete documentation
- [SETUP.md](SETUP.md) - Detailed setup guide
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [DEMO_GUIDE.md](DEMO_GUIDE.md) - Presentation guide

### Common Commands

```bash
# Continuous monitoring
python main.py monitor --interval 60

# Start webhook server
python main.py webhook

# Analyze specific failure
python main.py analyze <operation-id>

# View execution history
python main.py history --limit 10
```

### Customize

Edit `config.yaml` to customize:
- Monitoring intervals
- Risk thresholds
- Approval requirements
- Notification channels

---

## 🆘 Troubleshooting

### Demo Not Working?

```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check logs
cat logs/pipeline.log
```

### Production Issues?

```bash
# Validate config
python main.py validate-config

# Check component health
python main.py check-health

# Enable debug logging
python main.py --log-level DEBUG run-pipeline
```

### Need Help?

- Check [SETUP.md](SETUP.md) for detailed instructions
- Review [examples/README.md](examples/README.md) for demo help
- Open an issue on GitHub

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `python examples/demo_pipeline.py` | Interactive demo |
| `python examples/simulate_failure.py` | Simulate failures |
| `python main.py validate-config` | Validate setup |
| `python main.py run-pipeline` | Execute once |
| `python main.py monitor` | Continuous mode |
| `python main.py webhook` | Start webhook |
| `python main.py check-health` | Health check |

---

**Ready to automate? Start with the demo, then move to production!** 🚀