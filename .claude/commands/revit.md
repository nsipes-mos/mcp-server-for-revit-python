---
description: Choose which running Revit version this chat works in
argument-hint: 2026 | 2027 | default
---
Call the Revit connector's `select_revit_instance` tool with version "$ARGUMENTS".
If `$ARGUMENTS` is empty, call `list_revit_instances` and ask which version to use.
Then confirm the selected version and its open document in one line.
