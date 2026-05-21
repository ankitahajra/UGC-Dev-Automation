# Web Dashboard Quick Start Guide

## 🚀 How to Run

### Windows:
```bash
run_web_demo.bat
```

### Linux/Mac:
```bash
chmod +x run_web_demo.sh
./run_web_demo.sh
```

The dashboard will automatically open at: **http://localhost:3000**

---

## ✅ Verify Services Are Running

After starting, check the dashboard's "Services Status" section:
- ✅ **Mock ICA Service** should show a GREEN dot
- ✅ **Diagnostics Webhook** should show a GREEN dot

If either shows RED, click the "🔄 Refresh Status" button.

---

## 🐛 Troubleshooting

### Issue: "Make sure webhook is running" error

**Solution 1: Check if services started**
```bash
# Check if ports are in use
netstat -ano | findstr :5000
netstat -ano | findstr :8080
netstat -ano | findstr :3000
```

**Solution 2: Restart services manually**

Open 3 separate terminal windows:

**Terminal 1 - Mock ICA:**
```bash
set ICA_API_ENDPOINT=http://localhost:5000
set ICA_API_KEY=demo-key
python examples\mock_ica_service.py
```

**Terminal 2 - Webhook:**
```bash
set AZURE_SUBSCRIPTION_ID=demo-subscription
set AZURE_TENANT_ID=demo-tenant
set AZURE_CLIENT_ID=demo-client
set AZURE_CLIENT_SECRET=demo-secret
set AZURE_RESOURCE_GROUP=demo-rg
set AZURE_FUNCTION_NAME=demo-function
set ICA_API_ENDPOINT=http://localhost:5000
set ICA_API_KEY=demo-key
python main.py webhook --host 0.0.0.0 --port 8080
```

**Terminal 3 - Dashboard:**
```bash
python web_dashboard.py
```

**Solution 3: Test services individually**

Test Mock ICA:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Mock ICA Service",
  "version": "1.0.0"
}
```

Test Webhook:
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-14T12:00:00Z",
  "service": "diagnostics-webhook"
}
```

---

### Issue: Port already in use

**Solution:**
```bash
# Windows - Kill process on port
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Or use different ports
python examples\mock_ica_service.py  # Change port in code
python main.py webhook --port 8081   # Use different port
python web_dashboard.py              # Change port in code
```

---

### Issue: Dashboard not loading

**Solution:**
1. Check if Python is running: Look for `python.exe` in Task Manager
2. Check browser console for errors (F12)
3. Try accessing directly: http://localhost:3000
4. Clear browser cache and reload

---

### Issue: Services show RED in dashboard

**Solution:**
1. Click "🔄 Refresh Status" button
2. Wait 5 seconds and refresh again
3. Check logs:
   ```bash
   type logs\mock_ica.log
   type logs\webhook.log
   type logs\dashboard.log
   ```
4. Restart services manually (see Solution 2 above)

---

## 📝 Step-by-Step Demo Instructions

### 1. Start the Dashboard
```bash
run_web_demo.bat
```
Wait for browser to open automatically.

### 2. Verify Services
- Check that both services show GREEN dots
- If RED, click "🔄 Refresh Status"

### 3. Run Complete Pipeline
- Click "▶️ Run Complete Pipeline" button
- Watch the 5 stages execute:
  1. Monitoring (detects failure)
  2. Diagnostics (collects data)
  3. Analysis (ICA identifies root cause)
  4. Automation (BOB creates PR)
  5. Validation (verifies deployment)

### 4. Simulate Failures
Click any failure type button:
- **Null Reference** - Most common code error
- **Timeout** - Configuration issue
- **Out of Memory** - Resource problem
- **DB Connection** - Dependency failure

### 5. View Results
- Check "Key Metrics" for statistics
- Review "Execution History" for past runs
- Show the PR URL that was created

---

## 🎯 Demo Tips

### For Presentations:
1. **Start with services check** - Show everything is healthy
2. **Run pipeline first** - Let audience see complete flow
3. **Explain each stage** - Point out what's happening
4. **Simulate a failure** - Show it handles different types
5. **Highlight metrics** - Emphasize 3-minute resolution vs 2-4 hours manual

### Key Points to Emphasize:
- ✅ **Fully Automated** - No manual intervention
- ✅ **Fast** - 3 minutes vs 2-4 hours
- ✅ **Reliable** - Consistent results
- ✅ **Intelligent** - AI-powered analysis
- ✅ **Safe** - Risk assessment and validation

---

## 🔧 Advanced Usage

### Run Services Separately

If you need more control, run each service in its own terminal:

```bash
# Terminal 1
python examples\mock_ica_service.py

# Terminal 2  
python main.py webhook

# Terminal 3
python web_dashboard.py
```

### Check Logs in Real-Time

```bash
# Windows
powershell Get-Content logs\webhook.log -Wait

# Linux/Mac
tail -f logs/webhook.log
```

### Test API Endpoints

```bash
# Get pipeline status
curl http://localhost:3000/api/status

# Check services
curl http://localhost:3000/api/services/check

# Get execution history
curl http://localhost:3000/api/executions
```

---

## 📊 What Each Button Does

| Button | Action |
|--------|--------|
| **▶️ Run Complete Pipeline** | Executes all 5 stages automatically |
| **🔄 Reset** | Reloads the page and clears state |
| **🔄 Refresh Status** | Checks if services are running |
| **Null Reference** | Simulates NullReferenceException |
| **Timeout** | Simulates TimeoutException |
| **Out of Memory** | Simulates OutOfMemoryException |
| **DB Connection** | Simulates DatabaseConnectionException |

---

## 🆘 Still Having Issues?

### Quick Diagnostic:

1. **Check Python version:**
   ```bash
   python --version
   ```
   Need 3.8 or higher.

2. **Check if Flask is installed:**
   ```bash
   pip list | findstr flask
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install flask flask-cors pyyaml python-dotenv requests --force-reinstall
   ```

4. **Check firewall:**
   - Allow Python through Windows Firewall
   - Ports 3000, 5000, 8080 must be open

5. **Try the simple demo instead:**
   ```bash
   python examples\demo_pipeline.py
   ```

---

## 📞 Need Help?

If services still won't start:

1. Check the log files in `logs/` directory
2. Make sure no other applications are using ports 3000, 5000, or 8080
3. Try running services manually in separate terminals
4. Restart your computer and try again

---

## ✨ Success Checklist

- [ ] `run_web_demo.bat` executed without errors
- [ ] Browser opened to http://localhost:3000
- [ ] Both services show GREEN dots
- [ ] "Run Complete Pipeline" button works
- [ ] Stages progress through all 5 steps
- [ ] Failure simulation works
- [ ] Metrics update correctly

**If all checked, you're ready to demo!** 🎉

---

For more information, see:
- [README.md](README.md) - Complete documentation
- [RUN_NOW.md](RUN_NOW.md) - Quick start guide
- [DEMO_GUIDE.md](DEMO_GUIDE.md) - Presentation guide