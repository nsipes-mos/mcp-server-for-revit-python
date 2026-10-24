# -*- coding: utf-8 -*-
"""Ribbon status circles: Auto-Approve mode, and Connect/Disconnect pairing state."""
import os
from .pairing import get_auto_approve, set_auto_approve, get_token, PairingError

IMAGES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")
TAB_NAME = "PyMoseley"
AUTO_BUTTONS = {"Auto1Off": "off", "Auto2Safe": "safe", "Auto3All": "all"}


def _image(color):
    return os.path.join(IMAGES, "auto_{}.png".format(color))


def is_paired():
    try:
        get_token()
        return True
    except Exception:
        # IronPython 2 raises IOError (not an OSError) for a missing file,
        # and DPAPI failures vary; any failure means not paired.
        return False


def icon_for(mode):
    return _image("green" if get_auto_approve() == mode else "gray")


def connect_icon():
    """Green while paired."""
    return _image("green" if is_paired() else "gray")


def disconnect_icon():
    """Red while disconnected."""
    return _image("gray" if is_paired() else "red")


def _icon_for_button(name):
    if name in AUTO_BUTTONS:
        return icon_for(AUTO_BUTTONS[name])
    if name == "Connect":
        return connect_icon()
    if name == "Disconnect":
        return disconnect_icon()
    return None


def _walk(component):
    yield component
    for sub in list(getattr(component, "_sub_pyrvt_components", {}).values()):
        for found in _walk(sub):
            yield found


def refresh_icons():
    from pyrevit.coreutils.ribbon import get_current_ui, ICON_SMALL
    for tab in get_current_ui().get_pyrevit_tabs():
        if getattr(tab, "name", None) != TAB_NAME:
            continue
        for component in _walk(tab):
            icon = _icon_for_button(getattr(component, "name", None))
            if icon and hasattr(component, "set_icon"):
                component.set_icon(icon, icon_size=ICON_SMALL)


def select(mode):
    set_auto_approve(mode)
    refresh_icons()
