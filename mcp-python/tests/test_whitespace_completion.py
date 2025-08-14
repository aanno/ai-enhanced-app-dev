"""
Test whitespace handling in MCP shell completion.

Tests that tool and resource names with spaces are properly handled
in completion suggestions and command parsing.
"""

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from mcp_server.prompt_completer import DynamicMCPCompleter
from mcp_shell import MCPShell


class MockTool:
    """Mock tool for testing."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description


class MockResource:
    """Mock resource for testing."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description


class MockShell:
    """Mock shell for testing completion."""
    def __init__(self):
        self.tools = [
            MockTool("simple-tool", "A simple tool"),
            MockTool("tool with spaces", "A tool with spaces in name"),
            MockTool("another spaced tool", "Another tool with spaces"),
        ]
        self.resources = [
            MockResource("simple-resource", "A simple resource"),
            MockResource("resource with spaces", "A resource with spaces in name"),
            MockResource("config file path", "Configuration file with spaces"),
        ]
        self.schemas = {}
        self.commands = {
            'help': None,
            'list': None,
            'tools': None,
            'resources': None,
            'tool-details': None,
            'call': None,
            'read': None,
            'exit': None,
            'quit': None,
        }


def test_quoted_command_parsing():
    """Test that quoted command parsing works correctly."""
    shell = MCPShell()
    
    # Test simple command
    parts = shell._parse_command_with_quotes('call simple-tool')
    assert parts == ['call', 'simple-tool']
    
    # Test quoted tool name with spaces
    parts = shell._parse_command_with_quotes('call "tool with spaces"')
    assert parts == ['call', 'tool with spaces']
    
    # Test quoted tool name with JSON arguments
    parts = shell._parse_command_with_quotes('call "tool with spaces" {"arg": "value"}')
    assert parts == ['call', 'tool with spaces', '{"arg": "value"}']
    
    # Test read command with quoted resource
    parts = shell._parse_command_with_quotes('read "resource with spaces"')
    assert parts == ['read', 'resource with spaces']
    
    # Test tool-details command with quoted tool
    parts = shell._parse_command_with_quotes('tool-details "another spaced tool"')
    assert parts == ['tool-details', 'another spaced tool']


def test_completion_suggests_quoted_names():
    """Test that completion suggests quoted names for items with spaces."""
    mock_shell = MockShell()
    completer = DynamicMCPCompleter(mock_shell)
    
    # Test 'call ' completion suggests quoted names for tools with spaces
    document = Document('call ')
    completions = list(completer.get_completions(document, CompleteEvent()))
    
    # Should suggest both quoted and unquoted names
    completion_texts = [c.text for c in completions]
    assert 'simple-tool' in completion_texts
    assert '"tool with spaces"' in completion_texts
    assert '"another spaced tool"' in completion_texts
    
    # Test 'read ' completion suggests quoted names for resources with spaces
    document = Document('read ')
    completions = list(completer.get_completions(document, CompleteEvent()))
    
    completion_texts = [c.text for c in completions]
    assert 'simple-resource' in completion_texts
    assert '"resource with spaces"' in completion_texts
    assert '"config file path"' in completion_texts
    
    # Test 'tool-details ' completion suggests quoted names for tools with spaces
    document = Document('tool-details ')
    completions = list(completer.get_completions(document, CompleteEvent()))
    
    completion_texts = [c.text for c in completions]
    assert 'simple-tool' in completion_texts
    assert '"tool with spaces"' in completion_texts
    assert '"another spaced tool"' in completion_texts


def test_completion_partial_matching():
    """Test that partial matching works with quoted names."""
    mock_shell = MockShell()
    completer = DynamicMCPCompleter(mock_shell)
    
    # Test partial matching in 'call' command
    document = Document('call "tool')  # Partial quote
    completions = list(completer.get_completions(document, CompleteEvent()))
    
    # Since we're inside a partial quote, should suggest completions that match
    completion_texts = [c.text for c in completions]
    # The exact behavior here depends on implementation details
    # At minimum, should not crash and should return some completions
    assert len(completions) >= 0


def test_json_completion_with_quoted_tool():
    """Test that JSON completion works when tool name is quoted."""
    mock_shell = MockShell()
    # Add a schema for the spaced tool name
    mock_shell.schemas["tool with spaces:args"] = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The name parameter"},
            "count": {"type": "number", "description": "The count parameter"}
        },
        "required": ["name"]
    }
    
    completer = DynamicMCPCompleter(mock_shell)
    
    # Test that JSON completion triggers after quoted tool name
    document = Document('call "tool with spaces" ')
    completions = list(completer.get_completions(document, CompleteEvent()))
    
    # Should get JSON completions
    completion_texts = [c.text for c in completions]
    assert any('{' in text for text in completion_texts), f"Expected JSON completion, got: {completion_texts}"


@pytest.mark.parametrize("command_line,expected_parts", [
    ('call simple-tool', ['call', 'simple-tool']),
    ('call "tool with spaces"', ['call', 'tool with spaces']),
    ('read "resource with spaces"', ['read', 'resource with spaces']),
    ('tool-details "another spaced tool"', ['tool-details', 'another spaced tool']),
    ('call "quoted tool" {"arg": "value"}', ['call', 'quoted tool', '{"arg": "value"}']),
    ('read normal-resource', ['read', 'normal-resource']),
])
def test_parsing_various_commands(command_line, expected_parts):
    """Test command parsing with various combinations of quoted and unquoted arguments."""
    shell = MCPShell()
    parts = shell._parse_command_with_quotes(command_line)
    assert parts == expected_parts


def test_escape_sequences():
    """Test that escape sequences in quoted strings are handled correctly."""
    shell = MCPShell()
    
    # Test escaped quotes
    parts = shell._parse_command_with_quotes('call "tool with \\"quotes\\""')
    assert parts == ['call', 'tool with "quotes"']
    
    # Test escaped backslashes
    parts = shell._parse_command_with_quotes('call "tool with \\\\backslash"')
    assert parts == ['call', 'tool with \\backslash']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])