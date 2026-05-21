"""
Cron Job Dashboard
Web interface for running mock cron jobs and viewing automated fixes.
"""

from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime
import json

from mock_cron_jobs import CronJobManager
from cron_job_fixer import CronJobFixer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize managers
job_manager = CronJobManager()
job_fixer = CronJobFixer()


@app.route('/')
def index():
    """Render main dashboard page."""
    return render_template('cron_dashboard.html')


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """
    List all available cron jobs.
    
    Returns:
        JSON list of jobs
    """
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


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Get details of a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JSON job details
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({
                'status': 'error',
                'message': f'Job {job_id} not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'job': {
                'job_id': job.job_id,
                'name': job.name,
                'description': job.description,
                'status': job.status.value,
                'last_execution': job.last_execution_time,
                'last_error': job.last_error
            }
        })
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/execute', methods=['POST'])
def execute_job(job_id):
    """
    Execute a specific cron job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JSON execution result
    """
    try:
        logger.info(f"Executing job: {job_id}")
        result = job_manager.execute_job(job_id)
        
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


@app.route('/api/jobs/<job_id>/fix', methods=['POST'])
def fix_job(job_id):
    """
    Analyze and fix a failed job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JSON fix analysis and recommendations
    """
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
        
        logger.info(f"Analyzing and fixing job: {job_id}")
        fix_result = job_fixer.analyze_and_fix(job_result)
        
        return jsonify({
            'status': 'success',
            'fix_analysis': fix_result,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fixing job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/history', methods=['GET'])
def get_job_history(job_id):
    """
    Get execution history for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JSON execution history
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        history = job_manager.get_job_history(job_id, limit)
        
        return jsonify({
            'status': 'success',
            'job_id': job_id,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Error getting history for job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/fixes/history', methods=['GET'])
def get_fix_history():
    """
    Get fix history.
    
    Returns:
        JSON fix history
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        history = job_fixer.get_fix_history(limit)
        
        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Error getting fix history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Cron Job Dashboard'
    })


def run_dashboard(host='0.0.0.0', port=5001, debug=False):
    """
    Run the dashboard server.
    
    Args:
        host: Host address
        port: Port number
        debug: Debug mode
    """
    logger.info(f"Starting Cron Job Dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_dashboard(debug=True)


# Made with Bob