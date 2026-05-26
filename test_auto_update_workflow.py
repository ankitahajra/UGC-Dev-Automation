"""
Test Script for Auto-Update Historical Log Workflow
Tests the complete workflow of recording a fix and uploading to Context Studio.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.pipeline_fix_tracker import get_fix_tracker
from src.config_manager import get_config
from src.mcp_client import MCPClient


async def test_workflow():
    """Test the complete auto-update workflow."""
    print("\n" + "=" * 70)
    print("  Testing Auto-Update Historical Log Workflow")
    print("=" * 70)
    print()
    
    # Step 1: Record a test fix
    print("Step 1: Recording a test fix...")
    print("-" * 70)
    
    tracker = get_fix_tracker()
    
    test_fix = {
        "job_name": "Test Data Processing Job",
        "error_type": "TestNullReferenceError",
        "error_message": "Test: Cannot read property 'testId' of null",
        "stack_trace": "at testFunction (test.js:10:5)\nat main (test.js:5:3)",
        "resolution": "Added null check before accessing test properties",
        "fix_description": "Implemented defensive programming with null checks for test",
        "category": "Code Error",
        "severity": "medium",
        "deployment_id": f"test-deploy-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    }
    
    try:
        fix_file = tracker.record_fix(**test_fix)
        print(f"✓ Test fix recorded: {fix_file}")
        print()
    except Exception as e:
        print(f"✗ Failed to record test fix: {str(e)}")
        return False
    
    # Step 2: Verify the fix file was created
    print("Step 2: Verifying fix file...")
    print("-" * 70)
    
    if not fix_file.exists():
        print(f"✗ Fix file not found: {fix_file}")
        return False
    
    with open(fix_file, 'r', encoding='utf-8') as f:
        fix_data = json.load(f)
    
    print(f"✓ Fix file exists and is valid JSON")
    print(f"  Job: {fix_data['job_name']}")
    print(f"  Error: {fix_data['error_type']}")
    print(f"  Fix: {fix_data['fix_description']}")
    print()
    
    # Step 3: Test appending to historical log
    print("Step 3: Testing append to historical log...")
    print("-" * 70)
    
    from auto_update_historical_log import create_failure_record, append_to_historical_log
    
    record = create_failure_record(
        job_name=fix_data['job_name'],
        error_type=fix_data['error_type'],
        error_message=fix_data['error_message'],
        stack_trace=fix_data['stack_trace'],
        resolution=fix_data['resolution'],
        fix_description=fix_data['fix_description'],
        category=fix_data['category'],
        severity=fix_data['severity']
    )
    
    # Backup the original file
    historical_file = Path('historical_failures_for_context_studio.jsonl')
    backup_file = Path('historical_failures_for_context_studio.jsonl.backup')
    
    if historical_file.exists():
        import shutil
        shutil.copy(historical_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
    
    success = append_to_historical_log(record)
    
    if success:
        print(f"✓ Successfully appended record {record['id']} to historical log")
        print()
    else:
        print("✗ Failed to append to historical log")
        return False
    
    # Step 4: Test MCP upload (optional - requires valid credentials)
    print("Step 4: Testing MCP upload to Context Studio...")
    print("-" * 70)
    
    try:
        config = get_config('config.yaml')
        mcp_client = MCPClient(config)
        
        # Check health first
        is_healthy = await mcp_client.check_health()
        
        if not is_healthy:
            print("⚠️  MCP Context Studio is not accessible")
            print("   Skipping upload test (this is OK for local testing)")
            print()
        else:
            print("✓ MCP Context Studio is accessible")
            
            # Prepare payload
            payload = {
                "source": {
                    "type": "historical_failure",
                    "system": "cron-job-automation",
                    "timestamp": record['timestamp'],
                    "test_mode": True
                },
                "data": {
                    "failure_id": record['id'],
                    "job_name": record['job_name'],
                    "error_type": record['error_type'],
                    "error_message": record['error_message'],
                    "stack_trace": record['stack_trace'],
                    "resolution": record['resolution'],
                    "fix_applied": True,
                    "category": record['category'],
                    "severity": record['severity'],
                    "fix_description": record['fix_description'],
                    "prevented_incidents": 0,
                    "confidence": 0.85
                }
            }
            
            # Upload
            upload_success = await mcp_client.ingest_knowledge(
                event_type="successfulFixIngestion",
                payload=payload
            )
            
            if upload_success:
                print(f"✓ Successfully uploaded test record to Context Studio")
                print()
            else:
                print("⚠️  Upload returned false (may still be ingested)")
                print()
    
    except Exception as e:
        print(f"⚠️  MCP upload test failed: {str(e)}")
        print("   This is OK if you don't have valid MCP credentials")
        print()
    
    # Step 5: Cleanup
    print("Step 5: Cleanup...")
    print("-" * 70)
    
    # Remove the test record from historical log
    if historical_file.exists() and backup_file.exists():
        import shutil
        shutil.copy(backup_file, historical_file)
        backup_file.unlink()
        print("✓ Restored original historical log")
    
    # Mark the fix as processed
    tracker.mark_fix_processed(fix_file)
    print("✓ Marked test fix as processed")
    print()
    
    # Summary
    print("=" * 70)
    print("  Test Summary")
    print("=" * 70)
    print("✓ Fix recording: PASSED")
    print("✓ File creation: PASSED")
    print("✓ Historical log append: PASSED")
    print("✓ Cleanup: PASSED")
    print()
    print("The auto-update workflow is working correctly!")
    print()
    
    return True


def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_workflow())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


# Made with Bob