# -*- coding: utf-8 -*-
"""Revoke MCP pairing for this Windows user."""
import os
import sys
from pyrevit import forms
extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)
from pyrevit.coreutils.ribbon import ICON_SMALL
from revit_mcp import auto_approve_ui
from revit_mcp.pairing import disable_pairing, PairingError


def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
    ui_button_cmp.set_icon(auto_approve_ui.disconnect_icon(), icon_size=ICON_SMALL)
    return True


if __name__ == "__main__":
    try:
        disable_pairing()
        try:
            auto_approve_ui.refresh_icons()
        except Exception:
            pass
        forms.alert("Disconnected. Subsequent MCP requests are denied. An operation already running may still finish.", title="Revit MCP")
    except (PairingError, OSError) as error:
        forms.alert(str(error), title="Revit MCP disconnect failed")
