# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys
import httpx
import anyio
from mcp.server.fastmcp import FastMCP, Image, Context
import base64
from typing import Optional, Dict, Any, Union
from revit_mcp.pairing import authorization_headers
from tools.http_security import PairingMiddleware

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
# The submitted local architecture only connects to the same machine.
# Remote pyRevit Routes requires a separately reviewed authenticated HTTPS design.
REVIT_HOST = os.environ.get("REVIT_HOST", "127.0.0.1")
if REVIT_HOST not in {"127.0.0.1", "localhost", "::1"}:
    raise ValueError("REVIT_HOST must be loopback; remote HTTP bridges are not supported.")
REVIT_PORT = int(os.environ.get("REVIT_PORT", "48884"))
if not 1 <= REVIT_PORT <= 65535:
    raise ValueError("REVIT_PORT must be between 1 and 65535.")
URL_HOST = "[::1]" if REVIT_HOST == "::1" else REVIT_HOST
BASE_URL = f"http://{URL_HOST}:{REVIT_PORT}/revit_mcp"

# Several Revit versions can run side by side, each with its own pyRevit Routes
# port. Setting REVIT_VERSION (e.g. "2027") selects the port by asking Windows
# which running Revit.exe owns each candidate port. An explicit REVIT_PORT wins.
REVIT_VERSION = os.environ.get("REVIT_VERSION", "").strip()
if REVIT_VERSION and not re.fullmatch(r"20\d\d", REVIT_VERSION):
    raise ValueError("REVIT_VERSION must be a four-digit Revit year such as 2027.")
REVIT_PORT_SCAN = range(48884, 48904)


def _process_path(pid):
    """Full executable path for a process id, or None."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value
        return None
    finally:
        kernel32.CloseHandle(handle)


def scan_revit_instances():
    """Every running Revit.exe with a Routes port: [{"version", "port", "pid"}]."""
    if sys.platform != "win32":
        return []
    output = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True,
                            text=True, timeout=10).stdout
    found = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[3] != "LISTENING":
            continue
        host, _, port = parts[1].rpartition(":")
        if host not in {"127.0.0.1", "[::1]"} or not port.isdigit():
            continue
        port = int(port)
        if port not in REVIT_PORT_SCAN:
            continue
        pid = int(parts[4])
        path = _process_path(pid) or ""
        match = re.search(r"Revit (20\d\d)", path)
        if match and path.lower().endswith("revit.exe"):
            found.append({"version": match.group(1), "port": port, "pid": pid})
    return sorted(found, key=lambda item: item["port"])


def find_revit_ports():
    """Map Revit year -> pyRevit Routes port (lowest port if a year runs twice)."""
    ports = {}
    for item in scan_revit_instances():
        ports.setdefault(item["version"], item["port"])
    return ports


# The version calls are routed to; select_revit_instance changes it at runtime.
_selected_version = REVIT_VERSION


def _routes_url(port):
    return f"http://{URL_HOST}:{port}/revit_mcp"


def _version_port(version):
    ports = find_revit_ports()
    if version not in ports:
        running = ", ".join(sorted(ports)) or "none"
        raise RuntimeError(f"Revit {version} is not running with the MCP bridge "
                           f"listening. Running versions: {running}.")
    return ports[version]


def _base_url():
    """Routes URL for the selected Revit; re-resolved on every call so a
    restarted Revit that came up on a different port is picked up."""
    if "REVIT_PORT" in os.environ:
        return BASE_URL
    if _selected_version:
        return _routes_url(_version_port(_selected_version))
    # Nothing chosen: a lone running Revit is unambiguous; otherwise keep the
    # default port (the first Revit started).
    instances = scan_revit_instances()
    if len(instances) == 1:
        return _routes_url(instances[0]["port"])
    return BASE_URL


async def list_revit_instances():
    """Running Revit instances with the open document, flagged if selected."""
    instances = scan_revit_instances()
    selected = _selected_version or None
    async with httpx.AsyncClient(timeout=10.0, trust_env=False,
                                 headers=authorization_headers()) as client:
        for item in instances:
            try:
                response = await client.get(_routes_url(item["port"]) + "/status/")
                item["document"] = response.json().get("document_title")
            except Exception:
                item["document"] = None
            item["selected"] = item["version"] == selected
    return instances


def select_revit_instance(version):
    """Route later calls to the running Revit of this year ("default" resets)."""
    global _selected_version
    if "REVIT_PORT" in os.environ:
        raise RuntimeError("REVIT_PORT is set in the connector's environment, which "
                           "fixes the target. Remove it to select by version.")
    if version.strip().lower() in {"", "default"}:
        _selected_version = REVIT_VERSION
        return {"selected": _selected_version or None, "port": REVIT_PORT}
    version = version.strip()
    if not re.fullmatch(r"20\d\d", version):
        raise ValueError("version must be a four-digit Revit year such as 2027.")
    port = _version_port(version)
    _selected_version = version
    return {"selected": version, "port": port}


async def revit_get(endpoint: str, ctx: Context = None, **kwargs) -> Union[Dict, str]:
    """Simple GET request to Revit API"""
    return await _revit_call("GET", endpoint, ctx=ctx, **kwargs)


async def revit_post(endpoint: str, data: Dict[str, Any], ctx: Context = None, **kwargs) -> Union[Dict, str]:
    """Simple POST request to Revit API"""
    return await _revit_call("POST", endpoint, data=data, ctx=ctx, **kwargs)


async def revit_image(endpoint: str, ctx: Context = None) -> Union[Image, str]:
    """GET request that returns an Image object"""
    try:
        async with httpx.AsyncClient(timeout=60.0, trust_env=False, headers=authorization_headers()) as client:
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
        async with httpx.AsyncClient(timeout=timeout, trust_env=False, headers=authorization_headers()) as client:
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
register_tools(mcp, revit_get, revit_post, revit_image,
               instances=(list_revit_instances, select_revit_instance))


def build_http_app(transport):
    """Build an authenticated app for the selected loopback transport."""
    if transport not in {"sse", "streamable-http", "combined"}:
        raise ValueError("Unknown HTTP transport.")
    if transport == "sse":
        http_app = mcp.sse_app()
    else:
        http_app = mcp.streamable_http_app()
        if transport == "combined":
            http_app.routes.extend(mcp.sse_app().routes)
    http_app.add_middleware(PairingMiddleware)
    return http_app


async def run_http_async(transport):
    """Run paired, loopback-only SSE, streamable HTTP, or both."""
    import uvicorn
    http_app = build_http_app(transport)

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
        transport = "combined"

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        anyio.run(run_http_async, transport)