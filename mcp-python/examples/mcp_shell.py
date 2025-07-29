import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from mcp import Client
from mcp.model import ToolInvocation, ToolResponse, ResourceRequest, ResourceResponse
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from json.decoder import JSONDecodeError

@dataclass
class ServerInfo:
    tools: List[str]
    resources: List[str]

class MCPShell:
    def __init__(self, host: str = '127.0.0.1', port: int = 8000):
        self.client = Client(host, port)
        self.server_info = ServerInfo(tools=[], resources=[])
        self.session = PromptSession(
            history=FileHistory('.mcp_shell_history'),
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
            # Using the correct tool invocation format
            tools_resp = await self.client.call_tool(ToolInvocation(
                tool="mcp:list_tools",
                parameters={}
            ))
            resources_resp = await self.client.call_tool(ToolInvocation(
                tool="mcp:list_resources",
                parameters={}
            ))
            
            self.server_info.tools = tools_resp.result.get('tools', [])
            self.server_info.resources = resources_resp.result.get('resources', [])
        except Exception as e:
            print(f"⚠️  Failed to fetch server info: {e}")

    async def run(self) -> None:
        print(HTML("<b>MCP Interactive Shell</b> (type 'help' for commands)"))
        
        while True:
            try:
                completer = WordCompleter(list(self.commands.keys()) + self.server_info.tools + self.server_info.resources)
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

        parts = cmd.split()
        command = parts[0].lower()
        
        if command in self.commands:
            await self.commands[command](parts[1:])
        elif command in self.server_info.tools:
            await self.cmd_call([command] + parts[1:])
        elif command in self.server_info.resources:
            await self.cmd_read([command] + parts[1:])
        else:
            print(f"Unknown command or endpoint: {command}")

    async def cmd_help(self, args: List[str]) -> None:
        """Show help for available commands"""
        print("\nAvailable commands:")
        print("  list               - List all available tools and resources")
        print("  call <tool> [args] - Call a tool endpoint with optional arguments")
        print("  read <resource>    - Read from a resource endpoint")
        print("  help               - Show this help message")
        print("  exit               - Exit the shell\n")
        print("You can also type tool/resource names directly")
        print("Example: 'example:greet name=\"Alice\"'")

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
            print("Usage: call <tool> [params]")
            print("Example: call example:greet name=Alice")
            return

        tool_name = args[0]
        if tool_name not in self.server_info.tools:
            print(f"Unknown tool: {tool_name}")
            return

        try:
            # Parse parameters from command line
            params = {}
            for arg in args[1:]:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    params[key] = value
                else:
                    params[arg] = True
            
            response = await self.client.call_tool(
                ToolInvocation(
                    tool=tool_name,
                    parameters=params
                )
            )
            
            self._pretty_print_response(response.result)
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
            response = await self.client.read_resource(
                ResourceRequest(
                    resource=resource_name,
                    parameters={}  # Can add parameters here if needed
                )
            )
            
            self._pretty_print_response(response.result)
        except Exception as e:
            print(f"Error reading resource: {e}")

    def _pretty_print_response(self, data: Any) -> None:
        """Pretty print response data"""
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2))
        elif isinstance(data, str):
            print(data)
        else:
            print(str(data))

    async def cmd_exit(self, args: List[str]) -> None:
        """Exit the shell"""
        print("Goodbye!")
        raise KeyboardInterrupt()

    async def close(self) -> None:
        await self.client.close()

async def main():
    shell = MCPShell(port=8001)
    try:
        await shell.connect()
        await shell.run()
    finally:
        await shell.close()

if __name__ == "__main__":
    asyncio.run(main())
