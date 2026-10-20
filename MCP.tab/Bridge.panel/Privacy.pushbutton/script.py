# -*- coding: utf-8 -*-
"""Open the privacy information shipped with this extension."""
import os
from pyrevit import script
extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
privacy_path = os.path.join(extension_root, "PRIVACY.md")
try:
    with open(privacy_path) as privacy_file:
        script.get_output().print_md(privacy_file.read())
except IOError:
    script.get_output().print_md("PRIVACY.md could not be found in this extension.")
