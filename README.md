# Azure Function Auto-Diagnose and Auto-Fix Pipeline

A comprehensive, production-ready tool for automated detection, analysis, and remediation of Azure Function failures. This pipeline integrates Azure Monitor, Intelligent Code Analyzer (ICA), and BOB (Build, Open PR, Branch) automation to provide end-to-end failure resolution.

## 🌟 Features

- **Automated Failure Detection**: Continuously monitors Azure Functions using Application Insights and Azure Monitor
- **Intelligent Root Cause Analysis**: Leverages ICA to analyze failures and identify root causes
- **Automated Fix Generation**: Generates code, infrastructure, and configuration fixes
- **Pull Request Automation**: Automatically creates branches, applies fixes, and opens PRs
- **Risk Assessment**: Evaluates fix risk and determines approval requirements
- **Post-Deployment Validation**: Verifies fixes after deployment
- **Webhook Support**: Receives alerts from Event Grid and Logic Apps
- **Comprehensive Logging**: Structured JSON logging with multiple output formats
- **Extensible Architecture**: Modular design for easy customization

## 📋 Prerequisites

- Python 3.8 or higher
- Azure subscription with:
  - Azure Function App
  - Application Insights
  - Azure Monitor
  - Event Grid (optional)
- Git repository (GitHub, GitLab, or Azure DevOps)
- ICA service endpoint (or mock implementation)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd cron-job-automation

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure credentials and configuration
# Edit config.yaml for advanced settings
```

### 3. Validate Configuration

```bash
python main.py validate-config
```

### 4. Run the Pipeline

```bash
# Execute pipeline once
python main.py run-pipeline

# Continuous monitoring mode
python main.py monitor --interval 60

# Start webhook server
python main.py webhook --host 0.0.0.0 --port 8080
```

## 📖 Usage

### Command-Line Interface

The tool provides a comprehensive CLI with multiple commands:

#### Validate Configuration
```bash
python main.py validate-config
```

#### Run Pipeline Once
```bash
# Process latest failure
python main.py run-pipeline

# Process specific operation
python main.py run-pipeline --operation-id <operation-id>
```

#### Continuous Monitoring
```bash
python main.py monitor --interval 60
```

#### Start Webhook Server
```bash
python main.py webhook --host 0.0.0.0 --port 8080
```

#### Check Component Health
```bash
python main.py check-health
```

#### View Execution History
```bash
python main.py history --limit 10
```

#### Analyze Specific Failure
```bash
python main.py analyze <operation-id>
```

#### Show Version
```bash
python main.py version
```

### Configuration Options

Edit `config.yaml` to customize:

- **Azure Settings**: Subscription, resource group, function name
- **Monitoring**: Alert thresholds, check intervals
- **ICA Settings**: API endpoint, analysis depth
- **BOB Settings**: Repository URL, approval requirements
- **Notifications**: Email, Slack, Teams
- **Logging**: Level, format, output destinations
- **Risk Management**: Approval thresholds, auto-merge settings

## 🏗️ Architecture

### Pipeline Stages

1. **Monitoring**: Detects failures using Azure Monitor and Application Insights
2. **Diagnostics**: Collects logs, metrics, and context
3. **Analysis**: ICA analyzes root cause and generates fixes
4. **Automation**: BOB applies fixes and creates pull requests
5. **Validation**: Verifies deployment success

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Azure     │    │     ICA      │    │     BOB      │
│   Monitor    │───▶│    Client    │───▶│  Automation  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                                        │
        ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│ Diagnostics  │                        │  Git/GitHub  │
│   Webhook    │                        │   PR/Merge   │
└──────────────┘                        └──────────────┘
```

## 📁 Project Structure

```
cron-job-automation/
├── config.yaml              # Main configuration file
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
├── main.py                 # CLI entry point
├── bob-pipeline.yaml       # CI/CD pipeline definition
├── workflow.yaml           # Workflow specification
├── src/
│   ├── __init__.py
│   ├── config_manager.py   # Configuration management
│   ├── logger.py           # Logging setup
│   ├── utils.py            # Utility functions
│   ├── azure_monitor.py    # Azure monitoring integration
│   ├── diagnostics_webhook.py  # Webhook server
│   ├── ica_client.py       # ICA integration
│   ├── bob_automation.py   # BOB automation
│   └── pipeline_orchestrator.py  # Main orchestrator
├── logs/                   # Log files (created automatically)
└── temp_repo/             # Temporary git repository (created automatically)
```

## 🔧 Configuration Details

### Environment Variables

Required environment variables (see `.env.example`):

