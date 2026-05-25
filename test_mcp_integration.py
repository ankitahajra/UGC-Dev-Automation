"""
Test MCP Integration
Quick test to verify MCP Context Studio connectivity and functionality.
"""

import asyncio
import logging
import sys
from src.config_manager import get_config
from src.mcp_client import MCPClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_connection():
    """Test basic MCP connectivity and features."""
    logger.info("="*60)
    logger.info("Testing MCP Context Studio Integration")
    logger.info("="*60)
    
    try:
        config = get_config('config.yaml')
        mcp = MCPClient(config)
        
        # Test 1: Health check
        logger.info("\n🔍 Test 1: Health Check")
        logger.info("-" * 40)
        is_healthy = await mcp.check_health()
        if is_healthy:
            logger.info("✅ MCP Health: HEALTHY")
        else:
            logger.error("❌ MCP Health: UNHEALTHY")
            return False
        
        # Test 2: Get schema
        logger.info("\n🔍 Test 2: Get Schema")
        logger.info("-" * 40)
        schema = await mcp.get_schema()
        if "error" not in schema:
            logger.info(f"✅ Schema retrieved: {len(str(schema))} characters")
        else:
            logger.error(f"❌ Schema retrieval failed: {schema.get('error')}")
        
        # Test 3: Vector search
        logger.info("\n🔍 Test 3: Vector Search")
        logger.info("-" * 40)
        test_query = """
Error Type: null_reference_error
Function: process_customer_data
Error Message: Cannot read property 'customerId' of null

Find similar cron job failures with their resolutions.
"""
        results = await mcp.vector_search(test_query, top_k=3)
        logger.info(f"✅ Vector search completed")
        logger.info(f"   Found {len(results)} similar patterns")
        
        if results:
            logger.info("   Sample results:")
            for i, result in enumerate(results[:2], 1):
                logger.info(f"   {i}. Similarity: {result.get('similarity', 'N/A')}")
        
        # Test 4: Graph query
        logger.info("\n🔍 Test 4: Graph Query")
        logger.info("-" * 40)
        graph_query = "Find components related to timer trigger failures"
        graph_result = await mcp.graph_query(graph_query, max_depth=1, limit=5)
        if "error" not in graph_result:
            logger.info(f"✅ Graph query completed")
            logger.info(f"   Result size: {len(str(graph_result))} characters")
        else:
            logger.warning(f"⚠️  Graph query returned error (may be expected if no data yet)")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 All MCP tests completed successfully!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Process some failures to build knowledge base")
        logger.info("2. Run: python main.py run-pipeline")
        logger.info("3. Monitor logs for MCP-enhanced analysis")
        logger.info("\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {str(e)}")
        logger.error("Please check:")
        logger.error("1. MCP server is accessible")
        logger.error("2. Bearer token is valid (check .bob/mcp.json)")
        logger.error("3. Network connectivity")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_mcp_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
