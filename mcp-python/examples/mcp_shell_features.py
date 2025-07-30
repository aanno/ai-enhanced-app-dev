#!/usr/bin/env python3
"""
MCP Shell Features Example

This example demonstrates advanced MCP shell functionality including:
- JSON formatting and syntax highlighting
- Schema validation  
- Tool metadata access
- Error handling

Usage:
    python examples/mcp_shell_features.py

Make sure the MCP server is running first:
    python -m mcp_server.mcp_server --port 8002
"""

import asyncio
import json
from datetime import timedelta
from typing import Optional, Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Note: This example demonstrates shell features without importing the actual shell
# to avoid dependency issues. In practice, you would import from examples.mcp_shell


class SimpleMCPShellDemo:
    """Simplified MCP shell to demonstrate features."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.tools: list[Any] = []
        self.resources: list[Any] = []
        self.schemas: dict[str, Any] = {}

    async def connect_and_setup(self):
        """Connect to server and populate tools/resources/schemas."""
        async with streamablehttp_client(
            url=self.server_url,
            timeout=timedelta(seconds=30),
        ) as (read_stream, write_stream, get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                self.session = session
                await session.initialize()
                await self.refresh_server_info()
                return session

    async def refresh_server_info(self):
        """Refresh tools, resources, and schemas."""
        if not self.session:
            return

        # Get tools
        tools_result = await self.session.list_tools()
        self.tools = tools_result.tools if hasattr(tools_result, 'tools') else []

        # Get resources  
        resources_result = await self.session.list_resources()
        self.resources = resources_result.resources if hasattr(resources_result, 'resources') else []

        # Cache schemas
        await self.cache_schemas()

    async def cache_schemas(self):
        """Cache JSON schemas from tool metadata."""
        for tool in self.tools:
            tool_data = tool.model_dump()
            meta = tool_data.get('meta')

            if meta:
                # Cache argument schema
                if 'args_schema_resource' in meta:
                    schema_resource_name = meta['args_schema_resource']
                    await self.fetch_schema(f"{tool.name}:args", schema_resource_name)

    async def fetch_schema(self, schema_key: str, schema_resource_name: str):
        """Fetch and cache a JSON schema."""
        if schema_key in self.schemas or not self.session:
            return

        schema_resource = next((r for r in self.resources if r.name == schema_resource_name), None)
        if schema_resource:
            try:
                result = await self.session.read_resource(schema_resource.uri)
                if hasattr(result, 'contents') and result.contents:
                    for content in result.contents:
                        if hasattr(content, 'text'):
                            schema_data = json.loads(content.text)
                            self.schemas[schema_key] = schema_data
                            print(f"  ✅ Cached schema for {schema_key}")
                            break
            except Exception as e:
                print(f"  ❌ Failed to fetch schema {schema_resource_name}: {e}")

    def format_json_output(self, content: str) -> str:
        """Format JSON output with syntax highlighting."""
        try:
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2)

            try:
                from pygments import highlight
                from pygments.formatters import TerminalFormatter
                from pygments.lexers import JsonLexer

                lexer = JsonLexer()
                formatter = TerminalFormatter()
                highlighted = highlight(formatted, lexer, formatter).rstrip()
                return highlighted
            except ImportError:
                print("  💡 Install pygments for syntax highlighting: pip install pygments")
                return formatted
        except json.JSONDecodeError:
            return content

    def validate_json_with_schema(self, data: dict, schema_key: str) -> list:
        """Validate JSON data against a cached schema."""
        warnings = []
        if schema_key not in self.schemas:
            warnings.append(f"⚠️  Schema not available for validation: {schema_key}")
            return warnings

        try:
            import jsonschema
            jsonschema.validate(data, self.schemas[schema_key])
            print(f"  ✅ Validation passed for {schema_key}")
        except jsonschema.ValidationError as e:
            warnings.append(f"⚠️  JSON validation warning: {e.message}")
        except Exception as e:
            warnings.append(f"⚠️  Schema validation error: {e}")

        return warnings


async def main():
    print("🚀 MCP Shell Features Example")
    print("=" * 50)

    server_url = "http://localhost:8002/mcp"
    shell = SimpleMCPShellDemo(server_url)

    try:
        async with shell.connect_and_setup():
            print(f"✅ Connected! Found {len(shell.tools)} tools and {len(shell.resources)} resources")
            print(f"📋 Cached schemas: {list(shell.schemas.keys())}")

            # Feature 1: JSON formatting and highlighting
            print("\n🎨 Feature 1: JSON formatting and highlighting")
            test_json = '{"greeting":"Hello, World!","timestamp":"2025-07-30T10:00:00","user":{"name":"Demo","preferences":{"language":"en"}}}'
            print("Raw JSON:", test_json)
            formatted = shell.format_json_output(test_json)
            print("Formatted JSON:")
            print(formatted)

            # Feature 2: Schema validation
            print("\n📋 Feature 2: Schema validation")
            test_valid_args = {"name": "TestUser"}
            test_invalid_args = {"invalid_field": "value"}

            print("Validating valid arguments...")
            warnings = shell.validate_json_with_schema(test_valid_args, "example:greetingJson:args")
            for warning in warnings:
                print(warning)

            print("\nValidating invalid arguments...")  
            warnings = shell.validate_json_with_schema(test_invalid_args, "example:greetingJson:args")
            for warning in warnings:
                print(warning)

            # Feature 3: Tool metadata access
            print("\n🔧 Feature 3: Tool metadata access")
            for tool in shell.tools:
                print(f"\nTool: {tool.name}")
                print(f"  Description: {tool.description}")
                
                tool_data = tool.model_dump()
                meta = tool_data.get('meta')
                if meta:
                    print(f"  Metadata:")
                    for key, value in meta.items():
                        print(f"    {key}: {value}")

            # Feature 4: Actual tool calls with validation
            print("\n🚀 Feature 4: Tool calls with validation")
            
            print("\nCalling greetingJson with valid input...")
            try:
                if shell.session:
                    result = await shell.session.call_tool("example:greetingJson", {
                        "name": "FeatureDemo",
                        "include_details": True,
                        "preferences": {"language": "es", "format": "detailed"}
                    })
                    
                    if hasattr(result, 'content') and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                print("Response:")
                                formatted_response = shell.format_json_output(content.text)
                                print(formatted_response)
            except Exception as e:
                print(f"❌ Tool call failed: {e}")

            print("\n🎉 MCP shell features demonstration completed!")

    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("💡 Make sure the server is running: python -m mcp_server.mcp_server --port 8002")


if __name__ == "__main__":
    asyncio.run(main())