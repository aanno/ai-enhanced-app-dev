import asyncio
import atexit
import contextlib
import logging
import signal
from types import FrameType
from typing import Any, AsyncIterator, Dict, List, Optional

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
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

# Contextual data resource - independent from schemas
SERVER_STATUS_DATA = {
    "server": {
        "name": "mcp-server-with-coverage",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": 0,
        "capabilities": ["tools", "resources", "json_schemas"]
    },
    "tools": {
        "available": ["example:greet", "example:greetingJson"],
        "total_calls": 0
    },
    "resources": {
        "available": 3,
        "types": ["text", "schema", "status"]
    }
}

# JSON Schemas for tools
JSON_SCHEMAS = {
    "example:greet:args": {
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
    },
    "example:greet:result": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["text"]},
                "text": {"type": "string"}
            },
            "required": ["type", "text"]
        }
    },
    "example:greetingJson:args": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the person to greet",
                "default": "World"
            },
            "include_details": {
                "type": "boolean",
                "description": "Include additional details in response",
                "default": False
            },
            "preferences": {
                "type": "object",
                "description": "User preferences",
                "properties": {
                    "language": {"type": "string", "enum": ["en", "es", "fr", "de"]},
                    "format": {"type": "string", "enum": ["simple", "detailed"]}
                }
            }
        },
        "required": ["name"]
    },
    "example:greetingJson:result": {
        "type": "object",
        "properties": {
            "greeting": {"type": "string"},
            "timestamp": {"type": "string"},
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "preferences": {"type": "object"}
                }
            },
            "server_info": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"}
                }
            }
        },
        "required": ["greeting"]
    }
}


@contextlib.asynccontextmanager
async def coverage_context(enable_coverage: bool = False) -> AsyncIterator[Optional[Coverage]]:
    """Context manager for coverage collection with robust cleanup"""
    cov: Optional[Coverage] = None
    if HAS_COVERAGE and enable_coverage:
        try:
            cov = coverage.Coverage()
            if cov is not None:
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

    # Don't re-raise KeyboardInterrupt to avoid task exception
    logger.info("Graceful shutdown completed")


