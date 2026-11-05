import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QDialog, QWidget

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language
from ui.par2_actions import Par2ActionsMixin
from ui.par2_options import Par2OptionsWidget
from ui.par2_set_dialog import (
    Par2SetDialog,
    last_options,
    remember_options,
)


class _Host(Par2ActionsMixin, QWidget):


    def __init__(self):
        QWidget.__init__(self)
        self.status_messages = []
        self.logged = []
        self._workers = []
        self._par2_create_dialog = None
        self._par2_worker = None

    def statusBar(self):
        return self

    def showMessage(self, text):
        self.status_messages.append(text)

    def log_output(self, text):
        self.logged.append(text)

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    def _on_refresh(self):
        pass

    def _load_container(self):
        return None, None


class _TmpCase(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile

        set_language("ru", str(ROOT / "locales"))
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_setdlg_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.arch = self.dir / "backup.zpaq"
        self.arch.write_bytes(b"Z" * 4096)
        remember_options({})
        self.addCleanup(remember_options, {})


class TestOptionsWidget(_TmpCase):


    def test_fields_present(self):
        w = Par2OptionsWidget(show_master=False)
        self.assertEqual(w.redundancy.value(), 5)
        self.assertTrue(w.auto_blocks.isChecked())
        self.assertFalse(w.manual_blocks.isChecked())

    def test_no_master_checkbox_without_master(self):
        w = Par2OptionsWidget(show_master=False)
        self.assertIsNone(w.master)
        self.assertTrue(w.box.isEnabled(),
                        "поля погашены, а создание уже выбрано")

    def test_master_present_when_asked(self):
        w = Par2OptionsWidget(show_master=True)
        self.assertIsNotNone(w.master)
        self.assertFalse(w.box.isEnabled(),
                         "галочка снята, значит поля недоступны")

    def test_manual_block_collected(self):
        w = Par2OptionsWidget(show_master=False)
        w.manual_blocks.click()
        w.block_size.setValue(262144)
        self.assertEqual(w.collect()["block_size"], 262144)

    def test_auto_block_collected_as_none(self):
        w = Par2OptionsWidget(show_master=False)
        self.assertIsNone(w.collect()["block_size"])

    def test_apply_round_trip(self):

        w = Par2OptionsWidget(show_master=False)
        w.apply({"redundancy": 17, "block_size": 131072, "threads": 4,
                 "uniform": True})
        self.assertEqual(w.redundancy.value(), 17)
        self.assertTrue(w.manual_blocks.isChecked())
        self.assertEqual(w.block_size.value(), 131072)
        self.assertEqual(w.threads.value(), 4)
        self.assertTrue(w.uniform.isChecked())


class TestSetDialog(_TmpCase):


    def test_shows_archive_name(self):
        dlg = Par2SetDialog("backup.zpaq", {"redundancy": 9})
        self.assertIn("backup.zpaq", dlg.windowTitle())
        dlg.deleteLater()

    def test_returns_chosen_options(self):
        dlg = Par2SetDialog("backup.zpaq", {"redundancy": 9})
        dlg.widget.redundancy.setValue(33)
        self.assertEqual(dlg.options()["redundancy"], 33)
        dlg.deleteLater()

    def test_no_master_checkbox(self):
        dlg = Par2SetDialog("backup.zpaq", None)
        self.assertIsNone(dlg.widget.master)
        dlg.deleteLater()


class TestCreateAsksParameters(_TmpCase):


    def _run(self, chosen=None, accepted=True, job_options=None):
        host = _Host()
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()

        class _Stub:
            last = None

            def __init__(self, archive_name="", options=None, parent=None):
                _Stub.last = dict(options or {})

            def exec(self):
                return QDialog.Accepted if accepted else QDialog.Rejected

            def options(self):
                return dict(chosen if chosen is not None else _Stub.last)

            def deleteLater(self):
                pass

        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        return_value=worker), \
             mock.patch("ui.par2_actions.Par2SetDialog", _Stub), \
             mock.patch.object(_Host, "_par2_job_for",
                               return_value=(None, job_options, False)):
            started = host._start_par2_create(str(self.arch))
        if started:
            host._workers.append(worker)
        return host, worker, started, _Stub

    def test_dialog_asked_before_creating(self):

        _host, _worker, started, _stub = self._run()
        self.assertTrue(started)

    def test_chosen_options_reach_worker(self):
        host = _Host()
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()
        seen = {}

        class _Stub:
            def __init__(self, archive_name="", options=None, parent=None):
                pass

            def exec(self):
                return QDialog.Accepted

            def options(self):
                return {"redundancy": 42, "block_size": 131072}

            def deleteLater(self):
                pass

        def _factory(bin_path, archive_path, options=None, **kw):
            seen["options"] = dict(options or {})
            return worker

        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        side_effect=_factory), \
             mock.patch("ui.par2_actions.Par2SetDialog", _Stub), \
             mock.patch.object(_Host, "_par2_job_for",
                               return_value=(None, None, False)):
            host._start_par2_create(str(self.arch))

        self.assertEqual(seen["options"]["redundancy"], 42)
        self.assertEqual(seen["options"]["block_size"], 131072)

    def test_cancelled_creates_nothing(self):
        _host, _worker, started, _stub = self._run(accepted=False)
        self.assertFalse(started)

    def test_job_settings_used_as_prefill(self):

        host = _Host()
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()
        prefill = {}

        class _Stub:
            def __init__(self, archive_name="", options=None, parent=None):
                prefill.update(dict(options or {}))

            def exec(self):
                return QDialog.Accepted

            def options(self):
                return dict(prefill)

            def deleteLater(self):
                pass

        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        return_value=worker), \
             mock.patch("ui.par2_actions.Par2SetDialog", _Stub), \
             mock.patch.object(_Host, "_par2_job_for",
                               return_value=(None, {"redundancy": 11},
                                             True)):
            host._start_par2_create(str(self.arch))
        self.assertEqual(prefill.get("redundancy"), 11)

    def test_previous_choice_reused_next_time(self):
        remember_options({"redundancy": 77})
        self.assertEqual(last_options()["redundancy"], 77)

        host = _Host()
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()
        prefill = {}

        class _Stub:
            def __init__(self, archive_name="", options=None, parent=None):
                prefill.update(dict(options or {}))

            def exec(self):
                return QDialog.Accepted

            def options(self):
                return dict(prefill)

            def deleteLater(self):
                pass

        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        return_value=worker), \
             mock.patch("ui.par2_actions.Par2SetDialog", _Stub), \
             mock.patch.object(_Host, "_par2_job_for",
                               return_value=(None, None, False)):
            host._start_par2_create(str(self.arch))
        self.assertEqual(prefill.get("redundancy"), 77)


if __name__ == "__main__":
    unittest.main()
