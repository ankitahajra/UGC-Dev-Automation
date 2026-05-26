"""
Pipeline Fix Tracker
Automatically tracks when a fix is applied and deployed in the pipeline.
This module integrates with the pipeline to capture fix details and trigger
the historical log update.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

PIPELINE_FIXES_DIR = Path('pipeline_fixes')


class PipelineFixTracker:
    """Tracks pipeline fixes and prepares them for historical log updates."""
    
    def __init__(self):
        """Initialize the fix tracker."""
        # Ensure the pipeline_fixes directory exists
        PIPELINE_FIXES_DIR.mkdir(exist_ok=True)
        logger.info("Pipeline Fix Tracker initialized")
    
    def record_fix(
        self,
        job_name: str,
        error_type: str,
        error_message: str,
        stack_trace: str,
        resolution: str,
        fix_description: str,
        category: str = "Unknown",
        severity: str = "medium",
        deployment_id: Optional[str] = None,
        **additional_metadata
    ) -> Path:
        """
        Record a fix that was applied and deployed.
        
        Args:
            job_name: Name of the job that failed
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace or error details
            resolution: How the issue was resolved
            fix_description: Brief description of the fix
            category: Error category
            severity: Severity level
            deployment_id: Optional deployment identifier
            **additional_metadata: Any additional metadata
            
        Returns:
            Path to the created fix log file
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create fix record
        fix_record = {
            "job_name": job_name,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "resolution": resolution,
            "fix_description": fix_description,
            "category": category,
            "severity": severity,
            "timestamp": timestamp,
            "deployment_id": deployment_id or f"deploy-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "metadata": additional_metadata
        }
        
        # Generate filename
        safe_job_name = job_name.replace(' ', '_').replace('/', '_')
        filename = f"fix_{safe_job_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        fix_file = PIPELINE_FIXES_DIR / filename
        
        # Save to file
        try:
            with open(fix_file, 'w', encoding='utf-8') as f:
                json.dump(fix_record, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Fix recorded: {fix_file}")
            return fix_file
            
        except Exception as e:
            logger.error(f"✗ Failed to record fix: {str(e)}")
            raise
    
    def get_pending_fixes(self) -> List[Path]:
        """
        Get all pending fix logs that haven't been processed yet.
        
        Returns:
            List of fix log file paths (excludes .processed.json files)
        """
        if not PIPELINE_FIXES_DIR.exists():
            return []
        
        # Get all fix_*.json files but exclude .processed.json files
        all_fixes = list(PIPELINE_FIXES_DIR.glob('fix_*.json'))
        pending_fixes = [f for f in all_fixes if not f.name.endswith('.processed.json')]
        
        return pending_fixes
    
    def mark_fix_processed(self, fix_file: Path) -> bool:
        """
        Mark a fix as processed by renaming it.
        
        Args:
            fix_file: Path to the fix log file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            processed_file = fix_file.with_suffix('.processed.json')
            fix_file.rename(processed_file)
            logger.info(f"✓ Marked fix as processed: {processed_file}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to mark fix as processed: {str(e)}")
            return False


# Global instance
_tracker_instance = None


def get_fix_tracker() -> PipelineFixTracker:
    """Get the global fix tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PipelineFixTracker()
    return _tracker_instance


# Made with Bob