# Claude Development Guide

This file contains instructions and context for Claude when working on this MCP Python project.

## Project Overview

This is a comprehensive MCP (Model Context Protocol) server and client implementation featuring:

- Protocol used: streaming HTTP
- JSON schema support with resource-based metadata
- Interactive shell with TAB completion and syntax highlighting
- Schema-aware JSON input assistance
- Comprehensive testing and validation

## Python Code

* Codebase is mypy ready, hence use type annotations and check them with `mypy src examples tests`
* Before start client, server, or tests, remove the appropriate log.
* Write code with DEBUG logging at interesting locations and consult the log to understand errors.
* Tests use the pytest framework and reside in `./tests`

## Memory Management

**Important**: Use the gw-memory MCP tool to store and retrieve project information:

### Storing Information

```bash
# Tag all entries with 'mcp-python' to indicate they relate to this project
mcp__gw-memory__store_memory(
    content="Your technical information here",
    metadata={"tags": ["mcp-python", "specific-tag"], "type": "note|fix|feature|bug"}
)
```

### Retrieving Context

**Always start by retrieving latest context:**
```bash
# Get recent project-related memories
mcp__gw-memory__recall_memory("mcp-python project work from last week")
# Or search by tags
mcp__gw-memory__search_by_tag(["mcp-python"])
```

## Architecture

### Server (`src/mcp_server/mcp_server.py`)

- **Tools**: `example:greet` (text) and `example:greetingJson` (JSON)
- **Resources**: JSON schemas served as resources with proper naming
- **Features**: Coverage collection, Click CLI, graceful shutdown
- **Key Fix**: Use `tool.model_dump().get('meta')` instead of `tool.meta` for metadata access

### Client (`examples/mcp_shell.py`)

- **Features**: Interactive shell, JSON completion, schema validation, syntax highlighting
- **Completers**: `DynamicMCPCompleter` and `JSONCompleter` for context-aware suggestions
- **Key Fix**: Schema caching works via `tool.model_dump()` pattern

## Development Workflow

1. **Check Memory**: Always retrieve latest context with gw-memory
2. **Run Tests**: Use the test files in project root for validation
3. **Start Server**: `python -m mcp_server.mcp_server --port 8002`
4. **Start Client**: `python examples/mcp_shell.py --port 8002`
5. **Test Completion**: Type `call example:greetingJson ` + TAB

## Known Issues & Solutions

### Meta Field Access

**Problem**: `tool.meta` returns None despite being in model_dump()
**Solution**: Always use `tool_data = tool.model_dump(); meta = tool_data.get('meta')`

### JSON Completion

**Working**: Completion triggers after `call example:greetingJson ` with 3 suggestions:

- `{` - Basic opening
- `{}` - Empty object  
- `{ "name": "" }` - Template with required fields

### Schema Validation

**Working**: Schemas cache properly and validation provides warnings only (non-blocking)

## Testing

Key test files:

- `simple_test.py` - Basic server/client communication
- `debug_schemas.py` - Schema caching verification  
- `test_interactive_completion.py` - TAB completion testing
- `final_test.py` - Comprehensive functionality test

## Dependencies

Core packages in `pyproject.toml`:

- `mcp>=1.12.0` - Model Context Protocol
- `click>=8.0.0` - CLI interface
- `jsonschema>=4.0.0` - JSON validation
- `pygments>=2.0.0` - Syntax highlighting
- `prompt-toolkit>=3.0.0` - Interactive shell

## Best Practices

1. **Always store significant discoveries in gw-memory**
2. **Tag everything with 'mcp-python' for project context**
3. **Test completion logic with the provided test scripts**
4. **Use model_dump() pattern for pydantic model field access**
5. **Verify schema caching before debugging completion issues**

## Latest Status

All major functionality implemented and tested:

- ✅ JSON highlighting working
- ✅ Schema caching fixed  
- ✅ TAB completion functional
- ✅ Validation warnings-only
- ✅ Meta field access resolved
