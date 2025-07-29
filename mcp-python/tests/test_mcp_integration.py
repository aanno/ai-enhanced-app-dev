import pytest
import asyncio
import json
from typing import AsyncIterator, Any
from mcp.client.client import Client
from mcp.types import ToolRequest, ReadResourceRequest
from mcp_server import create_mcp_server

@pytest.fixture
async def mcp_server() -> AsyncIterator[Any]:
    server = await create_mcp_server()
    await server.start('127.0.0.1', 8002)
    yield server
    await server.stop()

@pytest.fixture
async def mcp_client() -> AsyncIterator[Client]:
    client = Client('127.0.0.1', 8002)
    await client.connect()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_tool_invocation(mcp_server: Any, mcp_client: Client) -> None:
    response = await mcp_client.call_tool(
        ToolRequest(
            to="example:greet",
            body=json.dumps({"name": "Alice"}).encode()
        )
    )
    assert b"Hello, Alice" in response.body

@pytest.mark.asyncio
async def test_resource_request(mcp_server: Any, mcp_client: Client) -> None:
    response = await mcp_client.read_resource(
        ReadResourceRequest(
            resource="example:data",
            headers={}
        )
    )
    assert b"Resource data" in response.body

@pytest.mark.asyncio
async def test_list_endpoints(mcp_server: Any, mcp_client: Client) -> None:
    # Test tool listing
    tools_response = await mcp_client.call_tool(
        ToolRequest(
            to="mcp:list_tools",
            body=b""
        )
    )
    assert b"example:greet" in tools_response.body

    # Test resource listing
    resources_response = await mcp_client.call_tool(
        ToolRequest(
            to="mcp:list_resources",
            body=b""
        )
    )
    assert b"example:data" in resources_response.body
