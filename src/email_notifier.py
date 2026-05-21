"""
Email Notification Module
Sends email notifications with failure details, analysis, and next steps.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.config_manager import ConfigManager
from src.utils import format_timestamp

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Handles email notifications for pipeline events."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize email notifier.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.email_config = config.get('notifications.email', {})
        
        self.enabled = self.email_config.get('enabled', False)
        self.smtp_server = self.email_config.get('smtp_server', '')
        self.smtp_port = self.email_config.get('smtp_port', 587)
        self.smtp_username = self.email_config.get('smtp_username', '')
        self.smtp_password = self.email_config.get('smtp_password', '')
        self.from_address = self.email_config.get('from_address', 'autofix@example.com')
        self.to_addresses = self.email_config.get('to_addresses', [])
        
        if self.enabled:
            logger.info(f"Email notifier initialized (recipients: {len(self.to_addresses)})")
        else:
            logger.info("Email notifications disabled")
    
    def send_email(self, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email notification.
        
        Args:
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.info("Email notifications disabled, skipping")
            return False
        
        if not self.to_addresses:
            logger.warning("No recipient addresses configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_address
            msg['To'] = ', '.join(self.to_addresses)
            
            # Attach plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(self.to_addresses)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_failure_notification(self, failure_details: Dict[str, Any]) -> bool:
        """
        Send notification about function failure.
        
        Args:
            failure_details: Failure information
            
        Returns:
            True if successful, False otherwise
        """
        function_name = failure_details.get('function_name', 'Unknown')
        invocation_id = failure_details.get('operation_id', 'Unknown')
        exception_message = failure_details.get('error', {}).get('message', 'Unknown error')
        timestamp = failure_details.get('timestamp', format_timestamp())
        
        subject = f"🚨 Azure Function Failure: {function_name}"
        
        body = f"""Azure Function Failure Detected

Function Name: {function_name}
Invocation ID: {invocation_id}
Timestamp: {timestamp}

Exception Message:
{exception_message}

The automated diagnosis and fix pipeline has been triggered.
You will receive another notification once the analysis is complete.

---
Azure Function Auto-Diagnose and Auto-Fix Pipeline
"""
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #d32f2f; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f5f5f5; margin: 20px 0; border-radius: 5px; }}
        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }}
        .error-box {{ background-color: #ffebee; padding: 15px; margin: 10px 0; border-left: 4px solid #d32f2f; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
        strong {{ color: #1976D2; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 Azure Function Failure Detected</h2>
    </div>
    
    <div class="content">
        <div class="info-box">
            <p><strong>Function Name:</strong> {function_name}</p>
            <p><strong>Invocation ID:</strong> {invocation_id}</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
        </div>
        
        <div class="error-box">
            <h3>Exception Message:</h3>
            <pre>{exception_message}</pre>
        </div>
        
        <p>The automated diagnosis and fix pipeline has been triggered.</p>
        <p>You will receive another notification once the analysis is complete.</p>
    </div>
    
    <div class="footer">
        <p>Azure Function Auto-Diagnose and Auto-Fix Pipeline</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(subject, body, html_body)
    
    def send_analysis_complete_notification(
        self,
        failure_details: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> bool:
        """
        Send notification with analysis results and recommended fixes.
        
        Args:
            failure_details: Failure information
            analysis_result: Analysis results from ICA
            
        Returns:
            True if successful, False otherwise
        """
        function_name = failure_details.get('function_name', 'Unknown')
        invocation_id = failure_details.get('operation_id', 'Unknown')
        
        root_cause = analysis_result.get('root_cause', {})
        root_cause_summary = root_cause.get('summary', 'Unknown')
        root_cause_category = root_cause.get('category', 'unknown')
        confidence = root_cause.get('confidence', 0)
        
        fixes = analysis_result.get('fixes', {})
        risk_assessment = analysis_result.get('risk_assessment', {})
        next_steps = analysis_result.get('next_steps', [])
        
        subject = f"✅ Analysis Complete: {function_name}"
        
        # Build fix summary
        fix_types = []
        if fixes.get('code_fix'):
            fix_types.append('Code Fix')
        if fixes.get('iac_fix'):
            fix_types.append('Infrastructure Fix')
        if fixes.get('config_fix'):
            fix_types.append('Configuration Fix')
        
        fix_summary = ', '.join(fix_types) if fix_types else 'No automated fix available'
        
        body = f"""Analysis Complete for Azure Function Failure

Function Name: {function_name}
Invocation ID: {invocation_id}

ROOT CAUSE ANALYSIS
-------------------
Category: {root_cause_category}
Summary: {root_cause_summary}
Confidence: {confidence:.1%}

RECOMMENDED FIXES
-----------------
{fix_summary}

RISK ASSESSMENT
---------------
Overall Risk: {risk_assessment.get('overall_risk', 'medium')}
Impact Scope: {risk_assessment.get('impact_scope', 'unknown')}
Testing Required: {'Yes' if risk_assessment.get('testing_required', True) else 'No'}
Approval Required: {'Yes' if risk_assessment.get('approval_required', True) else 'No'}

NEXT STEPS
----------
"""
        
        for i, step in enumerate(next_steps, 1):
            body += f"{i}. {step}\n"
        
        body += """
---
A pull request with the automated fix will be created shortly.
You will receive a notification when it's ready for review.

