"""File-panel ribbon scripts (Save All, Open Templates) run against fake Revit objects."""
import datetime
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "PyMoseley.tab" / "3File.panel"
SAVE_ALL = PANEL / "2SaveAll.pushbutton" / "script.py"
OPEN_TEMPLATES = PANEL / "1OpenTemplates.pushbutton" / "script.py"
CLOSE_ALL = PANEL / "3CloseAll.pushbutton" / "script.py"
STRING = "String"
TODAY = datetime.date.today().strftime("%Y-%m-%d")


class FakeProgressBar:
    """Stands in for pyrevit.forms.ProgressBar; cancels after `cancel_after` updates."""
    cancel_after = None
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.updates = []
        self.instances.append(self)

    @property
    def cancelled(self):
        return self.cancel_after is not None and len(self.updates) >= self.cancel_after

    def update_progress(self, value, maximum):
        self.updates.append((value, maximum))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeEvent:
    """A .NET-style event: supports += and -=."""

    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def raise_dialog(self, **args):
        event = SimpleNamespace(OverrideResult=Mock(), **args)
        for handler in list(self.handlers):
            handler(None, event)
        return event


class FakeTransaction:
    log = []

    def __init__(self, doc, name):
        self.doc = doc

    def Start(self):
        self.log.append("start")

    def Commit(self):
        self.log.append("commit")

    def RollBack(self):
        self.log.append("rollback")


def make_param(value="2020-01-01", read_only=False, storage=STRING):
    param = SimpleNamespace(IsReadOnly=read_only, StorageType=storage, value=value)
    param.AsString = lambda: param.value
    param.Set = lambda new: setattr(param, "value", new)
    return param


def make_doc(title, path="C:/models/a.rvt", modified=True, linked=False, read_only=False,
             param="absent", save_error=None):
    info = SimpleNamespace(LookupParameter=lambda name: param if name == "Template Version" and param != "absent" else None)
    doc = SimpleNamespace(Title=title, PathName=path, IsModified=modified, IsLinked=linked,
                          IsReadOnly=read_only, ProjectInformation=info)
    doc.Save = Mock(side_effect=save_error)
    return doc


@pytest.fixture
def revit(monkeypatch):
    """Install fake pyrevit and Autodesk modules; return a handle to drive the scripts."""
    FakeProgressBar.cancel_after = None
    FakeProgressBar.instances = []
    FakeTransaction.log = []
    alert = Mock()
    forms = SimpleNamespace(alert=alert, ProgressBar=FakeProgressBar)
    uiapp = SimpleNamespace(Application=SimpleNamespace(Documents=[]),
                            OpenAndActivateDocument=Mock(), ActiveUIDocument=None,
                            PostCommand=Mock(), DialogBoxShowing=FakeEvent())
    host_app = SimpleNamespace(uiapp=uiapp, version="2027")
    pyrevit = ModuleType("pyrevit")
    pyrevit.forms, pyrevit.HOST_APP = forms, host_app
    db = ModuleType("Autodesk.Revit.DB")
    db.StorageType = SimpleNamespace(String=STRING)
    db.Transaction = FakeTransaction
    ui = ModuleType("Autodesk.Revit.UI")
    ui.PostableCommand = SimpleNamespace(Close="close")
    ui.RevitCommandId = SimpleNamespace(LookupPostableCommandId=lambda command: "id:" + command)
    answer_prompt = Mock(return_value="handler")
    document = ModuleType("revit_mcp.document")
    document._answer_next_save_prompt = answer_prompt
    for name, module in (("pyrevit", pyrevit), ("Autodesk", ModuleType("Autodesk")),
                         ("Autodesk.Revit", ModuleType("Autodesk.Revit")),
                         ("Autodesk.Revit.DB", db), ("Autodesk.Revit.UI", ui),
                         ("revit_mcp.document", document)):
        monkeypatch.setitem(sys.modules, name, module)
    return SimpleNamespace(alert=alert, uiapp=uiapp, host_app=host_app, answer_prompt=answer_prompt,
                           message=lambda: alert.call_args.args[0])


