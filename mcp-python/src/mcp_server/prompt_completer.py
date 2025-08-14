import asyncio
import json
import logging
import shlex
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


class JSONCompleter(Completer):
    """Enhanced JSON completion helper with schema support."""

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self.schema = schema

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        text_before_cursor = document.text_before_cursor
        text_after_cursor = document.text_after_cursor

        # Find JSON argument part (after tool name)
        lines = text_before_cursor.split('\n')
        current_line = lines[-1] if lines else ""

        # Check if we're in a tool call context
        if not current_line.startswith('call '):
            return

        # Extract the JSON part after tool name using proper quoted parsing
        try:
            # Handle special case for commands with JSON arguments (complete or partial)
            line = current_line.strip()
            if '{' in line:
                # Find the JSON part (from first { to end of line or last })
                json_start = line.find('{')
                json_end = line.rfind('}') if '}' in line else len(line)
                
                if json_start > 0:
                    # Split the non-JSON part with shlex
                    pre_json = line[:json_start].strip()
                    json_part = line[json_start:json_end + (1 if '}' in line else 0)]
                    parts = shlex.split(pre_json)
                    parts.append(json_part)
                else:
                    parts = shlex.split(current_line)
            else:
                parts = shlex.split(current_line)
        except ValueError:
            # If shlex fails, fall back to simple split
            parts = current_line.split(' ', 2)
        
        if len(parts) < 3:
            # We're right after the tool name - suggest opening JSON
            yield Completion('{', start_position=0)
            yield Completion('{}', start_position=0)
            yield Completion('{"', start_position=0)
            
            # Add schema-based completion if available
            if self.schema and 'properties' in self.schema:
                required_props = self.schema.get('required', [])
                if required_props:
                    # Suggest a JSON object with required properties
                    required_json_parts = []
                    for prop in required_props[:2]:  # Limit to first 2 required props
                        prop_schema = self.schema['properties'].get(prop, {})
                        prop_type = prop_schema.get('type', 'string')
                        if prop_type == 'string':
                            required_json_parts.append(f'"{prop}": ""')
                        elif prop_type == 'boolean':
                            required_json_parts.append(f'"{prop}": true')
                        else:
                            required_json_parts.append(f'"{prop}": ""')

                    if required_json_parts:
                        json_template = '{ ' + ', '.join(required_json_parts) + ' }'
                        yield Completion(json_template, start_position=0, display="Template with required fields")
            return

        json_part = parts[2]

        # Analyze JSON context
        yield from self._provide_json_completions(json_part, document)

    def _provide_json_completions(self, json_part: str, document: Document):
        """Provide contextual JSON completions."""

        # If empty or just whitespace, suggest object start
        if not json_part.strip():
            yield Completion('{', start_position=0)
            yield Completion('{}', start_position=0)
            return

        # If we have an opening brace but no closing, suggest properties
        if json_part.strip() == '{':
            yield Completion('"', start_position=0)
            if self.schema and 'properties' in self.schema:
                for prop_name, prop_schema in self.schema['properties'].items():
                    prop_type = prop_schema.get('type', 'string')
                    description = prop_schema.get('description', '')

                    # Create completion with appropriate value template
                    if prop_type == 'string':
                        completion = f'"{prop_name}": ""'
                        display = f'"{prop_name}": "..." - {description}'
                    elif prop_type == 'boolean':
                        completion = f'"{prop_name}": true'
                        display = f'"{prop_name}": true/false - {description}'
                    elif prop_type == 'object':
                        completion = f'"{prop_name}": {{}}'
                        display = f'"{prop_name}": {{}} - {description}'
                    else:
                        completion = f'"{prop_name}": '
                        display = f'"{prop_name}" - {description}'

                    yield Completion(
                        completion,
                        start_position=0,
                        display=display
                    )
            return

        # If we're after a comma, suggest next property
        if json_part.strip().endswith(','):
            yield Completion(' "', start_position=0)
            if self.schema and 'properties' in self.schema:
                # Find already used properties
                try:
                    # Simple parsing to find existing keys
                    used_props = set()
                    import re
                    for match in re.finditer(r'"([^"]+)":', json_part):
                        used_props.add(match.group(1))

                    # Suggest unused properties
                    for prop_name, prop_schema in self.schema['properties'].items():
                        if prop_name not in used_props:
                            prop_type = prop_schema.get('type', 'string')
                            description = prop_schema.get('description', '')

                            if prop_type == 'string':
                                completion = f' "{prop_name}": ""'
                            elif prop_type == 'boolean':
                                completion = f' "{prop_name}": true'
                            elif prop_type == 'object':
                                completion = f' "{prop_name}": {{}}'
                            else:
                                completion = f' "{prop_name}": '

                            yield Completion(
                                completion,
                                start_position=0,
                                display=f'"{prop_name}" - {description}'
                            )
                except BaseException:
                    # If parsing fails, just suggest quote
                    yield Completion(' "', start_position=0)
            return

        # Handle nested object completion
        if ':' in json_part and '{' in json_part:
            # Try to find nested object context
            try:
                # Look for property: { pattern
                import re
                nested_match = re.search(r'"(\w+)"\s*:\s*\{\s*$', json_part)
                if nested_match:
                    prop_name = nested_match.group(1)
                    if self.schema and 'properties' in self.schema:
                        prop_schema = self.schema['properties'].get(prop_name)
                        if prop_schema and prop_schema.get('type') == 'object' and 'properties' in prop_schema:
                            # We're in a nested object, suggest its properties
                            yield Completion('"', start_position=0)
                            for nested_prop, nested_schema in prop_schema['properties'].items():
                                nested_type = nested_schema.get('type', 'string')
                                description = nested_schema.get('description', '')
                                
                                if nested_type == 'string':
                                    completion = f'"{nested_prop}": ""'
                                elif nested_type == 'boolean':
                                    completion = f'"{nested_prop}": true'
                                else:
                                    completion = f'"{nested_prop}": '
                                
                                yield Completion(
                                    completion,
                                    start_position=0,
                                    display=f'"{nested_prop}" - {description}'
                                )
                            return
                
                # Check for empty object that needs closing
                if json_part.strip().endswith('{}'):
                    # Look for what comes after the empty object
                    remaining_pattern = r'\{\}\s*$'
                    if re.search(remaining_pattern, json_part):
                        yield Completion(', "', start_position=0)
                        yield Completion(' }', start_position=0)
                        return
                        
            except Exception:
                pass  # Fall through to other completion logic
        
        # If we're typing a property name (after quote)
        if '"' in json_part and json_part.count('"') % 2 == 1:
            # We're inside a property name
            if self.schema and 'properties' in self.schema:
                # Get the partial property name
                last_quote = json_part.rfind('"')
                if last_quote >= 0:
                    partial_prop = json_part[last_quote + 1:]

                    for prop_name in self.schema['properties'].keys():
                        if prop_name.startswith(partial_prop):
                            remaining = prop_name[len(partial_prop):]
                            completion = remaining + '": '
                            yield Completion(completion, start_position=0)
            return
        
        # Check if we need closing braces
        if '{' in json_part and json_part.count('{') > json_part.count('}'):
            # We have unclosed braces, suggest closing
            open_braces = json_part.count('{')
            close_braces = json_part.count('}')
            missing_braces = open_braces - close_braces
            
            if missing_braces > 0:
                closing = ' }' * missing_braces
                yield Completion(closing, start_position=0, display="Close JSON object")
                return


