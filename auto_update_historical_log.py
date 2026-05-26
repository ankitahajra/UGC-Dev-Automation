"""
Auto-Update Historical Log to Context Studio After Deployment
This script automatically appends new failure fixes to the historical log
and uploads them to Context Studio after a pipeline fix is deployed.

Usage:
    python auto_update_historical_log.py --job-name "Job Name" --error-type "ErrorType" --fix-description "Description"
    
Or call from pipeline:
    python auto_update_historical_log.py --from-pipeline-log pipeline_fix.json
"""

import asyncio
import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from src.config_manager import get_config
from src.mcp_client import MCPClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/auto_update_historical.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# File paths
HISTORICAL_LOG_FILE = Path('historical_failures_for_context_studio.jsonl')
PIPELINE_FIXES_DIR = Path('pipeline_fixes')


def generate_failure_id() -> str:
    """Generate a unique failure ID."""
    # Read existing file to get the next ID
    if HISTORICAL_LOG_FILE.exists():
        with open(HISTORICAL_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('//')]
            if lines:
                try:
                    last_record = json.loads(lines[-1])
                    last_id = last_record.get('id', 'failure-000')
                    # Extract number and increment
                    num = int(last_id.split('-')[1]) + 1
                    return f"failure-{num:03d}"
                except (json.JSONDecodeError, ValueError, IndexError):
                    pass
    
    # Default starting ID
    return "failure-018"


def create_failure_record(
    job_name: str,
    error_type: str,
    error_message: str,
    stack_trace: str,
    resolution: str,
    fix_description: str,
    category: str = "Unknown",
    severity: str = "medium",
    **additional_metadata
) -> Dict[str, Any]:
    """
    Create a standardized failure record.
    
    Args:
        job_name: Name of the job that failed
        error_type: Type of error (e.g., NullReferenceError, ConnectionError)
        error_message: Error message
        stack_trace: Stack trace or error details
        resolution: How the issue was resolved
        fix_description: Brief description of the fix
        category: Error category
        severity: Severity level (low, medium, high, critical)
        **additional_metadata: Any additional metadata
        
    Returns:
        Formatted failure record
    """
    failure_id = generate_failure_id()
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    record = {
        "id": failure_id,
        "timestamp": timestamp,
        "job_name": job_name,
        "error_type": error_type,
        "error_message": error_message,
        "stack_trace": stack_trace,
        "resolution": resolution,
        "fix_applied": True,
        "category": category,
        "severity": severity,
        "fix_description": fix_description,
        "prevented_incidents": 0,  # Will be updated over time
        "confidence": 0.85  # Default confidence
    }
    
    # Add any additional metadata
    record.update(additional_metadata)
    
    return record


def append_to_historical_log(record: Dict[str, Any]) -> bool:
    """
    Append a new failure record to the historical log file.
    
    Args:
        record: Failure record to append
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure the file exists
        if not HISTORICAL_LOG_FILE.exists():
            HISTORICAL_LOG_FILE.touch()
        
        # Append the record as a new line
        with open(HISTORICAL_LOG_FILE, 'a', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False)
            f.write('\n')
        
        logger.info(f"✓ Appended record {record['id']} to historical log")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to append to historical log: {str(e)}")
        return False


async def upload_to_context_studio(record: Dict[str, Any]) -> bool:
    """
    Upload a single failure record to Context Studio.
    
    Args:
        record: Failure record to upload
        
    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_config('config.yaml')
        mcp_client = MCPClient(config)
        
        logger.info(f"Uploading {record['id']} to Context Studio...")
        
        # Prepare payload for MCP ingestion
        payload = {
            "source": {
                "type": "historical_failure",
                "system": "cron-job-automation",
                "timestamp": record.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                "auto_updated": True
            },
            "data": {
                "failure_id": record['id'],
                "job_name": record['job_name'],
                "error_type": record['error_type'],
                "error_message": record.get('error_message', ''),
                "stack_trace": record.get('stack_trace', ''),
                "resolution": record.get('resolution', ''),
                "fix_applied": record.get('fix_applied', True),
                "category": record.get('category', 'Unknown'),
                "severity": record.get('severity', 'medium'),
                "fix_description": record.get('fix_description', ''),
                "prevented_incidents": record.get('prevented_incidents', 0),
                "confidence": record.get('confidence', 0.85),
                # Additional metadata
                "metadata": {
                    k: v for k, v in record.items() 
                    if k not in ['id', 'job_name', 'error_type', 'error_message', 
                                'stack_trace', 'resolution', 'fix_applied', 'category',
                                'severity', 'fix_description', 'prevented_incidents', 
                                'confidence', 'timestamp']
                }
            }
        }
        
        # Ingest into Context Studio
        success = await mcp_client.ingest_knowledge(
            event_type="successfulFixIngestion",
            payload=payload
        )
        
        if success:
            logger.info(f"✓ Successfully uploaded {record['id']} to Context Studio")
            return True
        else:
            logger.warning(f"⚠️  Upload returned false for {record['id']}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to upload to Context Studio: {str(e)}")
        return False


