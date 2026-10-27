import pytest

import main


NETSTAT = """
  Proto  Local Address          Foreign Address        State           PID
  TCP    127.0.0.1:48884        0.0.0.0:0              LISTENING       100
  TCP    127.0.0.1:48885        0.0.0.0:0              LISTENING       200
  TCP    127.0.0.1:3333         0.0.0.0:0              LISTENING       200
  TCP    0.0.0.0:48886          0.0.0.0:0              LISTENING       300
"""

PATHS = {
    100: r"C:\Program Files\Autodesk\Revit 2026\Revit.exe",
    200: r"C:\Program Files\Autodesk\Revit 2027\Revit.exe",
    300: r"C:\Program Files\Autodesk\Revit 2025\Revit.exe",
}


@pytest.fixture
def two_revits(monkeypatch):
    class Result:
        stdout = NETSTAT
    monkeypatch.setattr(main.sys, "platform", "win32")
    monkeypatch.setattr(main.subprocess, "run", lambda *a, **k: Result())
    monkeypatch.setattr(main, "_process_path", PATHS.get)


def test_ports_are_mapped_to_versions(two_revits):
    assert main.find_revit_ports() == {"2026": 48884, "2027": 48885}


def test_version_selects_matching_port(two_revits, monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "2027")
    assert main._base_url() == "http://127.0.0.1:48885/revit_mcp"


def test_missing_version_lists_running_versions(two_revits, monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "2025")
    with pytest.raises(RuntimeError, match="Running versions: 2026, 2027"):
        main._base_url()


def test_without_version_and_several_running_default_port_is_used(two_revits, monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "")
    assert main._base_url() == main.BASE_URL


def test_lone_running_revit_is_used_automatically(monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "")
    monkeypatch.setattr(main, "scan_revit_instances",
                        lambda: [{"version": "2027", "port": 48885, "pid": 1}])
    assert main._base_url() == "http://127.0.0.1:48885/revit_mcp"


def test_no_running_revit_falls_back_to_default_port(monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "")
    monkeypatch.setattr(main, "scan_revit_instances", lambda: [])
    assert main._base_url() == main.BASE_URL


def test_explicit_port_overrides_version(monkeypatch):
    monkeypatch.setenv("REVIT_PORT", "48890")
    monkeypatch.setattr(main, "_selected_version", "2027")
    assert main._base_url() == main.BASE_URL


def test_select_switches_target_and_default_resets(two_revits, monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "")
    assert main.select_revit_instance("2027") == {"selected": "2027", "port": 48885}
    assert main._base_url() == "http://127.0.0.1:48885/revit_mcp"
    main.select_revit_instance("default")
    assert main._base_url() == main.BASE_URL  # two running: back to the default port


def test_select_rejects_bad_or_missing_version(two_revits, monkeypatch):
    monkeypatch.delenv("REVIT_PORT", raising=False)
    monkeypatch.setattr(main, "_selected_version", "")
    with pytest.raises(ValueError):
        main.select_revit_instance("next")
    with pytest.raises(RuntimeError, match="not running"):
        main.select_revit_instance("2025")
    assert main._selected_version == ""


def test_select_refused_when_port_is_fixed(monkeypatch):
    monkeypatch.setenv("REVIT_PORT", "48884")
    with pytest.raises(RuntimeError, match="REVIT_PORT"):
        main.select_revit_instance("2027")


async def test_list_instances_reports_selection_and_document(two_revits, monkeypatch):
    import httpx
    original = httpx.AsyncClient
    handler = lambda request: httpx.Response(200, json={"document_title": "doc-" + str(request.url.port)})
    monkeypatch.setattr(main, "authorization_headers", lambda: {"Authorization": "Bearer x"})
    monkeypatch.setattr(main.httpx, "AsyncClient",
                        lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(main, "_selected_version", "2027")
    result = await main.list_revit_instances()
    assert [(i["version"], i["selected"]) for i in result] == [("2026", False), ("2027", True)]
    assert result[1]["document"] == "doc-48885"
