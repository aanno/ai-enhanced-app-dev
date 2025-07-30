import asyncio
import contextlib
import signal
import json
import logging
import anyio
from typing import AsyncIterator, Optional, Any, Dict, List
from types import FrameType

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.shared.exceptions import McpError
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

try:
    import coverage
    from coverage import Coverage
    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False
    Coverage = Any  # type: ignore

logger = logging.getLogger(__name__)

SAMPLE_RESOURCES = {
    "greeting": {
        "content": "Hello! This is a sample text resource.",
        "title": "Welcome Message",
    },
    "help": {
        "content": "This server provides a few sample text resources for testing.",
        "title": "Help Documentation",
    },
    "about": {
        "content": "This is the MCP server with coverage support.",
        "title": "About This Server",
    },
}

@contextlib.asynccontextmanager
async def coverage_context() -> AsyncIterator[Optional[Coverage]]:
    """Context manager for coverage collection"""
    cov: Optional[Coverage] = None
    if HAS_COVERAGE:
        cov = coverage.Coverage()
        cov.start()
        logger.info("Coverage collection started")
    
    try:
        yield cov
    finally:
        if cov is not None:
            cov.stop()
            cov.save()
            logger.info("Coverage data saved to .coverage")

async def graceful_shutdown(
    server: Any,
    cov: Optional[Coverage] = None,
    signum: Optional[int] = None,
    frame: Optional[FrameType] = None
) -> None:
    """Handle graceful shutdown with coverage saving"""
    logger.info("\nShutting down gracefully...")
    if hasattr(server, 'stop'):
        await server.stop()
    if cov is not None:
        cov.stop()
        cov.save()
        logger.info("Coverage data saved to .coverage")
    if signum is not None:
        signal.signal(signum, signal.SIG_DFL)
        if signum == signal.SIGINT:
            raise KeyboardInterrupt()

def create_mcp_server(json_response: bool = False) -> Starlette:
    """Create the MCP server application with both tools and resources"""
    app: Server = Server("mcp-server-with-coverage")

    # Tool endpoints
    @app.call_tool()
    async def greet_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        target_name = arguments.get("name", "World")
        return [types.TextContent(
            type="text",
            text=f"Hello, {target_name}!"
        )]

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="example:greet",
                description="Greet someone with a friendly message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the person to greet"
                        }
                    },
                    "required": []
                }
            )
        ]

    # Resource endpoints
    @app.list_resources()
    async def list_resources() -> List[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl(f"file:///{name}.txt"),
                name=name,
                title=data["title"],
                description=f"A sample text resource named {name}",
                mimeType="text/plain",
            )
            for name, data in SAMPLE_RESOURCES.items()
        ]

    @app.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        # Parse the URI to get the resource name
        uri_str = str(uri)
        if uri_str.startswith("file:///"):
            name = uri_str.replace("file:///", "").replace(".txt", "")
        else:
            name = uri_str.replace(".txt", "").lstrip("/")
            
        if name not in SAMPLE_RESOURCES:
            raise McpError(types.ErrorData(
                code=404,
                message=f"Resource not found: {uri_str}"
            ))
            
        return SAMPLE_RESOURCES[name]["content"]

    # Create session manager
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Lifespan context with coverage support"""
        async with coverage_context() as cov:
            # Set up signal handlers
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                def signal_handler(s: int = sig) -> None:
                    asyncio.create_task(graceful_shutdown(app, cov, s))
                loop.add_signal_handler(sig, signal_handler)
            
            logger.info("Server started")
            # Run the session manager
            async with session_manager.run():
                try:
                    yield
                finally:
                    logger.info("Server shutting down...")

    return Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

async def run_server(port: int = 8000) -> None:
    """Run the server with coverage support"""
    starlette_app = create_mcp_server()
    
    import uvicorn
    config = uvicorn.Config(
        starlette_app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        pass
    finally:
        if not server.started:
            await server.startup()
        if server.started and not server.should_exit:
            await server.shutdown()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    asyncio.run(run_server(port=8001))
