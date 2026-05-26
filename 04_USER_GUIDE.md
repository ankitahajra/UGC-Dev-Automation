# User Guide - How to Use and Run This Solution

## Table of Contents
1. [Quick Start](#1-quick-start)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Running the Solution](#4-running-the-solution)
5. [Using the Dashboard](#5-using-the-dashboard)
6. [Command Reference](#6-command-reference)
7. [Demo Mode](#7-demo-mode)
8. [Production Deployment](#8-production-deployment)
9. [Troubleshooting](#9-troubleshooting)
10. [Best Practices](#10-best-practices)

---

## 1. Quick Start

### 1.1 Fastest Way to Get Started (Demo Mode)

**No Azure resources required!**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start all demos (dashboard + services)
START_ALL_DEMOS.bat

# 3. Open browser to http://localhost:5002
```

**What you'll see:**
- Interactive dashboard with mock cron jobs
- Vector search querying historical data from Context Studio
- Real-time automation pipeline
- MCP intelligence demonstration

### 1.2 Prerequisites

**Required**:
- Python 3.8 or higher
- pip (Python package manager)
- Git

**Optional (for production)**:
- Azure subscription
- Azure CLI
- ICA API access
- GitHub/Azure DevOps account

---

## 2. Installation

### 2.1 Clone the Repository

```bash
git clone https://github.com/your-org/cron-job-automation.git
cd cron-job-automation
```

### 2.2 Install Dependencies

**Windows**:
```bash
pip install -r requirements.txt
```

**Linux/Mac**:
```bash
pip3 install -r requirements.txt
```

### 2.3 Verify Installation

```bash
python --version  # Should be 3.8+
python main.py --help  # Should show command options
```

---

## 3. Configuration

### 3.1 Demo Mode (No Configuration Needed)

For demo mode, the system uses mock services. No configuration required!

### 3.2 Production Mode

#### Step 1: Create Environment File

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

#### Step 2: Configure Azure Credentials

```bash
# .env file
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_FUNCTION_NAME=your-function-name

# Application Insights
APP_INSIGHTS_KEY=your-app-insights-key
APP_INSIGHTS_CONNECTION_STRING=your-connection-string
```

#### Step 3: Configure ICA Service

```bash
# .env file
ICA_API_ENDPOINT=https://your-ica-endpoint.com/api
ICA_API_KEY=your-ica-api-key
```

#### Step 4: Configure Git Repository

```bash
# .env file
GIT_REPOSITORY_URL=https://github.com/your-org/your-repo.git
GIT_TOKEN=your-git-token
```

#### Step 5: Configure MCP Context Studio

Edit `.bob/mcp.json`:
```json
{
  "mcpServers": {
    "context-studio": {
      "command": "npx",
      "args": [
        "-y",
        "@ibm-client-engineering/context-mcp-server@latest"
      ],
      "env": {
        "CONTEXT_STUDIO_BEARER_TOKEN": "your-token",
        "CONTEXT_ID": "ctx_7c3822579dfd"
      }
    }
  }
}
```

#### Step 6: Validate Configuration

```bash
python main.py validate-config
```

Expected output:
```
✓ Azure credentials valid
✓ ICA API accessible
✓ MCP Context Studio connected
✓ Git repository accessible
✓ Configuration valid
```

---

## 4. Running the Solution

### 4.1 Demo Mode (Recommended for First Time)

**Option 1: All-in-One Demo**
```bash
# Windows
START_ALL_DEMOS.bat

# Linux/Mac
chmod +x run_demo.sh
./run_demo.sh
```

This starts:
- Mock ICA service (port 5000)
- Unified dashboard (port 5002)
- Mock cron jobs

**Option 2: Individual Components**

Terminal 1 - Start Dashboard:
```bash
python unified_dashboard.py
```

Terminal 2 - Run Demo Pipeline:
```bash
python demo_mcp_with_history.py
```

### 4.2 Production Mode

**Option 1: Run Pipeline Once**
```bash
python main.py run-pipeline
```

**Option 2: Continuous Monitoring**
```bash
python main.py monitor --interval 60
```

**Option 3: Webhook Server**
```bash
python main.py webhook --host 0.0.0.0 --port 8080
```

**Option 4: Docker Deployment**
```bash
# Build image
docker build -t cron-automation .

# Run container
docker run -d \
  --env-file .env \
  -p 8080:8080 \
  cron-automation
```

---

## 5. Using the Dashboard

### 5.1 Access the Dashboard

Open your browser to: **http://localhost:5002**

### 5.2 Dashboard Features

#### Main View
- **Job List**: All cron jobs with status indicators
- **Status Colors**:
  - 🟢 Green: Success
  - 🔴 Red: Failed
  - 🟡 Yellow: Running
  - ⚪ Gray: Pending

#### Actions Available

**1. Run Job**
```
Click "▶ Run" button next to any job
→ Job executes
→ Status updates in real-time
→ Results displayed
```

**2. Analyze Failure**
```
Click "🔍 Analyze" button on failed job
→ ICA analyzes the failure
→ Root cause displayed
→ Fix suggestions shown
→ Confidence score provided
```

**3. Search Similar Failures**
```
Click "📊 Search Similar" button
→ MCP vector search executes
→ Historical matches displayed
→ Proven solutions shown
→ Success rates included
```

**4. View All Historical Data**
```
Click "📊 Show All Historical Data" button
→ All 17 historical patterns displayed
→ Searchable and filterable
→ Detailed information for each pattern
```

**5. Trigger Automation**
```
Click "🤖 Trigger Automation" button
→ Complete pipeline executes
→ Progress shown in real-time
→ Results displayed
```

### 5.3 Understanding Results

**Analysis Results**:
```json
{
  "root_cause": "Missing null check for customer object",
  "confidence": 0.95,
  "category": "null_reference_error",
  "historical_matches": 2
}
```

**Fix Suggestions**:
```json
{
  "type": "code_fix",
  "file": "index.js",
  "description": "Add null safety check",
  "risk_level": "low",
  "historical_success_rate": 1.0
}
```

**Vector Search Results**:
```json
{
  "similarity_score": 0.95,
  "job_name": "Data Processing Job",
  "error_type": "NullReferenceError",
  "resolution": "Added null check before accessing properties",
  "success_rate": 1.0
}
```

---

## 6. Command Reference

### 6.1 Main Commands

**Validate Configuration**:
```bash
python main.py validate-config
```

**Run Pipeline Once**:
```bash
python main.py run-pipeline
```

**Continuous Monitoring**:
```bash
python main.py monitor --interval 60
```

**Start Webhook Server**:
```bash
python main.py webhook --host 0.0.0.0 --port 8080
```

**Check Component Health**:
```bash
python main.py check-health
```

**View Execution History**:
```bash
python main.py history --limit 10
```

**Analyze Specific Failure**:
```bash
python main.py analyze <operation-id>
```

### 6.2 Dashboard Commands

**Start Unified Dashboard**:
```bash
python unified_dashboard.py
```

**Start with Custom Port**:
```bash
python unified_dashboard.py --port 5003
```

### 6.3 Demo Commands

**Upload Historical Data to Context Studio**:
```bash
# Windows
UPLOAD_TO_CONTEXT_STUDIO.bat

# Linux/Mac
python upload_to_context_studio.py
```

**Start All Demos**:
```bash
# Windows
START_ALL_DEMOS.bat

# Linux/Mac
./run_demo.sh
```

**Run MCP History Demo**:
```bash
python demo_mcp_with_history.py
```

**Test Auto-Update Workflow**:
```bash
python test_auto_update_workflow.py
```

### 6.4 Utility Commands

**Record Manual Fix**:
```bash
python post_deployment_hook.py \
  --job-name "Customer Data Validation Job" \
  --error-type "ValidationError" \
  --fix-description "Enhanced validation rules" \
  --severity "high"
```

**Verify Context Studio Upload**:
```bash
python verify_upload.py
```

**Generate Sample MCP Data**:
```bash
python generate_sample_mcp_data.py
```

---

## 7. Demo Mode

### 7.1 What is Demo Mode?

Demo mode allows you to explore the system without:
- Azure subscription
- ICA API access
- Real cron jobs
- Production credentials

### 7.2 Running Demo Mode

**Step 1: Start the Demo**
```bash
START_ALL_DEMOS.bat
```

**Step 2: Open Dashboard**
```
Browser → http://localhost:5002
```

**Step 3: Try Features**
1. Click "▶ Run" on any job
2. Watch it fail (intentionally)
3. Click "🔍 Analyze" to see AI analysis
4. Click "📊 Search Similar" to see vector search
5. Click "🤖 Trigger Automation" to see full pipeline

### 7.3 Demo Scenarios

**Scenario 1: Null Reference Error**
```
1. Run "Data Processing Job"
2. Job fails with null reference error
3. Analyze → Shows root cause
4. Search Similar → Finds 3 historical matches
5. Trigger Automation → Creates fix
```

**Scenario 2: Validation Error**
```
1. Run "Customer Data Validation Job"
2. Job fails with validation error
3. Analyze → Shows missing columns
4. Search Similar → Finds similar validation issues
5. Trigger Automation → Suggests config fix
```

**Scenario 3: Connection Error**
```
1. Run "External API Sync"
2. Job fails with connection timeout
3. Analyze → Shows timeout issue
4. Search Similar → Finds timeout patterns
5. Trigger Automation → Suggests retry logic
```

### 7.4 Demo Data

The demo uses 17 pre-loaded historical patterns:
- NullReferenceError patterns
- ConnectionError patterns
- TimeoutError patterns
- ValidationError patterns
- MemoryError patterns
- And more...

All stored in: `historical_failures_for_context_studio.txt`

---

## 8. Production Deployment

### 8.1 Pre-Deployment Checklist

- [ ] Configuration validated (`python main.py validate-config`)
- [ ] Azure credentials configured
- [ ] ICA API accessible
- [ ] MCP Context Studio connected
- [ ] Git repository accessible
- [ ] Historical data uploaded to Context Studio
- [ ] Tests passing
- [ ] Logs directory created

### 8.2 Deployment Options

#### Option 1: Local Server

```bash
# Start webhook server
python main.py webhook --host 0.0.0.0 --port 8080

# In another terminal, start monitoring
python main.py monitor --interval 60
```

#### Option 2: Docker Container

```bash
# Build
docker build -t cron-automation .

# Run
docker run -d \
  --name cron-automation \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  cron-automation
```

#### Option 3: Azure Container Instance

```bash
az container create \
  --resource-group my-rg \
  --name cron-automation \
  --image cron-automation:latest \
  --environment-variables-file .env \
  --ports 8080 \
  --cpu 1 \
  --memory 1
```

#### Option 4: Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cron-automation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cron-automation
  template:
    metadata:
      labels:
        app: cron-automation
    spec:
      containers:
      - name: cron-automation
        image: cron-automation:latest
        ports:
        - containerPort: 8080
        envFrom:
        - secretRef:
            name: cron-automation-secrets
```

### 8.3 Post-Deployment

**1. Verify Health**:
```bash
curl http://your-server:8080/health
```

**2. Check Logs**:
```bash
tail -f logs/pipeline.log
```

**3. Monitor Metrics**:
```bash
python main.py check-health
```

**4. Test Webhook**:
```bash
curl -X POST http://your-server:8080/webhook/diagnostics \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

---

## 9. Troubleshooting

### 9.1 Common Issues

#### Issue: Configuration Validation Fails

**Symptoms**:
```
✗ Azure credentials invalid
```

**Solution**:
```bash
# Check environment variables
echo $AZURE_SUBSCRIPTION_ID

# Verify Azure login
az login

# Test credentials
az account show
```

#### Issue: MCP Context Studio Not Responding

**Symptoms**:
```
Error: MCP connection timeout
```

**Solution**:
```bash
# Check MCP configuration
cat .bob/mcp.json

# Verify bearer token
# Wait 5-10 minutes after upload for indexing

# Test connection
python -c "from src.mcp_client import MCPClientSync; from src.config_manager import get_config; client = MCPClientSync(get_config('config.yaml')); print('MCP OK' if client else 'MCP Failed')"
```

#### Issue: Dashboard Not Loading

**Symptoms**:
```
Browser shows "Connection refused"
```

**Solution**:
```bash
# Check if dashboard is running
netstat -ano | findstr :5002  # Windows
lsof -i :5002                 # Linux/Mac

# Check logs
cat logs/dashboard.log

# Restart dashboard
python unified_dashboard.py
```

#### Issue: Jobs Not Running

**Symptoms**:
```
Jobs stuck in "Pending" status
```

**Solution**:
```bash
# Check mock services
curl http://localhost:5000/health  # Mock ICA

# Restart services
START_ALL_DEMOS.bat

# Check logs
cat logs/mock_ica.log
```

#### Issue: Vector Search Returns No Results

**Symptoms**:
```
"No similar failures found"
```

**Solution**:
```bash
# Verify historical data uploaded
python verify_upload.py

# Check Context Studio indexing (wait 5-10 min)
# Re-upload if needed
UPLOAD_TO_CONTEXT_STUDIO.bat

# Check similarity threshold in config.yaml
# Lower threshold if too strict (default: 0.7)
```

### 9.2 Debug Mode

**Enable Debug Logging**:
```bash
python main.py --log-level DEBUG run-pipeline
```

**Check All Logs**:
```bash
# Windows
dir logs\

# Linux/Mac
ls -la logs/

# View specific log
cat logs/pipeline.log
cat logs/webhook.log
cat logs/mock_ica.log
```

### 9.3 Getting Help

**Check Documentation**:
- README.md - Overview and quick start
- ARCHITECTURE.md - Technical details
- USE_CASES.md - Examples
- This file - User guide

**Check Logs**:
```bash
# Pipeline logs
cat logs/pipeline.log

# Webhook logs
cat logs/webhook.log

# Auto-update logs
cat logs/auto_update_historical.log
```

**Run Health Check**:
```bash
python main.py check-health
```

---

## 10. Best Practices

### 10.1 Configuration Management

**DO**:
- ✅ Use environment variables for secrets
- ✅ Keep .env file out of version control
- ✅ Validate configuration before deployment
- ✅ Use Azure Key Vault in production

**DON'T**:
- ❌ Hardcode credentials in code
- ❌ Commit .env file to Git
- ❌ Share credentials in plain text
- ❌ Use demo credentials in production

### 10.2 Monitoring

**DO**:
- ✅ Monitor logs regularly
- ✅ Set up alerts for failures
- ✅ Track success metrics
- ✅ Review knowledge base growth

**DON'T**:
- ❌ Ignore warning logs
- ❌ Skip health checks
- ❌ Forget to rotate credentials
- ❌ Neglect performance metrics

### 10.3 Knowledge Base Management

**DO**:
- ✅ Upload initial historical data
- ✅ Let system learn from successes
- ✅ Review ingested patterns periodically
- ✅ Document custom patterns

**DON'T**:
- ❌ Ingest low-confidence fixes
- ❌ Pollute with failed attempts
- ❌ Skip validation before ingestion
- ❌ Forget to backup historical data

### 10.4 Fix Application

**DO**:
- ✅ Review high-risk fixes before approval
- ✅ Test fixes in staging first
- ✅ Monitor post-deployment
- ✅ Keep audit trail

**DON'T**:
- ❌ Auto-merge high-risk fixes
- ❌ Skip automated tests
- ❌ Deploy without validation
- ❌ Ignore rollback procedures

### 10.5 Performance Optimization

**DO**:
- ✅ Use MCP caching for known patterns
- ✅ Monitor resolution times
- ✅ Optimize similarity thresholds
- ✅ Scale horizontally when needed

**DON'T**:
- ❌ Query MCP for every failure
- ❌ Set thresholds too high/low
- ❌ Ignore cache hit rates
- ❌ Over-provision resources

---

## 11. Quick Reference

### 11.1 Essential Commands

```bash
# Start demo
START_ALL_DEMOS.bat

# Validate config
python main.py validate-config

# Run pipeline
python main.py run-pipeline

# Start monitoring
python main.py monitor --interval 60

# Start dashboard
python unified_dashboard.py

# Upload historical data
UPLOAD_TO_CONTEXT_STUDIO.bat

# Record manual fix
python post_deployment_hook.py --job-name "Job Name" --error-type "Error" --fix-description "Fix"
```

### 11.2 Important URLs

- **Dashboard**: http://localhost:5002
- **Mock ICA**: http://localhost:5000
- **Webhook**: http://localhost:8080
- **Health Check**: http://localhost:8080/health

### 11.3 Important Files

- **Configuration**: `config.yaml`
- **Environment**: `.env`
- **MCP Config**: `.bob/mcp.json`
- **Historical Data**: `historical_failures_for_context_studio.txt`
- **Logs**: `logs/` directory
- **Fix Records**: `pipeline_fixes/` directory

### 11.4 Support Resources

- **Documentation**: All .md files in root directory
- **Examples**: `examples/` directory
- **Mock Data**: `mock_data/` directory
- **Logs**: `logs/` directory

---

## 12. Next Steps

### 12.1 After First Run

1. ✅ Explore the dashboard
2. ✅ Try different failure scenarios
3. ✅ Review vector search results
4. ✅ Check logs for understanding
5. ✅ Read USE_CASES.md for examples

### 12.2 Before Production

1. ✅ Configure Azure credentials
2. ✅ Set up ICA API access
3. ✅ Upload historical data
4. ✅ Test with real failures
5. ✅ Train team on workflows

### 12.3 Continuous Improvement

1. ✅ Monitor success metrics
2. ✅ Grow knowledge base
3. ✅ Optimize thresholds
4. ✅ Share learnings with team
5. ✅ Document custom patterns

---

**Version**: 2.0.0  
**Last Updated**: 2026-05-26  
**Status**: Ready for Use

**Need Help?** Check the logs in `logs/` directory or review the documentation files.

**Transform failures into learning opportunities! 🚀**