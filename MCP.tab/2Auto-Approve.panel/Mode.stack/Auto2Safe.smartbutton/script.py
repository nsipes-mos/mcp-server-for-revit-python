# -*- coding: utf-8 -*-
"""Set the Revit MCP auto-approve mode to "safe"."""
import os
import sys
from pyrevit import forms
from pyrevit.coreutils.ribbon import ICON_SMALL
extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)
from revit_mcp import auto_approve_ui
from revit_mcp.pairing import PairingError

MODE = "safe"


def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
    ui_button_cmp.set_icon(auto_approve_ui.icon_for(MODE), icon_size=ICON_SMALL)
    return True


if __name__ == "__main__":
    try:
        auto_approve_ui.select(MODE)
    except (PairingError, OSError) as error:
        forms.alert(str(error), title="Revit MCP auto-approve failed")
