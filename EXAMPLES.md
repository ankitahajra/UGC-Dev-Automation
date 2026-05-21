# Usage Examples

This document provides practical examples of using the Azure Function Auto-Diagnose and Auto-Fix Pipeline.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Advanced Scenarios](#advanced-scenarios)
3. [Integration Examples](#integration-examples)
4. [Custom Workflows](#custom-workflows)
5. [API Usage](#api-usage)

## Basic Usage

### Example 1: Single Pipeline Execution

Execute the pipeline once to process the latest failure:

```bash
python main.py run-pipeline
```

**Output:**
```
Starting pipeline execution...

Pipeline Status: success
Duration: 2m 34s
Final Stage: completed

MONITORING:
  Status: success

DIAGNOSTICS:
  Status: success

ANALYSIS:
  Status: success

AUTOMATION:
  Status: success
  Pull Request: https://github.com/your-org/your-repo/pull/123

✓ Pipeline completed successfully
```

### Example 2: Process Specific Failure

Analyze and fix a specific operation by ID:

```bash
python main.py run-pipeline --operation-id abc123-def456-ghi789
```

### Example 3: Continuous Monitoring

Run continuous monitoring with custom interval:

```bash
# Check every 30 seconds
python main.py monitor --interval 30

# Check every 5 minutes
python main.py monitor --interval 300
```

**Output:**
```
Starting continuous monitoring (interval: 30s)
Press Ctrl+C to stop

[2026-05-14 12:00:00] INFO - Checking for failures...
[2026-05-14 12:00:05] INFO - No failures detected
[2026-05-14 12:00:30] INFO - Checking for failures...
[2026-05-14 12:00:35] WARNING - Detected 1 failures, triggering pipeline
[2026-05-14 12:00:40] INFO - Pipeline execution started
...
```

### Example 4: Start Webhook Server

Start the webhook server to receive alerts:

```bash
python main.py webhook --host 0.0.0.0 --port 8080
```

**Test the webhook:**
```bash
curl -X POST http://localhost:8080/diagnostics \
  -H "Content-Type: application/json" \
  -d '{
    "functionName": "my-function",
    "invocationId": "abc123",
    "exceptionMessage": "NullReferenceException",
    "timestamp": "2026-05-14T12:00:00Z"
  }'
```

## Advanced Scenarios

### Example 5: Analyze Without Fixing

Analyze a failure without applying fixes:

```bash
python main.py analyze abc123-def456-ghi789
```

**Output:**
```
Analyzing operation: abc123-def456-ghi789

Diagnostic Package Created:
  Function: my-autofix-function
  Timestamp: 2026-05-14 12:00:00

✓ Analysis completed successfully

Root Cause:
  Category: code_error
  Summary: NullReferenceException in ProcessRequest method
  Confidence: 95.5%

Risk Assessment:
  Overall Risk: medium
  Approval Required: True

Recommended Fixes:
  ✓ Code fix available
  ✓ Configuration fix available
```

### Example 6: Check System Health

Verify all components are working:

```bash
python main.py check-health
```

**Output:**
```
Checking component health...

✓ Azure Function: Healthy
✓ ICA Service: Healthy
✓ BOB Automation: Configured

All components are healthy
```

### Example 7: View Execution History

Review recent pipeline executions:

```bash
python main.py history --limit 5
```

**Output:**
```
Showing last 5 executions:

1. Pipeline ID: pipeline-1715684400
   Status: success
   Start Time: 2026-05-14 12:00:00
   Duration: 2m 34s
   Final Stage: completed

2. Pipeline ID: pipeline-1715680800
   Status: success
   Start Time: 2026-05-14 11:00:00
   Duration: 3m 12s
   Final Stage: completed

...
```

## Integration Examples

### Example 8: Azure DevOps Pipeline Integration

Create `.azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.9'

- script: |
    pip install -r requirements.txt
  displayName: 'Install dependencies'

- script: |
    python main.py validate-config
  displayName: 'Validate configuration'

- script: |
    python main.py check-health
  displayName: 'Health check'

- script: |
    python main.py run-pipeline
  displayName: 'Execute pipeline'
  env:
    AZURE_CLIENT_SECRET: $(AZURE_CLIENT_SECRET)
    GIT_TOKEN: $(GIT_TOKEN)
```

### Example 9: GitHub Actions Integration

Create `.github/workflows/autofix.yml`:

```yaml
name: Auto-Fix Pipeline

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:

jobs:
  autofix:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run pipeline
      env:
        AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
        AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
        AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
        AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
        GIT_TOKEN: ${{ secrets.GIT_TOKEN }}
      run: python main.py run-pipeline
```

### Example 10: Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  autofix-pipeline:
    build: .
    container_name: autofix-pipeline
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/app/logs
      - ./config.yaml:/app/config.yaml
    command: python main.py monitor --interval 60
    
  autofix-webhook:
    build: .
    container_name: autofix-webhook
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8081:8080"
    volumes:
      - ./logs:/app/logs
      - ./config.yaml:/app/config.yaml
    command: python main.py webhook --host 0.0.0.0 --port 8080
```

Run with:
```bash
docker-compose up -d
```

## Custom Workflows

### Example 11: Custom Python Script

Create a custom script `custom_workflow.py`:

```python
#!/usr/bin/env python3
"""Custom workflow example"""

from src.config_manager import get_config
from src.pipeline_orchestrator import PipelineOrchestrator
from src.azure_monitor import AzureMonitor
from src.ica_client import ICAClient
from src.logger import setup_logging, get_logger

# Setup
setup_logging(level='INFO', log_format='json', output='both')
logger = get_logger(__name__)

config = get_config('config.yaml')

# Initialize components
orchestrator = PipelineOrchestrator(config)
azure_monitor = AzureMonitor(config)
ica_client = ICAClient(config)

# Custom workflow
def custom_failure_handler():
    """Handle failures with custom logic"""
    
    # Detect failures
    failures = azure_monitor.detect_failures(time_window_minutes=10)
    
    if not failures:
        logger.info("No failures detected")
        return
    
    # Process each failure
    for failure in failures:
        operation_id = failure.get('operation_Id', '')
        logger.info(f"Processing failure: {operation_id}")
        
        # Create diagnostic package
        diagnostic_package = azure_monitor.create_diagnostic_package(operation_id)
        
        # Analyze with ICA
        analysis = ica_client.process_analysis(diagnostic_package)
        
        # Check risk level
        risk = analysis.get('risk_assessment', {}).get('overall_risk', 'medium')
        
        # Only auto-fix low risk issues
        if risk == 'low':
            logger.info(f"Auto-fixing low risk issue: {operation_id}")
            result = orchestrator.execute_pipeline(operation_id)
            logger.info(f"Pipeline result: {result['status']}")
        else:
            logger.warning(f"High risk issue detected, manual review required: {operation_id}")
            # Send notification or create ticket
            pass

if __name__ == '__main__':
    custom_failure_handler()
```

Run the custom script:
```bash
python custom_workflow.py
```

### Example 12: Scheduled Task (Windows)

Create `run_pipeline.bat`:

```batch
@echo off
cd C:\path\to\cron-job-automation
call venv\Scripts\activate
python main.py run-pipeline >> logs\scheduled.log 2>&1
```

Schedule with Task Scheduler:
```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\run_pipeline.bat"
$trigger = New-ScheduledTaskTrigger -Once -At 12:00AM -RepetitionInterval (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "AutoFixPipeline" -Action $action -Trigger $trigger
```

### Example 13: Cron Job (Linux)

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add entry (runs every 15 minutes)
*/15 * * * * cd /home/user/cron-job-automation && /home/user/cron-job-automation/venv/bin/python main.py run-pipeline >> logs/cron.log 2>&1
```

## API Usage

### Example 14: Programmatic Pipeline Execution

```python
from src.config_manager import get_config
from src.pipeline_orchestrator import PipelineOrchestrator

# Load configuration
config = get_config('config.yaml')

# Create orchestrator
orchestrator = PipelineOrchestrator(config)

# Execute pipeline
result = orchestrator.execute_pipeline()

# Check result
if result['status'] == 'success':
    print(f"Pipeline completed in {result['duration']}")
    
    # Get automation result
    automation = result['stages']['automation']['automation_result']
    print(f"PR created: {automation['pr_url']}")
else:
    print(f"Pipeline failed: {result.get('error', 'Unknown error')}")
```

### Example 15: Custom Monitoring Logic

```python
from src.azure_monitor import AzureMonitor
from src.config_manager import get_config
import time

config = get_config('config.yaml')
monitor = AzureMonitor(config)

def custom_monitor():
    """Custom monitoring with specific criteria"""
    
    while True:
        # Check function health
        health = monitor.check_function_health()
        
        if health['state'] != 'Running':
            print(f"Function unhealthy: {health['state']}")
            # Trigger alert
        
        # Check for failures
        failures = monitor.detect_failures(time_window_minutes=5)
        
        if len(failures) > 5:
            print(f"High failure rate detected: {len(failures)} failures")
            # Trigger escalation
        
        # Get performance metrics
        metrics = monitor.get_performance_metrics(time_window_minutes=15)
        
        if metrics.get('success_rate', 100) < 95:
            print(f"Low success rate: {metrics['success_rate']:.2f}%")
            # Trigger investigation
        
        time.sleep(60)

if __name__ == '__main__':
    custom_monitor()
```

### Example 16: Webhook Event Handler

```python
from flask import Flask, request, jsonify
from src.config_manager import get_config
from src.pipeline_orchestrator import PipelineOrchestrator

app = Flask(__name__)
config = get_config('config.yaml')
orchestrator = PipelineOrchestrator(config)

@app.route('/webhook/failure', methods=['POST'])
def handle_failure():
    """Custom webhook handler"""
    
    data = request.get_json()
    
    # Extract operation ID
    operation_id = data.get('operation_id')
    severity = data.get('severity', 'medium')
    
    # Only process critical failures immediately
    if severity == 'critical':
        result = orchestrator.execute_pipeline(operation_id)
        return jsonify(result), 200
    else:
        # Queue for later processing
        return jsonify({'status': 'queued'}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Example 17: Batch Processing

```python
from src.config_manager import get_config
from src.azure_monitor import AzureMonitor
from src.pipeline_orchestrator import PipelineOrchestrator
import concurrent.futures

config = get_config('config.yaml')
monitor = AzureMonitor(config)
orchestrator = PipelineOrchestrator(config)

def process_failure(operation_id):
    """Process a single failure"""
    return orchestrator.execute_pipeline(operation_id)

def batch_process_failures():
    """Process multiple failures in parallel"""
    
    # Get all failures from last hour
    failures = monitor.detect_failures(time_window_minutes=60)
    
    if not failures:
        print("No failures to process")
        return
    
    # Extract operation IDs
    operation_ids = [f.get('operation_Id', '') for f in failures]
    
    # Process in parallel (max 3 concurrent)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = executor.map(process_failure, operation_ids)
    
    # Summarize results
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"Processed {len(operation_ids)} failures: {success_count} successful")

if __name__ == '__main__':
    batch_process_failures()
```

## Testing Examples

### Example 18: Mock ICA Service

Create a mock ICA service for testing:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Mock ICA analysis endpoint"""
    
    data = request.get_json()
    
    # Return mock analysis
    return jsonify({
        'status': 'success',
        'root_cause': {
            'category': 'code_error',
            'summary': 'Mock error for testing',
            'confidence': 0.95,
            'details': 'This is a mock analysis for testing purposes'
        },
        'recommended_fixes': {
            'code_fix': {
                'file_path': 'src/example.py',
                'changes': [
                    {
                        'old': 'old_code',
                        'new': 'new_code'
                    }
                ],
                'description': 'Fix null reference',
                'risk_level': 'low'
            }
        },
        'risk_assessment': {
            'overall_risk': 'low',
            'approval_required': False
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run mock service:
```bash
python mock_ica.py
```

Update config.yaml:
```yaml
ica:
  api_endpoint: "http://localhost:5000"
  api_key: "mock-key"
```

## Troubleshooting Examples

### Example 19: Debug Mode

Run with debug logging:

```bash
python main.py --log-level DEBUG run-pipeline
```

### Example 20: Dry Run

Test configuration without executing:

```bash
python main.py validate-config
python main.py check-health
```

---

For more examples and use cases, refer to the [README.md](README.md) and [SETUP.md](SETUP.md).