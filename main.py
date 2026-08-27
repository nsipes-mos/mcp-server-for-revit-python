# -*- coding: utf-8 -*-
import sys
import httpx
import anyio
from mcp.server.fastmcp import FastMCP, Image, Context
import base64
from typing import Optional, Dict, Any, Union

# Create a generic MCP server for interacting with Revit
# Use stateless_http=True and json_response=True for better compatibility
mcp = FastMCP(
    "Revit MCP Server", 
    host="127.0.0.1", 
    port=8000,
    stateless_http=True,
    json_response=True
)

# Configuration
REVIT_HOST = "127.0.0.1"
DEFAULT_REVIT_PORT = 48884

# pyRevit's Routes server assigns each running Revit process its own port,
# starting at DEFAULT_REVIT_PORT and incrementing for every additional
# instance already running (see pyrevit.routes.server.serverinfo). This is
# how many sequential ports we'll probe when looking for a live instance to
# ask for the full sister list.
PORT_SCAN_RANGE = 16

# Currently targeted Revit instance. Defaults to the base port; switch it
# with the select_revit_instance tool once multiple Revit versions are open.
_active_port = DEFAULT_REVIT_PORT
_active_version = None


def _base_url() -> str:
    return f"http://{REVIT_HOST}:{_active_port}/revit_mcp"


async def discover_revit_instances() -> list:
    """Enumerate every running Revit instance with pyRevit Routes active.

    Every pyRevit Routes server exposes a built-in `/routes/sisters`
    endpoint that lists ALL registered Routes servers on the machine (one
    per running Revit process), regardless of which port answers. So we
    only need to find one live port to get the complete picture.
    """
    async with httpx.AsyncClient(timeout=3.0) as client:
        for port in range(DEFAULT_REVIT_PORT, DEFAULT_REVIT_PORT + PORT_SCAN_RANGE):
            try:
                response = await client.get(f"http://{REVIT_HOST}:{port}/routes/sisters")
                if response.status_code == 200:
                    return response.json()
            except Exception:
                continue
    return []


async def revit_get(endpoint: str, ctx: Context = None, **kwargs) -> Union[Dict, str]:
    """Simple GET request to Revit API"""
    return await _revit_call("GET", endpoint, ctx=ctx, **kwargs)


async def revit_post(endpoint: str, data: Dict[str, Any], ctx: Context = None, **kwargs) -> Union[Dict, str]:
    """Simple POST request to Revit API"""
    return await _revit_call("POST", endpoint, data=data, ctx=ctx, **kwargs)


async def revit_image(endpoint: str, ctx: Context = None) -> Union[Image, str]:
    """GET request that returns an Image object"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{_base_url()}{endpoint}")

            if response.status_code == 200:
                data = response.json()
                image_bytes = base64.b64decode(data["image_data"])
                return Image(data=image_bytes, format="png")
            else:
                return f"Error: {response.status_code} - {response.text}"
    except httpx.TimeoutException:
        return "Error: Image export timed out after 60 seconds."
    except Exception as e:
        msg = str(e) or type(e).__name__
        return f"Error: {msg}"


async def _revit_call(method: str, endpoint: str, data: Dict = None, ctx: Context = None,
                     timeout: float = 30.0, params: Dict = None) -> Union[Dict, str]:
    """Internal function handling all HTTP calls"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{_base_url()}{endpoint}"

            if method == "GET":
                response = await client.get(url, params=params)
            else:  # POST
                response = await client.post(url, json=data, headers={"Content-Type": "application/json"})

            return response.json() if response.status_code == 200 else f"Error: {response.status_code} - {response.text}"
    except httpx.TimeoutException:
        return f"Error: Request timed out after {timeout} seconds. The operation may still be running in Revit."
    except Exception as e:
        msg = str(e) or type(e).__name__
        return f"Error: {msg}"


# Register all tools BEFORE the main block
from tools import register_tools
register_tools(mcp, revit_get, revit_post, revit_image)


@mcp.tool()
async def list_revit_instances() -> str:
    """List every running Revit instance with pyRevit Routes active on this machine.

    Each running Revit process (e.g. 2026 and 2027 open at the same time) gets
    its own Routes port automatically. Use select_revit_instance() to choose
    which one subsequent tool calls talk to.
    """
    instances = await discover_revit_instances()
    if not instances:
        return "No running Revit instances with pyRevit Routes were found."

    lines = ["=== RUNNING REVIT INSTANCES ==="]
    for inst in instances:
        marker = " (active)" if inst["server_port"] == _active_port else ""
        lines.append(
            "Version {version} - port {port} - pid {pid} - {host}{marker}".format(
                version=inst.get("version", "?"),
                port=inst.get("server_port", "?"),
                pid=inst.get("process_id", "?"),
                host=inst.get("host", "?"),
                marker=marker,
            )
        )
    return "\n".join(lines)


@mcp.tool()
async def select_revit_instance(version: str) -> str:
    """Target a specific running Revit version for all subsequent tool calls.

    Args:
        version: Revit version year to target, e.g. "2026" or "2027". Must
            match one of the instances returned by list_revit_instances().
    """
    global _active_port, _active_version

    instances = await discover_revit_instances()
    if not instances:
        return "No running Revit instances with pyRevit Routes were found."

    match = next((i for i in instances if str(i.get("version")) == str(version)), None)
    if not match:
        available = ", ".join(sorted({str(i.get("version")) for i in instances})) or "none"
        return f"Error: no running Revit {version} instance found. Available: {available}"

    _active_port = match["server_port"]
    _active_version = match["version"]
    return "Now targeting Revit {version} on port {port} ({host}).".format(
        version=match["version"], port=match["server_port"], host=match.get("host", "?")
    )


async def run_combined_async():
    """Run server with both SSE and streamable-http endpoints.

    This allows clients to connect via either:
    - SSE: GET /sse, POST /messages/
    - Streamable-HTTP: POST/GET /mcp
    """
    import uvicorn

    # Get the streamable-http app first - it has the proper lifespan
    # that initializes the session manager's task group
    http_app = mcp.streamable_http_app()

    # Get SSE routes (SSE doesn't need special lifespan - it creates
    # task groups per-request in connect_sse())
    sse_app = mcp.sse_app()

    # Add SSE routes to the http app (preserving its lifespan)
    for route in sse_app.routes:
        http_app.routes.append(route)

    config = uvicorn.Config(
        http_app,
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    transport = "stdio"

    if "--sse" in sys.argv:
        transport = "sse"
    elif "--http" in sys.argv or "--streamable-http" in sys.argv:
        transport = "streamable-http"
    elif "--combined" in sys.argv:
        # Run both SSE and streamable-http transports simultaneously
        print("Starting combined server with SSE (/sse, /messages/) and streamable-http (/mcp) endpoints...")
        anyio.run(run_combined_async)
        sys.exit(0)

    mcp.run(transport=transport)