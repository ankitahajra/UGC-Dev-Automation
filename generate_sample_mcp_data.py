"""
Generate Sample MCP Historical Run Data
Creates realistic historical failure and resolution data to showcase MCP intelligence.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

from src.config_manager import get_config
from src.mcp_client import MCPClient

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/sample_data_generation.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# Sample historical failure scenarios with resolutions
HISTORICAL_SCENARIOS = [
    {
        "run_id": "run-2024-01-15-001",
        "timestamp": "2024-01-15T08:30:00Z",
        "job_id": "cron-job-1",
        "job_name": "Data Processing Job",
        "failure": {
            "error_type": "NullReferenceError",
            "error_message": "Cannot read property 'customerId' of null",
            "function": "process_customer_data",
            "line": "index.js:45",
            "stack_trace": [
                "at processCustomerData (index.js:45:12)",
                "at Array.forEach (<anonymous>)",
                "at main (index.js:30:8)"
            ],
            "context": {
                "data_source": "customers_null_values.csv",
                "records_processed": 150,
                "failed_at_record": 151
            }
        },
        "resolution": {
            "type": "code_fix",
            "description": "Added null check before accessing customer properties",
            "fix_applied": "Added: if (!customer || !customer.customerId) { skip record }",
            "time_to_fix": "15 minutes",
            "success_rate": 0.95,
            "verified": True,
            "prevented_incidents": 8
        },
        "metrics": {
            "downtime_minutes": 15,
            "affected_records": 1,
            "recovery_time": 5
        }
    },
    {
        "run_id": "run-2024-01-18-002",
        "timestamp": "2024-01-18T10:15:00Z",
        "job_id": "cron-job-1",
        "job_name": "Data Processing Job",
        "failure": {
            "error_type": "NullReferenceError",
            "error_message": "Cannot access property 'name' of undefined",
            "function": "process_customer_data",
            "line": "index.js:48",
            "stack_trace": [
                "at processCustomerData (index.js:48:15)",
                "at processRecords (index.js:35:10)"
            ],
            "context": {
                "data_source": "customers_null_values.csv",
                "records_processed": 200,
                "failed_at_record": 201
            }
        },
        "resolution": {
            "type": "code_fix",
            "description": "Enhanced null checking with optional chaining",
            "fix_applied": "Changed to: customer?.name || 'Unknown'",
            "time_to_fix": "8 minutes",
            "success_rate": 0.98,
            "verified": True,
            "prevented_incidents": 12
        },
        "metrics": {
            "downtime_minutes": 8,
            "affected_records": 1,
            "recovery_time": 3
        }
    },
    {
        "run_id": "run-2024-01-20-003",
        "timestamp": "2024-01-20T14:30:00Z",
        "job_id": "cron-job-2",
        "job_name": "Bulk Report Generation",
        "failure": {
            "error_type": "MemoryError",
            "error_message": "Out of memory: Cannot allocate 8.5GB for dataset",
            "function": "generate_reports",
            "line": "report_gen.py:120",
            "stack_trace": [
                "at load_all_customers (report_gen.py:120:5)",
                "at generate_reports (report_gen.py:85:10)"
            ],
            "context": {
                "data_source": "customers_large_volume.csv",
                "records_attempted": 500000,
                "memory_used": "8.5GB",
                "memory_limit": "8GB"
            }
        },
        "resolution": {
            "type": "architecture_fix",
            "description": "Implemented batch processing with pagination",
            "fix_applied": "Process records in chunks of 1000 instead of loading all",
            "time_to_fix": "45 minutes",
            "success_rate": 0.92,
            "verified": True,
            "prevented_incidents": 15
        },
        "metrics": {
            "downtime_minutes": 45,
            "affected_records": 500000,
            "recovery_time": 10
        }
    },
    {
        "run_id": "run-2024-01-22-004",
        "timestamp": "2024-01-22T09:00:00Z",
        "job_id": "cron-job-2",
        "job_name": "Bulk Report Generation",
        "failure": {
            "error_type": "MemoryError",
            "error_message": "Memory limit exceeded during data expansion",
            "function": "expand_customer_data",
            "line": "report_gen.py:145",
            "stack_trace": [
                "at expand_customer_data (report_gen.py:145:8)",
                "at process_batch (report_gen.py:95:12)"
            ],
            "context": {
                "data_source": "customers_large_volume.csv",
                "batch_size": 5000,
                "memory_used": "7.8GB"
            }
        },
        "resolution": {
            "type": "optimization",
            "description": "Reduced batch size and added memory monitoring",
            "fix_applied": "Reduced batch size to 1000 and added memory checks",
            "time_to_fix": "20 minutes",
            "success_rate": 0.96,
            "verified": True,
            "prevented_incidents": 10
        },
        "metrics": {
            "downtime_minutes": 20,
            "affected_records": 5000,
            "recovery_time": 5
        }
    },
    {
        "run_id": "run-2024-01-25-005",
        "timestamp": "2024-01-25T11:45:00Z",
        "job_id": "cron-job-3",
        "job_name": "External API Sync",
        "failure": {
            "error_type": "TimeoutError",
            "error_message": "Operation timed out after 5 seconds",
            "function": "sync_external_api",
            "line": "api_sync.py:78",
            "stack_trace": [
                "at call_api (api_sync.py:78:10)",
                "at sync_external_api (api_sync.py:45:8)"
            ],
            "context": {
                "api_endpoint": "https://external-api.example.com/sync",
                "timeout_limit": 5,
                "actual_duration": 8.5
            }
        },
        "resolution": {
            "type": "config_fix",
            "description": "Increased timeout and added retry logic",
            "fix_applied": "Timeout: 5s -> 15s, Added 3 retries with exponential backoff",
            "time_to_fix": "12 minutes",
            "success_rate": 0.89,
            "verified": True,
            "prevented_incidents": 6
        },
        "metrics": {
            "downtime_minutes": 12,
            "affected_records": 0,
            "recovery_time": 2
        }
    },
    {
        "run_id": "run-2024-01-28-006",
        "timestamp": "2024-01-28T16:20:00Z",
        "job_id": "cron-job-3",
        "job_name": "External API Sync",
        "failure": {
            "error_type": "TimeoutError",
            "error_message": "API connection timeout after 10 seconds",
            "function": "fetch_external_data",
            "line": "api_sync.py:92",
            "stack_trace": [
                "at fetch_external_data (api_sync.py:92:5)",
                "at sync_data (api_sync.py:55:10)"
            ],
            "context": {
                "api_endpoint": "https://external-api.example.com/data",
                "timeout_limit": 10,
                "retry_count": 2
            }
        },
        "resolution": {
            "type": "circuit_breaker",
            "description": "Implemented circuit breaker pattern",
            "fix_applied": "Added circuit breaker with 3 failure threshold",
            "time_to_fix": "30 minutes",
            "success_rate": 0.94,
            "verified": True,
            "prevented_incidents": 20
        },
        "metrics": {
            "downtime_minutes": 30,
            "affected_records": 0,
            "recovery_time": 8
        }
    },
    {
        "run_id": "run-2024-02-01-007",
        "timestamp": "2024-02-01T13:10:00Z",
        "job_id": "cron-job-4",
        "job_name": "Database Cleanup Job",
        "failure": {
            "error_type": "DatabaseLockError",
            "error_message": "Could not acquire lock on table 'customers' after 30 seconds",
            "function": "cleanup_old_records",
            "line": "db_cleanup.py:65",
            "stack_trace": [
                "at acquire_lock (db_cleanup.py:65:8)",
                "at cleanup_old_records (db_cleanup.py:40:12)"
            ],
            "context": {
                "table": "customers",
                "lock_timeout": 30,
                "conflicting_process": "backup_job"
            }
        },
        "resolution": {
            "type": "scheduling_fix",
            "description": "Adjusted job schedule to avoid conflicts",
            "fix_applied": "Moved cleanup job to run after backup completes",
            "time_to_fix": "10 minutes",
            "success_rate": 0.97,
            "verified": True,
            "prevented_incidents": 25
        },
        "metrics": {
            "downtime_minutes": 10,
            "affected_records": 0,
            "recovery_time": 2
        }
    },
    {
        "run_id": "run-2024-02-05-008",
        "timestamp": "2024-02-05T07:30:00Z",
        "job_id": "cron-job-4",
        "job_name": "Database Cleanup Job",
        "failure": {
            "error_type": "DatabaseLockError",
            "error_message": "Lock timeout on table 'orders' during cleanup",
            "function": "cleanup_orders",
            "line": "db_cleanup.py:88",
            "stack_trace": [
                "at cleanup_orders (db_cleanup.py:88:10)",
                "at run_cleanup (db_cleanup.py:25:8)"
            ],
            "context": {
                "table": "orders",
                "lock_timeout": 30,
                "records_to_delete": 50000
            }
        },
        "resolution": {
            "type": "optimization",
            "description": "Implemented row-level locking and batch deletes",
            "fix_applied": "Delete in batches of 1000 with row-level locks",
            "time_to_fix": "25 minutes",
            "success_rate": 0.93,
            "verified": True,
            "prevented_incidents": 18
        },
        "metrics": {
            "downtime_minutes": 25,
            "affected_records": 50000,
            "recovery_time": 5
        }
    }
]


async def ingest_historical_scenario(mcp: MCPClient, scenario: Dict[str, Any]) -> bool:
    """
    Ingest a single historical scenario into MCP.
    
    Args:
        mcp: MCP client instance
        scenario: Historical scenario data
        
    Returns:
        True if successful
    """
    logger.info(f"Ingesting scenario: {scenario['run_id']}")
    
    # Create comprehensive payload
    payload = {
        "source": "cron-job-automation-historical",
        "timestamp": scenario["timestamp"],
        "data": {
            "run_metadata": {
                "run_id": scenario["run_id"],
                "job_id": scenario["job_id"],
                "job_name": scenario["job_name"],
                "timestamp": scenario["timestamp"]
            },
            "failure_signature": {
                "error_type": scenario["failure"]["error_type"],
                "error_message": scenario["failure"]["error_message"],
                "function": scenario["failure"]["function"],
                "pattern": f"{scenario['failure']['error_type']}_{scenario['failure']['function']}",
                "context": scenario["failure"]["context"]
            },
            "applied_fix": {
                "type": scenario["resolution"]["type"],
                "description": scenario["resolution"]["description"],
                "fix_applied": scenario["resolution"]["fix_applied"],
                "time_to_fix": scenario["resolution"]["time_to_fix"]
            },
            "outcome": {
                "status": "successful",
                "success_rate": scenario["resolution"]["success_rate"],
                "verified": scenario["resolution"]["verified"],
                "incidents_prevented": scenario["resolution"]["prevented_incidents"],
                "metrics": scenario["metrics"]
            }
        }
    }
    
    try:
        success = await mcp.ingest_knowledge(
            event_type="successfulFixIngestion",
            payload=payload
        )
        
        if success:
            logger.info(f"✅ Successfully ingested: {scenario['run_id']}")
        else:
            logger.warning(f"⚠️  Failed to ingest: {scenario['run_id']}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error ingesting {scenario['run_id']}: {str(e)}")
        return False


async def generate_sample_data():
    """Generate and ingest sample historical data."""
    logger.info("="*80)
    logger.info("  GENERATING SAMPLE MCP HISTORICAL DATA")
    logger.info("="*80)
    
    try:
        # Initialize MCP client
        config = get_config('config.yaml')
        mcp = MCPClient(config)
        
        # Check MCP health
        logger.info("\n🔍 Checking MCP server health...")
        is_healthy = await mcp.check_health()
        
        if not is_healthy:
            logger.error("❌ MCP server is not healthy. Cannot proceed.")
            logger.error("Please check:")
            logger.error("  1. Network connectivity")
            logger.error("  2. Bearer token in .bob/mcp.json")
            logger.error("  3. MCP server status")
            return False
        
        logger.info("✅ MCP server is healthy!\n")
        
        # Ingest all historical scenarios
        logger.info(f"📊 Ingesting {len(HISTORICAL_SCENARIOS)} historical scenarios...")
        logger.info("-"*80)
        
        success_count = 0
        for i, scenario in enumerate(HISTORICAL_SCENARIOS, 1):
            logger.info(f"\n[{i}/{len(HISTORICAL_SCENARIOS)}] Processing: {scenario['job_name']}")
            logger.info(f"   Run ID: {scenario['run_id']}")
            logger.info(f"   Error: {scenario['failure']['error_type']}")
            logger.info(f"   Resolution: {scenario['resolution']['type']}")
            
            success = await ingest_historical_scenario(mcp, scenario)
            if success:
                success_count += 1
            
            # Small delay between ingestions
            await asyncio.sleep(0.5)
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("  INGESTION COMPLETE")
        logger.info("="*80)
        logger.info(f"\n✅ Successfully ingested: {success_count}/{len(HISTORICAL_SCENARIOS)} scenarios")
        
        if success_count > 0:
            logger.info("\n📈 Knowledge Base Summary:")
            logger.info(f"   - Total historical runs: {len(HISTORICAL_SCENARIOS)}")
            logger.info(f"   - Unique job types: 4")
            logger.info(f"   - Error patterns: 4 types")
            logger.info(f"   - Resolution strategies: 6 types")
            logger.info(f"   - Total incidents prevented: {sum(s['resolution']['prevented_incidents'] for s in HISTORICAL_SCENARIOS)}")
            
            logger.info("\n🎯 What You Can Now Test:")
            logger.info("   1. Run mock cron jobs - they will fail")
            logger.info("   2. MCP will find similar historical failures")
            logger.info("   3. Analysis confidence will be boosted")
            logger.info("   4. Faster resolution with proven fixes")
            
            logger.info("\n📝 Next Steps:")
            logger.info("   1. Run: python demo_mcp_with_history.py")
            logger.info("   2. Run: python mock_cron_jobs.py")
            logger.info("   3. Check logs for MCP-enhanced analysis")
            
            logger.info("\n📄 Log file: logs/sample_data_generation.log")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"\n❌ Error generating sample data: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(generate_sample_data())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob