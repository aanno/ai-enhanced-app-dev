import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from mcp.client.client import Client
from mcp.types import ToolRequest, ReadResourceRequest
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

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
            tools_resp = await self.client.call_tool(
                ToolRequest(to="mcp:list_tools", body=b"")
            )
            resources_resp = await self.client.call_tool(
                ToolRequest(to="mcp:list_resources", body=b"")
            )
            
            self.server_info.tools = json.loads(tools_resp.body.decode()).get('tools', [])
            self.server_info.resources = json.loads(resources_resp.body.decode()).get('resources', [])
        except Exception as e:
            print(f"⚠️  Failed to fetch server info: {e}")

    # ... [rest of the shell implementation remains the same] ...
