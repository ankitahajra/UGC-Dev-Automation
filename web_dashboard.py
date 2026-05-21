"""
Web Dashboard for Azure Function Auto-Fix Pipeline Demo
Interactive web interface to demonstrate the automation
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.config_manager import ConfigManager
from src.logger import setup_logging, get_logger

# Setup logging
setup_logging(level='INFO', log_format='json', output='file', log_file='logs/dashboard.log')
logger = get_logger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Global state
pipeline_state = {
    'status': 'idle',
    'current_stage': None,
    'stages': {},
    'failures': [],
    'executions': [],
    'services': {
        'mock_ica': False,
        'webhook': False
    }
}

# Mock components for demo
class MockAzureMonitor:
    def detect_failures(self, time_window_minutes=5):
        time.sleep(1)
        return [{
            'operation_Id': f'demo-op-{int(time.time())}',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'resultCode': '500',
            'duration': 1234,
            'operation_Name': 'ProcessDataRequest'
        }]
    
    def create_diagnostic_package(self, operation_id):
        time.sleep(1)
        return {
            'operation_id': operation_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'function_name': 'demo-function',
            'error': {
                'message': 'NullReferenceException: Object reference not set',
                'stack_trace': 'at DataProcessor.ProcessRequest()',
                'type': 'NullReferenceException'
            },
            'logs': [
                {'timestamp': datetime.utcnow().isoformat() + 'Z', 'level': 'ERROR', 'message': 'NullReferenceException occurred'}
            ],
            'metrics': {'cpu_usage': 45, 'memory_usage': 256, 'error_rate': 15.5}
        }

class MockICAClient:
    def process_analysis(self, diagnostic_package):
        time.sleep(2)
        return {
            'status': 'success',
            'operation_id': diagnostic_package['operation_id'],
            'root_cause': {
                'category': 'code_error',
                'summary': 'Null reference exception in data processing',
                'confidence': 0.95,
                'details': 'The variable "userData" is null when accessed'
            },
            'fixes': {
                'code_fix': {
                    'file_path': 'src/DataProcessor.cs',
                    'description': 'Add null-conditional operator',
                    'risk_level': 'low'
                }
            },
            'risk_assessment': {
                'overall_risk': 'low',
                'approval_required': False
            }
        }

class MockBOBAutomation:
    def apply_patches(self, analysis_package, operation_id):
        time.sleep(2)
        return {
            'status': 'success',
            'branch_name': f'autofix/{operation_id}',
            'pr_url': f'https://github.com/demo-org/demo-repo/pull/{int(time.time()) % 100}',
            'fixes_applied': ['code']
        }


# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current pipeline status"""
    return jsonify(pipeline_state)

@app.route('/api/services/check')
def check_services():
    """Check if services are running"""
    import requests
    
    # Check Mock ICA
    try:
        response = requests.get('http://localhost:5000/health', timeout=2)
        pipeline_state['services']['mock_ica'] = response.status_code == 200
    except:
        pipeline_state['services']['mock_ica'] = False
    
    # Check Webhook
    try:
        response = requests.get('http://localhost:8080/health', timeout=2)
        pipeline_state['services']['webhook'] = response.status_code == 200
    except:
        pipeline_state['services']['webhook'] = False
    
    return jsonify(pipeline_state['services'])

@app.route('/api/pipeline/run', methods=['POST'])
def run_pipeline():
    """Run the complete pipeline"""
    if pipeline_state['status'] == 'running':
        return jsonify({'error': 'Pipeline already running'}), 400
    
    # Run pipeline in background thread
    thread = threading.Thread(target=execute_pipeline)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Pipeline started', 'status': 'running'})

