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
from typing import Any, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import mcp.types as types

logger = logging.getLogger(__name__)


class MCPShell:
    """Interactive MCP client shell."""

    def __init__(self, server_url: str = "http://localhost:8001/mcp"):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.tools: List[types.Tool] = []
        self.resources: List[types.Resource] = []
        
        # Setup prompt toolkit
        self.prompt_session = PromptSession(
            history=FileHistory('.mcp_shell_history'),
            auto_suggest=AutoSuggestFromHistory(),
            style=Style.from_dict({
                'rprompt': 'bg:#008800 #ffffff',
                'completion-menu.completion': 'bg:#008888 #ffffff',
                'completion-menu.completion.current': 'bg:#00aaaa #000000',
                'prompt': 'bold',
            })
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
                    
                    session_id = get_session_id() if get_session_id else None
                    if session_id:
                        print(f"📋 Session ID: {session_id}")
                    
                    # Fetch initial server capabilities
                    await self._refresh_server_info()
                    
                    print(f"✅ Connected successfully!")
                    print(f"Found {len(self.tools)} tools and {len(self.resources)} resources")
                    
                    # Start interactive shell
                    await self._run_interactive_shell()
                    
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
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
            
            logger.info(f"Found {len(self.tools)} tools and {len(self.resources)} resources")
            
        except Exception as e:
            logger.error(f"Failed to refresh server info: {e}")
            print(f"⚠️  Failed to refresh server info: {e}")

    async def _run_interactive_shell(self) -> None:
        """Run the interactive shell loop."""
        print(HTML("\n<b>🐚 MCP Interactive Shell</b>"))
        print("Type 'help' for available commands or 'exit' to quit.")
        
        while True:
            try:
                # Create dynamic completer
                completions = list(self.commands.keys())
                completions.extend([tool.name for tool in self.tools])
                completions.extend([resource.name for resource in self.resources])
                completer = WordCompleter(completions, ignore_case=True)
                
                # Show server info in right prompt
                rprompt = HTML(
                    f"<rprompt>Tools: {len(self.tools)} | Resources: {len(self.resources)}</rprompt>"
                )
                
                # Get user input
                text = await self.prompt_session.prompt_async(
                    "mcp> ",
                    completer=completer,
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
            # Show input schema if available
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                required_params = tool.inputSchema.get('required', [])
                if required_params:
                    print(f"     Required: {', '.join(required_params)}")
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
            print("❌ Not connected to server")
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
            
        # Parse arguments
        arguments = {}
        if len(args) > 1:
            try:
                # Join remaining args and parse as JSON
                args_str = ' '.join(args[1:])
                arguments = json.loads(args_str)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON arguments: {e}")
                print("Example: call example:greet {\"name\": \"Alice\"}")
                return
                
        try:
            print(f"🔧 Calling tool '{tool_name}'...")
            result = await self.session.call_tool(tool_name, arguments)
            
            print(f"\n✅ Tool '{tool_name}' result:")
            if hasattr(result, 'content') and result.content:
                for content in result.content:
                    if hasattr(content, 'type') and content.type == "text":
                        print(content.text)
                    else:
                        print(content)
            else:
                print(result)
                
        except Exception as e:
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
            result = await self.session.read_resource(resource.uri)
            
            print(f"\n✅ Resource '{resource_name}' content:")
            if hasattr(result, 'contents') and result.contents:
                for content in result.contents:
                    # Handle different resource content types
                    if hasattr(content, 'text'):
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
        print("👋 Goodbye!")
        raise KeyboardInterrupt()


async def main():
    """Main entry point."""
    import sys
    
    # Parse command line arguments
    server_url = "http://localhost:8001/mcp"
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        server_url = f"http://localhost:{port}/mcp"
    
    print("🚀 MCP Interactive Shell")
    print(f"Server: {server_url}")
    print()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler('.mcp_shell.log')]
    )
    
    # Start shell
    shell = MCPShell(server_url)
    await shell.connect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")