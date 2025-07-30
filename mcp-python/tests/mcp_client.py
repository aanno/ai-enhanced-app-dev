import json
from typing import Any, Dict, List, Optional
from datetime import timedelta

from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession


class MCPTestClient:
    """Client designed specifically for testing MCP servers"""

    def __init__(self, host: str = '127.0.0.1', port: int = 8001):
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}/mcp"
        self.session: Optional[ClientSession] = None
        self._client_context: Any = None
        self._session_context: Optional[ClientSession] = None

    async def connect(self):
        """Connect to the MCP server"""
        self._client_context = streamablehttp_client(
            url=self.server_url,
            timeout=timedelta(seconds=30)
        )
        read_stream, write_stream, get_session_id = await self._client_context.__aenter__()
        
        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

    async def close(self):
        """Close the connection"""
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore context exit errors during cleanup
        if self._client_context:
            try:
                await self._client_context.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore context exit errors during cleanup

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def call_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool and return result info"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        result = await self.session.call_tool(tool_name, params or {})
        
        # Return structured result info
        response: Dict[str, Any] = {
            "isError": getattr(result, 'isError', False),
            "content": []
        }
        
        if hasattr(result, 'content') and result.content:
            content_list = response["content"]
            if isinstance(content_list, list):
                for content in result.content:
                    if hasattr(content, 'text'):
                        content_list.append(content.text)
        
        if hasattr(result, 'structuredContent') and result.structuredContent:
            response["structuredContent"] = result.structuredContent
            
        return response

    async def read_resource(self, resource_name: str) -> str:
        """Read a resource and return text content"""
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        # Get list of resources to find the URI
        resources_result = await self.session.list_resources()
        resource = next((r for r in resources_result.resources if r.name == resource_name), None)
        
        if not resource:
            raise RuntimeError(f"Resource '{resource_name}' not found")
            
        result = await self.session.read_resource(resource.uri)
        
        if hasattr(result, 'contents') and result.contents:
            for content in result.contents:
                if hasattr(content, 'text'):
                    return content.text
        
        return ""

    async def list_tools(self) -> List[str]:
        """Get list of available tool names"""
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        result = await self.session.list_tools()
        return [tool.name for tool in result.tools]

    async def list_resources(self) -> List[str]:
        """Get list of available resource names"""
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        result = await self.session.list_resources() 
        return [resource.name for resource in result.resources]
