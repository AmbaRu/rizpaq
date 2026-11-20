                       












from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QThread, Signal              
from PySide6.QtWidgets import QApplication, QDialog, QWidget              

_APP = QApplication.instance() or QApplication(sys.argv)

from ui import i18n              

i18n.set_language("ru", notify=False)

from ui.i18n import tr              

                                                                        


class TestRunWithStream(unittest.TestCase):
    pass

    def test_lines_arrive_live(self):
        from core import par2_ops

        got = []
        rc, log = par2_ops._run(
            sys.executable,
            ["-c", "print('line one'); print('line two')"],
            timeout=60,
            on_line=got.append,
        )
        self.assertEqual(rc, 0)
                                                           
        self.assertIn("line one", got)
        self.assertIn("line two", got)
                                       
        self.assertIn("line one", log)
        self.assertIn("line two", log)

    def test_without_callback_old_path_kept(self):
        pass
        from core import par2_ops

        rc, log = par2_ops._run(
            sys.executable,
            ["-c", "print('chunk')"],
            timeout=60,
        )
        self.assertEqual(rc, 0)
        self.assertIn("chunk", log)

    def test_callback_exception_does_not_break_reading(self):
        pass
        from core import par2_ops

        def bad(_line):
            raise RuntimeError("приёмник сломан")

        rc, log = par2_ops._run(
            sys.executable,
            ["-c", "print('a'); print('b')"],
            timeout=60,
            on_line=bad,
        )
        self.assertEqual(rc, 0)
        self.assertIn("a", log)
        self.assertIn("b", log)


class TestStreamPipedThrough(unittest.TestCase):
    pass

    def test_worker_passes_line_signal(self):
        from core import par2_ops
        from workers.par2_worker import Par2CreateWorker

        captured = {}
        real = par2_ops.refresh_par2_set

        def fake_refresh(*args, **kwargs):
            captured["on_line"] = kwargs.get("on_line")
            return par2_ops.Par2Result(
                True, par2_ops.STATE_OK, "", recorded_size=None)

        worker = Par2CreateWorker("par2.exe", "backup.zpaq")
        with mock.patch.object(par2_ops, "refresh_par2_set",
                               side_effect=fake_refresh):
            worker.run()                          

                                                              
                                                                   
                                                       
        got = []
        worker.line_received.connect(got.append)
        captured["on_line"]("строка из par2")
        self.assertEqual(got, ["строка из par2"])

    def test_refresh_signature_accepts_on_line(self):
        pass
        import inspect

        from core import par2_ops

        self.assertIn("on_line", inspect.signature(
            par2_ops.refresh_par2_set).parameters)
        self.assertIn("on_line", inspect.signature(
            par2_ops.create_parset).parameters)
        self.assertIn("on_line", inspect.signature(
            par2_ops._run).parameters)


                                                                        


class TestDialogStage(unittest.TestCase):
    pass

    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
                                                                     
                                      
        self.dlg = _new_dialog()

    def test_stage_title_and_log_kept(self):
        dlg = self.dlg
        dlg.append_output("строка этапа бэкапа")
        dlg.begin_par2_stage("backup.zpaq")
        self.assertIn(
            tr("progress.par2_stage", name="backup.zpaq"),
            dlg._title.text(),
        )
                                                          
        log_text = dlg._log.toPlainText()
        self.assertIn("строка этапа бэкапа", log_text)
                                               
        self.assertEqual(dlg._btn.text(), tr("progress.cancel"))

    def test_live_fields_visible(self):
        pass
        dlg = self.dlg
        dlg.begin_par2_stage("backup.zpaq")
        self.assertFalse(dlg._files_label.isVisible())
        self.assertFalse(dlg._dirs_label.isVisible())
        self.assertTrue(dlg._speed_label.isVisible())
        self.assertTrue(dlg._elapsed_label.isVisible())
        self.assertTrue(dlg._eta_label.isVisible())
        self.assertTrue(dlg._read_label.isVisible())
        self.assertTrue(dlg._written_label.isVisible())
        self.assertTrue(dlg._blocks_label.isVisible())
        self.assertTrue(dlg._redundancy_label.isVisible())

    def test_system_load_fields_visible(self):
        dlg = self.dlg
        dlg.begin_par2_stage("backup.zpaq")
        self.assertTrue(dlg._sys_group.isVisible())
        self.assertTrue(dlg._cpu_label.isVisible())
        self.assertTrue(dlg._disk_label.isVisible())
        self.assertTrue(dlg._memory_label.isVisible())
        self.assertIsNotNone(dlg._sys_sampler)

    def test_final_verdict_stays_open(self):
        pass
        dlg = self.dlg
        dlg._finished = False
        dlg.finish(True, "итог", stay=True)
        self.assertTrue(dlg._finished)
                                         
        self.assertTrue(dlg.isVisible())
        dlg.close()


