"""
Pipeline Orchestrator
Main orchestrator that coordinates all components of the auto-fix pipeline.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from src.config_manager import ConfigManager
from src.azure_monitor import AzureMonitor
from src.diagnostics_webhook import DiagnosticsWebhook
from src.ica_client import ICAClient
from src.bob_automation import BOBAutomation
from src.email_notifier import EmailNotifier
from src.utils import format_timestamp, format_duration, calculate_time_difference

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline execution stages."""
    MONITORING = "monitoring"
    DIAGNOSTICS = "diagnostics"
    ANALYSIS = "analysis"
    FIX_GENERATION = "fix_generation"
    AUTOMATION = "automation"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineOrchestrator:
    """Orchestrates the complete auto-diagnose and auto-fix pipeline."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize pipeline orchestrator.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        
        # Initialize components
        logger.info("Initializing pipeline components...")
        
        self.azure_monitor = AzureMonitor(config)
        self.ica_client = ICAClient(config)
        self.bob_automation = BOBAutomation(config)
        self.diagnostics_webhook = DiagnosticsWebhook(config, self.azure_monitor)
        self.email_notifier = EmailNotifier(config)
        
        # Pipeline state
        self.current_stage = PipelineStage.MONITORING
        self.execution_history = []
        
        logger.info("Pipeline orchestrator initialized successfully")
    
    def execute_pipeline(self, operation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the complete pipeline for a failure.
        
        Args:
            operation_id: Optional operation ID to process specific failure
            
        Returns:
            Pipeline execution result
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting pipeline execution at {format_timestamp()}")
        
        execution_result = {
            'pipeline_id': f"pipeline-{int(time.time())}",
            'start_time': format_timestamp(start_time),
            'stages': {},
            'status': 'in_progress'
        }
        
        try:
            # Stage 1: Monitoring and Detection
            self.current_stage = PipelineStage.MONITORING
            monitoring_result = self._execute_monitoring_stage(operation_id)
            execution_result['stages']['monitoring'] = monitoring_result
            
            if monitoring_result['status'] != 'success':
                raise Exception(f"Monitoring stage failed: {monitoring_result.get('message', 'Unknown error')}")
            
            # Stage 2: Diagnostics Collection
            self.current_stage = PipelineStage.DIAGNOSTICS
            diagnostics_result = self._execute_diagnostics_stage(monitoring_result)
            execution_result['stages']['diagnostics'] = diagnostics_result
            
            if diagnostics_result['status'] != 'success':
                raise Exception(f"Diagnostics stage failed: {diagnostics_result.get('message', 'Unknown error')}")
            
            # Send failure notification email
            diagnostic_package = diagnostics_result.get('diagnostic_package', {})
            if diagnostic_package:
                logger.info("Sending failure notification email")
                self.email_notifier.send_failure_notification(diagnostic_package)
            
            # Stage 3: ICA Analysis
            self.current_stage = PipelineStage.ANALYSIS
            analysis_result = self._execute_analysis_stage(diagnostics_result)
            execution_result['stages']['analysis'] = analysis_result
            
            if analysis_result['status'] != 'success':
                raise Exception(f"Analysis stage failed: {analysis_result.get('message', 'Unknown error')}")
            
            # Send analysis complete notification email
            analysis_package = analysis_result.get('analysis_package', {})
            if analysis_package and diagnostic_package:
                logger.info("Sending analysis complete notification email")
                self.email_notifier.send_analysis_complete_notification(
                    diagnostic_package,
                    analysis_package
                )
            
            # Stage 4: BOB Automation
            self.current_stage = PipelineStage.AUTOMATION
            automation_result = self._execute_automation_stage(analysis_result)
            execution_result['stages']['automation'] = automation_result
            
            if automation_result['status'] != 'success':
                raise Exception(f"Automation stage failed: {automation_result.get('message', 'Unknown error')}")
            
            # Send PR created notification email
            bob_result = automation_result.get('automation_result', {})
            pr_url = bob_result.get('pr_url')
            if pr_url and diagnostic_package:
                logger.info("Sending PR created notification email")
                self.email_notifier.send_pr_created_notification(
                    diagnostic_package,
                    pr_url,
                    bob_result.get('branch_name', ''),
                    bob_result.get('fixes_applied', [])
                )
            
            # Stage 5: Post-Deployment Validation (if auto-merge enabled)
            if self.config.get('bob.auto_merge_on_approval', True):
                self.current_stage = PipelineStage.VALIDATION
                validation_result = self._execute_validation_stage(automation_result)
                execution_result['stages']['validation'] = validation_result
            
            # Pipeline completed successfully
            self.current_stage = PipelineStage.COMPLETED
            execution_result['status'] = 'success'
            execution_result['message'] = 'Pipeline executed successfully'
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            self.current_stage = PipelineStage.FAILED
            execution_result['status'] = 'failed'
            execution_result['error'] = str(e)
            
            # Send rollback notification if diagnostics stage was reached
            stages = execution_result.get('stages', {})
            if isinstance(stages, dict) and 'diagnostics' in stages:
                diagnostics_stage = stages.get('diagnostics', {})
                if isinstance(diagnostics_stage, dict):
                    diagnostic_package = diagnostics_stage.get('diagnostic_package', {})
                    if diagnostic_package:
                        logger.info("Sending rollback notification email")
                        self.email_notifier.send_rollback_notification(
                            diagnostic_package,
                            str(e)
                        )
        
        finally:
            # Calculate execution time
            end_time = datetime.utcnow()
            duration = calculate_time_difference(start_time, end_time)
            execution_result['end_time'] = format_timestamp(end_time)
            execution_result['duration'] = format_duration(duration)
            execution_result['final_stage'] = self.current_stage.value
            
            # Store in execution history
            self.execution_history.append(execution_result)
            
            logger.info(f"Pipeline execution completed with status: {execution_result['status']}")
        
        return execution_result
    
    def _execute_monitoring_stage(self, operation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute monitoring stage to detect failures.
        
        Args:
            operation_id: Optional specific operation ID to process
            
        Returns:
            Stage result
        """
        logger.info("Executing monitoring stage...")
        
        try:
            if operation_id:
                # Process specific operation
                logger.info(f"Processing specific operation: {operation_id}")
                return {
                    'status': 'success',
                    'operation_id': operation_id,
                    'timestamp': format_timestamp()
                }
            else:
                # Detect failures
                failures = self.azure_monitor.detect_failures(
                    time_window_minutes=self.config.get('monitoring.alert_window_minutes', 5)
                )
                
                if not failures:
                    return {
                        'status': 'success',
                        'message': 'No failures detected',
                        'failures_count': 0,
                        'timestamp': format_timestamp()
                    }
                
                # Process the most recent failure
                latest_failure = failures[0]
                operation_id = latest_failure.get('operation_Id', '')
                
                logger.info(f"Detected {len(failures)} failures, processing operation {operation_id}")
                
                return {
                    'status': 'success',
                    'operation_id': operation_id,
                    'failures_count': len(failures),
                    'failure_details': latest_failure,
                    'timestamp': format_timestamp()
                }
                
        except Exception as e:
            logger.error(f"Monitoring stage failed: {str(e)}")
            return {
                'status': 'failed',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def _execute_diagnostics_stage(self, monitoring_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute diagnostics stage to collect detailed information.
        
        Args:
            monitoring_result: Result from monitoring stage
            
        Returns:
            Stage result
        """
        logger.info("Executing diagnostics stage...")
        
        try:
            operation_id = monitoring_result.get('operation_id', '')
            
            if not operation_id:
                raise ValueError("No operation ID provided from monitoring stage")
            
            # Create diagnostic package
            diagnostic_package = self.azure_monitor.create_diagnostic_package(operation_id)
            
            logger.info(f"Diagnostic package created for operation {operation_id}")
            
            return {
                'status': 'success',
                'operation_id': operation_id,
                'diagnostic_package': diagnostic_package,
                'timestamp': format_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Diagnostics stage failed: {str(e)}")
            return {
                'status': 'failed',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def _execute_analysis_stage(self, diagnostics_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute analysis stage using ICA.
        
        Args:
            diagnostics_result: Result from diagnostics stage
            
        Returns:
            Stage result
        """
        logger.info("Executing analysis stage...")
        
        try:
            diagnostic_package = diagnostics_result.get('diagnostic_package', {})
            
            if not diagnostic_package:
                raise ValueError("No diagnostic package provided from diagnostics stage")
            
            # Process analysis with ICA
            analysis_package = self.ica_client.process_analysis(diagnostic_package)
            
            if analysis_package.get('status') != 'success':
                raise Exception(f"ICA analysis failed: {analysis_package.get('message', 'Unknown error')}")
            
            logger.info(f"Analysis completed for operation {analysis_package.get('operation_id', '')}")
            
            return {
                'status': 'success',
                'analysis_package': analysis_package,
                'timestamp': format_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Analysis stage failed: {str(e)}")
            return {
                'status': 'failed',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def _execute_automation_stage(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute automation stage using BOB.
        
        Args:
            analysis_result: Result from analysis stage
            
        Returns:
            Stage result
        """
        logger.info("Executing automation stage...")
        
        try:
            analysis_package = analysis_result.get('analysis_package', {})
            
            if not analysis_package:
                raise ValueError("No analysis package provided from analysis stage")
            
            operation_id = analysis_package.get('operation_id', '')
            
            # Check risk level
            risk_assessment = analysis_package.get('risk_assessment', {})
            overall_risk = risk_assessment.get('overall_risk', 'medium')
            
            # Check if approval is required based on risk
            require_approval = self.config.get('bob.require_approval', True)
            low_risk_threshold = self.config.get('extensibility.low_risk_threshold', 0.3)
            no_approval_for_low_risk = self.config.get('extensibility.no_approval_for_low_risk', False)
            
            if no_approval_for_low_risk and overall_risk == 'low':
                logger.info("Low risk fix detected, proceeding without approval requirement")
                require_approval = False
            
            # Apply patches and create PR
            automation_result = self.bob_automation.apply_patches(analysis_package, operation_id)
            
            if automation_result.get('status') != 'success':
                raise Exception(f"BOB automation failed: {automation_result.get('message', 'Unknown error')}")
            
            automation_result['requires_approval'] = require_approval
            automation_result['risk_level'] = overall_risk
            
            logger.info(f"Automation completed, PR created: {automation_result.get('pr_url', 'N/A')}")
            
            return {
                'status': 'success',
                'automation_result': automation_result,
                'timestamp': format_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Automation stage failed: {str(e)}")
            return {
                'status': 'failed',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def _execute_validation_stage(self, automation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute post-deployment validation stage.
        
        Args:
            automation_result: Result from automation stage
            
        Returns:
            Stage result
        """
        logger.info("Executing validation stage...")
        
        try:
            # Wait for deployment to complete
            wait_time = self.config.get('validation.wait_time_seconds', 300)
            logger.info(f"Waiting {wait_time} seconds for deployment to stabilize...")
            time.sleep(wait_time)
            
            # Check function health
            health_status = self.azure_monitor.check_function_health()
            
            # Check for new failures
            failures = self.azure_monitor.detect_failures(time_window_minutes=5)
            
            is_healthy = (
                health_status.get('state') == 'Running' and
                len(failures) == 0
            )
            
            if is_healthy:
                logger.info("Validation successful: Function is healthy")
                return {
                    'status': 'success',
                    'message': 'Function is healthy after deployment',
                    'health_status': health_status,
                    'failures_detected': 0,
                    'timestamp': format_timestamp()
                }
            else:
                logger.warning("Validation failed: Issues detected after deployment")
                return {
                    'status': 'failed',
                    'message': 'Issues detected after deployment',
                    'health_status': health_status,
                    'failures_detected': len(failures),
                    'timestamp': format_timestamp()
                }
                
        except Exception as e:
            logger.error(f"Validation stage failed: {str(e)}")
            return {
                'status': 'failed',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def monitor_continuously(self, check_interval_seconds: int = 60) -> None:
        """
        Continuously monitor for failures and trigger pipeline.
        
        Args:
            check_interval_seconds: Interval between checks
        """
        logger.info(f"Starting continuous monitoring (interval: {check_interval_seconds}s)")
        
        while True:
            try:
                # Check for failures
                failures = self.azure_monitor.detect_failures(
                    time_window_minutes=self.config.get('monitoring.alert_window_minutes', 5)
                )
                
                if failures:
                    logger.info(f"Detected {len(failures)} failures, triggering pipeline")
                    
                    # Execute pipeline for the most recent failure
                    result = self.execute_pipeline()
                    
                    logger.info(f"Pipeline execution completed: {result['status']}")
                
                # Wait before next check
                time.sleep(check_interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Continuous monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                time.sleep(check_interval_seconds)
    
    def get_execution_history(self, limit: int = 10) -> list:
        """
        Get recent pipeline execution history.
        
        Args:
            limit: Maximum number of executions to return
            
        Returns:
            List of execution results
        """
        return self.execution_history[-limit:]
    
    def get_current_stage(self) -> str:
        """
        Get current pipeline stage.
        
        Returns:
            Current stage name
        """
        return self.current_stage.value

# Made with Bob
