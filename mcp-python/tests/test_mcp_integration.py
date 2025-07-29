import pytest
import asyncio
from typing import AsyncIterator
from mcp_server.mcp_server import create_mcp_server
from mcp_client import MCPClient

@pytest.fixture
async def mcp_server() -> AsyncIterator[Any]:
    server = await create_mcp_server(port=8002)
    await server.start('127.0.0.1', 8002)
    yield server
    await server.stop()

@pytest.fixture
async def mcp_client() -> AsyncIterator[MCPClient]:
    client = MCPClient(port=8002)
    await client.connect()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_tool_call(mcp_server: Any, mcp_client: MCPClient) -> None:
    response = await mcp_client.call_tool("example:greet", b"Bob")
    assert "Hello, Bob!" in response

@pytest.mark.asyncio
async def test_resource_read(mcp_server: Any, mcp_client: MCPClient) -> None:
    response = await mcp_client.read_resource("example:data")
    assert "Resource data" in response

@pytest.mark.asyncio
async def test_list_tools(mcp_server: Any, mcp_client: MCPClient) -> None:
    tools = await mcp_client.list_tools()
    assert "example:greet" in tools

@pytest.mark.asyncio
async def test_client_server_interaction(mcp_server: Any) -> None:
    async with MCPClient(port=8002) as client:
        await client.connect()
        response = await client.call_tool("example:greet", b"Eve")
        assert "Hello, Eve!" in response
