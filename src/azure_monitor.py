"""
Azure Monitor Integration
Handles monitoring Azure Functions and detecting failures.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.web import WebSiteManagementClient

from src.config_manager import ConfigManager
from src.utils import retry_with_backoff, format_timestamp

logger = logging.getLogger(__name__)


class AzureMonitor:
    """Monitors Azure Functions for failures and collects diagnostics."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize Azure Monitor client.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.azure_config = config.get_azure_config()
        
        # Initialize Azure credentials
        self.credential = ClientSecretCredential(
            tenant_id=self.azure_config['tenant_id'],
            client_id=self.azure_config['client_id'],
            client_secret=self.azure_config['client_secret']
        )
        
        # Initialize Azure clients
        self.logs_client = LogsQueryClient(self.credential)
        self.monitor_client = MonitorManagementClient(
            self.credential,
            self.azure_config['subscription_id']
        )
        self.web_client = WebSiteManagementClient(
            self.credential,
            self.azure_config['subscription_id']
        )
        
        logger.info("Azure Monitor initialized")
    
    @retry_with_backoff(max_retries=3)
    def check_function_health(self) -> Dict[str, Any]:
        """
        Check the health status of the Azure Function.
        
        Returns:
            Dictionary containing health status and metrics
        """
        resource_group = self.azure_config['resource_group']
        function_name = self.azure_config['function_name']
        
        try:
            # Get function app details
            function_app = self.web_client.web_apps.get(resource_group, function_name)
            
            health_status = {
                'function_name': function_name,
                'state': function_app.state,
                'enabled': function_app.enabled,
                'availability_state': function_app.availability_state,
                'last_modified': function_app.last_modified_time_utc.isoformat() if function_app.last_modified_time_utc else None,
                'timestamp': format_timestamp()
            }
            
            logger.info(f"Function health check completed: {health_status['state']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking function health: {str(e)}")
            raise
    
    @retry_with_backoff(max_retries=3)
    def query_application_insights(
        self,
        query: str,
        timespan: Optional[timedelta] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Application Insights logs.
        
        Args:
            query: KQL query string
            timespan: Time range for query (defaults to last 5 minutes)
            
        Returns:
            List of query results
        """
        if timespan is None:
            timespan = timedelta(minutes=5)
        
        workspace_id = self.config.get('application_insights.workspace_id')
        if not workspace_id:
            workspace_id = self.config.get('log_analytics.workspace_id')
        
        try:
            response = self.logs_client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=timespan
            )
            
            if response.status == LogsQueryStatus.SUCCESS:
                results = []
                for table in response.tables:
                    for row in table.rows:
                        result = dict(zip([col.name for col in table.columns], row))
                        results.append(result)
                
                logger.info(f"Application Insights query returned {len(results)} results")
                return results
            else:
                logger.error(f"Query failed with status: {response.status}")
                return []
                
        except Exception as e:
            logger.error(f"Error querying Application Insights: {str(e)}")
            raise
    
    def detect_failures(self, time_window_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Detect function failures in the specified time window.
        
        Args:
            time_window_minutes: Time window to check for failures
            
        Returns:
            List of failure events
        """
        function_name = self.azure_config['function_name']
        
        # KQL query to detect failures
        query = f"""
        requests
        | where timestamp > ago({time_window_minutes}m)
        | where cloud_RoleName == "{function_name}"
        | where success == false
        | project 
            timestamp,
            operation_Id,
            operation_Name,
            resultCode,
            duration,
            customDimensions
        | order by timestamp desc
        """
        
        try:
            failures = self.query_application_insights(
                query,
                timespan=timedelta(minutes=time_window_minutes)
            )
            
            if failures:
                logger.warning(f"Detected {len(failures)} failures in the last {time_window_minutes} minutes")
            else:
                logger.info(f"No failures detected in the last {time_window_minutes} minutes")
            
            return failures
            
        except Exception as e:
            logger.error(f"Error detecting failures: {str(e)}")
            return []
    
    def get_failure_details(self, operation_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific failure.
        
        Args:
            operation_id: Operation ID of the failed request
            
        Returns:
            Dictionary containing failure details
        """
        # Query for exceptions
        exception_query = f"""
        exceptions
        | where operation_Id == "{operation_id}"
        | project 
            timestamp,
            type,
            outerMessage,
            innermostMessage,
            details,
            problemId,
            severityLevel
        | order by timestamp desc
        | take 1
        """
        
        # Query for traces/logs
        trace_query = f"""
        traces
        | where operation_Id == "{operation_id}"
        | project 
            timestamp,
            message,
            severityLevel,
            customDimensions
        | order by timestamp desc
        | take 50
        """
        
        # Query for dependencies
        dependency_query = f"""
        dependencies
        | where operation_Id == "{operation_id}"
        | project 
            timestamp,
            name,
            type,
            target,
            data,
            resultCode,
            success,
            duration
        | order by timestamp desc
        """
        
        try:
            exceptions = self.query_application_insights(exception_query)
            traces = self.query_application_insights(trace_query)
            dependencies = self.query_application_insights(dependency_query)
            
            failure_details = {
                'operation_id': operation_id,
                'exception': exceptions[0] if exceptions else None,
                'traces': traces,
                'dependencies': dependencies,
                'timestamp': format_timestamp()
            }
            
            logger.info(f"Retrieved failure details for operation {operation_id}")
            return failure_details
            
        except Exception as e:
            logger.error(f"Error getting failure details: {str(e)}")
            return {
                'operation_id': operation_id,
                'error': str(e)
            }
    
    def get_performance_metrics(self, time_window_minutes: int = 5) -> Dict[str, Any]:
        """
        Get performance metrics for the function.
        
        Args:
            time_window_minutes: Time window for metrics
            
        Returns:
            Dictionary containing performance metrics
        """
        function_name = self.azure_config['function_name']
        
        query = f"""
        requests
        | where timestamp > ago({time_window_minutes}m)
        | where cloud_RoleName == "{function_name}"
        | summarize 
            TotalRequests = count(),
            SuccessfulRequests = countif(success == true),
            FailedRequests = countif(success == false),
            AvgDuration = avg(duration),
            P95Duration = percentile(duration, 95),
            P99Duration = percentile(duration, 99)
        """
        
        try:
            results = self.query_application_insights(
                query,
                timespan=timedelta(minutes=time_window_minutes)
            )
            
            if results:
                metrics = results[0]
                metrics['success_rate'] = (
                    metrics.get('SuccessfulRequests', 0) / metrics.get('TotalRequests', 1) * 100
                    if metrics.get('TotalRequests', 0) > 0 else 0
                )
                logger.info(f"Performance metrics retrieved: {metrics}")
                return metrics
            else:
                logger.warning("No performance metrics available")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    def create_diagnostic_package(self, operation_id: str) -> Dict[str, Any]:
        """
        Create a comprehensive diagnostic package for a failure.
        
        Args:
            operation_id: Operation ID of the failed request
            
        Returns:
            Diagnostic package with all relevant information
        """
        logger.info(f"Creating diagnostic package for operation {operation_id}")
        
        try:
            # Get failure details
            failure_details = self.get_failure_details(operation_id)
            
            # Get health status
            health_status = self.check_function_health()
            
            # Get performance metrics
            performance_metrics = self.get_performance_metrics()
            
            # Build diagnostic package
            diagnostic_package = {
                'operation_id': operation_id,
                'timestamp': format_timestamp(),
                'function_name': self.azure_config['function_name'],
                'failure_details': failure_details,
                'health_status': health_status,
                'performance_metrics': performance_metrics,
                'environment': {
                    'resource_group': self.azure_config['resource_group'],
                    'subscription_id': self.azure_config['subscription_id']
                }
            }
            
            logger.info(f"Diagnostic package created for operation {operation_id}")
            return diagnostic_package
            
        except Exception as e:
            logger.error(f"Error creating diagnostic package: {str(e)}")
            return {
                'operation_id': operation_id,
                'error': str(e),
                'timestamp': format_timestamp()
            }

# Made with Bob