def run(script):
    runpy.run_path(str(script))


# --- Save All ---------------------------------------------------------------

def test_save_all_saves_only_modified_documents(revit):
    modified = make_doc("Modified")
    clean = make_doc("Clean", modified=False)
    revit.uiapp.Application.Documents = [modified, clean]
    run(SAVE_ALL)
    modified.Save.assert_called_once()
    clean.Save.assert_not_called()
    assert "Saved 1" in revit.message() and "Modified" in revit.message()


def test_save_all_skips_linked_unsaved_and_read_only(revit):
    linked = make_doc("Linked", linked=True)
    unsaved = make_doc("Untitled", path="")
    read_only = make_doc("ReadOnly", read_only=True)
    revit.uiapp.Application.Documents = [linked, unsaved, read_only]
    run(SAVE_ALL)
    for doc in (linked, unsaved, read_only):
        doc.Save.assert_not_called()
    message = revit.message()
    assert "Linked" not in message
    assert "Untitled (never saved; use Save As)" in message
    assert "ReadOnly (read-only)" in message


def test_save_all_reports_failure_and_continues(revit):
    broken = make_doc("Broken", save_error=RuntimeError("disk full"))
    fine = make_doc("Fine")
    revit.uiapp.Application.Documents = [broken, fine]
    run(SAVE_ALL)
    fine.Save.assert_called_once()
    assert "Broken: disk full" in revit.message()
    assert "Saved 1" in revit.message()


def test_save_all_with_nothing_to_save(revit):
    revit.uiapp.Application.Documents = [make_doc("Clean", modified=False)]
    run(SAVE_ALL)
    assert "No unsaved changes" in revit.message()


def test_template_version_is_stamped_with_today(revit):
    param = make_param("2020-01-01")
    template = make_doc("Template", path="C:/t/Struc 2027.rte", param=param)
    revit.uiapp.Application.Documents = [template]
    run(SAVE_ALL)
    assert param.value == TODAY
    assert FakeTransaction.log == ["start", "commit"]
    template.Save.assert_called_once()
    assert "Template Version set to " + TODAY in revit.message()


def test_template_version_already_today_still_saves_without_note(revit):
    param = make_param(TODAY)
    template = make_doc("Template", path="C:/t/Struc 2027.RTE", param=param)
    revit.uiapp.Application.Documents = [template]
    run(SAVE_ALL)
    assert FakeTransaction.log == []
    template.Save.assert_called_once()
    assert "Template Version" not in revit.message()


@pytest.mark.parametrize("param,note", [
    ("absent", "Template Version parameter missing"),
    (make_param(read_only=True), "Template Version not usable (read-only)"),
    (make_param(storage="Integer"), "Template Version not usable (not a text parameter)"),
])
def test_template_version_problems_are_reported_and_file_still_saves(revit, param, note):
    template = make_doc("Template", path="C:/t/Struc 2027.rte", param=param)
    revit.uiapp.Application.Documents = [template]
    run(SAVE_ALL)
    template.Save.assert_called_once()
    assert FakeTransaction.log == []
    assert note in revit.message()


def test_non_template_documents_are_never_stamped(revit):
    param = make_param("2020-01-01")
    project = make_doc("Project", path="C:/m/project.rvt", param=param)
    revit.uiapp.Application.Documents = [project]
    run(SAVE_ALL)
    assert param.value == "2020-01-01"
    assert "Template Version" not in revit.message()


def test_unmodified_template_is_not_stamped(revit):
    param = make_param("2020-01-01")
    template = make_doc("Template", path="C:/t/Struc 2027.rte", modified=False, param=param)
    revit.uiapp.Application.Documents = [template]
    run(SAVE_ALL)
    assert param.value == "2020-01-01"
    template.Save.assert_not_called()


# --- Open Templates ---------------------------------------------------------

NAMES = ["ArchIntr_C_J", "ArchIntr_K12_HE", "ArchIntr_SL_MFH", "MechElecSec",
         "MechElecSec_SL_MFH", "PlumbFire", "Struc"]


