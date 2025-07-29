import asyncio
from typing import Optional, Any
from mcp.client import Client
from mcp.message import ToolRequest, ResourceRequest

class MCPClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 8001):
        self.client = Client(host, port, protocol="streamingHttp")
    
    async def connect(self) -> None:
        await self.client.connect()
    
    async def close(self) -> None:
        await self.client.close()
    
    async def call_tool(self, tool_name: str, body: Optional[bytes] = None) -> Any:
        response = await self.client.call_tool(
            ToolRequest(
                to=tool_name,
                body=body or b''
            )
        )
        return response.body.decode()
    
    async def read_resource(self, resource_name: str) -> Any:
        response = await self.client.read_resource(
            ResourceRequest(
                method="GET",
                to=resource_name
            )
        )
        return response.body.decode()
    
    async def list_tools(self) -> list[str]:
        response = await self.client.call_tool(
            ToolRequest(
                to="mcp:list_tools",
                body=b''
            )
        )
        return response.body.decode()

async def main():
    client = MCPClient(port=8001)
    try:
        await client.connect()
        
        # Call tool example
        greeting = await client.call_tool("example:greet", b"Alice")
        print(f"Tool response: {greeting}")
        
        # Read resource example
        resource_data = await client.read_resource("example:data")
        print(f"Resource data: {resource_data}")
        
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {tools}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
