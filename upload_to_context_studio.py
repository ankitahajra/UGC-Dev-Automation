"""
Upload Historical Failures to Context Studio via MCP API (ONE-TIME SETUP)
Reads historical_failures_for_context_studio.txt and uploads it as a data file to Context Studio.

IMPORTANT: This is a ONE-TIME upload. Once the historical data is uploaded to Context Studio,
it becomes part of the knowledge base and does NOT need to be re-uploaded for each demo.

The uploaded file (historical_failures_for_context_studio.txt) will be used by Context Studio
for all future vector searches and demonstrations. You only need to run this script again if:
1. You want to add new historical failure patterns
2. You need to update existing patterns
3. The Context Studio data was cleared/reset
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

from src.config_manager import get_config
from src.mcp_client import MCPClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/context_studio_upload.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def upload_historical_failures():
    """Upload historical failures from JSONL file to Context Studio."""
    
    logger.info("=" * 70)
    logger.info("  Context Studio Historical Failures Upload")
    logger.info("=" * 70)
    logger.info("")
    
    # Initialize MCP client
    try:
        config = get_config('config.yaml')
        mcp_client = MCPClient(config)
        logger.info("✓ MCP Client initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize MCP client: {str(e)}")
        return False
    
    # Check MCP health
    logger.info("Checking MCP Context Studio connection...")
    is_healthy = await mcp_client.check_health()
    if not is_healthy:
        logger.error("✗ MCP Context Studio is not accessible")
        logger.error("  Please check your connection and credentials in .bob/mcp.json")
        return False
    logger.info("✓ MCP Context Studio connected successfully")
    logger.info("")
    
    # Read the JSONL file
    jsonl_file = Path('historical_failures_for_context_studio.jsonl')
    if not jsonl_file.exists():
        logger.error(f"✗ File not found: {jsonl_file}")
        return False
    
    logger.info(f"Reading file: {jsonl_file}")
    
    failures = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                failure = json.loads(line.strip())
                failures.append(failure)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Skipping invalid JSON on line {line_num}: {str(e)}")
    
    logger.info(f"✓ Loaded {len(failures)} failure records")
    logger.info("")
    
    # Upload each failure to Context Studio
    logger.info("Starting upload to Context Studio...")
    logger.info("")
    
    successful = 0
    failed = 0
    
    for i, failure in enumerate(failures, 1):
        failure_id = failure.get('id', f'unknown-{i}')
        job_name = failure.get('job_name', 'Unknown Job')
        error_type = failure.get('error_type', 'Unknown Error')
        
        logger.info(f"[{i}/{len(failures)}] Uploading: {failure_id}")
        logger.info(f"   Job: {job_name}")
        logger.info(f"   Error: {error_type}")
        
        try:
            # Prepare payload for MCP ingestion
            payload = {
                "source": {
                    "type": "historical_failure",
                    "system": "cron-job-automation",
                    "timestamp": failure.get('timestamp', datetime.utcnow().isoformat() + 'Z')
                },
                "data": {
                    "failure_id": failure_id,
                    "job_name": job_name,
                    "error_type": error_type,
                    "error_message": failure.get('error_message', ''),
                    "stack_trace": failure.get('stack_trace', ''),
                    "resolution": failure.get('resolution', ''),
                    "fix_applied": failure.get('fix_applied', False),
                    "category": failure.get('category', 'Unknown'),
                    "severity": failure.get('severity', 'medium'),
                    "fix_description": failure.get('fix_description', ''),
                    "prevented_incidents": failure.get('prevented_incidents', 0),
                    "confidence": failure.get('confidence', 0.0),
                    # Additional metadata
                    "metadata": {
                        k: v for k, v in failure.items() 
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
                logger.info(f"   ✓ Successfully uploaded")
                successful += 1
            else:
                logger.warning(f"   ⚠️  Upload returned false (may still be ingested)")
                failed += 1
                
        except Exception as e:
            logger.error(f"   ✗ Failed to upload: {str(e)}")
            failed += 1
        
        logger.info("")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Summary
    logger.info("=" * 70)
    logger.info("  Upload Summary")
    logger.info("=" * 70)
    logger.info(f"Total records: {len(failures)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {(successful/len(failures)*100):.1f}%")
    logger.info("")
    
    if successful > 0:
        logger.info("✓ Upload completed!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Wait 5-10 minutes for Context Studio to index the data")
        logger.info("  2. Start the dashboard: START_ALL_DEMOS.bat")
        logger.info("  3. Run a job and click 'Search Similar Failures'")
        logger.info("  4. You should see real MCP results from uploaded data!")
        logger.info("")
        return True
    else:
        logger.error("✗ No records were uploaded successfully")
        logger.error("  Check the logs above for error details")
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("  Context Studio Historical Failures Upload")
    print("=" * 70)
    print("\nThis script will upload historical failure data to Context Studio")
    print("via the MCP API for vector search demonstration.\n")
    
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Run the async upload
    try:
        success = asyncio.run(upload_historical_failures())
        
        if success:
            print("\n✓ Upload completed successfully!")
            print("\nCheck logs/context_studio_upload.log for details")
            sys.exit(0)
        else:
            print("\n✗ Upload failed!")
            print("\nCheck logs/context_studio_upload.log for error details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        logger.exception("Unexpected error during upload")
        sys.exit(1)


if __name__ == '__main__':
    main()


# Made with Bob