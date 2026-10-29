# -*- coding: utf-8 -*-
"""Close every open document, asking before unsaved changes are discarded."""
import os
import sys
from pyrevit import forms, HOST_APP
from Autodesk.Revit.UI import RevitCommandId, PostableCommand

extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)
from revit_mcp.document import _answer_next_save_prompt

IDNO = 7

uiapp = HOST_APP.uiapp
documents = [doc for doc in list(uiapp.Application.Documents) if not doc.IsLinked]
active_uidoc = uiapp.ActiveUIDocument
active = active_uidoc.Document if active_uidoc else None

if not documents:
    forms.alert("No open documents.", title="Close All")
else:
    unsaved = [doc.Title for doc in documents if doc.IsModified]
    proceed = True
    if unsaved:
        proceed = forms.alert(
            "These documents have unsaved changes that will be discarded:\n  {}\n\n"
            "Close all documents anyway?".format("\n  ".join(unsaved)),
            title="Close All", yes=True, no=True, warn_icon=True)
    if proceed:
        closed, failed = [], []
        # The active document cannot be closed with Document.Close, so close the
        # others first and post the Close command for the active one last.
        for doc in documents:
            if active is not None and doc == active:
                continue
            title = doc.Title
            try:
                doc.Close(False)
                closed.append(title)
            except Exception as error:
                failed.append("{}: {}".format(title, error))
        if active is not None:
            title = active.Title
            handler = None
            if active.IsModified:
                handler = _answer_next_save_prompt(uiapp, IDNO, title)
            try:
                uiapp.PostCommand(RevitCommandId.LookupPostableCommandId(PostableCommand.Close))
                closed.append(title)
            except Exception as error:
                if handler is not None:
                    uiapp.DialogBoxShowing -= handler
                failed.append("{}: {}".format(title, error))
        if failed:
            forms.alert("Closed {}.\n\nFailed:\n  {}".format(len(closed), "\n  ".join(failed)),
                        title="Close All")
