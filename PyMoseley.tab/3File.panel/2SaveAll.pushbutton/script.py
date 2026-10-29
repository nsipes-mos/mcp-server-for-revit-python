# -*- coding: utf-8 -*-
"""Save every open, modified document that already has a file path.

Modified project templates (.rte) with a "Template Version" parameter on
Project Information are stamped with today's date before saving.
"""
import datetime
from Autodesk.Revit.DB import StorageType, Transaction
from pyrevit import forms, HOST_APP

VERSION_PARAMETER = "Template Version"
DATE_FORMAT = "%Y-%m-%d"


def stamp_template_version(doc):
    """Set Template Version to today's date; return a note for the report, or None."""
    if not doc.PathName.lower().endswith(".rte"):
        return None
    info = doc.ProjectInformation
    param = info.LookupParameter(VERSION_PARAMETER) if info else None
    if param is None:
        return "Template Version parameter missing"
    if param.IsReadOnly:
        return "Template Version not usable (read-only)"
    if param.StorageType != StorageType.String:
        return "Template Version not usable (not a text parameter)"
    today = datetime.date.today().strftime(DATE_FORMAT)
    if param.AsString() == today:
        return None
    transaction = Transaction(doc, "Update Template Version")
    transaction.Start()
    try:
        param.Set(today)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    return "Template Version set to " + today


saved, skipped, failed = [], [], []
for doc in list(HOST_APP.uiapp.Application.Documents):
    if doc.IsLinked:
        continue
    title = doc.Title
    if not doc.PathName:
        skipped.append(title + " (never saved; use Save As)")
    elif doc.IsReadOnly:
        skipped.append(title + " (read-only)")
    elif not doc.IsModified:
        continue
    else:
        try:
            note = stamp_template_version(doc)
            doc.Save()
            saved.append(title + (" ({})".format(note) if note else ""))
        except Exception as error:
            failed.append("{}: {}".format(title, error))

lines = []
if saved:
    lines.append("Saved {}:\n  {}".format(len(saved), "\n  ".join(saved)))
if skipped:
    lines.append("Skipped:\n  " + "\n  ".join(skipped))
if failed:
    lines.append("Failed:\n  " + "\n  ".join(failed))
forms.alert("\n\n".join(lines) or "No unsaved changes in any open document.", title="Save All")
