# -*- coding: utf-8 -*-
"""Open the Moseley project templates (.rte files, excluding Revit backups).

The folder follows the running Revit version (Revit 2026, Revit 2027, ...)."""
import os
import re
from pyrevit import forms, HOST_APP

TEMPLATE_DIR = os.path.join(
    os.path.expandvars("%userprofile%"),
    "dc", "ACCDocs", "Moseley", "000027 - Revit Template Updates",
    "Project Files", "Revit " + str(HOST_APP.version))
# Revit backups look like "Name 2027.0063.rte".
BACKUP = re.compile(r"\.\d{4}\.rte$", re.IGNORECASE)

if not os.path.isdir(TEMPLATE_DIR):
    forms.alert("Template folder not found:\n" + TEMPLATE_DIR, title="Open Templates")
else:
    paths = sorted(
        os.path.join(TEMPLATE_DIR, name) for name in os.listdir(TEMPLATE_DIR)
        if name.lower().endswith(".rte") and not BACKUP.search(name))
    already_open = set(doc.PathName.lower() for doc in HOST_APP.uiapp.Application.Documents)
    opened, skipped, failed, not_opened = [], [], [], []
    cancelled = False
    with forms.ProgressBar(title="Opening templates: {value} of {max_value}",
                           cancellable=True) as progress:
        for index, path in enumerate(paths):
            if progress.cancelled:
                cancelled = True
                not_opened = [os.path.basename(p) for p in paths[index:]]
                break
            # Revit blocks while a file loads, so the bar refreshes between files.
            progress.update_progress(index + 1, len(paths))
            name = os.path.basename(path)
            if path.lower() in already_open:
                skipped.append(name)
                continue
            try:
                HOST_APP.uiapp.OpenAndActivateDocument(path)
                opened.append(name)
            except Exception as error:
                failed.append("{}: {}".format(name, error))

    lines = []
    if cancelled:
        lines.append("Cancelled. Not opened:\n  " + "\n  ".join(not_opened))
    if opened:
        lines.append("Opened {}:\n  {}".format(len(opened), "\n  ".join(opened)))
    if skipped:
        lines.append("Already open:\n  " + "\n  ".join(skipped))
    if failed:
        lines.append("Failed:\n  " + "\n  ".join(failed))
    forms.alert("\n\n".join(lines) or "No template files found in:\n" + TEMPLATE_DIR, title="Open Templates")
