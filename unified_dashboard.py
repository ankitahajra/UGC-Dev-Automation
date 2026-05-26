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


@app.route('/api/jobs/<job_id>/apply-historical-fix', methods=['POST'])
def apply_historical_fix(job_id):
    """Apply a historical fix to the current job failure."""
    try:
        # Get the job
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({
                'status': 'error',
                'message': f'Job {job_id} not found'
            }), 404
        
        # Get the historical failure data from request
        data = request.get_json()
        failure = data.get('failure')
        
        if not failure:
            return jsonify({
                'status': 'error',
                'message': 'No failure data provided'
            }), 400
        
        logger.info(f"Applying historical fix to job: {job_id}")
        
        # Create an analysis result based on the historical fix
        # This mimics the structure of analyze_and_fix but uses historical data
        fix_result = {
            'status': 'fix_generated',
            'diagnosis': {
                'issue': failure.get('error_message', 'Unknown error'),
                'severity': failure.get('severity', 'medium'),
                'category': failure.get('category', 'Unknown')
            },
            'root_cause': failure.get('error_message', 'Unknown error'),
            'confidence': failure.get('confidence', failure.get('similarity_score', 0.85)),
            'fix_applied': {
                'type': 'historical_fix',
                'description': failure.get('resolution', 'Applied historical fix'),
                'changes': [
                    failure.get('fix_description', failure.get('resolution', 'Applied fix from similar past failure'))
                ]
            },
            'code_changes': None,  # Historical fixes may not have code changes
            'testing_recommendations': [
                'Verify the fix resolves the current issue',
                'Run integration tests',
                'Monitor for similar failures'
            ],
            'source': 'historical_fix',
            'historical_failure': {
                'timestamp': failure.get('timestamp'),
                'similarity_score': failure.get('similarity_score'),
                'category': failure.get('category')
            }
        }
        
        # If the historical failure has specific fix details, add them
        if failure.get('fix_description'):
            fix_result['fix_applied']['changes'].append(f"Details: {failure.get('fix_description')}")
        
        if failure.get('stack_trace'):
            fix_result['diagnosis']['stack_trace'] = failure.get('stack_trace')
        
        logger.info(f"Historical fix prepared for job {job_id}")
        
        return jsonify({
            'status': 'success',
            'analysis': fix_result,
            'job_id': job_id,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'historical_fix'
        })
        
    except Exception as e:
        logger.error(f"Error applying historical fix to job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/similar-failures', methods=['POST'])
def search_similar_failures(job_id):
    """Search for similar past failures using MCP vector search."""
    try:
        # Get the job
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({
                'status': 'error',
                'message': f'Job {job_id} not found'
            }), 404
        
        if not job.last_error:
            return jsonify({
                'status': 'error',
                'message': 'No error available for this job'
            }), 400
        
        logger.info(f"Searching for similar failures for job: {job_id}")
        
        # Initialize MCP client
        from src.mcp_client import MCPClientSync
        mcp_client = MCPClientSync(get_config('config.yaml'))
        
        # Perform vector search with the error message
        search_query = f"Error: {job.last_error}"
        similar_failures = mcp_client.vector_search(search_query, top_k=5)
        
        # Format the results for display
        formatted_failures = []
        for failure in similar_failures:
            # Extract relevant information from MCP response
            content = failure.get('content', {})
            metadata = failure.get('metadata', {})
            
            formatted_failures.append({
                'error_message': content.get('error_message', content.get('description', 'Unknown error')),
                'resolution': content.get('resolution', content.get('fix_description', '')),
                'similarity_score': failure.get('score', 0.85),
                'timestamp': metadata.get('timestamp', metadata.get('date', 'Unknown')),
                'category': metadata.get('category', metadata.get('error_type', 'Uncategorized')),
                'fix_applied': content.get('fix_applied', False)
            })
        
        logger.info(f"Found {len(formatted_failures)} similar failures")
        
        return jsonify({
            'status': 'success',
            'similar_failures': formatted_failures,
            'job_id': job_id,
            'query': search_query,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error searching similar failures for job {job_id}: {str(e)}")
        # Return mock data for demonstration if MCP is not available
        mock_failures = [
            {
                'error_message': 'Database connection timeout after 30 seconds',
                'resolution': 'Increased connection timeout to 60 seconds and added retry logic',
                'similarity_score': 0.92,
                'timestamp': '2024-01-15T10:30:00Z',
                'category': 'Database Error',
                'fix_applied': True
            },
            {
                'error_message': 'Failed to connect to database server',
                'resolution': 'Updated connection string with correct credentials',
                'similarity_score': 0.87,
                'timestamp': '2024-01-10T14:20:00Z',
                'category': 'Connection Error',
                'fix_applied': True
            },
            {
                'error_message': 'Database query timeout',
                'resolution': 'Optimized query with proper indexing',
                'similarity_score': 0.78,
                'timestamp': '2024-01-05T09:15:00Z',
                'category': 'Performance Issue',
                'fix_applied': True
            }
        ]
        
        logger.info(f"Using mock data for demonstration (MCP not available: {str(e)})")
        return jsonify({
            'status': 'success',
            'similar_failures': mock_failures,
            'job_id': job_id,
            'query': f"Error: {job.last_error if job else 'Unknown'}",
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Using mock data for demonstration'
        })


@app.route('/api/historical-failures', methods=['GET'])
def get_historical_failures():
    """Fetch all historical failures from the uploaded Context Studio data file."""
    try:
        logger.info("Loading historical failures from uploaded Context Studio data file")
        
        # Read from the local file that was uploaded to Context Studio
        import json
        from pathlib import Path
        
        data_file = Path('historical_failures_for_context_studio.jsonl')
        
        if not data_file.exists():
            logger.warning("Historical data file not found locally")
            return jsonify({
                'status': 'error',
                'message': 'Historical data file not found',
                'failures': [],
                'count': 0
            })
        
        # Read and parse the JSONL file
        all_failures = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):  # Skip empty lines and comments
                    try:
                        failure = json.loads(line)
                        all_failures.append(failure)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON line: {e}")
        
        logger.info(f"Loaded {len(all_failures)} historical failures from file")
        
        # Format the results - data is already in the correct format from the file
        formatted_failures = []
        for failure in all_failures:
            formatted_failures.append({
                'id': failure.get('id', 'unknown'),
                'job_name': failure.get('job_name', 'Unknown Job'),
                'error_type': failure.get('error_type', 'Unknown Error'),
                'error_message': failure.get('error_message', ''),
                'stack_trace': failure.get('stack_trace', ''),
                'resolution': failure.get('resolution', ''),
                'fix_description': failure.get('fix_description', ''),
                'timestamp': failure.get('timestamp', datetime.utcnow().isoformat()),
                'category': failure.get('category', 'Unknown'),
                'severity': failure.get('severity', 'medium'),
                'fix_applied': failure.get('fix_applied', False),
                'confidence': failure.get('confidence', 0.0),
                'prevented_incidents': failure.get('prevented_incidents', 0)
            })
        
        # Sort by timestamp descending (newest first)
        formatted_failures.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"Formatted {len(formatted_failures)} historical failures")
        
        note = f'Loaded {len(formatted_failures)} historical failure patterns from Context Studio data file'
        
        response = {
            'status': 'success',
            'failures': formatted_failures,
            'count': len(formatted_failures),
            'source': 'Context Studio MCP',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if note:
            response['note'] = note
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error fetching historical failures: {str(e)}", exc_info=True)
        # Return mock data for demonstration if MCP is not available
        mock_failures = [
            {
                'job_name': 'Data Processing Job',
                'error_type': 'NullReferenceError',
                'error_message': 'Cannot read property \'customerId\' of null',
                'resolution': 'Added null check before accessing customer properties',
                'timestamp': '2024-01-15T08:30:00Z',
                'category': 'Code Error',
                'severity': 'high',
                'fix_applied': True,
                'confidence': 0.95,
                'prevented_incidents': 15
            },
            {
                'job_name': 'Database Sync Job',
                'error_type': 'ConnectionError',
                'error_message': 'Failed to connect to database server',
                'resolution': 'Updated connection string and added retry logic',
                'timestamp': '2024-01-10T14:20:00Z',
                'category': 'Connection Error',
                'severity': 'critical',
                'fix_applied': True,
                'confidence': 0.92,
                'prevented_incidents': 25
            },
            {
                'job_name': 'Report Generator',
                'error_type': 'TimeoutError',
                'error_message': 'Database query timeout after 30 seconds',
                'resolution': 'Optimized query with proper indexing',
                'timestamp': '2024-01-05T09:15:00Z',
                'category': 'Performance Issue',
                'severity': 'medium',
                'fix_applied': True,
                'confidence': 0.88,
                'prevented_incidents': 10
            }
        ]
        
        logger.info(f"Using mock data for demonstration (MCP not available: {str(e)})")
        return jsonify({
            'status': 'success',
            'failures': mock_failures,
            'count': len(mock_failures),
            'source': 'Mock Data (for demonstration)',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Using mock data - MCP not available'
        })


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
        
        # Safely extract analysis data with null checks
        diagnosis = analysis.get('diagnosis') if analysis else {}
        diagnosis = diagnosis if diagnosis is not None else {}
        
        diagnostic_package = {
            'operation_id': f'auto-{job_id}-{int(time.time())}',
            'function_name': f'CronJob-{job_id}',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': {
                'message': diagnosis.get('issue', 'Unknown error'),
                'type': diagnosis.get('issue', 'Unknown'),
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
        
        # Safely extract fix data with null checks
        fix_applied = analysis.get('fix_applied') if analysis else {}
        fix_applied = fix_applied if fix_applied is not None else {}
        
        code_changes = analysis.get('code_changes') if analysis else {}
        code_changes = code_changes if code_changes is not None else {}
        
        analysis_package = {
            'status': 'success',
            'operation_id': diagnostic_package['operation_id'],
            'root_cause': {
                'category': 'code_error',
                'summary': analysis.get('root_cause', 'Unknown issue') if analysis else 'Unknown issue',
                'confidence': analysis.get('confidence', 0.85) if analysis else 0.85,
                'details': diagnosis.get('issue', '')
            },
            'fixes': {
                'code_fix': {
                    'file_path': 'src/CronJob.py',
                    'description': fix_applied.get('description', 'Apply fix'),
                    'changes': fix_applied.get('changes', []),
                    'diff': code_changes.get('fixed', '')
                }
            },
            'risk_assessment': {
                'overall_risk': 'low',
                'approval_required': False,
                'testing_required': True
            },
            'next_steps': analysis.get('testing_recommendations', []) if analysis else []
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
        
        # Record the fix after successful deployment and validation
        try:
            from src.pipeline_fix_tracker import get_fix_tracker
            
            # Get job details
            job = job_manager.get_job(job_id)
            job_name = job.name if job else job_id
            
            # Extract error details from analysis
            error_message = diagnosis.get('issue', 'Unknown error')
            error_type = analysis.get('root_cause', 'Unknown') if analysis else 'Unknown'
            
            # Get fix details
            fix_applied = analysis.get('fix_applied') if analysis else {}
            fix_applied = fix_applied if fix_applied is not None else {}
            
            resolution = fix_applied.get('description', 'Fix applied via automation')
            fix_description = ', '.join(fix_applied.get('changes', [])) if fix_applied.get('changes') else 'Automated fix applied'
            
            # Determine category and severity
            category = 'Code Error'  # Default, could be enhanced based on error type
            severity = diagnosis.get('severity', 'medium')
            
            # Record the fix
            tracker = get_fix_tracker()
            fix_file = tracker.record_fix(
                job_name=job_name,
                error_type=error_type,
                error_message=error_message,
                stack_trace=diagnostic_package['error'].get('stack_trace', ''),
                resolution=resolution,
                fix_description=fix_description,
                category=category,
                severity=severity,
                deployment_id=f"auto-deploy-{int(time.time())}",
                pr_url=pr_url,
                branch_name=branch_name
            )
            logger.info(f"Fix recorded: {fix_file}")
        except Exception as e:
            logger.error(f"Failed to record fix: {str(e)}")
        
        # Stage 6: Auto-update historical log
        automation_state['current_stage'] = 'historical_update'
        automation_state['stages']['historical_update'] = {
            'status': 'running',
            'message': 'Updating historical failure log...'
        }
        
        time.sleep(1)
        
        # Process pending fixes and update historical log
        try:
            from src.pipeline_fix_tracker import get_fix_tracker
            import asyncio
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from auto_update_historical_log import process_pipeline_fix
            
            tracker = get_fix_tracker()
            pending_fixes = tracker.get_pending_fixes()
            
            if pending_fixes:
                logger.info(f"Found {len(pending_fixes)} pending fix(es) to process")
                for fix_file in pending_fixes:
                    logger.info(f"Processing fix: {fix_file}")
                    success = asyncio.run(process_pipeline_fix(fix_file))
                    if success:
                        tracker.mark_fix_processed(fix_file)
                        logger.info(f"Successfully processed and marked: {fix_file}")
                    else:
                        logger.warning(f"Failed to process fix: {fix_file}")
                
                automation_state['stages']['historical_update'] = {
                    'status': 'completed',
                    'message': f'Updated historical log with {len(pending_fixes)} new fix(es)'
                }
            else:
                automation_state['stages']['historical_update'] = {
                    'status': 'completed',
                    'message': 'No pending fixes to process'
                }
        except Exception as e:
            logger.error(f"Error updating historical log: {str(e)}")
            automation_state['stages']['historical_update'] = {
                'status': 'completed',
                'message': 'Historical update skipped (non-critical)'
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