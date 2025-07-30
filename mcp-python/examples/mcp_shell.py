import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

from mcp.client.client import Client
from mcp.types import ToolRequest, ReadResourceRequest

logger = logging.getLogger(__name__)

@dataclass
class ServerInfo:
    tools: List[str]
    resources: List[str]

class MCPClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 8001):
        self.client = Client(host, port)
        self.server_info = ServerInfo(tools=[], resources=[])
        self.session = PromptSession(
            history=FileHistory('.mcp_client_history'),
            auto_suggest=AutoSuggestFromHistory(),
            style=Style.from_dict({
                'rprompt': 'bg:#008800 #ffffff',
                'completion-menu.completion': 'bg:#008888 #ffffff',
                'completion-menu.completion.current': 'bg:#00aaaa #000000',
            })
        )
        self.commands = {
            'help': self.cmd_help,
            'list': self.cmd_list,
            'call': self.cmd_call,
            'read': self.cmd_read,
            'exit': self.cmd_exit,
        }

    async def connect(self) -> None:
        await self.client.connect()
        await self.fetch_server_info()

    async def fetch_server_info(self) -> None:
        try:
            # Get available tools
            tools_resp = await self.client.call_tool(
                ToolRequest(to="mcp:list_tools", body=b"")
            )
            self.server_info.tools = json.loads(tools_resp.body.decode()).get('tools', [])
            
            # Get available resources
            resources_resp = await self.client.call_tool(
                ToolRequest(to="mcp:list_resources", body=b"")
            )
            self.server_info.resources = json.loads(resources_resp.body.decode()).get('resources', [])
            
            logger.info("Fetched server info: %d tools, %d resources", 
                        len(self.server_info.tools), len(self.server_info.resources))
        except Exception as e:
            logger.error("Failed to fetch server info: %s", e)
            print(f"⚠️  Failed to fetch server info: {e}")

    async def run(self) -> None:
        print(HTML("<b>MCP Interactive Client</b> (type 'help' for commands)"))
        
        while True:
            try:
                # Create dynamic completer with commands and endpoints
                completions = list(self.commands.keys()) + self.server_info.tools + self.server_info.resources
                completer = WordCompleter(completions, ignore_case=True)
                
                # Show endpoint counts in right prompt
                text = await self.session.prompt_async(
                    "mcp> ",
                    completer=completer,
                    rprompt=HTML(f"<rprompt>Tools: {len(self.server_info.tools)} | Resources: {len(self.server_info.resources)}</rprompt>")
                )
                await self.process_command(text.strip())
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"Error: {e}")

    async def process_command(self, cmd: str) -> None:
        if not cmd:
            return

        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in self.commands:
            await self.commands[command](args.split() if args else [])
        elif command in self.server_info.tools:
            await self.cmd_call([command] + (args.split() if args else []))
        elif command in self.server_info.resources:
            await self.cmd_read([command] + (args.split() if args else []))
        else:
            print(f"Unknown command or endpoint: {command}")

    async def cmd_help(self, args: List[str]) -> None:
        """Show help for available commands"""
        print("\nAvailable commands:")
        print("  list               - List all available tools and resources")
        print("  call <tool> [args] - Call a tool endpoint with optional JSON arguments")
        print("  read <resource>    - Read from a resource endpoint")
        print("  help               - Show this help message")
        print("  exit               - Exit the client\n")
        print("You can also type tool/resource names directly")
        print("Examples:")
        print("  example:greet {\"name\": \"Alice\"}")
        print("  read greeting\n")

    async def cmd_list(self, args: List[str]) -> None:
        """List all available endpoints"""
        await self.fetch_server_info()  # Refresh list
        
        print("\nTools:")
        for tool in sorted(self.server_info.tools):
            print(f"  {tool}")
        
        print("\nResources:")
        for resource in sorted(self.server_info.resources):
            print(f"  {resource}")
        
        print()

    async def cmd_call(self, args: List[str]) -> None:
        """Call a tool endpoint"""
        if not args:
            print("Usage: call <tool> [json_args]")
            print("Example: call example:greet {\"name\": \"Alice\"}")
            return

        tool_name = args[0]
        if tool_name not in self.server_info.tools:
            print(f"Unknown tool: {tool_name}")
            return

        try:
            # Try to parse remaining args as JSON
            body = b""
            if len(args) > 1:
                try:
                    json_args = json.loads(" ".join(args[1:]))
                    body = json.dumps(json_args).encode()
                except json.JSONDecodeError:
                    body = " ".join(args[1:]).encode()
            
            response = await self.client.call_tool(
                ToolRequest(
                    to=tool_name,
                    body=body
                )
            )
            
            self._pretty_print_response(response.body)
        except Exception as e:
            print(f"Error calling tool: {e}")

    async def cmd_read(self, args: List[str]) -> None:
        """Read from a resource endpoint"""
        if not args:
            print("Usage: read <resource>")
            return

        resource_name = args[0]
        if resource_name not in self.server_info.resources:
            print(f"Unknown resource: {resource_name}")
            return

        try:
            # Construct resource URI based on server implementation
            resource_uri = f"file:///{resource_name}.txt"
            
            response = await self.client.read_resource(
                ReadResourceRequest(
                    resource=resource_uri,
                    headers={}
                )
            )
            
            self._pretty_print_response(response.body)
        except Exception as e:
            print(f"Error reading resource: {e}")

    def _pretty_print_response(self, data: bytes) -> None:
        """Pretty print response data"""
        try:
            # Try to decode as JSON
            decoded = data.decode()
            try:
                parsed = json.loads(decoded)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                # Print as plain text if not JSON
                print(decoded)
        except UnicodeDecodeError:
            print(f"<binary data ({len(data)} bytes)>")

    async def cmd_exit(self, args: List[str]) -> None:
        """Exit the client"""
        print("Goodbye!")
        raise KeyboardInterrupt()

    async def close(self) -> None:
        await self.client.close()

async def main():
    client = MCPClient(port=8001)
    try:
        await client.connect()
        await client.run()
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
