# MCP Python Example

A comprehensive Model Context Protocol (MCP) server and client streaming HTTP example with advanced JSON schema support, interactive completion, and syntax highlighting.

## Features

### 🚀 MCP Server

- **Two Example Tools**: Text-based greeting (`example:greet`) and JSON response (`example:greetingJson`)
- **JSON Schema Resources**: Comprehensive schema definitions served as MCP resources
- **Coverage Support**: Optional code coverage collection with graceful cleanup
- **CLI Interface**: Click-based command line with `--port` and `--coverage` flags

### 🖥️ Interactive Client

- **Smart JSON Completion**: Context-aware TAB completion for tool arguments
- **Schema Validation**: Non-blocking warnings for JSON input validation  
- **Syntax Highlighting**: Pygments-powered JSON highlighting for responses and schemas
- **Rich Interface**: Prompt-toolkit based shell with history and auto-suggestions

## Quick Start

### Prerequisites

```bash
pip install -e .
```

### Running the Server

```bash
# Basic server on default port 8001
python -m mcp_server.mcp_server

# Custom port with coverage collection
python -m mcp_server.mcp_server --port 8002 --coverage
```

### Running the Interactive Client

```bash
# Connect to default server
python examples/mcp_shell.py

# Connect to custom port
python examples/mcp_shell.py --port 8002
```

## Usage Examples

### Basic Tool Calls

```bash
mcp> call example:greet {"name": "Alice", "language": "es"}
mcp> call example:greetingJson {"name": "Bob", "include_details": true}
```

### Smart JSON Completion

1. Type: `call example:greetingJson ` (with space)
2. Press **TAB** to see completion options:
   - `{` - Basic JSON opening
   - `{}` - Empty object
   - `{ "name": "" }` - Template with required fields

### Reading Schema Resources

```bash
mcp> read example:greetingJson:args:schema
mcp> resources
```

## Project Structure

```
├── src/mcp_server/
│   └── mcp_server.py          # MCP server implementation
├── examples/
│   └── mcp_shell.py           # Interactive client shell
├── pyproject.toml             # Dependencies and configuration
├── CLAUDE.md                  # Claude development guide
└── README.md                  # This file
```

## Architecture

### Server Components

- **Tool Handlers**: Async functions handling `example:greet` and `example:greetingJson`
- **Resource Handlers**: Serving both text resources and JSON schemas
- **Schema System**: Comprehensive JSON schemas with validation rules
- **Lifecycle Management**: Graceful shutdown with coverage data preservation

### Client Components

- **DynamicMCPCompleter**: Context-aware completion routing
- **JSONCompleter**: Schema-based JSON input assistance
- **Schema Caching**: Automatic fetch and cache of tool schemas
- **Validation Engine**: Non-blocking JSON validation with helpful warnings

## Advanced Features

### JSON Schema Support

The server provides comprehensive JSON schemas as MCP resources:

- **Argument Schemas**: Define tool input requirements and validation
- **Result Schemas**: Document expected tool output formats
- **Resource Naming**: Follows pattern `{tool_name}:{type}:schema`

### Intelligent Completion

The client provides context-aware completions:

- **Tool Names**: Complete available tool names after `call`
- **JSON Structure**: Smart JSON completion based on tool schemas
- **Property Suggestions**: Schema-aware property name completion
- **Type Hints**: Contextual suggestions based on property types

### Syntax Highlighting

Full JSON syntax highlighting using Pygments:

- **Tool Responses**: Automatic detection and highlighting of JSON responses
- **Schema Resources**: Beautiful display of schema definitions
- **Error Messages**: Clear formatting for validation warnings

## Development

### Testing
```bash
# Test basic server functionality
python simple_test.py

# Test schema caching
python debug_schemas.py

# Test JSON completion
python test_interactive_completion.py

# Comprehensive test suite
python final_test.py
```

### Dependencies

- **Core**: `mcp>=1.12.0`, `click>=8.0.0`, `prompt-toolkit>=3.0.0`
- **Validation**: `jsonschema>=4.0.0`
- **Highlighting**: `pygments>=2.0.0`
- **Optional**: `coverage>=7.9.2` (for test coverage)

## Troubleshooting

### TAB Completion Not Working

1. Ensure server is running and connected
2. Verify schemas are cached: check client startup messages
3. Try pressing TAB twice in some terminals
4. Test with different terminal applications if needed

### Schema Validation Issues

- Schemas are cached automatically on client startup
- Validation provides warnings only (non-blocking)
- Check `📋 Cached schemas:` in client startup output

### Meta Field Access

If extending the code, use the pattern:

```python
tool_data = tool.model_dump()
meta = tool_data.get('meta')
```

Instead of direct `tool.meta` access due to Pydantic serialization.

## Contributing

This is an example project demonstrating MCP capabilities. Feel free to:

- Add new tools with different schema patterns
- Enhance the completion system
- Improve syntax highlighting
- Add more comprehensive validation

## License

Example code for educational and development purposes.
