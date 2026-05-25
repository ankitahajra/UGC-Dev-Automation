"""
MCP Client Wrapper for Context Studio Integration
Provides async interface to Context Studio MCP server.
"""

import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with Context Studio via MCP."""
    
    def __init__(self, config):
        """
        Initialize MCP client.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        
        # MCP Configuration from .bob/mcp.json
        self.mcp_url = "https://servicesessentials.ibm.com/mcp-gateway/service/gateway/servers/8ccdd203bdee4014b08e82eedb6046e2/mcp"
        self.bearer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaHJhZGRoYS5wYXJpa2gxQGlibS5jb20iLCJqdGkiOiJkZWU2ZTlkNi1hM2E5LTRkMTgtOGQ1Yy0yMTI2YmExNDc2NGMiLCJ0b2tlbl91c2UiOiJhcGkiLCJpYXQiOjE3NzkxMDc0NTcsImlzcyI6Im1jcGdhdGV3YXkiLCJhdWQiOiJtY3BnYXRld2F5LWFwaSIsInVzZXIiOnsiZW1haWwiOiJzaHJhZGRoYS5wYXJpa2gxQGlibS5jb20iLCJmdWxsX25hbWUiOiJBUEkgVG9rZW4gVXNlciIsImlzX2FkbWluIjp0cnVlLCJhdXRoX3Byb3ZpZGVyIjoiYXBpX3Rva2VuIn0sInRlYW1zIjpudWxsLCJzY29wZXMiOnsic2VydmVyX2lkIjoiOGNjZGQyMDNiZGVlNDAxNGIwOGU4MmVlZGI2MDQ2ZTIiLCJwZXJtaXNzaW9ucyI6W10sImlwX3Jlc3RyaWN0aW9ucyI6W10sInRpbWVfcmVzdHJpY3Rpb25zIjp7fX0sImV4cCI6MTgxMDY0MzQ1N30.L5uNOwPaRllbuwRX0pIbYh3fnhD5kY_gOGgv3soMsZY"
        
        # Context configuration
        self.context_id = config.get('mcp.context_id', 'ctx_7c3822579dfd')
        self.agent_persona = config.get('mcp.agent_persona', 'FailureAnalyzer')
        
        # Headers for MCP requests
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        logger.info("MCP Client initialized for Context Studio")
    
    async def _call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool via HTTP.
        
        Args:
            tool_name: Name of the MCP tool
            arguments: Tool arguments
            
        Returns:
            Tool response
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Update headers to accept JSON
            headers = self.headers.copy()
            headers["Accept"] = "application/json"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.mcp_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"MCP tool {tool_name} executed successfully")
                        # Extract result from JSON-RPC response
                        if "result" in result:
                            return result["result"]
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"MCP tool call failed: {error_text}")
                        return {"error": error_text, "status": response.status}
                        
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {"error": str(e)}
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search for similar failures.
        
        Args:
            query: Search query (error message, stack trace, etc.)
            top_k: Number of results to return
            
        Returns:
            List of similar failures with context
        """
        logger.info(f"Performing vector search: {query[:100]}...")
        
        result = await self._call_mcp_tool(
            "context-broker-vector-query",
            {
                "context_id": self.context_id,
                "AgentPersona": self.agent_persona,
                "query": query,
                "top_k": top_k
            }
        )
        
        return result.get("results", [])
    
    async def graph_query(
        self,
        query: str,
        max_depth: int = 1,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Perform graph traversal to understand component relationships.
        
        Args:
            query: Graph query
            max_depth: Maximum traversal depth (1 for fast response)
            limit: Maximum number of seed nodes
            
        Returns:
            Graph analysis with nodes and edges
        """
        logger.info(f"Performing graph query: {query[:100]}...")
        
        result = await self._call_mcp_tool(
            "context-broker-graph-query",
            {
                "context_id": self.context_id,
                "AgentPersona": self.agent_persona,
                "query": query,
                "max_depth": max_depth,
                "limit": limit
            }
        )
        
        return result
    
    async def hybrid_query(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        semantic_weight: float = 0.6,
        graph_weight: float = 0.4
    ) -> Dict[str, Any]:
        """
        Perform hybrid query combining vector and graph search.
        
        Args:
            query: Search query
            sources: List of sources (default: ["graph", "vector"])
            semantic_weight: Weight for semantic similarity
            graph_weight: Weight for graph relationships
            
        Returns:
            Combined results from multiple sources
        """
        if sources is None:
            sources = ["graph", "vector"]
        
        logger.info(f"Performing hybrid query: {query[:100]}...")
        
        result = await self._call_mcp_tool(
            "context-broker-hybrid-query",
            {
                "context_id": self.context_id,
                "AgentPersona": self.agent_persona,
                "query": query,
                "sources": sources,
                "semantic_weight": semantic_weight,
                "graph_weight": graph_weight
            }
        )
        
        return result
    
    async def get_schema(
        self,
        ontology_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve ontology schema from Context Studio.
        
        Args:
            ontology_name: Specific ontology name (optional)
            
        Returns:
            Schema definition
        """
        logger.info(f"Retrieving schema: {ontology_name or 'all'}")
        
        arguments = {"context_id": self.context_id}
        if ontology_name:
            arguments["ontology_name"] = ontology_name
        
        result = await self._call_mcp_tool(
            "context-broker-get-context-schema",
            arguments
        )
        
        return result
    
    async def ingest_knowledge(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Ingest new knowledge into Context Studio.
        
        Args:
            event_type: Type of event (e.g., 'successfulFixIngestion')
            payload: Event payload with source info and data
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Ingesting knowledge: {event_type}")
        
        result = await self._call_mcp_tool(
            "context-broker-post-events",
            {
                "context_id": self.context_id,
                "event_type": event_type,
                "payload": payload
            }
        )
        
        return result.get("status") == "success"
    
    async def check_health(self) -> bool:
        """
        Check if MCP Context Studio is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            result = await self.get_schema()
            return "error" not in result
        except Exception as e:
            logger.error(f"MCP health check failed: {str(e)}")
            return False


# Synchronous wrapper for backward compatibility
class MCPClientSync:
    """Synchronous wrapper for MCPClient."""
    
    def __init__(self, config):
        self.async_client = MCPClient(config)
        self._cache = {}
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Synchronous vector search with caching."""
        import asyncio
        
        # Simple cache key
        cache_key = f"{query[:100]}_{top_k}"
        if cache_key in self._cache:
            logger.info("Using cached vector search result")
            return self._cache[cache_key]
        
        result = asyncio.run(self.async_client.vector_search(query, top_k))
        self._cache[cache_key] = result
        return result
    
    def graph_query(self, query: str, max_depth: int = 1, limit: int = 5) -> Dict[str, Any]:
        """Synchronous graph query."""
        import asyncio
        return asyncio.run(self.async_client.graph_query(query, max_depth, limit))
    
    def hybrid_query(self, query: str) -> Dict[str, Any]:
        """Synchronous hybrid query."""
        import asyncio
        return asyncio.run(self.async_client.hybrid_query(query))
    
    def ingest_knowledge(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Synchronous knowledge ingestion."""
        import asyncio
        return asyncio.run(self.async_client.ingest_knowledge(event_type, payload))
    
    def check_health(self) -> bool:
        """Synchronous health check."""
        import asyncio
        return asyncio.run(self.async_client.check_health())


# Made with Bob