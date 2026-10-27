# -*- coding: utf-8 -*-
"""Tools for working with several running Revit versions"""

import json
from mcp.server.fastmcp import Context


def register_instance_tools(mcp, list_instances, select_instance):
    """Register running-instance discovery and selection tools"""

    @mcp.tool()
    async def list_revit_instances(ctx: Context) -> str:
        """List running Revit instances on this machine.

        Shows each instance's version, bridge port and open document, and which
        one MCP tools are currently sent to. Use this when more than one Revit
        version is open.
        """
        try:
            instances = await list_instances()
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)}, indent=2)
        return json.dumps(
            {"status": "success", "instances": instances, "count": len(instances)},
            indent=2,
        )

    @mcp.tool()
    async def select_revit_instance(ctx: Context, version: str) -> str:
        """Send later MCP tool calls to the running Revit of a given version.

        Args:
            version: Revit year such as "2027", or "default" to restore the
                connector's configured target.
        """
        try:
            result = select_instance(version)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)}, indent=2)
        return json.dumps({"status": "success", **result}, indent=2)
