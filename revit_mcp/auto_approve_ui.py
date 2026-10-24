# -*- coding: utf-8 -*-
"""Ribbon helpers for the Auto-Approve tab: gray circle, green when active."""
import os
from .pairing import get_auto_approve, set_auto_approve

BUTTONS = {"Auto1Off": "off", "Auto2Safe": "safe", "Auto3All": "all"}
IMAGES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")


def icon_for(mode):
    name = "auto_green.png" if get_auto_approve() == mode else "auto_gray.png"
    return os.path.join(IMAGES, name)


def _walk(component):
    yield component
    for sub in list(getattr(component, "_sub_pyrvt_components", {}).values()):
        for found in _walk(sub):
            yield found


def refresh_icons():
    from pyrevit.coreutils.ribbon import get_current_ui, ICON_SMALL
    for tab in get_current_ui().get_pyrevit_tabs():
        for component in _walk(tab):
            mode = BUTTONS.get(getattr(component, "name", None))
            if mode and hasattr(component, "set_icon"):
                component.set_icon(icon_for(mode), icon_size=ICON_SMALL)


def select(mode):
    set_auto_approve(mode)
    refresh_icons()
