#!/bin/bash -x
# https://github.com/modelcontextprotocol/servers/tree/main/src/memory

export MEMORY_FILE_PATH=".local/state/mcp-memory/memory.json"
mkdir -p "$(dirname "$MEMORY_FILE_PATH")"
pnpm dlx @modelcontextprotocol/server-memory
