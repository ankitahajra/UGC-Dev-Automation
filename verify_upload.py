"""Quick script to verify uploaded data"""
import asyncio
from src.config_manager import get_config
from src.mcp_client import MCPClient

async def verify():
    mcp = MCPClient(get_config('config.yaml'))
    
    # Search for cron job failures
    results = await mcp.vector_search('cron job failure NullReferenceError database', top_k=20)
    
    print(f"\n{'='*70}")
    print(f"Found {len(results)} results in Context Studio")
    print(f"{'='*70}\n")
    
    # Check what types of data we have
    cron_failures = 0
    docs = 0
    
    for r in results:
        metadata = r.get('metadata', {})
        source_file = metadata.get('source_file', '')
        
        if 'failure' in source_file.lower() or 'cron' in str(r.get('content', '')).lower():
            cron_failures += 1
            print(f"✓ Cron Failure: {metadata.get('title', 'N/A')}")
        else:
            docs += 1
    
    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  - Cron Job Failures: {cron_failures}")
    print(f"  - Documentation: {docs}")
    print(f"  - Total: {len(results)}")
    print(f"{'='*70}\n")
    
    if cron_failures > 0:
        print("✅ SUCCESS: Cron job failure data is now in Context Studio!")
    else:
        print("⚠️  WARNING: No cron job failure data found yet. Upload may still be in progress.")

if __name__ == "__main__":
    asyncio.run(verify())

# Made with Bob