def load_pipeline_fix_log(log_file: Path) -> Optional[Dict[str, Any]]:
    """
    Load a pipeline fix log file.
    
    Args:
        log_file: Path to the pipeline fix log JSON file
        
    Returns:
        Parsed log data or None if failed
    """
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load pipeline fix log: {str(e)}")
        return None


async def process_pipeline_fix(log_file: Path, delete_after_upload: bool = True) -> bool:
    """
    Process a pipeline fix log and update historical data.
    
    Args:
        log_file: Path to the pipeline fix log
        delete_after_upload: If True, delete the processed file after successful upload
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing pipeline fix log: {log_file}")
    
    # Load the fix log
    fix_data = load_pipeline_fix_log(log_file)
    if not fix_data:
        return False
    
    # Create failure record from fix log
    record = create_failure_record(
        job_name=fix_data.get('job_name', 'Unknown Job'),
        error_type=fix_data.get('error_type', 'Unknown Error'),
        error_message=fix_data.get('error_message', ''),
        stack_trace=fix_data.get('stack_trace', ''),
        resolution=fix_data.get('resolution', ''),
        fix_description=fix_data.get('fix_description', ''),
        category=fix_data.get('category', 'Unknown'),
        severity=fix_data.get('severity', 'medium'),
        **fix_data.get('metadata', {})
    )
    
    # Append to historical log
    if not append_to_historical_log(record):
        return False
    
    # Upload to Context Studio
    success = await upload_to_context_studio(record)
    
    # Delete the processed file if upload was successful
    if success and delete_after_upload:
        try:
            log_file.unlink()
            logger.info(f"✓ Deleted processed file: {log_file}")
        except Exception as e:
            logger.warning(f"⚠️  Could not delete processed file {log_file}: {str(e)}")
            # Don't fail the whole operation if we can't delete the file
    
    return success


async def add_manual_fix(args) -> bool:
    """
    Add a manual fix entry.
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Adding manual fix entry...")
    
    # Create failure record from command line args
    record = create_failure_record(
        job_name=args.job_name,
        error_type=args.error_type,
        error_message=args.error_message or f"{args.error_type} occurred in {args.job_name}",
        stack_trace=args.stack_trace or "Stack trace not provided",
        resolution=args.resolution or "Fix applied and deployed",
        fix_description=args.fix_description,
        category=args.category,
        severity=args.severity
    )
    
    # Append to historical log
    if not append_to_historical_log(record):
        return False
    
    # Upload to Context Studio
    success = await upload_to_context_studio(record)
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Auto-update historical log after deployment and failure fix'
    )
    
    # Option 1: Load from pipeline fix log
    parser.add_argument(
        '--from-pipeline-log',
        type=str,
        help='Path to pipeline fix log JSON file'
    )
    
    # Option 2: Manual entry
    parser.add_argument('--job-name', type=str, help='Name of the job')
    parser.add_argument('--error-type', type=str, help='Type of error')
    parser.add_argument('--error-message', type=str, help='Error message')
    parser.add_argument('--stack-trace', type=str, help='Stack trace')
    parser.add_argument('--resolution', type=str, help='How the issue was resolved')
    parser.add_argument('--fix-description', type=str, help='Brief description of the fix')
    parser.add_argument('--category', type=str, default='Unknown', help='Error category')
    parser.add_argument('--severity', type=str, default='medium', 
                       choices=['low', 'medium', 'high', 'critical'],
                       help='Severity level')
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Create pipeline_fixes directory if it doesn't exist
    PIPELINE_FIXES_DIR.mkdir(exist_ok=True)
    
    print("\n" + "=" * 70)
    print("  Auto-Update Historical Log to Context Studio")
    print("=" * 70)
    print()
    
    try:
        if args.from_pipeline_log:
            # Process pipeline fix log
            log_file = Path(args.from_pipeline_log)
            if not log_file.exists():
                print(f"✗ Pipeline fix log not found: {log_file}")
                sys.exit(1)
            
            success = asyncio.run(process_pipeline_fix(log_file))
            
        elif args.job_name and args.error_type and args.fix_description:
            # Manual entry
            success = asyncio.run(add_manual_fix(args))
            
        else:
            print("✗ Invalid arguments!")
            print("\nUsage:")
            print("  1. From pipeline log:")
            print("     python auto_update_historical_log.py --from-pipeline-log pipeline_fix.json")
            print()
            print("  2. Manual entry:")
            print("     python auto_update_historical_log.py \\")
            print("       --job-name \"Job Name\" \\")
            print("       --error-type \"ErrorType\" \\")
            print("       --fix-description \"Description of fix\"")
            sys.exit(1)
        
        if success:
            print("\n✓ Historical log updated and uploaded to Context Studio!")
            print("\nThe new failure pattern is now available for:")
            print("  - Vector search in the dashboard")
            print("  - Future failure predictions")
            print("  - Automated fix suggestions")
            sys.exit(0)
        else:
            print("\n✗ Failed to update historical log")
            print("\nCheck logs/auto_update_historical.log for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        logger.exception("Unexpected error during update")
        sys.exit(1)


if __name__ == '__main__':
    main()


# Made with Bob