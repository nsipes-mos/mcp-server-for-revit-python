import json
import subprocess
import sys

from scripts.session_start import ROOT, describe

TWO = [{"version": "2026", "port": 48884, "pid": 1}, {"version": "2027", "port": 48885, "pid": 2}]


def test_several_running_lists_versions_and_points_to_revit_command():
    message, context = describe(TWO)
    assert message == "Running Revit: 2026, 2027. Use /revit YYYY to choose the version."
    assert "ask the user which version" in context


def test_single_running_reports_it_without_asking():
    message, context = describe(TWO[1:])
    assert message == "Revit 2027 is running and will be used."
    assert "ask" not in context


def test_none_running():
    message, _ = describe([])
    assert message == "No Revit is running with the MCP bridge."


def test_configured_version_wins():
    message, _ = describe(TWO, configured="2027")
    assert message == "Revit 2027 is selected by REVIT_VERSION."


def test_hook_script_prints_valid_hook_json():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "session_start.py")],
                         capture_output=True, text=True, timeout=60, cwd=str(ROOT)).stdout
    data = json.loads(out)
    assert data["systemMessage"]
    assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
