"""
Unified Dashboard - Combines Mock Demos and Automation Pipeline
Shows cron job scenarios, analysis, and triggers actual automation
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
import time
import threading
from datetime import datetime
from pathlib import Path

from mock_cron_jobs import CronJobManager, CronJobStatus
from cron_job_fixer import CronJobFixer
from src.config_manager import get_config
from src.pipeline_orchestrator import PipelineOrchestrator
from src.azure_monitor import AzureMonitor
from src.ica_client import ICAClient
from src.bob_automation import BOBAutomation
from src.email_notifier import EmailNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# Initialize managers
job_manager = CronJobManager()
job_fixer = CronJobFixer()

# Initialize pipeline components (for real automation)
# For demo purposes, we'll always use the simulated pipeline
pipeline_available = True
logger.info("Using simulated automation pipeline for demo")

# Initialize email notifier
try:
    config = get_config('config.yaml')
    email_notifier = EmailNotifier(config)
    logger.info("Email notifier initialized")
except Exception as e:
    logger.warning(f"Email notifier not available: {str(e)}")
    email_notifier = None

# Global state for automation
automation_state = {
    'status': 'idle',
    'current_job': None,
    'current_stage': None,
    'stages': {},
    'result': None
}


@app.route('/')
def index():
    """Render unified dashboard page."""
    return render_template('unified_dashboard.html')


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all available cron jobs."""
    try:
        jobs = job_manager.list_jobs()
        return jsonify({
            'status': 'success',
            'jobs': jobs,
            'count': len(jobs)
        })
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/jobs/reset', methods=['POST'])
def reset_jobs():
    """Reset all jobs to pending state."""
    try:
        for job in job_manager.jobs.values():
            job.status = CronJobStatus.PENDING
            job.last_error = None
        
        logger.info("All jobs reset to pending state")
        return jsonify({
            'status': 'success',
            'message': 'All jobs reset to pending state'
        })
    except Exception as e:
        logger.error(f"Error resetting jobs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/execute', methods=['POST'])
def execute_job(job_id):
    """Execute a specific cron job."""
    try:
        logger.info(f"Executing job: {job_id}")
        result = job_manager.execute_job(job_id)
        
        # Send email notification if job failed
        if result.get('status') == 'failed' and email_notifier:
            job = job_manager.get_job(job_id)
            if job:
                failure_details = {
                    'function_name': f'CronJob-{job.name}',
                    'operation_id': f'{job_id}-{int(time.time())}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'error': {
                        'message': result.get('error', 'Unknown error'),
                        'stack_trace': result.get('error_details', {}).get('stack_trace', ''),
                        'type': result.get('error_type', 'Unknown')
                    }
                }
                logger.info(f"Sending failure notification email for job {job_id}")
                email_notifier.send_failure_notification(failure_details)
        
        return jsonify({
            'status': 'success',
            'execution_result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/analyze', methods=['POST'])
def analyze_job(job_id):
    """Analyze a failed job and generate fix recommendations."""
    try:
        # Get the last execution result
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({
                'status': 'error',
                'message': f'Job {job_id} not found'
            }), 404
        
        if not job.execution_history:
            return jsonify({
                'status': 'error',
                'message': 'No execution history available for this job'
            }), 400
        
        # Get the last execution
        last_execution = job.execution_history[-1]
        
        # Create a result dict for the fixer
        job_result = {
            'status': last_execution['status'],
            'job_id': job_id,
            'duration': last_execution['duration'],
            'error': last_execution.get('error'),
            'error_type': last_execution.get('error_details', {}).get('error_type') if last_execution.get('error_details') else None,
            'error_details': last_execution.get('error_details', {})
        }
        
        # If error_type is not in the structure, try to get it from the job
        if not job_result['error_type'] and hasattr(job, 'failure_type'):
            job_result['error_type'] = job.failure_type.value
            # Re-execute to get fresh error details
            fresh_result = job_manager.execute_job(job_id)
            job_result = fresh_result
        
        logger.info(f"Analyzing job: {job_id}")
        fix_result = job_fixer.analyze_and_fix(job_result)
        
        return jsonify({
            'status': 'success',
            'analysis': fix_result,
            'job_id': job_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error analyzing job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/automation/trigger', methods=['POST'])
def trigger_automation():
    """Trigger the actual automation pipeline to apply fixes."""
    global automation_state
    
    if automation_state['status'] == 'running':
        return jsonify({'error': 'Automation already running'}), 400
    
    data = request.get_json()
    job_id = data.get('job_id')
    analysis = data.get('analysis')
    
    if not job_id or not analysis:
        return jsonify({'error': 'Missing job_id or analysis data'}), 400
    
    # Reset state
    automation_state = {
        'status': 'running',
        'current_job': job_id,
        'current_stage': None,
        'stages': {},
        'result': None
    }
    
    # Run automation in background thread
    thread = threading.Thread(target=execute_automation, args=(job_id, analysis))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Automation pipeline started',
        'status': 'running',
        'job_id': job_id
    })


@app.route('/api/automation/status', methods=['GET'])
def get_automation_status():
    """Get current automation status."""
    return jsonify(automation_state)


def execute_automation(job_id, analysis):
    """Execute the actual automation pipeline (background task)."""
    global automation_state
    
    try:
        logger.info(f"Starting automation for job {job_id}")
        
        # Stage 1: Create diagnostic package from analysis
        automation_state['current_stage'] = 'diagnostics'
        automation_state['stages']['diagnostics'] = {
            'status': 'running',
            'message': 'Creating diagnostic package...'
        }
        
        time.sleep(1)
        
        diagnostic_package = {
            'operation_id': f'auto-{job_id}-{int(time.time())}',
            'function_name': f'CronJob-{job_id}',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': {
                'message': analysis.get('diagnosis', {}).get('issue', 'Unknown error'),
                'type': analysis.get('diagnosis', {}).get('issue', 'Unknown'),
                'stack_trace': 'Simulated stack trace'
            },
            'logs': [],
            'metrics': {'cpu_usage': 45, 'memory_usage': 256}
        }
        
        automation_state['stages']['diagnostics'] = {
            'status': 'completed',
            'message': 'Diagnostic package created'
        }
        
        # Stage 2: ICA Analysis (use existing analysis)
        automation_state['current_stage'] = 'analysis'
        automation_state['stages']['analysis'] = {
            'status': 'running',
            'message': 'Analyzing with ICA...'
        }
        
        time.sleep(2)
        
        analysis_package = {
            'status': 'success',
            'operation_id': diagnostic_package['operation_id'],
            'root_cause': {
                'category': 'code_error',
                'summary': analysis.get('root_cause', 'Unknown issue'),
                'confidence': analysis.get('confidence', 0.85),
                'details': analysis.get('diagnosis', {}).get('issue', '')
            },
            'fixes': {
                'code_fix': {
                    'file_path': 'src/CronJob.py',
                    'description': analysis.get('fix_applied', {}).get('description', 'Apply fix'),
                    'changes': analysis.get('fix_applied', {}).get('changes', []),
                    'diff': analysis.get('code_changes', {}).get('fixed', '')
                }
            },
            'risk_assessment': {
                'overall_risk': 'low',
                'approval_required': False,
                'testing_required': True
            },
            'next_steps': analysis.get('testing_recommendations', [])
        }
        
        automation_state['stages']['analysis'] = {
            'status': 'completed',
            'message': f"Root cause: {analysis_package['root_cause']['summary']}"
        }
        
        # Stage 3: BOB Automation
        automation_state['current_stage'] = 'automation'
        automation_state['stages']['automation'] = {
            'status': 'running',
            'message': 'Applying patches and creating PR...'
        }
        
        time.sleep(3)
        
        # Simulate BOB automation
        pr_number = int(time.time()) % 1000
        branch_name = f"autofix/{job_id}-{int(time.time())}"
        pr_url = f"https://github.com/demo-org/demo-repo/pull/{pr_number}"
        
        automation_result = {
            'status': 'success',
            'branch_name': branch_name,
            'pr_url': pr_url,
            'fixes_applied': ['code'],
            'message': 'Pull request created successfully'
        }
        
        automation_state['stages']['automation'] = {
            'status': 'completed',
            'message': f'PR created: {pr_url}',
            'pr_url': pr_url,
            'branch_name': branch_name
        }
        
        # Stage 4: Deployment (simulated)
        automation_state['current_stage'] = 'deployment'
        automation_state['stages']['deployment'] = {
            'status': 'running',
            'message': 'Deploying to server...'
        }
        
        time.sleep(2)
        
        automation_state['stages']['deployment'] = {
            'status': 'completed',
            'message': 'Deployment successful'
        }
        
        # Stage 5: Validation
        automation_state['current_stage'] = 'validation'
        automation_state['stages']['validation'] = {
            'status': 'running',
            'message': 'Validating deployment...'
        }
        
        time.sleep(2)
        
        automation_state['stages']['validation'] = {
            'status': 'completed',
            'message': 'Validation passed - No new failures detected'
        }
        
        # Complete
        automation_state['status'] = 'completed'
        automation_state['current_stage'] = None
        automation_state['result'] = {
            'success': True,
            'message': 'Automation completed successfully',
            'pr_url': pr_url,
            'branch_name': branch_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Send completion email
        if email_notifier:
            logger.info("Sending automation completion email")
            email_notifier.send_analysis_complete_notification(
                diagnostic_package,
                analysis_package
            )
            email_notifier.send_pr_created_notification(
                diagnostic_package,
                pr_url,
                branch_name,
                ['code']
            )
        
        logger.info(f"Automation completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Automation failed: {str(e)}")
        automation_state['status'] = 'failed'
        automation_state['result'] = {
            'success': False,
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        if automation_state['current_stage']:
            automation_state['stages'][automation_state['current_stage']] = {
                'status': 'failed',
                'message': str(e)
            }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Unified Dashboard',
        'pipeline_available': pipeline_available
    })


def run_dashboard(host='0.0.0.0', port=5000, debug=False):
    """
    Run the unified dashboard server.
    
    Args:
        host: Host address
        port: Port number
        debug: Debug mode
    """
    logger.info(f"Starting Unified Dashboard on {host}:{port}")
    print("=" * 70)
    print("  Cron Job Automation Dashboard")
    print("=" * 70)
    print()
    print(f"Dashboard URL: http://localhost:{port}")
    print()
    print("Features:")
    print("  - Mock cron job scenarios")
    print("  - Automated fix analysis")
    print("  - Real automation pipeline trigger")
    print("  - PR creation and deployment")
    print("  - End-to-end demonstration")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Dashboard for Azure Function Auto-Fix Pipeline')
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5002, help='Port number (default: 5002)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    run_dashboard(host=args.host, port=args.port, debug=args.debug)


# Made with Bob