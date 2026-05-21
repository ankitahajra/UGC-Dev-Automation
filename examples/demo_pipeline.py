"""
Demo Pipeline Execution
Demonstrates the complete auto-fix pipeline with mock data.
Run this to showcase the automation without real Azure resources.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config_manager import ConfigManager
from src.logger import setup_logging, get_logger

# Setup logging
setup_logging(level='INFO', log_format='text', output='console')
logger = get_logger(__name__)


class MockAzureMonitor:
    """Mock Azure Monitor for demo"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Mock Azure Monitor initialized")
    
    def detect_failures(self, time_window_minutes=5):
        """Simulate failure detection"""
        logger.info(f"Checking for failures in last {time_window_minutes} minutes...")
        time.sleep(1)
        
        # Simulate finding a failure
        failures = [{
            'operation_Id': 'demo-op-12345',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'resultCode': '500',
            'duration': 1234,
            'operation_Name': 'ProcessDataRequest'
        }]
        
        logger.warning(f"Detected {len(failures)} failure(s)")
        return failures
    
    def create_diagnostic_package(self, operation_id):
        """Create mock diagnostic package"""
        logger.info(f"Creating diagnostic package for operation {operation_id}")
        time.sleep(1)
        
        return {
            'operation_id': operation_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'function_name': 'demo-function',
            'error': {
                'message': 'NullReferenceException: Object reference not set to an instance of an object',
                'stack_trace': 'at DataProcessor.ProcessRequest(UserData userData)\nat Function.Run(HttpRequest req)',
                'type': 'NullReferenceException'
            },
            'logs': [
                {'timestamp': '2026-05-14T12:00:00Z', 'level': 'INFO', 'message': 'Function started'},
                {'timestamp': '2026-05-14T12:00:01Z', 'level': 'ERROR', 'message': 'NullReferenceException occurred'},
            ],
            'metrics': {
                'cpu_usage': 45,
                'memory_usage': 256,
                'error_rate': 15.5
            }
        }
    
    def check_function_health(self):
        """Check function health"""
        logger.info("Checking function health...")
        time.sleep(0.5)
        return {
            'function_name': 'demo-function',
            'state': 'Running',
            'enabled': True,
            'availability_state': 'Normal'
        }