@pytest.fixture
def template_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    def make(version):
        folder = (tmp_path / "dc" / "ACCDocs" / "Moseley" / "000027 - Revit Template Updates"
                  / "Project Files" / ("Revit " + version))
        folder.mkdir(parents=True)
        for name in NAMES:
            (folder / "{} {}.rte".format(name, version)).touch()
            for backup in ("0001", "0002"):
                (folder / "{} {}.{}.rte".format(name, version, backup)).touch()
        (folder / "notes.txt").touch()
        return folder
    return make


def opened_names(revit):
    return [Path(call.args[0]).name for call in revit.uiapp.OpenAndActivateDocument.call_args_list]


@pytest.mark.parametrize("version", ["2026", "2027"])
def test_open_templates_opens_the_seven_non_backup_files_for_the_version(revit, template_dir, version):
    folder = template_dir(version)
    revit.host_app.version = version
    run(OPEN_TEMPLATES)
    assert opened_names(revit) == ["{} {}.rte".format(name, version) for name in sorted(NAMES)]
    assert all(Path(call.args[0]).parent == folder
               for call in revit.uiapp.OpenAndActivateDocument.call_args_list)
    assert "Opened 7" in revit.message()
    assert FakeProgressBar.instances[0].updates[-1] == (7, 7)


def test_open_templates_reports_missing_folder(revit, template_dir):
    run(OPEN_TEMPLATES)
    revit.uiapp.OpenAndActivateDocument.assert_not_called()
    assert "Template folder not found" in revit.message()
    assert "Revit 2027" in revit.message()


def test_open_templates_skips_documents_that_are_already_open(revit, template_dir):
    folder = template_dir("2027")
    already = folder / "Struc 2027.rte"
    revit.uiapp.Application.Documents = [SimpleNamespace(PathName=str(already).upper())]
    run(OPEN_TEMPLATES)
    assert "Struc 2027.rte" not in opened_names(revit)
    assert len(opened_names(revit)) == 6
    assert "Already open:\n  Struc 2027.rte" in revit.message()


def test_open_templates_reports_failures_and_continues(revit, template_dir):
    template_dir("2027")

    def opener(path):
        if "PlumbFire" in path:
            raise RuntimeError("cannot open")
    revit.uiapp.OpenAndActivateDocument.side_effect = opener
    run(OPEN_TEMPLATES)
    assert len(opened_names(revit)) == 7
    assert "PlumbFire 2027.rte: cannot open" in revit.message()
    assert "Opened 6" in revit.message()


def test_open_templates_cancel_lists_unopened_files(revit, template_dir):
    template_dir("2027")
    FakeProgressBar.cancel_after = 3
    run(OPEN_TEMPLATES)
    assert len(opened_names(revit)) == 3
    message = revit.message()
    assert "Cancelled. Not opened:" in message
    for name in sorted(NAMES)[3:]:
        assert "{} 2027.rte".format(name) in message.split("Opened")[0]
    assert "Opened 3" in message


def test_open_templates_is_hidden_before_revit_2026():
    bundle = (PANEL / "1OpenTemplates.pushbutton" / "bundle.yaml").read_text()
    assert "min_revit_version: 2026" in bundle


def test_open_templates_is_available_with_no_open_document():
    bundle = (PANEL / "1OpenTemplates.pushbutton" / "bundle.yaml").read_text()
    assert "context: zero-doc" in bundle


# --- Close All --------------------------------------------------------------

def make_closable(title, modified=False, linked=False, close_error=None):
    doc = make_doc(title, modified=modified, linked=linked)
    doc.Close = Mock(side_effect=close_error)
    return doc


def test_close_all_with_no_documents(revit):
    run(CLOSE_ALL)
    assert "No open documents" in revit.message()
    revit.uiapp.PostCommand.assert_not_called()


