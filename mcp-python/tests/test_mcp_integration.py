import pytest
import asyncio
from typing import AsyncIterator
from mcp.client import Client
from mcp.model import ToolInvocation, ResourceRequest
from mcp_server import create_mcp_server

@pytest.fixture
async def mcp_server() -> AsyncIterator[Any]:
    server = create_mcp_server()
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
        ToolInvocation(
            tool="example:greet",
            parameters={"name": "Alice"}
        )
    )
    assert "Hello, Alice!" in response.result

@pytest.mark.asyncio
async def test_resource_request(mcp_server: Any, mcp_client: Client) -> None:
    response = await mcp_client.read_resource(
        ResourceRequest(
            resource="example:data",
            parameters={}
        )
    )
    assert response.result["message"] == "Resource data"

@pytest.mark.asyncio
async def test_list_endpoints(mcp_server: Any, mcp_client: Client) -> None:
    # Test tool listing
    tools_response = await mcp_client.call_tool(
        ToolInvocation(
            tool="mcp:list_tools",
            parameters={}
        )
    )
    assert "example:greet" in tools_response.result["tools"]

    # Test resource listing
    resources_response = await mcp_client.call_tool(
        ToolInvocation(
            tool="mcp:list_resources",
            parameters={}
        )
    )
    assert "example:data" in resources_response.result["resources"]