@app.route('/api/failures/simulate', methods=['POST'])
def simulate_failure():
    """Simulate a failure"""
    data = request.get_json()
    failure_type = data.get('type', 'NullReferenceException')
    
    import requests
    
    failure_data = {
        'functionName': 'DemoFunction',
        'invocationId': f'inv-{int(time.time())}',
        'exceptionMessage': f'{failure_type}: Simulated error',
        'errorType': failure_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'cpuUsage': 45.5,
        'memoryUsage': 256
    }
    
    try:
        response = requests.post('http://localhost:8080/diagnostics', json=failure_data, timeout=10)
        if response.status_code == 200:
            pipeline_state['failures'].append(failure_data)
            return jsonify({'message': 'Failure simulated', 'data': failure_data})
        else:
            return jsonify({'error': 'Failed to send to webhook'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    log_file = Path('logs/pipeline.log')
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-50:]  # Last 50 lines
            return jsonify({'logs': recent_logs})
    return jsonify({'logs': []})

@app.route('/api/executions')
def get_executions():
    """Get execution history"""
    return jsonify({'executions': pipeline_state['executions']})


def execute_pipeline():
    """Execute the complete pipeline (background task)"""
    global pipeline_state
    
    pipeline_state['status'] = 'running'
    pipeline_state['current_stage'] = 'monitoring'
    
    execution = {
        'id': f'exec-{int(time.time())}',
        'start_time': datetime.utcnow().isoformat() + 'Z',
        'stages': {}
    }
    
    try:
        # Initialize components
        azure_monitor = MockAzureMonitor()
        ica_client = MockICAClient()
        bob_automation = MockBOBAutomation()
        
        # Stage 1: Monitoring
        pipeline_state['current_stage'] = 'monitoring'
        pipeline_state['stages']['monitoring'] = {'status': 'running', 'progress': 0}
        
        failures = azure_monitor.detect_failures()
        
        pipeline_state['stages']['monitoring'] = {
            'status': 'completed',
            'progress': 100,
            'result': f'Detected {len(failures)} failure(s)'
        }
        execution['stages']['monitoring'] = pipeline_state['stages']['monitoring']
        time.sleep(1)
        
        if not failures:
            pipeline_state['status'] = 'completed'
            return
        
        operation_id = failures[0]['operation_Id']
        
        # Stage 2: Diagnostics
        pipeline_state['current_stage'] = 'diagnostics'
        pipeline_state['stages']['diagnostics'] = {'status': 'running', 'progress': 0}
        
        diagnostic_package = azure_monitor.create_diagnostic_package(operation_id)
        
        pipeline_state['stages']['diagnostics'] = {
            'status': 'completed',
            'progress': 100,
            'result': f'Collected diagnostics for {operation_id}'
        }
        execution['stages']['diagnostics'] = pipeline_state['stages']['diagnostics']
        time.sleep(1)
        
        # Stage 3: Analysis
        pipeline_state['current_stage'] = 'analysis'
        pipeline_state['stages']['analysis'] = {'status': 'running', 'progress': 0}
        
        analysis = ica_client.process_analysis(diagnostic_package)
        
        pipeline_state['stages']['analysis'] = {
            'status': 'completed',
            'progress': 100,
            'result': f"Root cause: {analysis['root_cause']['summary']}"
        }
        execution['stages']['analysis'] = pipeline_state['stages']['analysis']
        time.sleep(1)
        
        # Stage 4: Automation
        pipeline_state['current_stage'] = 'automation'
        pipeline_state['stages']['automation'] = {'status': 'running', 'progress': 0}
        
        automation_result = bob_automation.apply_patches(analysis, operation_id)
        
        pipeline_state['stages']['automation'] = {
            'status': 'completed',
            'progress': 100,
            'result': f"PR created: {automation_result['pr_url']}"
        }
        execution['stages']['automation'] = pipeline_state['stages']['automation']
        time.sleep(1)
        
        # Stage 5: Validation
        pipeline_state['current_stage'] = 'validation'
        pipeline_state['stages']['validation'] = {'status': 'running', 'progress': 0}
        
        time.sleep(2)
        
        pipeline_state['stages']['validation'] = {
            'status': 'completed',
            'progress': 100,
            'result': 'Deployment validated successfully'
        }
        execution['stages']['validation'] = pipeline_state['stages']['validation']
        
        # Complete
        execution['end_time'] = datetime.utcnow().isoformat() + 'Z'
        execution['status'] = 'success'
        pipeline_state['executions'].insert(0, execution)
        pipeline_state['status'] = 'completed'
        pipeline_state['current_stage'] = None
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        pipeline_state['status'] = 'failed'
        pipeline_state['stages'][pipeline_state['current_stage']] = {
            'status': 'failed',
            'error': str(e)
        }


if __name__ == '__main__':
    print("=" * 70)
    print("  Azure Function Auto-Fix Pipeline - Web Dashboard")
    print("=" * 70)
    print()
    print("Starting dashboard server...")
    print()
    print("Dashboard URL: http://localhost:3000")
    print()
    print("Features:")
    print("  - Visual pipeline execution")
    print("  - Real-time status updates")
    print("  - Failure simulation")
    print("  - Execution history")
    print("  - Service health monitoring")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=3000, debug=False)

# Made with Bob
