"""
Diagnostics Webhook
HTTP endpoint for receiving and processing failure alerts.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.config_manager import ConfigManager
from src.azure_monitor import AzureMonitor
from src.utils import format_timestamp, validate_required_fields

logger = logging.getLogger(__name__)


class DiagnosticsWebhook:
    """Webhook server for receiving and processing diagnostics data."""
    
    def __init__(self, config: ConfigManager, azure_monitor: AzureMonitor):
        """
        Initialize diagnostics webhook.
        
        Args:
            config: Configuration manager instance
            azure_monitor: Azure monitor instance
        """
        self.config = config
        self.azure_monitor = azure_monitor
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Register routes
        self._register_routes()
        
        logger.info("Diagnostics webhook initialized")
    
    def _register_routes(self) -> None:
        """Register Flask routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': format_timestamp(),
                'service': 'diagnostics-webhook'
            }), 200
        
        @self.app.route('/diagnostics', methods=['POST'])
        def receive_diagnostics():
            """Receive diagnostics data from Event Grid or Logic App."""
            try:
                payload = request.get_json()
                
                if not payload:
                    return jsonify({'error': 'No payload provided'}), 400
                
                # Process the diagnostics payload
                result = self.process_diagnostics(payload)
                
                return jsonify(result), 200
                
            except Exception as e:
                logger.error(f"Error processing diagnostics: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/alert', methods=['POST'])
        def receive_alert():
            """Receive alert from Azure Monitor."""
            try:
                alert_data = request.get_json()
                
                if not alert_data:
                    return jsonify({'error': 'No alert data provided'}), 400
                
                # Process the alert
                result = self.process_alert(alert_data)
                
                return jsonify(result), 200
                
            except Exception as e:
                logger.error(f"Error processing alert: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    def normalize_logs(self, logs: list) -> list:
        """
        Normalize log entries to a standard format.
        
        Args:
            logs: List of log entries
            
        Returns:
            Normalized log entries
        """
        normalized = []
        
        for log in logs:
            normalized_log = {
                'timestamp': log.get('timestamp', format_timestamp()),
                'level': log.get('level', log.get('severityLevel', 'INFO')),
                'message': log.get('message', ''),
                'source': log.get('source', 'unknown'),
                'operation_id': log.get('operation_id', log.get('operation_Id', '')),
                'custom_dimensions': log.get('customDimensions', {})
            }
            normalized.append(normalized_log)
        
        logger.debug(f"Normalized {len(logs)} log entries")
        return normalized
    
    def aggregate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate and summarize metrics.
        
        Args:
            metrics: Raw metrics data
            
        Returns:
            Aggregated metrics
        """
        aggregated = {
            'cpu_usage': metrics.get('cpuUsage', 0),
            'memory_usage': metrics.get('memoryUsage', 0),
            'request_count': metrics.get('requestCount', 0),
            'error_count': metrics.get('errorCount', 0),
            'avg_response_time': metrics.get('avgResponseTime', 0),
            'timestamp': format_timestamp()
        }
        
        # Calculate error rate
        if aggregated['request_count'] > 0:
            aggregated['error_rate'] = (
                aggregated['error_count'] / aggregated['request_count'] * 100
            )
        else:
            aggregated['error_rate'] = 0
        
        logger.debug(f"Aggregated metrics: error_rate={aggregated['error_rate']:.2f}%")
        return aggregated
    
    def generate_diagnostic_package(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic package from payload.
        
        Args:
            payload: Input payload from alert
            
        Returns:
            Diagnostic package
        """
        logger.info("Generating diagnostic package")
        
        # Extract key information
        function_name = payload.get('functionName', self.config.get('azure.function_name'))
        operation_id = payload.get('invocationId', payload.get('operation_id', ''))
        exception_message = payload.get('exceptionMessage', '')
        stack_trace = payload.get('stackTrace', '')
        
        # Get additional diagnostics from Azure Monitor
        if operation_id:
            failure_details = self.azure_monitor.get_failure_details(operation_id)
        else:
            failure_details = {}
        
        # Normalize logs
        logs = payload.get('logsLast5Min', [])
        normalized_logs = self.normalize_logs(logs) if logs else []
        
        # Aggregate metrics
        metrics = {
            'cpuUsage': payload.get('cpuUsage', 0),
            'memoryUsage': payload.get('memoryUsage', 0)
        }
        aggregated_metrics = self.aggregate_metrics(metrics)
        
        # Build diagnostic package
        diagnostic_package = {
            'function_name': function_name,
            'operation_id': operation_id,
            'timestamp': payload.get('timestamp', format_timestamp()),
            'correlation_id': payload.get('correlationId', ''),
            'deployment_version': payload.get('deploymentVersion', 'unknown'),
            'error': {
                'message': exception_message,
                'stack_trace': stack_trace,
                'type': payload.get('errorType', 'unknown')
            },
            'logs': normalized_logs,
            'metrics': aggregated_metrics,
            'failure_details': failure_details,
            'context': {
                'source': payload.get('source', 'event-grid'),
                'alert_rule': payload.get('alertRule', ''),
                'severity': payload.get('severity', 'medium')
            }
        }
        
        logger.info(f"Diagnostic package generated for {function_name}")
        return diagnostic_package
    
    def process_diagnostics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process diagnostics payload.
        
        Args:
            payload: Diagnostics payload
            
        Returns:
            Processing result
        """
        logger.info("Processing diagnostics payload")
        
        try:
            # Validate required fields
            required_fields = ['functionName']
            is_valid, missing_fields = validate_required_fields(payload, required_fields)
            
            if not is_valid:
                logger.warning(f"Missing required fields: {missing_fields}")
                return {
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }
            
            # Generate diagnostic package
            diagnostic_package = self.generate_diagnostic_package(payload)
            
            # Store diagnostic package for ICA processing
            # This would typically be sent to a queue or storage
            logger.info(f"Diagnostic package ready for ICA: {diagnostic_package['operation_id']}")
            
            return {
                'status': 'success',
                'message': 'Diagnostics processed successfully',
                'operation_id': diagnostic_package['operation_id'],
                'timestamp': format_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error processing diagnostics: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def process_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process alert from Azure Monitor.
        
        Args:
            alert_data: Alert data
            
        Returns:
            Processing result
        """
        logger.info("Processing Azure Monitor alert")
        
        try:
            # Extract alert information
            alert_context = alert_data.get('data', {}).get('context', {})
            condition = alert_context.get('condition', {})
            
            # Check if this is a function failure alert
            metric_name = condition.get('allOf', [{}])[0].get('metricName', '')
            
            if 'failure' in metric_name.lower() or 'error' in metric_name.lower():
                # Detect recent failures
                failures = self.azure_monitor.detect_failures(time_window_minutes=5)
                
                if failures:
                    # Process the most recent failure
                    latest_failure = failures[0]
                    operation_id = latest_failure.get('operation_Id', '')
                    
                    # Create diagnostic package
                    diagnostic_package = self.azure_monitor.create_diagnostic_package(operation_id)
                    
                    logger.info(f"Alert processed, diagnostic package created for {operation_id}")
                    
                    return {
                        'status': 'success',
                        'message': 'Alert processed and diagnostic package created',
                        'operation_id': operation_id,
                        'failures_detected': len(failures),
                        'timestamp': format_timestamp()
                    }
                else:
                    logger.info("Alert received but no failures detected")
                    return {
                        'status': 'success',
                        'message': 'Alert received but no failures detected',
                        'timestamp': format_timestamp()
                    }
            else:
                logger.info(f"Alert for non-failure metric: {metric_name}")
                return {
                    'status': 'success',
                    'message': f'Alert received for metric: {metric_name}',
                    'timestamp': format_timestamp()
                }
                
        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def run(self, host: str = '0.0.0.0', port: int = 8080) -> None:
        """
        Run the webhook server.
        
        Args:
            host: Host address
            port: Port number
        """
        logger.info(f"Starting diagnostics webhook on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

# Made with Bob
