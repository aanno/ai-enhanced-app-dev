"""
Configuration file for pytest.

Sets up proper module paths for testing.
"""

import sys
import os

# Add the examples directory to the path so we can import mcp_shell
examples_path = os.path.join(os.path.dirname(__file__), '..', 'examples')
if examples_path not in sys.path:
    sys.path.insert(0, examples_path)

# Add the project root to the path so we can import mcp_server module
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)