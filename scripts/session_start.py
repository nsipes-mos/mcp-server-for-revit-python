"""SessionStart hook: report running Revit versions before the first prompt.

Prints the JSON a Claude Code SessionStart hook expects: a message for the
user and the same facts as context for Claude.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def describe(instances, configured=""):
    """(message for the user, context for Claude) for the running instances."""
    versions = sorted({item["version"] for item in instances})
    if configured:
        return ("Revit {} is selected by REVIT_VERSION.".format(configured),
                "The Revit connector targets Revit {} (REVIT_VERSION). Running: {}."
                .format(configured, ", ".join(versions) or "none"))
    if not instances:
        return ("No Revit is running with the MCP bridge.",
                "No Revit with the MCP bridge is running. Revit tools will fail "
                "until one is started (launch_revit can start one).")
    if len(instances) == 1:
        version = instances[0]["version"]
        return ("Revit {} is running and will be used.".format(version),
                "Only Revit {} is running, so the connector uses it automatically."
                .format(version))
    listing = ", ".join(versions)
    return ("Running Revit: {}. Use /revit YYYY to choose the version.".format(listing),
            "Several Revit versions are running ({}). No version is selected, so "
            "calls go to the first-started Revit. Before any Revit tool call, ask "
            "the user which version to use unless they already named one, then "
            "call select_revit_instance. Users can also type /revit YYYY."
            .format(listing))


def main():
    try:
        import main as connector
        instances = connector.scan_revit_instances()
        configured = connector.REVIT_VERSION
    except Exception as error:  # never block a session from starting
        print(json.dumps({"systemMessage": "Revit check skipped: {}".format(error)}))
        return
    message, context = describe(instances, configured)
    print(json.dumps({
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": "SessionStart",
                               "additionalContext": context},
    }))


if __name__ == "__main__":
    main()