def create_mcp_server(json_response: bool = False, enable_coverage: bool = False) -> Starlette:
    """Create the MCP server application with both tools and resources"""
    app: Server = Server("mcp-server-with-coverage")

    # Tool endpoints
    @app.call_tool()
    async def greet_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        import jsonschema
        
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

        result = [types.TextContent(
            type="text",
            text="\n".join(message_parts)
        )]
        
        # Validate result against output schema
        try:
            result_data = [{"type": "text", "text": result[0].text}]
            jsonschema.validate(result_data, JSON_SCHEMAS["example:greet:result"])
        except jsonschema.ValidationError as e:
            logger.warning(f"Tool result validation failed for example:greet: {e.message}")
        except Exception as e:
            logger.warning(f"Result validation error for example:greet: {e}")
        
        return result

    @app.call_tool()
    async def greetingJson_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        import datetime
        import json
        import jsonschema

        # Extract arguments
        target_name = arguments.get("name", "World")
        include_details = arguments.get("include_details", False)
        preferences = arguments.get("preferences", {})

        # Build JSON response
        response = {
            "greeting": f"Hello, {target_name}!",
            "timestamp": datetime.datetime.now().isoformat()
        }

        if include_details:
            response["user"] = {
                "name": target_name,
                "preferences": preferences
            }
            response["server_info"] = {
                "name": "mcp-server-with-coverage",
                "version": "1.0.0"
            }

        result = [types.TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
        
        # Validate result against output schema
        try:
            # Parse the JSON response to validate its structure
            parsed_response = json.loads(result[0].text)
            jsonschema.validate(parsed_response, JSON_SCHEMAS["example:greetingJson:result"])
        except jsonschema.ValidationError as e:
            logger.warning(f"Tool result validation failed for example:greetingJson: {e.message}")
        except Exception as e:
            logger.warning(f"Result validation error for example:greetingJson: {e}")
        
        return result

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="example:greet",
                description="Greet someone with a customizable message in different languages",
                inputSchema=JSON_SCHEMAS["example:greet:args"],
                outputSchema=JSON_SCHEMAS["example:greet:result"],
                # Custom metadata for schema references
                annotations=types.ToolAnnotations(
                    audience=["developer"],
                    tags=["greeting", "text"]
                ),
                meta={
                    "args_schema_resource": "example:greet:args:schema",
                    "result_schema_resource": "example:greet:result:schema",
                    "result_mime_type": "text/plain"
                }
            ),
            types.Tool(
                name="example:greetingJson",
                description="Greet someone and return structured JSON response",
                inputSchema=JSON_SCHEMAS["example:greetingJson:args"],
                outputSchema=JSON_SCHEMAS["example:greetingJson:result"],
                annotations=types.ToolAnnotations(
                    audience=["developer"],
                    tags=["greeting", "json"]
                ),
                meta={
                    "args_schema_resource": "example:greetingJson:args:schema",
                    "result_schema_resource": "example:greetingJson:result:schema",
                    "result_mime_type": "application/json"
                }
            )
        ]

    # Resource endpoints
    @app.list_resources()
    async def list_resources() -> List[types.Resource]:
        resources = []

        # Add regular text resources
        for name, data in SAMPLE_RESOURCES.items():
            resources.append(types.Resource(
                uri=AnyUrl(f"file:///{name}.txt"),
                name=name,
                title=data["title"],
                description=f"A sample text resource named {name}",
                mimeType="text/plain",
            ))
        
        # Add server status resource (contextual data)
        resources.append(types.Resource(
            uri=AnyUrl("internal:///server-status"),
            name="server-status",
            title="Server Status Information",
            description="Current server status, uptime, and statistics",
            mimeType="application/json",
        ))

        # Add JSON schema resources
        for schema_name in JSON_SCHEMAS.keys():
            resource_name = f"{schema_name}:schema"
            resources.append(types.Resource(
                uri=AnyUrl(f"file:///{resource_name}.json"),
                name=resource_name,
                title=f"JSON Schema for {schema_name}",
                description=f"JSON Schema definition for {schema_name}",
                mimeType="application/schema+json",
            ))

        return resources

    @app.read_resource()
    async def read_resource(uri: AnyUrl) -> List[ReadResourceContents]:
        import json
        import time
        uri_str = str(uri)

        # Handle internal:// resources (server status)
        if uri_str == "internal:///server-status":
            # Update dynamic data
            status_data = SERVER_STATUS_DATA.copy()
            status_data["server"]["uptime_seconds"] = int(time.time()) % 3600  # Simple uptime simulation
            status_data["timestamp"] = time.time()
            
            return [ReadResourceContents(
                content=json.dumps(status_data, indent=2),
                mime_type="application/json"
            )]

        # Handle file:// resources
        if uri_str.startswith("file:///"):
            resource_name = uri_str.replace("file:///", "")

            # Handle schema resources (end with :schema.json)
            if resource_name.endswith(":schema.json"):
                schema_key = resource_name.replace(":schema.json", "")
                if schema_key not in JSON_SCHEMAS:
                    raise McpError(types.ErrorData(
                        code=404,
                        message=f"Schema not found: {schema_key}"
                    ))

                return [ReadResourceContents(
                    content=json.dumps(JSON_SCHEMAS[schema_key], indent=2),
                    mime_type="application/schema+json"
                )]

            # Handle regular text resources (end with .txt)
            elif resource_name.endswith(".txt"):
                name = resource_name.replace(".txt", "")
                if name not in SAMPLE_RESOURCES:
                    raise McpError(types.ErrorData(
                        code=404,
                        message=f"Resource not found: {name}"
                    ))

                return [ReadResourceContents(
                    content=SAMPLE_RESOURCES[name]["content"],
                    mime_type="text/plain"
                )]

        # Fallback for other URI formats
        raise McpError(types.ErrorData(
            code=404,
            message=f"Resource not found: {uri_str}"
        ))

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
        print("\n🛑 Shutting down server gracefully...")
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        try:
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
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server gracefully...")
        print("👋 Server stopped.")
    except Exception as e:
        logger.error(f"Fatal server error: {e}")
        raise


if __name__ == "__main__":
    main()