Azure Function Auto-Diagnose and Auto-Fix Pipeline
"""
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .section {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .section h3 {{ color: #1976D2; margin-top: 0; }}
        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }}
        .success-box {{ background-color: #e8f5e9; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .warning-box {{ background-color: #fff3e0; padding: 15px; margin: 10px 0; border-left: 4px solid #FF9800; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
        strong {{ color: #1976D2; }}
        .confidence {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>✅ Analysis Complete</h2>
    </div>
    
    <div class="content">
        <div class="info-box">
            <p><strong>Function Name:</strong> {function_name}</p>
            <p><strong>Invocation ID:</strong> {invocation_id}</p>
        </div>
        
        <div class="section">
            <h3>🔍 Root Cause Analysis</h3>
            <p><strong>Category:</strong> {root_cause_category}</p>
            <p><strong>Summary:</strong> {root_cause_summary}</p>
            <p><strong>Confidence:</strong> <span class="confidence">{confidence:.1%}</span></p>
        </div>
        
        <div class="section">
            <h3>🔧 Recommended Fixes</h3>
            <div class="success-box">
                <p><strong>{fix_summary}</strong></p>
            </div>
        </div>
        
        <div class="section">
            <h3>⚠️ Risk Assessment</h3>
            <p><strong>Overall Risk:</strong> {risk_assessment.get('overall_risk', 'medium').upper()}</p>
            <p><strong>Impact Scope:</strong> {risk_assessment.get('impact_scope', 'unknown')}</p>
            <p><strong>Testing Required:</strong> {'Yes' if risk_assessment.get('testing_required', True) else 'No'}</p>
            <p><strong>Approval Required:</strong> {'Yes' if risk_assessment.get('approval_required', True) else 'No'}</p>
        </div>
        
        <div class="section">
            <h3>📋 Next Steps</h3>
            <ul>
"""
        
        for step in next_steps:
            html_body += f"                <li>{step}</li>\n"
        
        html_body += """
            </ul>
        </div>
        
        <div class="warning-box">
            <p><strong>Action Required:</strong> A pull request with the automated fix will be created shortly. You will receive a notification when it's ready for review.</p>
        </div>
    </div>
    
    <div class="footer">
        <p>Azure Function Auto-Diagnose and Auto-Fix Pipeline</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(subject, body, html_body)
    
    def send_pr_created_notification(
        self,
        failure_details: Dict[str, Any],
        pr_url: str,
        branch_name: str,
        fixes_applied: List[str]
    ) -> bool:
        """
        Send notification when pull request is created.
        
        Args:
            failure_details: Failure information
            pr_url: Pull request URL
            branch_name: Branch name
            fixes_applied: List of fix types applied
            
        Returns:
            True if successful, False otherwise
        """
        function_name = failure_details.get('function_name', 'Unknown')
        
        subject = f"🔀 Pull Request Created: {function_name}"
        
        fixes_list = ', '.join(fixes_applied).title()
        
        body = f"""Pull Request Created with Automated Fix

Function Name: {function_name}
Branch: {branch_name}
Fixes Applied: {fixes_list}

Pull Request URL:
{pr_url}

Please review the changes and approve the pull request to deploy the fix.

---
Azure Function Auto-Diagnose and Auto-Fix Pipeline
"""
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .info-box {{ background-color: #e3f2fd; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }}
        .action-box {{ background-color: #fff3e0; padding: 20px; margin: 20px 0; border-radius: 5px; text-align: center; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
        strong {{ color: #1976D2; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🔀 Pull Request Created</h2>
    </div>
    
    <div class="content">
        <div class="info-box">
            <p><strong>Function Name:</strong> {function_name}</p>
            <p><strong>Branch:</strong> {branch_name}</p>
            <p><strong>Fixes Applied:</strong> {fixes_list}</p>
        </div>
        
        <div class="action-box">
            <h3>Action Required: Review Pull Request</h3>
            <p>Please review the automated changes and approve the pull request to deploy the fix.</p>
            <a href="{pr_url}" class="button">View Pull Request</a>
        </div>
    </div>
    
    <div class="footer">
        <p>Azure Function Auto-Diagnose and Auto-Fix Pipeline</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(subject, body, html_body)
    
    def send_rollback_notification(
        self,
        failure_details: Dict[str, Any],
        reason: str
    ) -> bool:
        """
        Send notification when rollback is triggered.
        
        Args:
            failure_details: Failure information
            reason: Reason for rollback
            
        Returns:
            True if successful, False otherwise
        """
        function_name = failure_details.get('function_name', 'Unknown')
        
        subject = f"⚠️ Rollback Triggered: {function_name}"
        
        body = f"""Automatic Rollback Triggered

Function Name: {function_name}
Reason: {reason}
Timestamp: {format_timestamp()}

The deployment has been automatically rolled back to the previous successful version.

Please investigate the issue and review the logs for more details.

---
Azure Function Auto-Diagnose and Auto-Fix Pipeline
"""
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #FF9800; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .warning-box {{ background-color: #fff3e0; padding: 15px; margin: 10px 0; border-left: 4px solid #FF9800; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
        strong {{ color: #F57C00; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>⚠️ Automatic Rollback Triggered</h2>
    </div>
    
    <div class="content">
        <div class="warning-box">
            <p><strong>Function Name:</strong> {function_name}</p>
            <p><strong>Reason:</strong> {reason}</p>
            <p><strong>Timestamp:</strong> {format_timestamp()}</p>
        </div>
        
        <p>The deployment has been automatically rolled back to the previous successful version.</p>
        <p><strong>Action Required:</strong> Please investigate the issue and review the logs for more details.</p>
    </div>
    
    <div class="footer">
        <p>Azure Function Auto-Diagnose and Auto-Fix Pipeline</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(subject, body, html_body)


# Made with Bob