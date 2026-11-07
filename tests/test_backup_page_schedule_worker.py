

























from __future__ import annotations

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QThread              
from PySide6.QtWidgets import QApplication, QWidget              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language              

set_language("ru", notify=False)

from core.tasks import (              
    add_job,
    add_work,
    container_path,
    empty_container,
    save_container,
)
from ui import backup_page as bp              
from ui.backup_page import BackupPage, _ScheduleWorker              


class _QHost(QWidget):
    pass












    def __init__(self, tasks_dir):
        QWidget.__init__(self)
        cfg = type("Cfg", (), {"tasks_dir": tasks_dir})()
        self._cfg = cfg
        self._workers = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        pass

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)


class _TmpMixin(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_bp_sched_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write_container(self, works=None):
        c = empty_container()
        for w_spec in (works or []):
            w = add_work(
                c,
                title=w_spec.get("work_title", "W"),
                sources=w_spec.get("sources") or ["D:/src"],
                dest=w_spec.get("dest") or "D:/out.zpaq",
            )
            for j_spec in (w_spec.get("jobs") or []):
                add_job(c, w["id"], j_spec)
        save_container(container_path(self.dir), c)
        return c

    def _dispose_page(self, page, host):
        pass




        try:
            page._watch_timer.stop()
        except Exception:
            pass
        try:
            page._watcher.setPaths([])
        except Exception:
            pass

        worker = getattr(page, "_schedule_worker", None)
        if worker is not None:
            try:
                worker.cancel_request()
            except Exception:
                pass
            try:
                worker.wait(5000)
            except Exception:
                pass

        page.close()
        page.deleteLater()
        host.close()
        host.deleteLater()


class TestWorkerGoesToHostWorkers(_TmpMixin):
    pass

    def test_worker_added_to_host_workers(self):
        pass






        self.write_container([
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        host = _QHost(tasks_dir=str(self.dir))

                                                                   
                                    
        with unittest.mock.patch(
            "core.scheduler.schedule_info_for_container",
            return_value={},
        ):
            page = BackupPage(host)
        self.addCleanup(self._dispose_page, page, host)

        worker = getattr(page, "_schedule_worker", None)
        self.assertIsNotNone(
            worker,
            "_load_schedule не создал воркер, хотя в контейнере есть задания",
        )
        self.assertIn(
            worker, host._workers,
            "воркер _ScheduleWorker не попал в _host._workers — "
            "window_shell.py::closeEvent его не увидит и не остановит "
            "при закрытии окна",
        )

    def test_worker_is_real_qthread(self):
        pass






        self.write_container([
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        host = _QHost(tasks_dir=str(self.dir))

        with unittest.mock.patch(
            "core.scheduler.schedule_info_for_container",
            return_value={},
        ):
            page = BackupPage(host)
        self.addCleanup(self._dispose_page, page, host)

        worker = getattr(page, "_schedule_worker", None)
        self.assertIsInstance(worker, QThread)
        self.assertIsInstance(worker, _ScheduleWorker)


class TestCancelRequestStopsDone(_TmpMixin):
    pass








    def test_cancel_request_sets_flag(self):
        pass
        worker = _ScheduleWorker({})
        self.assertFalse(worker._cancel)
        worker.cancel_request()
        self.assertTrue(worker._cancel)

    def test_cancelled_worker_does_not_emit_done(self):
        pass






        received = []

        worker = _ScheduleWorker({})
        worker.done.connect(received.append)
        worker.cancel_request()

                                                                         
        with unittest.mock.patch(
            "core.scheduler.schedule_info_for_container",
            return_value={"j1": {"scheduled": True}},
        ):
            worker.run()

                                                                 
        _APP.processEvents()
                                                                        
                                                                        
        time.sleep(0.05)
        _APP.processEvents()

        self.assertEqual(
            received, [],
            "отменённый воркер всё равно эмитил done — на уничтоженной "
            "странице это привело бы к RuntimeError",
        )


class TestApplyScheduleSurvivesDeletedPage(_TmpMixin):
    pass







    def test_apply_schedule_survives_isvisible_runtimeerror(self):
        self.write_container([
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        host = _QHost(tasks_dir=str(self.dir))

        with unittest.mock.patch(
            "core.scheduler.schedule_info_for_container",
            return_value={},
        ):
            page = BackupPage(host)
        self.addCleanup(self._dispose_page, page, host)

                                                                  
                                                                       
                           
        def boom_is_visible():
            raise RuntimeError("Internal C++ object already deleted")

        page.isVisible = boom_is_visible

                                                       
        try:
            page._apply_schedule({"j1": {"scheduled": True, "next_run": "x"}})
        except RuntimeError:
            self.fail(
                "_apply_schedule не защищён от RuntimeError: на уничтоженной "
                "странице он упадёт в сигнале done — Qt напечатает это в "
                "stderr, а пользователь не увидит ничего"
            )


import unittest.mock                                                   


if __name__ == "__main__":
    unittest.main()
