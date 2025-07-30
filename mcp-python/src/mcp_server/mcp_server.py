import asyncio
import contextlib
import signal
import json
import logging
import anyio
import click
import atexit
from typing import AsyncIterator, Optional, Any, Dict, List
from types import FrameType

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.shared.exceptions import McpError
from mcp.server.lowlevel.helper_types import ReadResourceContents
from pydantic import AnyUrl
from typing import List
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
async def coverage_context(enable_coverage: bool = False) -> AsyncIterator[Optional[Coverage]]:
    """Context manager for coverage collection with robust cleanup"""
    cov: Optional[Coverage] = None
    if HAS_COVERAGE and enable_coverage:
        try:
            cov = coverage.Coverage()
            cov.start()
            logger.info("Coverage collection started")
        except Exception as e:
            logger.error(f"Failed to start coverage: {e}")
            cov = None
    
    try:
        yield cov
    finally:
        if cov is not None:
            try:
                logger.info("Stopping coverage collection...")
                cov.stop()
                cov.save()
                logger.info("Coverage data saved to .coverage")
            except Exception as e:
                logger.error(f"Error saving coverage data: {e}")
                # Try to save anyway with basic filename
                try:
                    cov.save()
                except Exception:
                    pass

async def graceful_shutdown(
    server: Any,
    cov: Optional[Coverage] = None,
    signum: Optional[int] = None,
    frame: Optional[FrameType] = None
) -> None:
    """Handle graceful shutdown with robust coverage saving"""
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
    
    # Save coverage data first (most important)
    if cov is not None:
        try:
            logger.info("Saving coverage data on shutdown...")
            cov.stop()
            cov.save()
            logger.info("Coverage data saved to .coverage")
        except Exception as e:
            logger.error(f"Error saving coverage on shutdown: {e}")
    
    # Stop server
    try:
        if hasattr(server, 'stop'):
            await server.stop()
    except Exception as e:
        logger.error(f"Error stopping server: {e}")
    
    # Reset signal handler and exit
    if signum is not None:
        signal.signal(signum, signal.SIG_DFL)
        if signum == signal.SIGINT:
            raise KeyboardInterrupt()

def create_mcp_server(json_response: bool = False, enable_coverage: bool = False) -> Starlette:
    """Create the MCP server application with both tools and resources"""
    app: Server = Server("mcp-server-with-coverage")

    # Tool endpoints
    @app.call_tool()
    async def greet_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        # Handle various argument types
        target_name = arguments.get("name", "World")
        greeting = arguments.get("greeting", "Hello")
        language = arguments.get("language", "en")
        include_time = arguments.get("include_time", False)
        user_info = arguments.get("user_info", {})
        
        # Build response based on arguments
        message_parts = []
        
        # Greeting in different languages
        greetings = {
            "en": greeting,
            "es": "Hola",
            "fr": "Bonjour", 
            "de": "Hallo"
        }
        
        selected_greeting = greetings.get(language, greeting)
        message_parts.append(f"{selected_greeting}, {target_name}!")
        
        # Add user info if provided
        if user_info:
            if "role" in user_info:
                message_parts.append(f"Role: {user_info['role']}")
            if "team" in user_info:
                message_parts.append(f"Team: {user_info['team']}")
        
        # Add timestamp if requested
        if include_time:
            import datetime
            message_parts.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return [types.TextContent(
            type="text",
            text="\n".join(message_parts)
        )]

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="example:greet",
                description="Greet someone with a customizable message in different languages",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the person to greet",
                            "default": "World"
                        },
                        "greeting": {
                            "type": "string", 
                            "description": "Custom greeting text (overridden by language setting)",
                            "default": "Hello"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language for greeting",
                            "enum": ["en", "es", "fr", "de"],
                            "default": "en"
                        },
                        "include_time": {
                            "type": "boolean",
                            "description": "Include current timestamp in response",
                            "default": False
                        },
                        "user_info": {
                            "type": "object",
                            "description": "Additional user information to include",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "description": "User's role"
                                },
                                "team": {
                                    "type": "string", 
                                    "description": "User's team"
                                }
                            }
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
    async def read_resource(uri: AnyUrl) -> List[ReadResourceContents]:
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
            
        return [ReadResourceContents(
            content=SAMPLE_RESOURCES[name]["content"],
            mime_type="text/plain"
        )]

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
        async with coverage_context(enable_coverage) as cov:
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

async def run_server(port: int = 8000, enable_coverage: bool = False) -> None:
    """Run the server with optional coverage support"""
    starlette_app = create_mcp_server(enable_coverage=enable_coverage)
    
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
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        try:
            if not server.started:
                await server.startup()
            if server.started and not server.should_exit:
                await server.shutdown()
        except Exception as e:
            logger.error(f"Error during server cleanup: {e}")

@click.command()
@click.option(
    '--port', 
    default=8001, 
    type=int, 
    help='Port number to run the MCP server on (default: 8001)'
)
@click.option(
    '--coverage',
    is_flag=True,
    help='Enable code coverage collection during server execution'
)
def main(port: int, coverage: bool) -> None:
    """Start the MCP server with optional coverage support."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Global coverage instance for atexit handler
    global_coverage: Optional[Coverage] = None
    
    def cleanup_coverage():
        """Emergency coverage cleanup on process exit"""
        if global_coverage is not None and HAS_COVERAGE and coverage:
            try:
                logger.info("Emergency coverage cleanup on exit...")
                global_coverage.stop()
                global_coverage.save()
                logger.info("Emergency coverage data saved")
            except Exception as e:
                logger.error(f"Error in emergency coverage cleanup: {e}")
    
    if coverage and HAS_COVERAGE:
        atexit.register(cleanup_coverage)
        print(f"🚀 Starting MCP server on port {port} with coverage enabled")
    else:
        print(f"🚀 Starting MCP server on port {port}")
    
    try:
        asyncio.run(run_server(port=port, enable_coverage=coverage))
    except Exception as e:
        logger.error(f"Fatal server error: {e}")
        raise


if __name__ == "__main__":
    main()
