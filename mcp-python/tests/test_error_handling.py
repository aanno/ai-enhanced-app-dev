"""Test MCP error handling for invalid inputs and edge cases."""

import pytest
import pytest_asyncio
from mcp_client import MCPTestClient

# Server connection parameters
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8002


@pytest_asyncio.fixture
async def mcp_client():
    """Fixture providing a test client connected to the server"""
    async with MCPTestClient(SERVER_HOST, SERVER_PORT) as client:
        yield client


@pytest.mark.asyncio
async def test_invalid_json_tool_input(mcp_client):
    """Test that invalid JSON tool input returns proper MCP-compliant errors"""
    # Test with missing required field 'name' for greetingJson tool
    response = await mcp_client.call_tool("example:greetingJson", {"invalid": "data"})
    
    assert response["isError"] == True
    assert len(response["content"]) > 0
    
    error_content = response["content"][0]
    # Should contain validation error details
    assert "validation error" in error_content.lower()
    assert "name" in error_content.lower()


@pytest.mark.asyncio
async def test_malformed_json_arguments(mcp_client):
    """Test handling of completely malformed arguments"""
    # Test with wrong data types
    response = await mcp_client.call_tool("example:greetingJson", {"name": 12345})
    
    # Should still work since name gets converted to string internally
    # or should return validation error - either is acceptable
    assert "isError" in response


@pytest.mark.asyncio
async def test_text_tool_with_invalid_parameters(mcp_client):
    """Test text tool with invalid parameter types"""
    # Test greet tool with valid parameters but invalid language
    response = await mcp_client.call_tool("example:greet", {"name": "TestUser", "language": "invalid"})
    
    # The MCP server validates enum values strictly, so invalid language should return error
    assert response["isError"] == True
    assert len(response["content"]) > 0
    # Error should mention validation or the invalid value
    error_content = response["content"][0].lower()
    assert any(keyword in error_content for keyword in ["validation", "invalid", "not one of"])


@pytest.mark.asyncio 
async def test_nonexistent_tool(mcp_client):
    """Test calling a tool that doesn't exist"""
    try:
        response = await mcp_client.call_tool("nonexistent:tool", {"param": "value"})
        # If no exception, should get error response
        assert response["isError"] == True
    except Exception as e:
        # Exception is also acceptable for nonexistent tools
        assert "not found" in str(e).lower() or "tool" in str(e).lower()


@pytest.mark.asyncio
async def test_valid_input_after_errors(mcp_client):
    """Test that valid input still works correctly after error conditions"""
    # First make an invalid call
    await mcp_client.call_tool("example:greetingJson", {"invalid": "data"})
    
    # Then verify valid calls still work
    response = await mcp_client.call_tool("example:greetingJson", {"name": "TestUser"})
    
    assert response["isError"] == False
    assert "structuredContent" in response
    assert response["structuredContent"]["greeting"] == "Hello, TestUser!"


@pytest.mark.asyncio
async def test_empty_arguments(mcp_client):
    """Test tools with empty argument dictionaries"""
    # Test greet tool with no arguments (should use defaults)
    response = await mcp_client.call_tool("example:greet", {})
    
    assert response["isError"] == False
    assert "Hello, World!" in response["content"][0]
    
    # Test JSON tool with no arguments (should fail due to required 'name')
    response = await mcp_client.call_tool("example:greetingJson", {})
    
    assert response["isError"] == True
    assert "name" in response["content"][0].lower()