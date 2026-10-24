# -*- coding: utf-8 -*-
"""Temporary development helper: reload pyRevit to pick up extension changes."""
from pyrevit.loader import sessionmgr

sessionmgr.reload_pyrevit()