def _new_dialog():
    from ui.archive_progress_dialog import ArchiveProgressDialog

    return ArchiveProgressDialog("backup.zpaq")


                                                                      


class _FakeWorker(QThread):
    done = Signal(dict)
    line_received = Signal(str)

    def __init__(self, *a, **k):
        super().__init__()
        self.started = False
        self.cancel_called = False

    def start(self):
        self.started = True

    def cancel_request(self):
        self.cancel_called = True


class _StageHost(QWidget):
    pass

    def __init__(self):
        QWidget.__init__(self)
        self.status_messages = []
        self.logged = []
        self._workers = []
        self._par2_worker = None
        self._report_gate = None
        self._create_report = None
        self._pending_create_report = None
        self.report_stages = []
        self.report_requested = False

    def statusBar(self):
        return self

    def showMessage(self, msg):
        self.status_messages.append(msg)

    def log_output(self, text):
        self.logged.append(text)

    def _cleanup_worker(self, worker):
        pass

    def _save_par2_marker(self, job_context, size):
        pass

                                                                       
                                                                 
    def _report_stage_done(self, stage):
        self.report_stages.append(stage)
        gate = getattr(self, "_report_gate", None)
        if gate:
            gate.discard(stage)
            if gate:
                return
            self._report_gate = None
        self._request_create_report()

    def _request_create_report(self):
        self.report_requested = True


class TestWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
        tmp = Path(tempfile.mkdtemp(prefix="par2_stage_"))
        self.arch = tmp / "backup.zpaq"
        self.arch.write_bytes(b"x" * 100)

    def _host_with_started_worker(self, result):
        pass
        from ui.par2_actions import Par2ActionsMixin

        class Host(_StageHost, Par2ActionsMixin):
            pass

        host = Host()
        dlg = _new_dialog()
        with mock.patch("ui.par2_actions.Par2CreateWorker",
                        _FakeWorker), \
             mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"):
            started = host._start_par2_worker(
                {}, str(self.arch),
                {"enabled": True, "options": {}},
                dialog=dlg,
            )
        self.assertTrue(started)
        worker = host._par2_worker
        self.assertTrue(worker.started)
        return host, dlg, worker

    def test_dialog_switches_to_stage(self):
        host, dlg, worker = self._host_with_started_worker(None)
        self.assertIn(
            tr("progress.par2_stage", name=self.arch.name),
            dlg._title.text(),
        )
        self.assertEqual(dlg._btn.text(), tr("progress.cancel"))

    def test_done_ok_leaves_final_verdict(self):
        host, dlg, worker = self._host_with_started_worker(None)
        host._on_par2_done({}, {
            "ok": True, "cancelled": False, "log": "",
            "recorded_size": None, "archive_path": str(self.arch),
            "skipped": False,
        }, dlg)
        self.assertTrue(dlg._finished)
        self.assertEqual(dlg._title.property("state"), "ok")
                                                 
        self.assertTrue(dlg.isVisible())

    def test_done_failed_is_painted_error(self):
        host, dlg, worker = self._host_with_started_worker(None)
        host._on_par2_done({}, {
            "ok": False, "cancelled": False, "log": "par2 error",
            "recorded_size": None, "archive_path": str(self.arch),
            "skipped": False,
        }, dlg)
        self.assertEqual(dlg._title.property("state"), "err")

    def test_done_cancelled_is_not_error(self):
        pass
        host, dlg, worker = self._host_with_started_worker(None)
        host._on_par2_done({}, {
            "ok": False, "cancelled": True, "log": "",
            "recorded_size": None, "archive_path": str(self.arch),
            "skipped": False,
        }, dlg)
        self.assertEqual(dlg._title.property("state"), "ok")

    def test_deferred_report_gets_par2_and_window_closes(self):
        pass
        host, dlg, worker = self._host_with_started_worker(None)
        host._report_gate = {"par2"}
        host._create_report = {
            "dest": str(self.arch), "is_update": True, "ok": True,
            "params_rows": [], "stats": None,
        }
        host._on_par2_done({}, {
            "ok": True, "cancelled": False, "log": "",
            "recorded_size": 100, "archive_path": str(self.arch),
            "skipped": False,
        }, dlg)
                                                            
        self.assertEqual(dlg.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(host._create_report["par2"]["status"], "ok")
        self.assertEqual(host._create_report["par2"]["size"], 100)
        self.assertIn("par2", host.report_stages)
        self.assertTrue(host.report_requested)
        self.assertIsNone(host._report_gate)

    def test_deferred_report_waits_for_check(self):
        pass
        host, dlg, worker = self._host_with_started_worker(None)
        host._report_gate = {"par2", "test"}
        host._create_report = {"dest": str(self.arch), "ok": True,
                               "is_update": False}
        host._on_par2_done({}, {
            "ok": False, "cancelled": False, "log": "par2 error",
            "recorded_size": None, "archive_path": str(self.arch),
            "skipped": False,
        }, dlg)
        self.assertEqual(host._create_report["par2"]["status"], "failed")
        self.assertEqual(host._create_report["par2"]["error"], "par2 error")
        self.assertFalse(host.report_requested)
        self.assertEqual(host._report_gate, {"test"})

    def test_report_waits_while_gate_busy(self):
        pass
        from ui.archive_actions import ArchiveActionsMixin

        class Host:
            _report_gate = {"par2"}
            _create_report = {"dest": "x.zpaq"}

            def _load_info(self, *a, **k):
                raise AssertionError("отчёт запрошен раньше времени")

        ArchiveActionsMixin._request_create_report(Host())             

    def test_gate_releases_only_after_last_stage(self):
        from ui.archive_actions import ArchiveActionsMixin

        class Host:
            _report_gate = {"par2", "test"}
            requested = 0

            def _request_create_report(self):
                self.requested += 1

        host = Host()
        ArchiveActionsMixin._report_stage_done(host, "par2")
        self.assertEqual(host.requested, 0)
        self.assertEqual(host._report_gate, {"test"})
        ArchiveActionsMixin._report_stage_done(host, "test")
        self.assertEqual(host.requested, 1)
        self.assertIsNone(host._report_gate)

    def test_cancel_cancels_par2_worker(self):
        pass
        from ui.archive_actions import ArchiveActionsMixin

        host = ArchiveActionsMixin.__new__(ArchiveActionsMixin)
        host._archive_create_worker = None
        par2 = _FakeWorker()
        host._par2_worker = par2
        messages = []
        host.statusBar = lambda: host
        host.showMessage = messages.append
        host._on_archive_progress_cancel()
        self.assertTrue(par2.cancel_called)


class TestDoneReportPar2Row(unittest.TestCase):
    pass

    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def _texts(self, report):
        from PySide6.QtWidgets import QLabel

        from ui.archive_done_dialog import ArchiveDoneDialog

        dlg = ArchiveDoneDialog(report, None, [])
        try:
            return [w.text() for w in dlg.findChildren(QLabel)]
        finally:
            dlg.deleteLater()

    def test_updated_archive_ok(self):
        texts = self._texts({
            "dest": "backup.zpaq", "is_update": True, "ok": True,
            "par2": {"status": "ok"},
        })
        self.assertIn(tr("create.done.par2"), texts)
        self.assertIn(tr("create.done.par2_ok"), texts)

    def test_new_archive_created(self):
        texts = self._texts({
            "dest": "backup.zpaq", "is_update": False, "ok": True,
            "par2": {"status": "ok"},
        })
        self.assertIn(tr("create.done.par2_created"), texts)

    def test_failed_shows_error(self):
        texts = self._texts({
            "dest": "backup.zpaq", "is_update": True, "ok": True,
            "par2": {"status": "failed", "error": "boom"},
        })
        self.assertIn(
            tr("create.done.par2_failed", error="boom"), texts)

    def test_no_par2_row_without_par2(self):
        texts = self._texts({
            "dest": "backup.zpaq", "is_update": True, "ok": True,
        })
        self.assertNotIn(tr("create.done.par2"), texts)


if __name__ == "__main__":
    unittest.main(verbosity=2)
