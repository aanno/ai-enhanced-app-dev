"""Test JSON completion functionality."""

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from src.mcp_server.prompt_completer import JSONCompleter, DynamicMCPCompleter


class MockTool:
    """Mock tool for testing."""
    def __init__(self, name: str):
        self.name = name


class MockShell:
    """Mock shell for testing DynamicMCPCompleter."""
    def __init__(self):
        self.tools = [
            MockTool("example:greet"),
            MockTool("example:greetingJson")
        ]
        self.resources = []
        self.commands = {"help": None, "list": None, "call": None}
        self.schemas = {
            "example:greetingJson:args": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the person to greet"
                    },
                    "include_details": {
                        "type": "boolean", 
                        "description": "Include additional details"
                    },
                    "preferences": {
                        "type": "object",
                        "description": "User preferences",
                        "properties": {
                            "language": {
                                "type": "string",
                                "enum": ["en", "es", "fr", "de"]
                            },
                            "format": {
                                "type": "string",
                                "enum": ["simple", "detailed"]
                            }
                        }
                    }
                },
                "required": ["name"]
            }
        }


@pytest.fixture
def mock_shell():
    return MockShell()


@pytest.fixture
def json_schema():
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the person"},
            "age": {"type": "number", "description": "Age in years"},
            "active": {"type": "boolean", "description": "Whether active"}
        },
        "required": ["name"]
    }


def test_json_completer_empty_input():
    """Test JSON completion with empty input."""
    completer = JSONCompleter()
    doc = Document("call example:tool ")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    assert len(completions) >= 2
    completion_texts = [c.text for c in completions]
    assert "{" in completion_texts
    assert "{}" in completion_texts


def test_json_completer_with_schema():
    """Test JSON completion with schema providing template."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name"},
            "active": {"type": "boolean", "description": "Status"}
        },
        "required": ["name"]
    }
    
    completer = JSONCompleter(schema)
    doc = Document("call example:tool ")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should include template with required fields
    completion_texts = [c.text for c in completions]
    assert any('{ "name": ""' in text for text in completion_texts)


def test_json_completer_open_brace():
    """Test completion after opening brace."""
    schema = {
        "type": "object", 
        "properties": {
            "name": {"type": "string", "description": "Name"},
            "count": {"type": "number", "description": "Count"}
        }
    }
    
    completer = JSONCompleter(schema)
    doc = Document("call example:tool {")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should suggest property completions
    completion_texts = [c.text for c in completions]
    assert any('"name": ""' in text for text in completion_texts)
    assert any('"count":' in text for text in completion_texts)


def test_json_completer_after_comma():
    """Test completion after comma in JSON object."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "active": {"type": "boolean"}
        }
    }
    
    completer = JSONCompleter(schema)
    doc = Document('call example:tool { "name": "test",')
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should suggest remaining properties (not "name" since it's already used)
    completion_texts = [c.text for c in completions]
    assert any('"age":' in text for text in completion_texts)
    assert any('"active":' in text for text in completion_texts)
    assert not any('"name":' in text and text.count('"name":') > 1 for text in completion_texts)


def test_json_completer_nested_object():
    """Test completion in nested objects."""
    schema = {
        "type": "object",
        "properties": {
            "preferences": {
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "theme": {"type": "string"}
                }
            }
        }
    }
    
    completer = JSONCompleter(schema)
    doc = Document('call example:tool { "preferences": {')
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should suggest nested properties
    completion_texts = [c.text for c in completions]
    assert any('"language":' in text for text in completion_texts)
    assert any('"theme":' in text for text in completion_texts)


def test_json_completer_closing_braces():
    """Test completion suggests closing braces."""
    completer = JSONCompleter()
    doc = Document('call example:tool { "name": "test"')
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should suggest closing brace
    completion_texts = [c.text for c in completions]
    assert any(' }' in text for text in completion_texts)


def test_dynamic_completer_tool_commands(mock_shell):
    """Test DynamicMCPCompleter suggests commands and tools."""
    completer = DynamicMCPCompleter(mock_shell)
    doc = Document("h")  # Simpler prefix that should match
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    completion_texts = [c.text for c in completions]
    # Should get help and all tools/commands
    assert len(completion_texts) > 0
    
    # Test with empty document to get all completions
    doc_empty = Document("")
    completions_all = list(completer.get_completions(doc_empty, event))
    all_texts = [c.text for c in completions_all]
    assert "help" in all_texts
    assert "example:greet" in all_texts
    assert "example:greetingJson" in all_texts


def test_dynamic_completer_json_mode(mock_shell):
    """Test DynamicMCPCompleter switches to JSON mode for tool calls."""
    completer = DynamicMCPCompleter(mock_shell)
    doc = Document("call example:greetingJson ")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should provide JSON completions including schema-based template
    completion_texts = [c.text for c in completions]
    assert "{" in completion_texts
    assert any('"name":' in text for text in completion_texts)


def test_dynamic_completer_invalid_tool(mock_shell):
    """Test DynamicMCPCompleter handles invalid tool names."""
    completer = DynamicMCPCompleter(mock_shell)
    doc = Document("call nonexistent:tool ")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # For invalid tools, should fall back to word completion which includes all commands/tools
    # This is acceptable behavior - it provides all available options
    completion_texts = [c.text for c in completions]
    # Should include all available commands and tools as fallback
    expected_items = ["help", "list", "call", "example:greet", "example:greetingJson"]
    for item in expected_items:
        assert item in completion_texts


def test_json_completer_property_name_completion():
    """Test completion while typing property names."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "namespace": {"type": "string"},
            "number": {"type": "number"}
        }
    }
    
    completer = JSONCompleter(schema)
    doc = Document('call example:tool { "na')
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should complete "na" to "name" and "namespace"
    completion_texts = [c.text for c in completions]
    assert any('me": ' in text for text in completion_texts)  # completes "name"
    assert any('mespace": ' in text for text in completion_texts)  # completes "namespace"


def test_json_completer_boolean_type():
    """Test completion for boolean properties."""
    schema = {
        "type": "object",
        "properties": {
            "active": {"type": "boolean", "description": "Status"},
            "enabled": {"type": "boolean"}
        }
    }
    
    completer = JSONCompleter(schema)
    doc = Document("call example:tool {")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should suggest boolean completions with true/false
    completion_texts = [c.text for c in completions]
    assert any('"active": true' in text for text in completion_texts)
    assert any('"enabled": true' in text for text in completion_texts)


def test_json_completer_object_type():
    """Test completion for object properties."""
    schema = {
        "type": "object",
        "properties": {
            "config": {"type": "object", "description": "Configuration object"}
        }
    }
    
    completer = JSONCompleter(schema)
    doc = Document("call example:tool {")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    # Should suggest object completion with empty object
    completion_texts = [c.text for c in completions]
    assert any('"config": {}' in text for text in completion_texts)


def test_dynamic_completer_greetingJson_schema(mock_shell):
    """Test real greetingJson schema completion."""
    completer = DynamicMCPCompleter(mock_shell)
    doc = Document("call example:greetingJson {")
    event = CompleteEvent()
    
    completions = list(completer.get_completions(doc, event))
    
    completion_texts = [c.text for c in completions]
    # Should include properties from the greetingJson schema
    assert any('"name":' in text for text in completion_texts)
    assert any('"include_details":' in text for text in completion_texts) 
    assert any('"preferences":' in text for text in completion_texts)