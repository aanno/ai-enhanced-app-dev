
import pytest
import pytest_asyncio
from mcp_client import MCPTestClient

# Server connection parameters (configure as needed)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8002  # Updated to match current working server port


@pytest_asyncio.fixture
async def mcp_client():
    """Fixture providing a test client connected to the server"""
    async with MCPTestClient(SERVER_HOST, SERVER_PORT) as client:
        yield client


@pytest.mark.asyncio
async def test_server_connection(mcp_client):
    """Test basic server connection and endpoint listing"""
    tools = await mcp_client.list_tools()
    resources = await mcp_client.list_resources()

    # Test tools that actually exist in our server
    assert "example:greet" in tools
    assert "example:greetingJson" in tools
    
    # Test resources that actually exist in our server
    assert "greeting" in resources
    assert "server-status" in resources
    assert "example:greetingJson:args:schema" in resources
    assert "example:greetingJson:result:schema" in resources


@pytest.mark.asyncio
async def test_greet_tool_invocation(mcp_client):
    """Test basic greet tool invocation"""
    # Test basic greeting
    response = await mcp_client.call_tool("example:greet", {"name": "Alice"})
    assert not response["isError"]
    assert len(response["content"]) > 0
    assert "Hello, Alice!" in response["content"][0]

    # Test default parameter (should use "World")
    response = await mcp_client.call_tool("example:greet", {})
    assert not response["isError"]
    assert "Hello, World!" in response["content"][0]
    
    # Test language parameter
    response = await mcp_client.call_tool("example:greet", {"name": "Alice", "language": "fr"})
    assert not response["isError"]
    assert "Bonjour, Alice!" in response["content"][0]
    
    # Test with user info
    response = await mcp_client.call_tool("example:greet", {
        "name": "Bob", 
        "language": "de",
        "user_info": {"role": "Developer", "team": "Backend"}
    })
    assert not response["isError"]
    content = response["content"][0]
    assert "Hallo, Bob!" in content
    assert "Role: Developer" in content
    assert "Team: Backend" in content


@pytest.mark.asyncio
async def test_greeting_json_tool_invocation(mcp_client):
    """Test JSON greeting tool invocation"""
    # Test valid input
    response = await mcp_client.call_tool("example:greetingJson", {"name": "TestUser"})
    assert not response["isError"]
    assert "structuredContent" in response
    assert response["structuredContent"]["greeting"] == "Hello, TestUser!"
    assert "timestamp" in response["structuredContent"]

    # Test with language preference
    response = await mcp_client.call_tool("example:greetingJson", {
        "name": "TestUser",
        "preferences": {"language": "fr"}
    })
    assert not response["isError"]
    assert response["structuredContent"]["greeting"] == "Bonjour, TestUser!"

    # Test with details
    response = await mcp_client.call_tool("example:greetingJson", {
        "name": "TestUser", 
        "include_details": True,
        "preferences": {"language": "de", "format": "detailed"}
    })
    assert not response["isError"]
    struct = response["structuredContent"]
    assert struct["greeting"] == "Hallo, TestUser!"
    assert "user" in struct
    assert struct["user"]["name"] == "TestUser"
    assert struct["user"]["preferences"]["language"] == "de"
    assert "server_info" in struct


@pytest.mark.asyncio
async def test_greeting_json_validation_errors(mcp_client):
    """Test JSON greeting tool validation errors"""
    # Test missing required field
    response = await mcp_client.call_tool("example:greetingJson", {"invalid": "data"})
    assert response["isError"]
    assert len(response["content"]) > 0
    assert "validation error" in response["content"][0]
    assert "name" in response["content"][0]


@pytest.mark.asyncio
async def test_resource_access(mcp_client):
    """Test resource reading"""
    # Test existing text resource
    content = await mcp_client.read_resource("greeting")
    assert "Hello! This is a sample text resource for MCP testing." in content

    # Test JSON status resource
    content = await mcp_client.read_resource("server-status")
    import json
    status_data = json.loads(content)
    assert "server" in status_data
    assert status_data["server"]["name"] == "mcp-server-with-coverage"

    # Test JSON schema resource
    content = await mcp_client.read_resource("example:greetingJson:args:schema")
    schema_data = json.loads(content)
    assert schema_data["type"] == "object"
    assert "name" in schema_data["properties"]
    assert "name" in schema_data["required"]

    # Test non-existent resource
    try:
        await mcp_client.read_resource("non_existent")
        pytest.fail("Should not reach here for non-existent resource")
    except Exception as e:
        assert "not found" in str(e).lower()


@pytest.mark.asyncio
async def test_language_support(mcp_client):
    """Test language support in greetings"""
    languages = {
        "en": "Hello",
        "es": "Hola", 
        "fr": "Bonjour",
        "de": "Hallo"
    }
    
    for lang_code, expected_greeting in languages.items():
        # Test text tool (now working correctly)
        response = await mcp_client.call_tool("example:greet", {
            "name": "TestUser",
            "language": lang_code
        })
        assert not response["isError"]
        assert f"{expected_greeting}, TestUser!" in response["content"][0]
        
        # Test JSON tool
        response = await mcp_client.call_tool("example:greetingJson", {
            "name": "TestUser",
            "preferences": {"language": lang_code}
        })
        assert not response["isError"]
        assert response["structuredContent"]["greeting"] == f"{expected_greeting}, TestUser!"


@pytest.mark.asyncio
async def test_endpoint_discovery(mcp_client):
    """Verify that endpoint discovery works correctly"""
    tools = await mcp_client.list_tools()
    resources = await mcp_client.list_resources()

    # Verify we have the expected tools
    expected_tools = ["example:greet", "example:greetingJson"]
    for tool in expected_tools:
        assert tool in tools

    # Verify we have the expected resources
    expected_resources = [
        "greeting", 
        "server-status",
        "example:greetingJson:args:schema",
        "example:greetingJson:result:schema"
    ]
    for resource in expected_resources:
        assert resource in resources


@pytest.mark.asyncio
async def test_mcp_error_handling(mcp_client):
    """Test MCP-compliant error handling"""
    # Test tool-level error (validation failure)
    response = await mcp_client.call_tool("example:greetingJson", {"badfield": 123})
    assert response["isError"] == True
    assert len(response["content"]) > 0
    error_msg = response["content"][0]
    assert "Input validation error" in error_msg
    assert "name" in error_msg  # Should mention the missing required field

    # Test successful call for comparison
    response = await mcp_client.call_tool("example:greetingJson", {"name": "TestUser"})
    assert response["isError"] == False
    assert "structuredContent" in response
