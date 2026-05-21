# Setup Guide

This guide provides detailed instructions for setting up the Azure Function Auto-Diagnose and Auto-Fix Pipeline.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Setup](#azure-setup)
3. [Application Setup](#application-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Deployment Options](#deployment-options)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **Git**: [Download Git](https://git-scm.com/downloads/)
- **Azure CLI**: [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

### Required Accounts

- Azure subscription with appropriate permissions
- GitHub/GitLab/Azure DevOps account
- Access to ICA service (or ability to deploy mock service)

## Azure Setup

### 1. Create Service Principal

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "<your-subscription-id>"

# Create service principal
az ad sp create-for-rbac --name "autofix-pipeline-sp" --role Contributor --scopes /subscriptions/<subscription-id>

# Save the output - you'll need these values:
# - appId (client_id)
# - password (client_secret)
# - tenant (tenant_id)
```

### 2. Create Azure Function App

```bash
# Create resource group
az group create --name autofix-rg --location eastus

# Create storage account
az storage account create \
  --name autofixstorage \
  --resource-group autofix-rg \
  --location eastus \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --name my-autofix-function \
  --resource-group autofix-rg \
  --storage-account autofixstorage \
  --consumption-plan-location eastus \
  --runtime dotnet \
  --functions-version 4
```

### 3. Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app my-autofix-insights \
  --location eastus \
  --resource-group autofix-rg \
  --application-type web

# Get instrumentation key
az monitor app-insights component show \
  --app my-autofix-insights \
  --resource-group autofix-rg \
  --query instrumentationKey -o tsv

# Link to function app
az functionapp config appsettings set \
  --name my-autofix-function \
  --resource-group autofix-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=<instrumentation-key>
```

### 4. Create Log Analytics Workspace

```bash
# Create workspace
az monitor log-analytics workspace create \
  --resource-group autofix-rg \
  --workspace-name autofix-workspace \
  --location eastus

# Get workspace ID and key
az monitor log-analytics workspace show \
  --resource-group autofix-rg \
  --workspace-name autofix-workspace \
  --query customerId -o tsv

az monitor log-analytics workspace get-shared-keys \
  --resource-group autofix-rg \
  --workspace-name autofix-workspace \
  --query primarySharedKey -o tsv
```

### 5. Create Event Grid Topic (Optional)

```bash
# Create Event Grid topic
az eventgrid topic create \
  --name autofix-events \
  --resource-group autofix-rg \
  --location eastus

# Get endpoint and key
az eventgrid topic show \
  --name autofix-events \
  --resource-group autofix-rg \
  --query endpoint -o tsv

az eventgrid topic key list \
  --name autofix-events \
  --resource-group autofix-rg \
  --query key1 -o tsv
```

### 6. Create Azure Key Vault (Optional)

```bash
# Create Key Vault
az keyvault create \
  --name autofix-keyvault \
  --resource-group autofix-rg \
  --location eastus

# Grant service principal access
az keyvault set-policy \
  --name autofix-keyvault \
  --spn <service-principal-app-id> \
  --secret-permissions get list
```

### 7. Configure Azure Monitor Alerts

```bash
# Create action group for notifications
az monitor action-group create \
  --name autofix-alerts \
  --resource-group autofix-rg \
  --short-name autofix

# Create metric alert for function failures
az monitor metrics alert create \
  --name function-failure-alert \
  --resource-group autofix-rg \
  --scopes /subscriptions/<subscription-id>/resourceGroups/autofix-rg/providers/Microsoft.Web/sites/my-autofix-function \
  --condition "count requests > 0 where resultCode >= 400" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action autofix-alerts
```

## Application Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd cron-job-automation
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Directory Structure

```bash
# Create logs directory
mkdir logs

# Create temp directory for git operations
mkdir temp_repo
```

## Configuration

### 1. Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env file with your values
# Use a text editor or:
notepad .env  # Windows
nano .env     # Linux/Mac
```

Fill in the following values:

```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=<from-azure-setup>
AZURE_TENANT_ID=<from-service-principal>
AZURE_CLIENT_ID=<from-service-principal>
AZURE_CLIENT_SECRET=<from-service-principal>
AZURE_RESOURCE_GROUP=autofix-rg
AZURE_FUNCTION_NAME=my-autofix-function

# Application Insights
APP_INSIGHTS_KEY=<from-app-insights>
APP_INSIGHTS_CONNECTION_STRING=<from-app-insights>

# Log Analytics
LOG_ANALYTICS_WORKSPACE_ID=<from-log-analytics>
LOG_ANALYTICS_WORKSPACE_KEY=<from-log-analytics>

# Event Grid (if using)
EVENT_GRID_TOPIC_ENDPOINT=<from-event-grid>
EVENT_GRID_TOPIC_KEY=<from-event-grid>

# ICA Configuration
ICA_API_ENDPOINT=https://your-ica-endpoint.com/api
ICA_API_KEY=your-ica-api-key

# Git Configuration
GIT_REPOSITORY_URL=https://github.com/your-org/your-repo.git
GIT_TOKEN=<your-github-token>

# Azure Key Vault (if using)
AZURE_KEYVAULT_URL=https://autofix-keyvault.vault.azure.net/

# Email Notifications (if using)
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
```

### 2. Generate GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
4. Copy the token and add to `.env`

### 3. Configure config.yaml

Review and customize `config.yaml`:

```yaml
# Key settings to review:
monitoring:
  alert_threshold: 0  # Trigger on any failure
  alert_window_minutes: 5
  check_interval_seconds: 60

ica:
  enabled: true
  analysis_depth: "standard"  # Options: quick, standard, deep

bob:
  require_approval: true
  auto_merge_on_approval: false  # Set to true for automatic merging

logging:
  level: "INFO"  # Change to DEBUG for troubleshooting
  format: "json"
  output: "both"
```

## Verification

### 1. Validate Configuration

```bash
python main.py validate-config
```

Expected output:
```
✓ Configuration is valid

Key Configuration:
  Azure Function: my-autofix-function
  Resource Group: autofix-rg
  ICA Enabled: True
  BOB Approval Required: True
```

### 2. Check Component Health

```bash
python main.py check-health
```

Expected output:
```
Checking component health...

✓ Azure Function: Healthy
✓ ICA Service: Healthy
✓ BOB Automation: Configured

All components are healthy
```

### 3. Test Azure Connection

```bash
# Test Azure CLI authentication
az account show

# Test function app access
az functionapp show --name my-autofix-function --resource-group autofix-rg
```

### 4. Test Git Connection

```bash
# Test repository access
git ls-remote $GIT_REPOSITORY_URL
```

## Deployment Options

### Option 1: Local Development

Run the pipeline locally for testing:

```bash
# Single execution
python main.py run-pipeline

# Continuous monitoring
python main.py monitor --interval 60
```

### Option 2: Azure Container Instance

Deploy as a container:

```bash
# Build Docker image
docker build -t autofix-pipeline .

# Push to Azure Container Registry
az acr create --name autofixacr --resource-group autofix-rg --sku Basic
az acr login --name autofixacr
docker tag autofix-pipeline autofixacr.azurecr.io/autofix-pipeline:latest
docker push autofixacr.azurecr.io/autofix-pipeline:latest

# Deploy to ACI
az container create \
  --name autofix-pipeline \
  --resource-group autofix-rg \
  --image autofixacr.azurecr.io/autofix-pipeline:latest \
  --cpu 1 --memory 1 \
  --environment-variables-file .env
```

### Option 3: Azure VM

Deploy on a virtual machine:

```bash
# Create VM
az vm create \
  --name autofix-vm \
  --resource-group autofix-rg \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys

# SSH into VM
ssh azureuser@<vm-public-ip>

# Install dependencies and deploy
sudo apt update
sudo apt install python3-pip git -y
git clone <repository-url>
cd cron-job-automation
pip3 install -r requirements.txt

# Run as systemd service (see systemd section below)
```

### Option 4: Kubernetes

Deploy to AKS:

```bash
# Create AKS cluster
az aks create \
  --name autofix-aks \
  --resource-group autofix-rg \
  --node-count 2 \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --name autofix-aks --resource-group autofix-rg

# Deploy using kubectl
kubectl apply -f kubernetes/deployment.yaml
```

## Running as a Service

### Windows Service

Create `autofix-service.bat`:

```batch
@echo off
cd C:\path\to\cron-job-automation
call venv\Scripts\activate
python main.py monitor --interval 60
```

Use NSSM to install as service:
```bash
nssm install AutoFixPipeline "C:\path\to\autofix-service.bat"
nssm start AutoFixPipeline
```

### Linux Systemd Service

Create `/etc/systemd/system/autofix-pipeline.service`:

```ini
[Unit]
Description=Azure Function Auto-Fix Pipeline
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/cron-job-automation
Environment="PATH=/home/azureuser/cron-job-automation/venv/bin"
ExecStart=/home/azureuser/cron-job-automation/venv/bin/python main.py monitor --interval 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autofix-pipeline
sudo systemctl start autofix-pipeline
sudo systemctl status autofix-pipeline
```

## Webhook Setup

### 1. Start Webhook Server

```bash
python main.py webhook --host 0.0.0.0 --port 8080
```

### 2. Configure Event Grid Subscription

```bash
az eventgrid event-subscription create \
  --name autofix-subscription \
  --source-resource-id /subscriptions/<subscription-id>/resourceGroups/autofix-rg/providers/Microsoft.Web/sites/my-autofix-function \
  --endpoint http://<your-public-ip>:8080/diagnostics \
  --endpoint-type webhook
```

### 3. Expose Webhook (Production)

Use a reverse proxy like nginx:

```nginx
server {
    listen 80;
    server_name autofix.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Issue: Authentication Fails

```bash
# Verify service principal
az login --service-principal \
  -u $AZURE_CLIENT_ID \
  -p $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Check permissions
az role assignment list --assignee $AZURE_CLIENT_ID
```

### Issue: Cannot Access Application Insights

```bash
# Verify Application Insights exists
az monitor app-insights component show \
  --app my-autofix-insights \
  --resource-group autofix-rg

# Check connection string
az monitor app-insights component show \
  --app my-autofix-insights \
  --resource-group autofix-rg \
  --query connectionString
```

### Issue: Git Operations Fail

```bash
# Test token
curl -H "Authorization: token $GIT_TOKEN" https://api.github.com/user

# Verify repository access
git ls-remote https://$GIT_TOKEN@github.com/your-org/your-repo.git
```

### Issue: ICA Service Unreachable

```bash
# Test endpoint
curl -H "Authorization: Bearer $ICA_API_KEY" $ICA_API_ENDPOINT/health

# Check network connectivity
ping <ica-hostname>
```

### Enable Debug Logging

Edit `config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

Or use CLI flag:
```bash
python main.py --log-level DEBUG run-pipeline
```

## Next Steps

1. **Test the Pipeline**: Run a test execution with a known failure
2. **Configure Notifications**: Set up email/Slack/Teams notifications
3. **Customize Workflows**: Adjust approval rules and risk thresholds
4. **Monitor Performance**: Review logs and execution history
5. **Scale as Needed**: Deploy to production environment

## Support

For additional help:
- Review the [README.md](README.md)
- Check the [API documentation](README.md#api-reference)
- Open an issue on GitHub
- Contact the development team

---

**Setup Version**: 1.0.0  
**Last Updated**: 2026-05-14