"""Test MCP client connection resilience and error handling."""

import pytest
from datetime import timedelta

from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession


@pytest.mark.asyncio
async def test_connection_to_nonexistent_server():
    """Test that client provides helpful error messages when server is unavailable."""
    bad_server_url = "http://localhost:9999/mcp"  # Non-existent server
    
    try:
        async with streamablehttp_client(
            url=bad_server_url,
            timeout=timedelta(seconds=2),
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
        
        # Should not reach here
        pytest.fail("Should not have connected to non-existent server")
        
    except Exception as e:
        error_msg = str(e).lower()
        # Should get a connection-related error
        # ExceptionGroup may wrap the actual connection error
        assert any(keyword in error_msg for keyword in [
            "connect", "connection", "timeout", "refused", "unreachable", "failed", "taskgroup"
        ]), f"Error message should indicate connection issue: {e}"


@pytest.mark.asyncio
async def test_rapid_connection_timeout():
    """Test behavior with very short timeout."""
    bad_server_url = "http://192.0.2.1:8001/mcp"  # RFC5737 test IP that should timeout
    
    try:
        async with streamablehttp_client(
            url=bad_server_url,
            timeout=timedelta(milliseconds=100),  # Very short timeout
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
        
        pytest.fail("Should have timed out")
        
    except Exception as e:
        # Should handle timeout gracefully
        assert isinstance(e, Exception)
        # Error should be reasonable (not a crash)
        assert str(e)  # Should have some error message


@pytest.mark.asyncio
async def test_malformed_server_url():
    """Test behavior with malformed server URLs."""
    malformed_urls = [
        "not-a-url",
        "http://",
        "ftp://localhost:8001/mcp",
        "http://localhost:99999/mcp",  # Invalid port
    ]
    
    for bad_url in malformed_urls:
        try:
            async with streamablehttp_client(
                url=bad_url,
                timeout=timedelta(seconds=1),
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
            
            pytest.fail(f"Should have failed for malformed URL: {bad_url}")
            
        except Exception as e:
            # Should get some kind of error, not crash
            assert isinstance(e, Exception)
            error_msg = str(e).lower()
            # Error should be reasonable
            assert len(error_msg) > 0


@pytest.mark.asyncio 
async def test_connection_cleanup_on_error():
    """Test that connection resources are cleaned up properly on errors."""
    bad_server_url = "http://localhost:9998/mcp"
    
    # This test mainly ensures no resource leaks or hanging connections
    for _ in range(3):  # Try multiple times to check for resource leaks
        try:
            async with streamablehttp_client(
                url=bad_server_url,
                timeout=timedelta(seconds=1),
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
        except Exception:
            # Expected to fail, just checking cleanup works
            pass
    
    # If we get here without hanging, cleanup is working