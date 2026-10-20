# -*- coding: utf-8 -*-
"""Pair the local MCP client after explicit data-access consent."""
import os
import sys
from pyrevit import forms

extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)
from revit_mcp.pairing import enable_pairing, PairingError

notice = (
    "Allow this Windows user's MCP clients to read Revit model data and request changes?\n\n"
    "Pairing also permits discovery and launch of installed Revit versions.\n\n"
    "Responses may include project/client names, model paths, parameter values, rooms, "
    "linked-model details and view images. Your chosen AI client may send responses to its provider. "
    "Check that client's privacy settings and use only models you may share.\n\n"
    "Model changes and Python execution require a separate review in Revit. Python is not sandboxed "
    "and can access your files and network. Other processes running as you can access this pairing.\n\n"
    "Pairing persists until you click Disconnect. Connect again rotates the secret. "
    "Privacy details are available from the Privacy button."
)
if forms.alert(notice, title="Connect Revit MCP", ok=False, yes=True, no=True, warn_icon=True):
    try:
        enable_pairing()
        forms.alert("Paired. Enable the pyRevit Routes server if it is not running, then connect your local MCP client.",
                    title="Revit MCP")
    except (PairingError, OSError) as error:
        forms.alert(str(error), title="Revit MCP pairing failed")
