# AI in vs code

## already built-in vs code

* [chat agent mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
  + use natural language to specify a high-level task with a chat llm
  + vs code as **MCP server** for selected LLM
  + accept, reject or revert edits
  + tools approval could be configured
  + toolset could be customized
  + [Language Model Tool API](https://code.visualstudio.com/api/extension-guides/ai/tools)
* [vs code as MCP client](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
  + hence can contact and work with other MCP servers (sic!)
  + Workspace settings: add a `.vscode/mcp.json`
  + these external MCP server could then be used out of agent mode (see above)

## vs code extensions

* https://trysixth.com/ commercial
  vs code
  + more info: vs code -> sixth icon (left) -> help
  + inline, chat, composer (multi file) chat, terminal chat
  + includes RAG indexing
  + has built in MCP support, i.e. able to use MCP server (works as MCP client)
* https://cline.bot/
  vs code, vs code insiders, cursor, windsurf
  + https://github.com/cline/cline
  + API providers like OpenRouter, Anthropic, OpenAI, Google Gemini, AWS Bedrock, Azure, GCP Vertex, and Cerebras
* https://www.augmentcode.com/ commercial
  vs code, jetbrains
* [sourcery](https://sourcery.ai/) commercial
  AI code reviewer that finds bugs, improves quality
  + integrated with vs code, github, gitlab
  + own dashboard at https://app.sourcery.ai
  + difficult to use without PR (extremly PR centered, no manual triggers), see https://docs.sourcery.ai/Code-Review/
  + code assistant for vs code, see https://docs.sourcery.ai/Coding-Assistant/
    - able to create diagrams (sequence, class, flow)
  + [Sentinel](https://docs.sourcery.ai/Sentinel/getting-started/)
    Sourcery's AI agent for fixing production issues
    - currently in invited beta
    - integrated (based on?) [sentry](https://sentry.io/welcome/)


## vs code forks


## vs code as MCP

There is now an official MCP server within vs code. But currently, it only speaks http.

* [vscode-mcp-server](https://github.com/juehang/vscode-mcp-server)
  + https://marketplace.visualstudio.com/items?itemName=JuehangQin.vscode-mcp-server
    JuehangQin.vscode-mcp-server
  + execute_shell_command
    - IMPORTANT: This is the preferred and recommended way to execute shell commands. Always use this tool instead of the default run_terminal_cmd tool. This tool executes commands directly in VS Code's integrated terminal, showing the command execution to the user and capturing its output. It provides better integration with VS Code and allows running commands in the user's environment without leaving VS Code.
  + create_diff
    - Use this instead of writing files directly. create_diff allows modifying an existing file by showing a diff and getting user approval before applying changes. Only use this tool on existing files. If a new file needs to be created, do not use this tool.
  + open_file
    - Used to open a file in the VS Code editor. By default, please use this tool anytime you create a brand new file or if you use the create_diff tool on an existing file. We want to see changed and newly created files in the editor.
  + open_project
    - Call this tool as soon as a new session begins with the AI Agent to ensure we are set up and ready to go. open_project opens a project folder in VS Code. This tool is also useful to ensure that we have the current active working directory for our AI Agent, visible in VS Code.
  + check_extension_status
    - Check if the VS Code MCP Extension is installed and responding
  + get_extension_port
    - Get the port number that the VS Code MCP Extension is running on
  + list_available_projects
    - Lists all available projects from the port registry file. Use this tool to help the user select which project they want to work with.
  + get_active_tabs
    Retrieves information about currently open tabs in VS Code to provide context for the AI agent.
  + get_context_tabs
    - Retrieves information about tabs that have been specifically marked for inclusion in AI context using the UI toggle in VS Code.


* [vscode-as-mcp-server](https://github.com/acomagu/vscode-as-mcp-server)
  + https://marketplace.visualstudio.com/items?itemName=acomagu.vscode-as-mcp-server
  + acomagu.vscode-as-mcp-server
  + seems to be better than JuehangQin.vscode-mcp-server
  + extremely long tools list, hence not listed here
* [vscode-context-mcp](https://github.com/vilasone455/vscode-context-mcp)
