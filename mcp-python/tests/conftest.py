"""
Configuration file for pytest.

Sets up proper module paths and test configuration.
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

# MCP Server connection parameters (configurable via environment variables)
# Usage:
#   Default: pytest tests/
#   Custom port: MCP_TEST_PORT=8001 pytest tests/
#   Custom host: MCP_TEST_HOST=localhost MCP_TEST_PORT=8003 pytest tests/
MCP_TEST_HOST = os.getenv("MCP_TEST_HOST", "127.0.0.1")
MCP_TEST_PORT = int(os.getenv("MCP_TEST_PORT", "8002"))