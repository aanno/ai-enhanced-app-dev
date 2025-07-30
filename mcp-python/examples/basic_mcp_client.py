#!/usr/bin/env python3
"""
Basic MCP Client Example

This example demonstrates how to connect to an MCP server and perform
basic operations like listing tools/resources and calling tools.

Usage:
    python examples/basic_mcp_client.py

Make sure the MCP server is running first:
    python -m mcp_server.mcp_server --port 8002
"""

import asyncio
import json
from datetime import timedelta

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    print("🚀 Basic MCP Client Example")
    print("=" * 40)

    server_url = "http://localhost:8002/mcp"

    try:
        async with streamablehttp_client(
            url=server_url,
            timeout=timedelta(seconds=30),
        ) as (read_stream, write_stream, get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                print("✅ Connected to MCP server")

                # Step 1: List available tools
                print("\n📋 Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools if hasattr(tools_result, 'tools') else []
                print(f"Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  • {tool.name}: {tool.description}")

                # Step 2: List available resources
                print("\n📋 Listing available resources...")
                resources_result = await session.list_resources()
                resources = resources_result.resources if hasattr(resources_result, 'resources') else []
                print(f"Found {len(resources)} resources:")
                for resource in resources:
                    print(f"  • {resource.name}: {resource.description}")

                # Step 3: Call a text-based tool
                print("\n🔧 Calling text tool (example:greet)...")
                try:
                    result = await session.call_tool("example:greet", {"name": "World", "language": "en"})
                    if hasattr(result, 'content') and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                print(f"Response: {content.text}")
                except Exception as e:
                    print(f"❌ Text tool call failed: {e}")

                # Step 4: Call a JSON tool
                print("\n🔧 Calling JSON tool (example:greetingJson)...")
                try:
                    result = await session.call_tool("example:greetingJson", {
                        "name": "Alice",
                        "include_details": True,
                        "preferences": {
                            "language": "fr",
                            "format": "detailed"
                        }
                    })
                    if hasattr(result, 'content') and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                print("Raw response:", content.text)
                                try:
                                    parsed = json.loads(content.text)
                                    print("✅ Response is valid JSON")
                                    formatted = json.dumps(parsed, indent=2)
                                    print(f"Formatted response:\n{formatted}")
                                except json.JSONDecodeError:
                                    print("❌ Response is not valid JSON")
                except Exception as e:
                    print(f"❌ JSON tool call failed: {e}")

                # Step 5: Read a resource
                print("\n📄 Reading a resource...")
                try:
                    # Read the greeting resource
                    greeting_resource = None
                    for resource in resources:
                        if resource.name == "greeting":
                            greeting_resource = resource
                            break

                    if greeting_resource:
                        resource_result = await session.read_resource(greeting_resource.uri)
                        if hasattr(resource_result, 'contents') and resource_result.contents:
                            for resource_content in resource_result.contents:
                                if hasattr(resource_content, 'text'):
                                    print(f"Resource content: {resource_content.text}")
                    else:
                        print("❌ Greeting resource not found")
                except Exception as e:
                    print(f"❌ Resource read failed: {e}")

                print("\n🎉 Basic MCP client example completed!")

    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("💡 Make sure the server is running: python -m mcp_server.mcp_server --port 8002")


if __name__ == "__main__":
    asyncio.run(main())