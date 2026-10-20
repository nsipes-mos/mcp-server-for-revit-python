# -*- coding: utf-8 -*-
"""Revoke MCP pairing for this Windows user."""
import os
import sys
from pyrevit import forms
extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)
from revit_mcp.pairing import disable_pairing, PairingError

try:
    disable_pairing()
    forms.alert("Disconnected. Subsequent MCP requests are denied. An operation already running may still finish.", title="Revit MCP")
except (PairingError, OSError) as error:
    forms.alert(str(error), title="Revit MCP disconnect failed")
