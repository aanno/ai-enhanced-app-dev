import asyncio
import contextlib
import signal
from typing import AsyncIterator, Optional, Any, Dict, List, cast
from types import FrameType

from mcp.server.lowlevel import Server
# from mcp import message
# from mcp.message import ToolRequest, ToolResponse, ResourceRequest, ResourceResponse


try:
    import coverage
    from coverage import Coverage
    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False
    Coverage = Any  # type: ignore

class MyResourceHandler:
    @staticmethod
    async def handle_resource(request: ResourceRequest) -> ResourceResponse:
        if request.method == "GET":
            return ResourceResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                body=b'{"message": "Resource data"}'
            )
        return ResourceResponse(
            status=405,
            headers={},
            body=b'{"error": "Method not allowed"}'
        )

@contextlib.asynccontextmanager
async def coverage_context() -> AsyncIterator[Optional[Coverage]]:
    cov: Optional[Coverage] = None
    if HAS_COVERAGE:
        cov = coverage.Coverage()
        cov.start()
    
    try:
        yield cov
    finally:
        if cov is not None:
            cov.stop()
            cov.save()

async def graceful_shutdown(
    server: Server,
    cov: Optional[Coverage] = None,
    signum: Optional[int] = None,
    frame: Optional[FrameType] = None
) -> None:
    """Handle graceful shutdown with coverage saving"""
    print("\nShutting down gracefully...")
    await server.stop()
    if cov is not None:
        cov.stop()
        cov.save()
        print("Coverage data saved to .coverage")
    if signum is not None:
        signal.signal(signum, signal.SIG_DFL)
        if signum == signal.SIGINT:
            raise KeyboardInterrupt()

async def create_mcp_server(host: str = '127.0.0.1', port: int = 8000) -> Server:
    server = Server(protocol="streamingHttp")
    
    # Register tools using call_tool decorator
    @server.call_tool("example:greet")
    async def greet_tool(request: ToolRequest) -> ToolResponse:
        name = request.body.decode() if request.body else "World"
        return ToolResponse(
            status=200,
            headers={},
            body=f"Hello, {name}!".encode()
        )
    
    # Register resource using read_resource decorator
    @server.read_resource("example:data")
    async def data_resource(request: ResourceRequest) -> ResourceResponse:
        return await MyResourceHandler.handle_resource(request)
    
    # List available endpoints
    @server.list_tools()
    async def list_tools() -> Dict[str, List[str]]:
        return {"tools": ["example:greet"]}
    
    @server.list_resources()
    async def list_resources() -> Dict[str, List[str]]:
        return {"resources": ["example:data"]}
    
    return server

async def run_server() -> None:
    async with coverage_context() as cov:
        server = await create_mcp_server(port=8001)
        
        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(
                    graceful_shutdown(server, cov, s)
                )
            )
        
        try:
            await server.start('127.0.0.1', 8001)
            print(f"Server running on {server.host}:{server.port}")
            await asyncio.get_event_loop().create_future()  # run forever
        except asyncio.CancelledError:
            await graceful_shutdown(server, cov)

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
