
import pytest
from test_client import MCPTestClient

# Server connection parameters (configure as needed)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8001  # Should match your server's port


@pytest.fixture
async def mcp_client():
    """Fixture providing a test client connected to the server"""
    async with MCPTestClient(SERVER_HOST, SERVER_PORT) as client:
        yield client


@pytest.mark.asyncio
async def test_server_connection(mcp_client):
    """Test basic server connection and endpoint listing"""
    tools = await mcp_client.list_tools()
    resources = await mcp_client.list_resources()

    assert "example:greet" in tools
    assert "greeting" in resources
    assert "help" in resources
    assert "about" in resources


@pytest.mark.asyncio
async def test_tool_invocation(mcp_client):
    """Test tool invocation with parameters"""
    # Test valid input
    response = await mcp_client.call_tool("example:greet", {"name": "Alice"})
    assert "Hello, Alice!" in response.get("result", "")

    # Test default parameter
    response = await mcp_client.call_tool("example:greet", {})
    assert "Hello, World!" in response.get("result", "")

    # Test invalid input
    response = await mcp_client.call_tool("example:greet", "invalid")
    assert "error" in response


@pytest.mark.asyncio
async def test_resource_access(mcp_client):
    """Test resource reading"""
    # Test existing resource
    content = await mcp_client.read_resource("greeting")
    assert "Hello! This is a sample text resource." in content

    # Test another resource
    content = await mcp_client.read_resource("help")
    assert "This server provides" in content

    # Test non-existent resource (should be handled by your server implementation)
    try:
        await mcp_client.read_resource("non_existent")
        pytest.fail("Should not reach here for non-existent resource")
    except Exception as e:
        assert "404" in str(e) or "not found" in str(e).lower()


@pytest.mark.asyncio
async def test_endpoint_discovery(mcp_client):
    """Verify that endpoint discovery works correctly"""
    tools = await mcp_client.list_tools()
    resources = await mcp_client.list_resources()

    # Verify tool endpoints
    assert "example:greet" in tools
    assert "mcp:list_tools" in tools
    assert "mcp:list_resources" in tools

    # Verify resource endpoints
    assert "greeting" in resources
    assert "help" in resources
    assert "about" in resources
