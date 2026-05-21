"""
Mock ICA Service
A simple mock service that simulates the Intelligent Code Analyzer API.
Use this for testing and demonstrations without a real ICA service.
"""

from flask import Flask, request, jsonify
import random
import time
from datetime import datetime

app = Flask(__name__)

# Sample failure patterns and fixes
FAILURE_PATTERNS = {
    'NullReferenceException': {
        'category': 'code_error',
        'summary': 'Null reference exception in data processing',
        'confidence': 0.95,
        'details': 'The variable "userData" is null when accessed in ProcessRequest method',
        'fix': {
            'file_path': 'src/DataProcessor.cs',
            'old_code': 'var result = userData.Name;',
            'new_code': 'var result = userData?.Name ?? "Unknown";',
            'description': 'Add null-conditional operator and default value'
        },
        'risk': 'low'
    },
    'TimeoutException': {
        'category': 'configuration_error',
        'summary': 'HTTP client timeout too low for external API',
        'confidence': 0.88,
        'details': 'External API calls timing out due to 5-second timeout setting',
        'fix': {
            'config_file': 'appsettings.json',
            'setting': 'HttpClient.Timeout',
            'old_value': '5',
            'new_value': '30',
            'description': 'Increase HTTP client timeout to 30 seconds'
        },
        'risk': 'low'
    },
    'OutOfMemoryException': {
        'category': 'resource_error',
        'summary': 'Memory limit exceeded during batch processing',
        'confidence': 0.82,
        'details': 'Function app memory limit (512MB) insufficient for large batch operations',
        'fix': {
            'file_path': 'infrastructure/function-app.bicep',
            'old_code': 'sku: { name: "Y1", tier: "Dynamic" }',
            'new_code': 'sku: { name: "EP1", tier: "ElasticPremium" }',
            'description': 'Upgrade to Elastic Premium plan with 3.5GB memory'
        },
        'risk': 'medium'
    },
    'DatabaseConnectionException': {
        'category': 'dependency_error',
        'summary': 'Database connection string missing environment variable',
        'confidence': 0.92,
        'details': 'Connection string references undefined environment variable DB_CONNECTION',
        'fix': {
            'config_file': 'local.settings.json',
            'setting': 'DB_CONNECTION',
            'new_value': 'Server=localhost;Database=mydb;User Id=sa;Password=***;',
            'description': 'Add missing database connection string'
        },
        'risk': 'low'
    }
}


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Mock ICA Service',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze failure and generate fixes.
    Simulates ICA analysis with realistic delays and responses.
    """
    data = request.get_json()
    
    # Simulate processing time
    time.sleep(random.uniform(1, 3))
    
    # Extract failure information
    diagnostic_data = data.get('diagnostic_data', {})
    error_message = diagnostic_data.get('error', {}).get('message', '')
    
    # Determine failure pattern
    pattern = None
    for key, value in FAILURE_PATTERNS.items():
        if key.lower() in error_message.lower():
            pattern = value
            break
    
    # Default pattern if no match
    if not pattern:
        pattern = random.choice(list(FAILURE_PATTERNS.values()))
    
    # Build analysis response
    response = {
        'status': 'success',
        'analysis_id': f'analysis-{int(time.time())}',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'root_cause': {
            'category': pattern['category'],
            'summary': pattern['summary'],
            'confidence': pattern['confidence'],
            'details': pattern['details'],
            'affected_components': ['Azure Function', 'Data Processing Module']
        },
        'recommended_fixes': {},
        'risk_assessment': {
            'overall_risk': pattern['risk'],
            'impact_scope': 'function-level',
            'rollback_complexity': 'low',
            'testing_required': True,
            'approval_required': pattern['risk'] != 'low',
            'estimated_downtime': '0 minutes',
            'considerations': [
                'Test in staging environment first',
                'Monitor error rates after deployment',
                'Have rollback plan ready'
            ]
        },
        'recommendations': [
            'Deploy fix during low-traffic period',
            'Monitor Application Insights for 24 hours',
            'Update documentation with root cause'
        ],
        'next_steps': [
            'Review and approve pull request',
            'Merge to main branch',
            'Monitor deployment',
            'Verify fix effectiveness'
        ]
    }
    
    # Add appropriate fix based on category
    if pattern['category'] == 'code_error':
        response['recommended_fixes']['code_fix'] = {
            'file_path': pattern['fix']['file_path'],
            'changes': [{
                'old': pattern['fix']['old_code'],
                'new': pattern['fix']['new_code']
            }],
            'description': pattern['fix']['description'],
            'diff': f"""--- a/{pattern['fix']['file_path']}
+++ b/{pattern['fix']['file_path']}
@@ -10,7 +10,7 @@
 public class DataProcessor
 {{
     public string ProcessRequest(UserData userData)
     {{
-        {pattern['fix']['old_code']}
+        {pattern['fix']['new_code']}
         return result;
     }}
 }}""",
            'risk_level': pattern['risk'],
            'test_recommendations': [
                'Add unit test for null userData',
                'Test with various input scenarios',
                'Verify error handling'
            ]
        }
    
    elif pattern['category'] == 'configuration_error':
        response['recommended_fixes']['config_fix'] = {
            'config_file': pattern['fix']['config_file'],
            'settings': {
                pattern['fix']['setting']: pattern['fix']['new_value']
            },
            'description': pattern['fix']['description'],
            'risk_level': pattern['risk']
        }
    
    elif pattern['category'] in ['resource_error', 'infrastructure_error']:
        response['recommended_fixes']['iac_fix'] = {
            'file_path': pattern['fix']['file_path'],
            'changes': [{
                'old': pattern['fix']['old_code'],
                'new': pattern['fix']['new_code']
            }],
            'description': pattern['fix']['description'],
            'resource_type': 'Azure Function App',
            'risk_level': pattern['risk']
        }
    
    return jsonify(response), 200


@app.route('/status/<analysis_id>', methods=['GET'])
def get_status(analysis_id):
    """Get analysis status"""
    return jsonify({
        'analysis_id': analysis_id,
        'status': 'completed',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("Mock ICA Service Starting")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /health          - Health check")
    print("  POST /analyze         - Analyze failure")
    print("  GET  /status/<id>     - Get analysis status")
    print("=" * 60)
    print("Running on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

# Made with Bob