class MockICAClient:
    """Mock ICA Client for demo"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Mock ICA Client initialized")
    
    def process_analysis(self, diagnostic_package):
        """Simulate ICA analysis"""
        logger.info("Sending diagnostic package to ICA for analysis...")
        time.sleep(2)
        
        logger.info("ICA analysis in progress...")
        time.sleep(2)
        
        logger.info("ICA analysis completed")
        
        return {
            'status': 'success',
            'operation_id': diagnostic_package['operation_id'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'root_cause': {
                'category': 'code_error',
                'summary': 'Null reference exception in data processing',
                'confidence': 0.95,
                'details': 'The variable "userData" is null when accessed in ProcessRequest method',
                'affected_components': ['DataProcessor', 'ProcessRequest method']
            },
            'failure_category': 'code_error',
            'risk_assessment': {
                'overall_risk': 'low',
                'impact_scope': 'function-level',
                'rollback_complexity': 'low',
                'testing_required': True,
                'approval_required': False,
                'estimated_downtime': '0 minutes',
                'considerations': ['Test in staging first', 'Monitor after deployment']
            },
            'fixes': {
                'code_fix': {
                    'file_path': 'src/DataProcessor.cs',
                    'changes': [{
                        'old': 'var result = userData.Name;',
                        'new': 'var result = userData?.Name ?? "Unknown";'
                    }],
                    'description': 'Add null-conditional operator and default value',
                    'diff': '--- a/src/DataProcessor.cs\n+++ b/src/DataProcessor.cs\n@@ -10,7 +10,7 @@\n-        var result = userData.Name;\n+        var result = userData?.Name ?? "Unknown";',
                    'risk_level': 'low'
                }
            },
            'recommendations': [
                'Add unit tests for null userData scenarios',
                'Consider adding input validation',
                'Update error handling documentation'
            ],
            'next_steps': [
                'Review and approve pull request',
                'Merge to main branch',
                'Monitor deployment',
                'Verify fix effectiveness'
            ]
        }


class MockBOBAutomation:
    """Mock BOB Automation for demo"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Mock BOB Automation initialized")
    
    def apply_patches(self, analysis_package, operation_id):
        """Simulate applying patches and creating PR"""
        logger.info("Starting BOB automation workflow...")
        
        logger.info("Cloning repository...")
        time.sleep(1)
        
        logger.info("Creating branch: autofix/demo-op-12345")
        time.sleep(0.5)
        
        logger.info("Applying code fix to src/DataProcessor.cs...")
        time.sleep(1)
        
        logger.info("Running build...")
        time.sleep(2)
        logger.info("✓ Build successful")
        
        logger.info("Running tests...")
        time.sleep(2)
        logger.info("✓ All tests passed")
        
        logger.info("Committing changes...")
        time.sleep(0.5)
        
        logger.info("Pushing branch to remote...")
        time.sleep(1)
        
        logger.info("Creating pull request...")
        time.sleep(1)
        
        pr_url = "https://github.com/demo-org/demo-repo/pull/42"
        logger.info(f"✓ Pull request created: {pr_url}")
        
        return {
            'status': 'success',
            'message': 'Fixes applied and pull request created',
            'branch_name': 'autofix/demo-op-12345',
            'pr_url': pr_url,
            'fixes_applied': ['code'],
            'requires_approval': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_stage(stage_name, stage_num, total_stages):
    """Print stage header"""
    print(f"\n{'─' * 70}")
    print(f"Stage {stage_num}/{total_stages}: {stage_name}")
    print(f"{'─' * 70}\n")


def demo_pipeline():
    """Run complete demo pipeline"""
    
    print_banner("Azure Function Auto-Diagnose and Auto-Fix Pipeline - DEMO")
    
    print("This demo showcases the complete automation workflow:")
    print("1. Monitoring - Detect failures")
    print("2. Diagnostics - Collect failure information")
    print("3. Analysis - ICA analyzes root cause")
    print("4. Automation - BOB applies fixes and creates PR")
    print("5. Validation - Verify deployment")
    
    input("\nPress Enter to start the demo...")
    
    # Initialize components
    print_banner("Initializing Pipeline Components")
    
    # Create mock config
    config = type('MockConfig', (), {
        'get': lambda self, key, default=None: default,
        'get_azure_config': lambda self: {},
        'get_ica_config': lambda self: {},
        'get_bob_config': lambda self: {}
    })()
    
    azure_monitor = MockAzureMonitor(config)
    ica_client = MockICAClient(config)
    bob_automation = MockBOBAutomation(config)
    
    print("\n✓ All components initialized successfully")
    time.sleep(1)
    
    # Stage 1: Monitoring
    print_stage("Monitoring - Failure Detection", 1, 5)
    failures = azure_monitor.detect_failures(time_window_minutes=5)
    
    if not failures:
        print("No failures detected. Demo complete.")
        return
    
    latest_failure = failures[0]
    operation_id = latest_failure['operation_Id']
    
    print(f"\n✓ Failure detected:")
    print(f"  Operation ID: {operation_id}")
    print(f"  Result Code: {latest_failure['resultCode']}")
    print(f"  Operation: {latest_failure['operation_Name']}")
    
    input("\nPress Enter to continue to diagnostics...")
    
    # Stage 2: Diagnostics
    print_stage("Diagnostics - Information Collection", 2, 5)
    diagnostic_package = azure_monitor.create_diagnostic_package(operation_id)
    
    print(f"✓ Diagnostic package created:")
    print(f"  Function: {diagnostic_package['function_name']}")
    print(f"  Error Type: {diagnostic_package['error']['type']}")
    print(f"  Error Message: {diagnostic_package['error']['message'][:80]}...")
    print(f"  Logs Collected: {len(diagnostic_package['logs'])} entries")
    print(f"  CPU Usage: {diagnostic_package['metrics']['cpu_usage']}%")
    print(f"  Memory Usage: {diagnostic_package['metrics']['memory_usage']}MB")
    
    input("\nPress Enter to continue to analysis...")
    
    # Stage 3: Analysis
    print_stage("Analysis - ICA Root Cause Analysis", 3, 5)
    analysis_package = ica_client.process_analysis(diagnostic_package)
    
    print(f"✓ Analysis completed:")
    print(f"  Root Cause: {analysis_package['root_cause']['summary']}")
    print(f"  Category: {analysis_package['root_cause']['category']}")
    print(f"  Confidence: {analysis_package['root_cause']['confidence']:.1%}")
    print(f"  Risk Level: {analysis_package['risk_assessment']['overall_risk']}")
    print(f"  Approval Required: {analysis_package['risk_assessment']['approval_required']}")
    
    if analysis_package['fixes'].get('code_fix'):
        print(f"\n  Code Fix Available:")
        code_fix = analysis_package['fixes']['code_fix']
        print(f"    File: {code_fix['file_path']}")
        print(f"    Description: {code_fix['description']}")
    
    input("\nPress Enter to continue to automation...")
    
    # Stage 4: Automation
    print_stage("Automation - BOB Apply Fixes", 4, 5)
    automation_result = bob_automation.apply_patches(analysis_package, operation_id)
    
    print(f"\n✓ Automation completed:")
    print(f"  Status: {automation_result['status']}")
    print(f"  Branch: {automation_result['branch_name']}")
    print(f"  Pull Request: {automation_result['pr_url']}")
    print(f"  Fixes Applied: {', '.join(automation_result['fixes_applied'])}")
    
    input("\nPress Enter to continue to validation...")
    
    # Stage 5: Validation
    print_stage("Validation - Post-Deployment Check", 5, 5)
    logger.info("Waiting for deployment to stabilize...")
    time.sleep(2)
    
    health_status = azure_monitor.check_function_health()
    
    print(f"✓ Validation completed:")
    print(f"  Function State: {health_status['state']}")
    print(f"  Availability: {health_status['availability_state']}")
    print(f"  Enabled: {health_status['enabled']}")
    
    # Summary
    print_banner("Pipeline Execution Summary")
    
    print("✓ Pipeline completed successfully!")
    print(f"\nExecution Summary:")
    print(f"  Operation ID: {operation_id}")
    print(f"  Root Cause: {analysis_package['root_cause']['summary']}")
    print(f"  Fix Applied: Code fix in {analysis_package['fixes']['code_fix']['file_path']}")
    print(f"  Pull Request: {automation_result['pr_url']}")
    print(f"  Status: Ready for review and merge")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(analysis_package['next_steps'], 1):
        print(f"  {i}. {step}")
    
    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        demo_pipeline()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        raise

# Made with Bob