```bash
# Azure
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_FUNCTION_NAME=your-function-name

# Application Insights
APP_INSIGHTS_KEY=your-app-insights-key
APP_INSIGHTS_CONNECTION_STRING=your-connection-string

# ICA
ICA_API_ENDPOINT=https://your-ica-endpoint.com/api
ICA_API_KEY=your-ica-api-key

# Git
GIT_REPOSITORY_URL=https://github.com/your-org/your-repo.git
GIT_TOKEN=your-git-token
```

### Advanced Configuration

The `config.yaml` file provides extensive customization options:

- **Monitoring intervals and thresholds**
- **ICA analysis depth and timeout**
- **BOB branch naming and approval rules**
- **Risk assessment thresholds**
- **Notification channels**
- **Logging preferences**
- **Extensibility options**

## 🔐 Security

### Best Practices

1. **Never commit secrets**: Use environment variables or Azure Key Vault
2. **Use service principals**: Create dedicated service principals with minimal permissions
3. **Enable encryption**: Configure `security.encrypt_secrets: true` in config.yaml
4. **Rotate credentials**: Regularly rotate API keys and tokens
5. **Audit logs**: Review execution logs regularly

### Required Permissions

The service principal needs:

- **Azure Monitor**: Read access to Application Insights and Log Analytics
- **Azure Functions**: Read access to function app
- **Git Repository**: Write access to create branches and PRs
- **CI/CD**: Trigger pipeline execution

## 📊 Monitoring and Observability

### Logs

Logs are written to:
- Console (stdout)
- File (`logs/pipeline.log`)
- Structured JSON format for easy parsing

### Metrics

Track pipeline execution:
- Success/failure rates
- Execution duration
- Stage completion times
- Fix application success rates

### Alerts

Configure alerts for:
- Pipeline failures
- ICA analysis failures
- BOB automation failures
- Validation failures

## 🧪 Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### End-to-End Tests

```bash
pytest tests/e2e/
```

## 🔄 CI/CD Integration

### Azure Pipelines

The included `bob-pipeline.yaml` defines a complete CI/CD pipeline:

1. **Build**: Restore packages and build code
2. **Test**: Run unit and integration tests
3. **Review**: Wait for manual approval
4. **Deploy**: Deploy to Azure Function

### GitHub Actions

Create `.github/workflows/pipeline.yml`:

```yaml
name: Auto-Fix Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
      - name: Deploy
        run: python main.py run-pipeline
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Configuration validation fails
```bash
# Solution: Check environment variables
python main.py validate-config
```

**Issue**: Azure authentication fails
```bash
# Solution: Verify service principal credentials
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
```

**Issue**: ICA service unreachable
```bash
# Solution: Check ICA endpoint and API key
python main.py check-health
```

**Issue**: Git operations fail
```bash
# Solution: Verify Git token permissions
git ls-remote $GIT_REPOSITORY_URL
```

## 📚 API Reference

### PipelineOrchestrator

Main orchestrator class that coordinates all pipeline stages.

```python
from src.pipeline_orchestrator import PipelineOrchestrator
from src.config_manager import get_config

config = get_config('config.yaml')
orchestrator = PipelineOrchestrator(config)

# Execute pipeline
result = orchestrator.execute_pipeline()

# Continuous monitoring
orchestrator.monitor_continuously(check_interval_seconds=60)
```

### AzureMonitor

Azure monitoring and diagnostics collection.

```python
from src.azure_monitor import AzureMonitor

monitor = AzureMonitor(config)

# Detect failures
failures = monitor.detect_failures(time_window_minutes=5)

# Get failure details
details = monitor.get_failure_details(operation_id)

# Create diagnostic package
package = monitor.create_diagnostic_package(operation_id)
```

### ICAClient

Intelligent Code Analyzer integration.

```python
from src.ica_client import ICAClient

ica = ICAClient(config)

# Analyze failure
analysis = ica.process_analysis(diagnostic_package)

# Extract root cause
root_cause = ica.extract_root_cause(analysis)
```

### BOBAutomation

Build, Open PR, Branch automation.

```python
from src.bob_automation import BOBAutomation

bob = BOBAutomation(config)

# Apply patches and create PR
result = bob.apply_patches(analysis_package, operation_id)
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Azure SDK for Python
- Flask for webhook server
- Click for CLI
- GitPython for Git operations
- PyGithub for GitHub API

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

## 🗺️ Roadmap

- [ ] Support for multiple cloud providers
- [ ] Machine learning-based failure prediction
- [ ] Advanced analytics dashboard
- [ ] Slack/Teams bot integration
- [ ] Knowledge base for common failures
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] Kubernetes deployment

---

**Version**: 1.0.0  
**Last Updated**: 2026-05-14