class DynamicMCPCompleter(Completer):
    """Dynamic completer that provides different completions based on context."""

    def __init__(self, shell: Any):
        self.shell = shell

    def _parse_quoted_command(self, line: str, command: str) -> List[str]:
        """Parse command line respecting quoted arguments with spaces."""
        if not line.startswith(command):
            return []
        
        # Handle special case for commands with JSON arguments
        # Format: command "quoted-name" {...json...}
        line_stripped = line.strip()
        
        # Check if line starts with call/read/tool-details and has JSON
        if (line_stripped.startswith(('call ', 'read ', 'tool-details ')) and 
            '{' in line_stripped and '}' in line_stripped):
            
            # Find the JSON part (from first { to last })
            json_start = line_stripped.find('{')
            json_end = line_stripped.rfind('}')
            
            if json_start > 0 and json_end > json_start:
                # Split the non-JSON part with shlex
                pre_json = line_stripped[:json_start].strip()
                json_part = line_stripped[json_start:json_end + 1]
                
                try:
                    parts = shlex.split(pre_json)
                    parts.append(json_part)
                    return parts
                except ValueError:
                    # Fall back to simple parsing
                    pass
        
        # Default shlex parsing for other cases
        try:
            return shlex.split(line)
        except ValueError:
            # If shlex fails (e.g., unclosed quotes), fall back to simple split
            return line.split()

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        text = document.text_before_cursor

        # Check if we're in a tool call
        lines = text.split('\n')
        current_line = lines[-1] if lines else ""

        if current_line.startswith('call '):
            parts = self._parse_quoted_command(current_line, 'call ')
            if len(parts) >= 2:
                tool_name = parts[1]

                # Only provide JSON completions if we have a valid tool name
                # and there's either a third part (JSON arg) or space after tool name
                if tool_name and (len(parts) >= 3 or current_line.endswith(' ')):
                    # Check if this is a valid tool
                    if any(tool.name == tool_name for tool in self.shell.tools):
                        # Get schema for this tool
                        schema_key = f"{tool_name}:args"
                        schema = self.shell.schemas.get(schema_key)

                        # Create JSON completer with tool-specific schema
                        json_completer = JSONCompleter(schema)
                        yield from json_completer.get_completions(document, complete_event)
                        return

        # Handle 'read' command with quoted resource names
        if current_line.startswith('read '):
            parts = self._parse_quoted_command(current_line, 'read ')
            if len(parts) == 1:
                # User just typed 'read ', suggest resource names (quoted if they contain spaces)
                for resource in self.shell.resources:
                    if ' ' in resource.name:
                        # Suggest quoted name for resources with spaces
                        yield Completion(f'"{resource.name}"', start_position=0)
                    else:
                        yield Completion(resource.name, start_position=0)
                return

        # Handle 'call' command with quoted tool names  
        if current_line.startswith('call '):
            parts = self._parse_quoted_command(current_line, 'call ')
            if len(parts) == 1:
                # User just typed 'call ', suggest tool names (quoted if they contain spaces)
                for tool in self.shell.tools:
                    if ' ' in tool.name:
                        # Suggest quoted name for tools with spaces
                        yield Completion(f'"{tool.name}"', start_position=0)
                    else:
                        yield Completion(tool.name, start_position=0)
                return

        # Handle 'tool-details' command with quoted tool names
        if current_line.startswith('tool-details '):
            parts = self._parse_quoted_command(current_line, 'tool-details ')
            if len(parts) == 1:
                # User just typed 'tool-details ', suggest tool names (quoted if they contain spaces)
                for tool in self.shell.tools:
                    if ' ' in tool.name:
                        # Suggest quoted name for tools with spaces
                        yield Completion(f'"{tool.name}"', start_position=0)
                    else:
                        yield Completion(tool.name, start_position=0)
                return

        # Default command completion
        completions = list(self.shell.commands.keys())
        completions.extend([tool.name for tool in self.shell.tools])
        completions.extend([resource.name for resource in self.shell.resources])

        word_completer = WordCompleter(completions, ignore_case=True)
        yield from word_completer.get_completions(document, complete_event)

