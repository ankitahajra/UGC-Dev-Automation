"""
ICA (Intelligent Code Analyzer) Client
Integrates with ICA service for root cause analysis and fix generation.
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from enum import Enum

from src.config_manager import ConfigManager
from src.utils import retry_with_backoff, format_timestamp

logger = logging.getLogger(__name__)

# Import MCP client (lazy import to avoid circular dependencies)
try:
    from src.mcp_client import MCPClientSync
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP client not available, running without context enhancement")


class FailureCategory(Enum):
    """Categories of failures that ICA can analyze."""
    CODE_ERROR = "code_error"
    CONFIGURATION_ERROR = "configuration_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    DEPENDENCY_ERROR = "dependency_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk levels for proposed fixes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ICAClient:
    """Client for interacting with the Intelligent Code Analyzer service."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize ICA client.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.ica_config = config.get_ica_config()
        
        self.api_endpoint = self.ica_config.get('api_endpoint', '')
        self.api_key = self.ica_config.get('api_key', '')
        self.timeout = self.ica_config.get('timeout_seconds', 300)
        self.analysis_depth = self.ica_config.get('analysis_depth', 'standard')
        
        # Request headers
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Analysis-Depth': self.analysis_depth
        }
        
        # Initialize MCP client if available
        self.mcp_client = None
        self.use_mcp = config.get('mcp.enabled', True) and MCP_AVAILABLE
        if self.use_mcp:
            try:
                self.mcp_client = MCPClientSync(config)
                logger.info("ICA client initialized with MCP support")
            except Exception as e:
                logger.warning(f"Failed to initialize MCP client: {str(e)}")
                self.use_mcp = False
        else:
            logger.info("ICA client initialized without MCP support")
    
    @retry_with_backoff(max_retries=3)
    def analyze_failure(self, diagnostic_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send diagnostic package to ICA for analysis.
        
        Args:
            diagnostic_package: Diagnostic data from Azure Monitor
            
        Returns:
            Analysis results from ICA
        """
        logger.info(f"Sending diagnostic package to ICA for analysis")
        
        try:
            # Prepare request payload
            payload = {
                'diagnostic_data': diagnostic_package,
                'analysis_options': {
                    'depth': self.analysis_depth,
                    'include_code_fix': True,
                    'include_iac_fix': True,
                    'include_config_fix': True
                },
                'timestamp': format_timestamp()
            }
            
            # Send request to ICA
            response = requests.post(
                f"{self.api_endpoint}/analyze",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            analysis_result = response.json()
            logger.info(f"ICA analysis completed: {analysis_result.get('status', 'unknown')}")
            
            return analysis_result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with ICA: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during ICA analysis: {str(e)}")
            raise
    
    def extract_root_cause(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract root cause information from analysis result.
        
        Args:
            analysis_result: Analysis result from ICA
            
        Returns:
            Root cause information
        """
        root_cause = analysis_result.get('root_cause', {})
        
        extracted = {
            'category': root_cause.get('category', FailureCategory.UNKNOWN.value),
            'summary': root_cause.get('summary', 'Unknown cause'),
            'details': root_cause.get('details', ''),
            'confidence': root_cause.get('confidence', 0.0),
            'affected_components': root_cause.get('affected_components', []),
            'timestamp': format_timestamp()
        }
        
        logger.info(f"Root cause extracted: {extracted['category']} (confidence: {extracted['confidence']:.2%})")
        return extracted
    
    def classify_failure(self, analysis_result: Dict[str, Any]) -> FailureCategory:
        """
        Classify the failure type.
        
        Args:
            analysis_result: Analysis result from ICA
            
        Returns:
            Failure category
        """
        category_str = analysis_result.get('root_cause', {}).get('category', 'unknown')
        
        try:
            category = FailureCategory(category_str)
        except ValueError:
            logger.warning(f"Unknown failure category: {category_str}, defaulting to UNKNOWN")
            category = FailureCategory.UNKNOWN
        
        logger.info(f"Failure classified as: {category.value}")
        return category
    
    def generate_code_fix(self, analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract code fix from analysis result.
        
        Args:
            analysis_result: Analysis result from ICA
            
        Returns:
            Code fix information or None if not applicable
        """
        code_fix = analysis_result.get('recommended_fixes', {}).get('code_fix')
        
        if not code_fix:
            logger.info("No code fix recommended by ICA")
            return None
        
        fix_info = {
            'file_path': code_fix.get('file_path', ''),
            'changes': code_fix.get('changes', []),
            'description': code_fix.get('description', ''),
            'diff': code_fix.get('diff', ''),
            'risk_level': code_fix.get('risk_level', RiskLevel.MEDIUM.value),
            'test_recommendations': code_fix.get('test_recommendations', [])
        }
        
        logger.info(f"Code fix generated for {fix_info['file_path']}")
        return fix_info
    
    def generate_iac_fix(self, analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract Infrastructure as Code fix from analysis result.
        
        Args:
            analysis_result: Analysis result from ICA
            
        Returns:
            IaC fix information or None if not applicable
        """
        iac_fix = analysis_result.get('recommended_fixes', {}).get('iac_fix')
        
        if not iac_fix:
            logger.info("No IaC fix recommended by ICA")
            return None
        
        fix_info = {
            'file_path': iac_fix.get('file_path', ''),
            'changes': iac_fix.get('changes', []),
            'description': iac_fix.get('description', ''),
            'resource_type': iac_fix.get('resource_type', ''),
            'risk_level': iac_fix.get('risk_level', RiskLevel.MEDIUM.value)
        }
        
        logger.info(f"IaC fix generated for {fix_info['resource_type']}")
        return fix_info
    
    def generate_config_fix(self, analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract configuration fix from analysis result.
        
        Args:
            analysis_result: Analysis result from ICA
            
        Returns:
            Configuration fix information or None if not applicable
        """
        config_fix = analysis_result.get('recommended_fixes', {}).get('config_fix')
        
        if not config_fix:
            logger.info("No configuration fix recommended by ICA")
            return None
        
        fix_info = {
            'config_file': config_fix.get('config_file', ''),
            'settings': config_fix.get('settings', {}),
            'description': config_fix.get('description', ''),
            'risk_level': config_fix.get('risk_level', RiskLevel.LOW.value)
        }
        
        logger.info(f"Configuration fix generated for {fix_info['config_file']}")
        return fix_info
    
    def assess_risk(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the risk of applying the recommended fixes.
        
        Args:
            analysis_result: Analysis result from ICA
            
        Returns:
            Risk assessment
        """
        risk_assessment = analysis_result.get('risk_assessment', {})
        
        assessment = {
            'overall_risk': risk_assessment.get('overall_risk', RiskLevel.MEDIUM.value),
            'impact_scope': risk_assessment.get('impact_scope', 'unknown'),
            'rollback_complexity': risk_assessment.get('rollback_complexity', 'medium'),
            'testing_required': risk_assessment.get('testing_required', True),
            'approval_required': risk_assessment.get('approval_required', True),
            'estimated_downtime': risk_assessment.get('estimated_downtime', '0 minutes'),
            'considerations': risk_assessment.get('considerations', [])
        }
        
        logger.info(f"Risk assessment: {assessment['overall_risk']} risk")
        return assessment
    
    def process_analysis(self, diagnostic_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete analysis workflow: analyze, extract, and generate fixes.
        
        Args:
            diagnostic_package: Diagnostic data
            
        Returns:
            Complete analysis package with fixes
        """
        logger.info("Starting complete ICA analysis workflow")
        
        try:
            # Perform analysis
            analysis_result = self.analyze_failure(diagnostic_package)
            
            # Check if analysis was successful
            if analysis_result.get('status') != 'success':
                logger.error(f"ICA analysis failed: {analysis_result.get('message', 'Unknown error')}")
                return {
                    'status': 'failed',
                    'message': analysis_result.get('message', 'Analysis failed'),
                    'timestamp': format_timestamp()
                }
            
            # Extract information
            root_cause = self.extract_root_cause(analysis_result)
            failure_category = self.classify_failure(analysis_result)
            risk_assessment = self.assess_risk(analysis_result)
            
            # Generate fixes
            code_fix = self.generate_code_fix(analysis_result)
            iac_fix = self.generate_iac_fix(analysis_result)
            config_fix = self.generate_config_fix(analysis_result)
            
            # Build complete package
            complete_package = {
                'status': 'success',
                'operation_id': diagnostic_package.get('operation_id', ''),
                'timestamp': format_timestamp(),
                'root_cause': root_cause,
                'failure_category': failure_category.value,
                'risk_assessment': risk_assessment,
                'fixes': {
                    'code_fix': code_fix,
                    'iac_fix': iac_fix,
                    'config_fix': config_fix
                },
                'recommendations': analysis_result.get('recommendations', []),
                'next_steps': analysis_result.get('next_steps', [])
            }
            
            logger.info("ICA analysis workflow completed successfully")
            return complete_package
            
        except Exception as e:
            logger.error(f"Error in ICA analysis workflow: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def _build_search_query(self, diagnostic_package: Dict[str, Any]) -> str:
        """
        Build semantic search query from diagnostic package.
        
        Args:
            diagnostic_package: Diagnostic data
            
        Returns:
            Search query string
        """
        error_message = diagnostic_package.get('error_message', '')
        function_name = diagnostic_package.get('function_name', '')
        error_type = diagnostic_package.get('error_type', '')
        
        query = f"""
Error Type: {error_type}
Function: {function_name}
Error Message: {error_message}

Find similar cron job failures with their resolutions.
"""
        
        return query.strip()
    
    def process_analysis_with_context(
        self,
        diagnostic_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced analysis using MCP context + ICA intelligence.
        
        Args:
            diagnostic_package: Diagnostic data
            
        Returns:
            Complete analysis package with context
        """
        logger.info("Starting context-enhanced ICA analysis")
        
        try:
            # Step 1: Find similar historical failures (if MCP enabled)
            similar_failures = []
            if self.use_mcp and self.mcp_client:
                try:
                    query = self._build_search_query(diagnostic_package)
                    similar_failures = self.mcp_client.vector_search(query, top_k=5)
                    logger.info(f"Found {len(similar_failures)} similar historical failures")
                except Exception as e:
                    logger.warning(f"MCP vector search failed, continuing without context: {str(e)}")
            
            # Step 2: Enrich diagnostic package with context
            if similar_failures:
                diagnostic_package['historical_context'] = similar_failures
                diagnostic_package['confidence_boost'] = True
                logger.info("Diagnostic package enriched with historical context")
            
            # Step 3: Perform standard ICA analysis
            analysis_result = self.process_analysis(diagnostic_package)
            
            # Step 4: Enhance confidence if similar patterns found
            if similar_failures and analysis_result.get('status') == 'success':
                root_cause = analysis_result.get('root_cause', {})
                original_confidence = root_cause.get('confidence', 0.0)
                
                # Boost confidence based on historical matches
                confidence_boost = min(0.2, len(similar_failures) * 0.04)
                enhanced_confidence = min(1.0, original_confidence + confidence_boost)
                
                root_cause['confidence'] = enhanced_confidence
                root_cause['historical_matches'] = len(similar_failures)
                root_cause['mcp_enhanced'] = True
                
                logger.info(f"Confidence boosted from {original_confidence:.2%} to {enhanced_confidence:.2%}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in context-enhanced analysis: {str(e)}")
            # Fallback to standard analysis
            return self.process_analysis(diagnostic_package)
    
    def check_health(self) -> bool:
        """
        Check if ICA service is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_endpoint}/health",
                headers=self.headers,
                timeout=10
            )
            
            is_healthy = response.status_code == 200
            logger.info(f"ICA health check: {'healthy' if is_healthy else 'unhealthy'}")
            return is_healthy
            
        except Exception as e:
            logger.error(f"ICA health check failed: {str(e)}")
            return False

# Made with Bob