def test_close_all_closes_background_documents_and_posts_close_for_the_active_one(revit):
    active, other, linked = make_closable("Active"), make_closable("Other"), make_closable("Link", linked=True)
    revit.uiapp.Application.Documents = [other, active, linked]
    revit.uiapp.ActiveUIDocument = SimpleNamespace(Document=active)
    run(CLOSE_ALL)
    other.Close.assert_called_once_with(False)
    active.Close.assert_not_called()
    linked.Close.assert_not_called()
    revit.uiapp.PostCommand.assert_called_once_with("id:close")
    revit.alert.assert_not_called()
    revit.answer_prompt.assert_not_called()


def test_close_all_asks_before_discarding_unsaved_changes(revit):
    dirty, clean = make_closable("Dirty", modified=True), make_closable("Clean")
    revit.uiapp.Application.Documents = [dirty, clean]
    revit.alert.return_value = False
    run(CLOSE_ALL)
    assert "Dirty" in revit.message() and "Clean" not in revit.message()
    dirty.Close.assert_not_called()
    clean.Close.assert_not_called()
    revit.uiapp.PostCommand.assert_not_called()


def test_close_all_discards_after_confirmation_and_answers_the_active_save_prompt(revit):
    active, other = make_closable("Active", modified=True), make_closable("Other", modified=True)
    revit.uiapp.Application.Documents = [active, other]
    revit.uiapp.ActiveUIDocument = SimpleNamespace(Document=active)
    revit.alert.return_value = True
    run(CLOSE_ALL)
    other.Close.assert_called_once_with(False)
    revit.answer_prompt.assert_called_once_with(revit.uiapp, 7, "Active")
    revit.uiapp.PostCommand.assert_called_once_with("id:close")


def test_close_all_reports_failures_and_continues(revit):
    stuck = make_closable("Stuck", close_error=RuntimeError("in use"))
    other = make_closable("Other")
    revit.uiapp.Application.Documents = [stuck, other]
    run(CLOSE_ALL)
    other.Close.assert_called_once_with(False)
    assert "Stuck: in use" in revit.message()


# --- Open Templates: automatic dialog answers --------------------------------

def test_open_templates_answers_yes_to_dialogs_and_reports_them(revit, template_dir):
    template_dir("2027")
    events = []

    def opener(path):
        if "Struc" in path:
            events.append(revit.uiapp.DialogBoxShowing.raise_dialog(
                DialogId="TaskDialog_Upgrade", Message="Upgrade this file?\nContinue"))
    revit.uiapp.OpenAndActivateDocument.side_effect = opener
    run(OPEN_TEMPLATES)
    events[0].OverrideResult.assert_called_once_with(6)
    assert "Dialogs answered automatically" in revit.message()
    assert "Struc 2027.rte: TaskDialog_Upgrade [Yes] Upgrade this file? Continue" in revit.message()


def test_open_templates_falls_back_to_ok_when_yes_is_rejected(revit, template_dir):
    template_dir("2027")
    events = []

    def opener(path):
        if "PlumbFire" in path:
            event = revit.uiapp.DialogBoxShowing
            args = SimpleNamespace(DialogId="Info", Message="Done",
                                   OverrideResult=Mock(side_effect=[ValueError("no yes button"), None]))
            for handler in list(event.handlers):
                handler(None, args)
            events.append(args)
    revit.uiapp.OpenAndActivateDocument.side_effect = opener
    run(OPEN_TEMPLATES)
    assert [call.args[0] for call in events[0].OverrideResult.call_args_list] == [6, 1]
    assert "[OK]" in revit.message()


def test_open_templates_detaches_dialog_handler_afterwards(revit, template_dir):
    template_dir("2027")
    run(OPEN_TEMPLATES)
    assert revit.uiapp.DialogBoxShowing.handlers == []
    assert "Dialogs answered" not in revit.message()


def test_open_templates_detaches_dialog_handler_even_when_opening_crashes(revit, template_dir):
    template_dir("2027")
    FakeProgressBar.__enter__ = lambda self: (_ for _ in ()).throw(RuntimeError("ui broke"))
    try:
        with pytest.raises(RuntimeError):
            run(OPEN_TEMPLATES)
    finally:
        del FakeProgressBar.__enter__
        FakeProgressBar.__enter__ = lambda self: self
    assert revit.uiapp.DialogBoxShowing.handlers == []
