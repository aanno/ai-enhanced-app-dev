#!/bin/bash
# https://github.com/doobidoo/mcp-memory-service.git
# python
# must run _outside_ dev container

pnpm dlx supergateway --stdio 'uv --directory $GITHUB_HOME/mcp-memory-service run memory' --port 3012 --baseUrl http://localhost:3012 --ssePath /sse --messagePath /message
