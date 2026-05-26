"""
Test script to check MCP historical data retrieval
"""
import asyncio
import logging
import sys
from src.config_manager import get_config
from src.mcp_client import MCPClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def test_mcp_historical():
    """Test MCP historical data retrieval."""
    try:
        logger.info("="*80)
        logger.info("Testing MCP Historical Data Retrieval")
        logger.info("="*80)
        
        # Initialize MCP client
        config = get_config('config.yaml')
        mcp = MCPClient(config)
        
        # Check health
        logger.info("\n1. Checking MCP health...")
        is_healthy = await mcp.check_health()
        logger.info(f"   Health status: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        
        if not is_healthy:
            logger.error("MCP is not healthy. Cannot proceed.")
            return False
        
        # Test vector search with different queries
        queries = [
            "cron job failure error resolution fix",
            "NullReferenceError customer data",
            "database connection timeout",
            "error failure",
            ""  # Empty query to get all
        ]
        
        for i, query in enumerate(queries, 1):
            logger.info(f"\n{i}. Testing query: '{query}'")
            results = await mcp.vector_search(query, top_k=10)
            
            logger.info(f"   Results type: {type(results)}")
            logger.info(f"   Results count: {len(results) if isinstance(results, list) else 'N/A'}")
            
            if results and len(results) > 0:
                logger.info(f"   ✅ Got {len(results)} results!")
                logger.info(f"   First result keys: {results[0].keys() if isinstance(results[0], dict) else 'N/A'}")
                logger.info(f"   First result sample:")
                
                first = results[0]
                for key, value in (first.items() if isinstance(first, dict) else []):
                    if isinstance(value, str) and len(value) > 100:
                        logger.info(f"      {key}: {value[:100]}...")
                    else:
                        logger.info(f"      {key}: {value}")
                
                # Try to extract data
                content = first.get('content', first.get('data', {}))
                metadata = first.get('metadata', {})
                logger.info(f"\n   Content type: {type(content)}")
                logger.info(f"   Metadata type: {type(metadata)}")
                
                if isinstance(content, dict):
                    logger.info(f"   Content keys: {content.keys()}")
                if isinstance(metadata, dict):
                    logger.info(f"   Metadata keys: {metadata.keys()}")
                
                break  # Stop after first successful query
            else:
                logger.warning(f"   ⚠️  No results returned")
        
        logger.info("\n" + "="*80)
        logger.info("Test Complete")
        logger.info("="*80)
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_historical())
    sys.exit(0 if success else 1)

# Made with Bob
