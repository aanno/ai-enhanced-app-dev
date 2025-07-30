#!/usr/bin/env python3
"""
Interactive MCP client shell for testing MCP servers with streaming HTTP protocol.

This interactive shell connects to an MCP server using streamable HTTP transport
and provides commands to list tools/resources and call them interactively.
"""

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, cast

import click
import jsonschema
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    WordCompleter,
)
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from mcp_server.prompt_completer import DynamicMCPCompleter

logger = logging.getLogger(__name__)

class MCPShell:
    """Interactive MCP client shell with JSON schema support."""

    def __init__(self, server_url: str = "http://localhost:8001/mcp"):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.tools: List[types.Tool] = []
        self.resources: List[types.Resource] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}  # Cache for JSON schemas

        # Setup prompt toolkit with dynamic completer
        self.completer = DynamicMCPCompleter(self)
        self.prompt_session: PromptSession = PromptSession(
            history=FileHistory('.mcp_shell_history'),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer,
            style=Style.from_dict({
                'rprompt': 'bg:#008800 #ffffff',
                'completion-menu.completion': 'bg:#008888 #ffffff',
                'completion-menu.completion.current': 'bg:#00aaaa #000000',
                'prompt': 'bold',
            }),
            complete_while_typing=True
        )

        # Available commands
        self.commands = {
            'help': self._cmd_help,
            'list': self._cmd_list,
            'tools': self._cmd_list_tools,
            'resources': self._cmd_list_resources,
            'call': self._cmd_call_tool,
            'read': self._cmd_read_resource,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit,
        }

    async def connect(self) -> None:
        """Connect to the MCP server."""
        print(f"🔗 Connecting to MCP server at {self.server_url}...")

        try:
            async with streamablehttp_client(
                url=self.server_url,
                timeout=timedelta(seconds=30),
            ) as (read_stream, write_stream, get_session_id):
                print("🤝 Initializing MCP session...")
                async with ClientSession(read_stream, write_stream) as session:
                    self.session = session
                    print("⚡ Starting session initialization...")
                    await session.initialize()
                    print("✨ Session initialization complete!")

                    session_id = get_session_id() # if get_session_id else None
                    if session_id:
                        print(f"📋 Session ID: {session_id}")

                    # Fetch initial server capabilities
                    await self._refresh_server_info()

                    print(f"✅ Connected successfully!")
                    print(f"Found {len(self.tools)} tools and {len(self.resources)} resources")

                    # Start interactive shell
                    await self._run_interactive_shell()

        except Exception as e:
            error_msg = str(e)
            if "TaskGroup" in error_msg or "Connection" in error_msg or "connect" in error_msg.lower():
                print(f"❌ Failed to connect to MCP server at {self.server_url}")
                print("💡 Make sure the server is running. Try: python -m src.mcp_server.mcp_server")
            else:
                print(f"❌ Failed to connect: {error_msg}")
            logger.exception("Connection failed")

    async def _refresh_server_info(self) -> None:
        """Refresh the list of available tools and resources."""
        if not self.session:
            return

        try:
            # List tools
            tools_result = await self.session.list_tools()
            self.tools = tools_result.tools if hasattr(tools_result, 'tools') else []

            # List resources
            resources_result = await self.session.list_resources()
            self.resources = resources_result.resources if hasattr(resources_result, 'resources') else []

            # Cache JSON schemas from tools metadata
            await self._cache_schemas()

            logger.info(f"Found {len(self.tools)} tools and {len(self.resources)} resources")

        except Exception as e:
            error_msg = str(e)
            if "TaskGroup" in error_msg or "Connection" in error_msg or "stream" in error_msg.lower():
                print("🔌 Lost connection to server. The server may have been stopped.")
                print("💡 Server connection lost - please restart the server.")
                # Clear session to prevent further attempts but keep shell alive
                self.session = None
                self.tools = []
                self.resources = []
                self.schemas = {}
                return  # Return instead of raising, keeps shell alive
            else:
                logger.error(f"Failed to refresh server info: {e}")
                print(f"⚠️  Failed to refresh server info: {error_msg}")

    async def _cache_schemas(self) -> None:
        """Cache JSON schemas referenced in tool metadata."""
        for tool in self.tools:
            # Get meta field from model dump (works around pydantic serialization issues)
            tool_data = tool.model_dump()
            meta = tool_data.get('meta')

            if meta:
                # Cache argument schema
                if 'args_schema_resource' in meta:
                    schema_resource_name = meta['args_schema_resource']
                    await self._fetch_schema(f"{tool.name}:args", schema_resource_name)

                # Cache result schema
                if 'result_schema_resource' in meta:
                    schema_uri = meta['result_schema_resource']
                    await self._fetch_schema(f"{tool.name}:result", schema_uri)

    async def _fetch_schema(self, schema_key: str, schema_resource_name: str) -> None:
        """Fetch and cache a JSON schema from a resource name."""
        try:
            if schema_key in self.schemas or not self.session:
                return  # Already cached or no session

            # Find the resource by name
            schema_resource = next((r for r in self.resources if r.name == schema_resource_name), None)
            if not schema_resource:
                logger.warning(f"Schema resource not found: {schema_resource_name}")
                return

            result = await self.session.read_resource(schema_resource.uri)
            if hasattr(result, 'contents') and result.contents:
                # TODO: handle binary content: BlobResourceContents as well
                for content in cast(List[types.TextResourceContents], result.contents):
                    if hasattr(content, 'text'):
                        schema_data = json.loads(content.text)
                        self.schemas[schema_key] = schema_data
                        logger.info(f"✅ Cached schema for {schema_key}")
                        break
        except Exception as e:
            logger.warning(f"Failed to fetch schema {schema_resource_name}: {e}")

    def _validate_json_with_schema(self, data: Dict[str, Any], schema_key: str) -> List[str]:
        """Validate JSON data against a cached schema. Returns list of warnings."""
        warnings = []
        if schema_key not in self.schemas:
            warnings.append(f"⚠️  Schema not available for validation: {schema_key}")
            return warnings

        try:
            jsonschema.validate(data, self.schemas[schema_key])
        except jsonschema.ValidationError as e:
            warnings.append(f"⚠️  JSON validation warning: {e.message}")
        except Exception as e:
            warnings.append(f"⚠️  Schema validation error: {e}")

        return warnings

    def _format_json_output(self, content: str, mime_type: str = "application/json") -> str:
        """Format JSON output with syntax highlighting."""
        try:
            if mime_type == "application/json":
                # Parse and reformat JSON for better display
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2)

                # Try to add syntax highlighting if pygments is available
                try:
                    from pygments import highlight
                    from pygments.formatters import TerminalFormatter
                    from pygments.lexers import JsonLexer

                    lexer = JsonLexer()
                    # Always use color formatting (force colors even when not in TTY)
                    formatter = TerminalFormatter()
                    highlighted = highlight(formatted, lexer, formatter).rstrip()
                    
                    # Debug highlighting
                    logger.debug(f"Original JSON length: {len(formatted)}")
                    logger.debug(f"Highlighted length: {len(highlighted)}")
                    logger.debug(f"Contains ANSI codes: {'\\033[' in highlighted or '[' in highlighted}")
                    
                    # Debug: check if pygments returned error text instead of formatted JSON
                    # ANSI codes can make highlighted text 3-4x longer, so use a higher threshold
                    if "error" in highlighted.lower() or len(highlighted) > len(formatted) * 10:
                        logger.warning(f"Pygments may have returned error, falling back to plain JSON")
                        return formatted
                    return highlighted
                except ImportError:
                    # Fall back to plain formatting if pygments not available
                    pass
                except Exception as e:
                    logger.warning(f"Pygments formatting failed: {e}, using plain JSON")
                    pass

                return formatted
            return content
        except json.JSONDecodeError:
            return content

    async def _run_interactive_shell(self) -> None:
        """Run the interactive shell loop."""
        print("\n🐚 MCP Interactive Shell")
        print("Type 'help' for available commands or 'exit' to quit.")

        while True:
            try:
                # Show server info in right prompt
                rprompt = HTML(
                    f"<rprompt>Tools: {len(self.tools)} | Resources: {len(self.resources)}</rprompt>"
                )

                # Get user input - completer is already set up in the session
                text = await self.prompt_session.prompt_async(
                    "mcp> ",
                    rprompt=rprompt
                )

                await self._process_command(text.strip())

            except (EOFError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.exception("Shell command error")

    async def _process_command(self, command_line: str) -> None:
        """Process a command line input."""
        if not command_line:
            return

        parts = command_line.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command in self.commands:
            await self.commands[command](args)
        elif any(tool.name == command for tool in self.tools):
            # Direct tool call
            await self._cmd_call_tool([command] + args)
        elif any(resource.name == command for resource in self.resources):
            # Direct resource read
            await self._cmd_read_resource([command] + args)
        else:
            print(f"❌ Unknown command: {command}")
            print("Type 'help' for available commands.")

    async def _cmd_help(self, args: List[str]) -> None:
        """Show help information."""
        print("\n📖 Available commands:")
        print("  help                    - Show this help message")
        print("  list                    - List all tools and resources")
        print("  tools                   - List available tools only")
        print("  resources               - List available resources only")
        print("  call <tool> [args...]   - Call a tool with JSON arguments")
        print("  read <resource>         - Read a resource")
        print("  exit, quit              - Exit the shell")
        print("\n💡 You can also call tools and resources directly by name:")
        print("  example:greet {\"name\": \"Alice\"}")
        print("  greeting")
        print()

    async def _cmd_list(self, args: List[str]) -> None:
        """List all available tools and resources."""
        await self._refresh_server_info()
        await self._cmd_list_tools([])
        await self._cmd_list_resources([])

    async def _cmd_list_tools(self, args: List[str]) -> None:
        """List available tools."""
        await self._refresh_server_info()

        if not self.tools:
            print("🔧 No tools available")
            return

        print(f"\n🔧 Available tools ({len(self.tools)}):")
        for i, tool in enumerate(self.tools, 1):
            print(f"  {i}. {tool.name}")
            if tool.description:
                print(f"     {tool.description}")

            # Show metadata info
            tool_data = tool.model_dump()
            meta = tool_data.get('meta')
            if meta:
                if 'result_mime_type' in meta:
                    print(f"     Returns: {meta['result_mime_type']}")
                if 'args_schema_resource' in meta:
                    print(f"     📋 Args schema: {meta['args_schema_resource']}")
                if 'result_schema_resource' in meta:
                    print(f"     📋 Result schema: {meta['result_schema_resource']}")

            # Show input schema summary if available
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                required_params = tool.inputSchema.get('required', [])
                if required_params:
                    print(f"     Required: {', '.join(required_params)}")

                # Show available properties
                if 'properties' in tool.inputSchema:
                    props = list(tool.inputSchema['properties'].keys())
                    if props:
                        print(f"     Available params: {', '.join(props)}")
            
            # Show output schema info if available
            if hasattr(tool, 'outputSchema') and tool.outputSchema:
                print(f"     📤 Output schema: available")
                if 'type' in tool.outputSchema:
                    output_type = tool.outputSchema['type']
                    print(f"     Returns: {output_type}")
                    if output_type == 'object' and 'properties' in tool.outputSchema:
                        required_output = tool.outputSchema.get('required', [])
                        if required_output:
                            print(f"     Required output fields: {', '.join(required_output)}")
            print()

    async def _cmd_list_resources(self, args: List[str]) -> None:
        """List available resources."""
        await self._refresh_server_info()

        if not self.resources:
            print("📄 No resources available")
            return

        print(f"\n📄 Available resources ({len(self.resources)}):")
        for i, resource in enumerate(self.resources, 1):
            print(f"  {i}. {resource.name}")
            if resource.description:
                print(f"     {resource.description}")
            if hasattr(resource, 'mimeType') and resource.mimeType:
                print(f"     Type: {resource.mimeType}")
            print()

    async def _cmd_call_tool(self, args: List[str]) -> None:
        """Call a tool with arguments."""
        if not self.session:
            print("❌ Not connected to server. Please restart the server and reconnect.")
            return

        if not args:
            print("❌ Usage: call <tool_name> [arguments...]")
            print("Example: call example:greet {\"name\": \"Alice\"}")
            return

        tool_name = args[0]

        # Check if tool exists
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            print(f"❌ Unknown tool: {tool_name}")
            print("Use 'tools' command to see available tools.")
            return

        # Parse arguments with helpful error messages
        arguments = {}
        if len(args) > 1:
            try:
                # Join remaining args and parse as JSON
                args_str = ' '.join(args[1:])
                arguments = json.loads(args_str)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON arguments: {e}")
                print("Example: call example:greet {\"name\": \"Alice\"}")

                # Show schema-based help if available
                schema_key = f"{tool_name}:args"
                if schema_key in self.schemas:
                    schema = self.schemas[schema_key]
                    if 'properties' in schema:
                        print(f"💡 Available parameters for {tool_name}:")
                        for prop, prop_schema in schema['properties'].items():
                            prop_type = prop_schema.get('type', 'any')
                            description = prop_schema.get('description', '')
                            required = prop in schema.get('required', [])
                            req_marker = " (required)" if required else ""
                            print(f"  • {prop}: {prop_type}{req_marker} - {description}")
                return

        # Validate arguments against schema if available
        schema_key = f"{tool_name}:args"
        if arguments:
            warnings = self._validate_json_with_schema(arguments, schema_key)
            for warning in warnings:
                print(warning)

        try:
            print(f"🔧 Calling tool '{tool_name}'...")
            # types.CallToolResult
            result = await self.session.call_tool(tool_name, arguments)

            # Check if this is an error result first
            if hasattr(result, 'isError') and result.isError:
                print(f"\n❌ Tool '{tool_name}' error:")
                if hasattr(result, 'content') and result.content:
                    # TODO: handle other types.ContentBlock as well (not only types.TextContent)
                    # for content in cast(types.TextContent, result.content):
                    for content in result.content:
                        if hasattr(content, 'text') and content.text:
                            # TODO: handle other types.ContentBlock as well (not only types.TextContent)
                            c: types.TextContent = cast(types.TextContent, content)
                            print(f"💥 {c.text}")
                else:
                    print("Unknown error occurred")
                return
            
            print(f"\n✅ Tool '{tool_name}' result:")
            if hasattr(result, 'content') and result.content:
                # Check if this tool returns JSON based on metadata
                is_json_tool = False
                tool_data = tool.model_dump()
                meta = tool_data.get('meta')
                if meta and 'result_mime_type' in meta:
                    is_json_tool = meta['result_mime_type'] == "application/json"

                for content in result.content:
                    if hasattr(content, 'type') and content.type == "text":
                        if is_json_tool:
                            # This is JSON content even though type is "text"
                            logger.debug(f"Processing JSON tool response. Content: {repr(content.text)}")
                            formatted = self._format_json_output(content.text, "application/json")
                            logger.debug(f"Formatted result: {repr(formatted)}")
                            print(f"📄 JSON Response:")
                            print(formatted)

                            # Validate result against schema if available
                            result_schema_key = f"{tool_name}:result"
                            try:
                                parsed_result = json.loads(content.text)
                                warnings = self._validate_json_with_schema(parsed_result, result_schema_key)
                                for warning in warnings:
                                    print(warning)
                            except json.JSONDecodeError:
                                print("⚠️  Response is not valid JSON")
                        else:
                            # Check if content looks like JSON and format it
                            try:
                                json.loads(content.text)
                                # It's valid JSON, format it with highlighting
                                formatted = self._format_json_output(content.text, "application/json")
                                print(formatted)
                            except json.JSONDecodeError:
                                # Not JSON, print as plain text
                                print(content.text)
                        
                        # Validate against outputSchema if tool has one (do this once for both cases)
                        if hasattr(tool, 'outputSchema') and tool.outputSchema:
                            try:
                                if tool_name == "example:greet":
                                    # Text tool returns array of TextContent objects
                                    text_result = [{"type": "text", "text": content.text}]
                                    jsonschema.validate(text_result, tool.outputSchema)
                                else:
                                    # JSON tool validates the parsed JSON directly
                                    parsed_result = json.loads(content.text)
                                    jsonschema.validate(parsed_result, tool.outputSchema)
                                print("✅ Output schema validation passed")
                            except jsonschema.ValidationError as e:
                                print(f"⚠️  Output schema validation warning: {e.message}")
                            except json.JSONDecodeError:
                                print("⚠️  Cannot validate output schema: Response is not valid JSON")
                            except Exception as e:
                                print(f"⚠️  Output schema validation error: {e}")
                    else:
                        print(content)
            else:
                print(result)

        except Exception as e:
            error_msg = str(e)
            if "TaskGroup" in error_msg or "Connection" in error_msg or "stream" in error_msg.lower():
                print("🔌 Lost connection to server during tool call.")
                print("💡 Server connection lost - please restart the server and try again.")
                # Clear session but keep shell alive
                self.session = None
                self.tools = []
                self.resources = []
                self.schemas = {}
            else:
                print(f"❌ Failed to call tool '{tool_name}': {e}")
                logger.exception(f"Tool call failed: {tool_name}")

    async def _cmd_read_resource(self, args: List[str]) -> None:
        """Read a resource."""
        if not self.session:
            print("❌ Not connected to server")
            return

        if not args:
            print("❌ Usage: read <resource_name>")
            return

        resource_name = args[0]

        # Find resource by name
        resource = next((r for r in self.resources if r.name == resource_name), None)
        if not resource:
            print(f"❌ Unknown resource: {resource_name}")
            print("Use 'resources' command to see available resources.")
            return

        try:
            print(f"📄 Reading resource '{resource_name}'...")
            result: types.ReadResourceResult = await self.session.read_resource(resource.uri)

            print(f"\n✅ Resource '{resource_name}' content:")
            if hasattr(result, 'contents') and result.contents:
                # TODO: handle binary content: BlobResourceContents as well
                for content in cast(List[types.TextResourceContents], result.contents):
                    # Handle different resource content types
                    if hasattr(content, 'text') and content.text:
                        # Check if it's a JSON schema resource
                        if hasattr(resource, 'mimeType') and resource.mimeType == "application/schema+json":
                            formatted = self._format_json_output(content.text, "application/json")
                            print(f"📋 JSON Schema:\n{formatted}")
                            
                            # Validate that it's a valid JSON schema
                            try:
                                import jsonschema
                                schema_data = json.loads(content.text)
                                # Try to validate the schema itself using the meta-schema
                                jsonschema.Draft7Validator.check_schema(schema_data)
                                print("✅ JSON Schema is valid")
                            except json.JSONDecodeError as e:
                                print(f"⚠️  Schema validation warning: Invalid JSON - {e}")
                            except jsonschema.SchemaError as e:
                                print(f"⚠️  Schema validation warning: Invalid JSON Schema - {e.message}")
                            except Exception as e:
                                print(f"⚠️  Schema validation warning: {e}")
                                
                        elif hasattr(resource, 'mimeType') and resource.mimeType == "application/json":
                            formatted = self._format_json_output(content.text, "application/json")
                            print(formatted)
                            
                            # Validate that it's valid JSON
                            try:
                                json.loads(content.text)
                                print("✅ JSON is valid")
                            except json.JSONDecodeError as e:
                                print(f"⚠️  JSON validation warning: {e}")
                        else:
                            print(content.text)
                    elif hasattr(content, 'blob'):
                        print(f"<binary data ({len(content.blob)} bytes)>")
                    elif hasattr(content, 'content'):
                        # For simple string content
                        print(content.content)
                    else:
                        print(str(content))
            else:
                print(result)

        except Exception as e:
            print(f"❌ Failed to read resource '{resource_name}': {e}")
            logger.exception(f"Resource read failed: {resource_name}")

    async def _cmd_exit(self, args: List[str]) -> None:
        """Exit the shell."""
        raise KeyboardInterrupt()


@click.command()
@click.option(
    '--port',
    default=8001,
    type=int,
    help='Port number of the MCP server to connect to (default: 8001)'
)
def main(port: int) -> None:
    """Interactive MCP client shell for testing MCP servers."""
    async def run_shell():
        server_url = f"http://localhost:{port}/mcp"

        print("🚀 MCP Interactive Shell")
        print(f"Server: {server_url}")
        print()

        # Setup logging with DEBUG level
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler('.mcp_shell.log')]
        )

        # Start shell
        shell = MCPShell(server_url)
        await shell.connect()

    try:
        asyncio.run(run_shell())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")


if __name__ == "__main__":
    main()
