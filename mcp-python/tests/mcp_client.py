import asyncio
import json
from typing import Dict, Any, Optional

from mcp.client.client import Client
from mcp.types import ToolRequest, ReadResourceRequest

class MCPTestClient:
    """Client designed specifically for testing MCP servers"""
    def __init__(self, host: str = '127.0.0.1', port: int = 8000):
        self.client = Client(host, port)
    
    async def connect(self):
        """Connect to the MCP server"""
        await self.client.connect()
    
    async def close(self):
        """Close the connection"""
        await self.client.close()
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def call_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool endpoint and parse JSON response"""
        response = await self.client.call_tool(
            ToolRequest(
                to=tool_name,
                body=json.dumps(params or {}).encode()
            )
        )
        return json.loads(response.body.decode())
    
    async def read_resource(self, resource_name: str) -> str:
        """Read a resource endpoint and return text content"""
        # Construct resource URI based on server implementation
        resource_uri = f"file:///{resource_name}.txt"
        
        response = await self.client.read_resource(
            ReadResourceRequest(
                resource=resource_uri,
                headers={}
            )
        )
        return response.body.decode()
    
    async def list_tools(self) -> List[str]:
        """Get list of available tools"""
        response = await self.call_tool("mcp:list_tools")
        return response.get("tools", [])
    
    async def list_resources(self) -> List[str]:
        """Get list of available resources"""
        response = await self.call_tool("mcp:list_resources")
        return response.get("resources", [])
