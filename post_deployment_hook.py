"""
Post-Deployment Hook for Pipeline
This script should be called after a successful deployment where a fix was applied.
It automatically records the fix and updates the historical log in Context Studio.

Usage in pipeline (bob-pipeline.yaml):
  - name: Record Fix After Deployment
    run: |
      python post_deployment_hook.py \
        --job-name "$JOB_NAME" \
        --error-type "$ERROR_TYPE" \
        --fix-description "$FIX_DESCRIPTION"

Or call directly after manual fix:
  python post_deployment_hook.py --job-name "Data Processing Job" --error-type "NullReferenceError" --fix-description "Added null checks"
"""

import sys
import argparse
import logging
import subprocess
from pathlib import Path

from src.pipeline_fix_tracker import get_fix_tracker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/post_deployment.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for post-deployment hook."""
    parser = argparse.ArgumentParser(
        description='Post-deployment hook to record fixes and update historical log'
    )
    
    # Required arguments
    parser.add_argument('--job-name', required=True, help='Name of the job that was fixed')
    parser.add_argument('--error-type', required=True, help='Type of error that was fixed')
    parser.add_argument('--fix-description', required=True, help='Description of the fix applied')
    
    # Optional arguments
    parser.add_argument('--error-message', default='', help='Original error message')
    parser.add_argument('--stack-trace', default='', help='Original stack trace')
    parser.add_argument('--resolution', default='', help='Detailed resolution steps')
    parser.add_argument('--category', default='Code Error', help='Error category')
    parser.add_argument('--severity', default='medium', 
                       choices=['low', 'medium', 'high', 'critical'],
                       help='Severity level')
    parser.add_argument('--deployment-id', help='Deployment identifier')
    parser.add_argument('--auto-upload', action='store_true', 
                       help='Automatically upload to Context Studio (default: True)')
    parser.add_argument('--no-auto-upload', dest='auto_upload', action='store_false',
                       help='Do not automatically upload to Context Studio')
    parser.set_defaults(auto_upload=True)
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    print("\n" + "=" * 70)
    print("  Post-Deployment Hook - Recording Fix")
    print("=" * 70)
    print()
    
    try:
        # Get the fix tracker
        tracker = get_fix_tracker()
        
        # Record the fix
        logger.info(f"Recording fix for job: {args.job_name}")
        print(f"Job Name: {args.job_name}")
        print(f"Error Type: {args.error_type}")
        print(f"Fix: {args.fix_description}")
        print()
        
        fix_file = tracker.record_fix(
            job_name=args.job_name,
            error_type=args.error_type,
            error_message=args.error_message or f"{args.error_type} in {args.job_name}",
            stack_trace=args.stack_trace or "Stack trace not captured during deployment",
            resolution=args.resolution or f"Applied fix: {args.fix_description}",
            fix_description=args.fix_description,
            category=args.category,
            severity=args.severity,
            deployment_id=args.deployment_id
        )
        
        print(f"✓ Fix recorded: {fix_file}")
        print()
        
        # Automatically upload to Context Studio if enabled
        if args.auto_upload:
            print("Uploading to Context Studio...")
            print()
            
            # Call the auto_update_historical_log.py script
            result = subprocess.run(
                [
                    sys.executable,
                    'auto_update_historical_log.py',
                    '--from-pipeline-log',
                    str(fix_file)
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ Successfully uploaded to Context Studio!")
                print()
                print("The fix is now part of the historical knowledge base and will be")
                print("used for future failure predictions and automated suggestions.")
                
                # Mark as processed
                tracker.mark_fix_processed(fix_file)
                
            else:
                print("⚠️  Upload to Context Studio failed!")
                print()
                print("You can manually upload later using:")
                print(f"  python auto_update_historical_log.py --from-pipeline-log {fix_file}")
                print()
                print("Error output:")
                print(result.stderr)
                sys.exit(1)
        else:
            print("⚠️  Auto-upload disabled. To upload to Context Studio, run:")
            print(f"  python auto_update_historical_log.py --from-pipeline-log {fix_file}")
        
        print()
        print("=" * 70)
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        logger.exception("Error in post-deployment hook")
        sys.exit(1)


if __name__ == '__main__':
    main()


# Made with Bob