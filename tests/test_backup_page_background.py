from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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
from ui.backup_page import BackupPage
from ui.qt_compat import YES_BUTTON


class _QHost(QWidget):

    def __init__(self, tasks_dir):
        QWidget.__init__(self)
        self._cfg = type(
            "Cfg", (), {"tasks_dir": str(tasks_dir) if tasks_dir else None}
        )()
        self._workers = []
        self._messages = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        self._messages.append(text)

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)


class _PlainHost:

    def __init__(self, tasks_dir):
        self._cfg = type(
            "Cfg", (), {"tasks_dir": str(tasks_dir) if tasks_dir else None}
        )()
        self._workers = []
        self._messages = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        self._messages.append(text)

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)


class _TmpMixin(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_bg_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write_container(self, works=None):
        c = empty_container()
        for w_spec in works or []:
            w = add_work(c, w_spec["title"], ["D:/src"], "D:/out.zpaq")
            for j_spec in w_spec.get("jobs") or []:
                add_job(c, w["id"], j_spec)
        save_container(container_path(self.dir), c)
        return c

    def _dispose(self, page, host):
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
        if isinstance(host, QWidget):
            host.close()
            host.deleteLater()

    def _make_page(self, host, works):
        self.write_container(works)
        with mock.patch(
            "core.scheduler.schedule_info_for_container", return_value={}
        ):
            page = BackupPage(host)
        self.addCleanup(self._dispose, page, host)
        return page, page._container


class TestLaunchBackgroundWorker(_TmpMixin):


    def _fake_worker(self):
        from PySide6.QtCore import QObject, Signal

        class _W(QObject):
            done = Signal()
            finished = Signal()

            def __init__(self):
                super().__init__()
                self.started = False

            def start(self):
                self.started = True

        return _W()

    def test_returns_true_for_qwidget(self):
        host = _QHost(self.dir)
        page, _container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        w = self._fake_worker()
        self.assertTrue(page._launch_background_worker(w))
        self.assertIn(w, host._workers,
                      "воркер не добавлен в host._workers — "
                      "closeEvent его не остановит")

    def test_returns_false_for_plain_object(self):
        host = _PlainHost(self.dir)
        page, _container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])


        self.assertEqual(host._workers, [],
                         "_load_schedule добавил воркер в host._workers "
                         "при не-QWidget-хосте — там ему не место")
        w = self._fake_worker()
        self.assertFalse(page._launch_background_worker(w))
        self.assertEqual(host._workers, [])

    def test_started_called(self):
        host = _QHost(self.dir)
        page, _container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        w = self._fake_worker()
        page._launch_background_worker(w)
        self.assertTrue(w.started, "start() не вызван")


class TestPlainHostSyncSchedule(_TmpMixin):

    def test_no_worker_created_for_plain_host(self):

        host = _PlainHost(self.dir)
        page, _container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        self.assertIsNone(
            page._schedule_worker,
            "при не-QWidget-хосте _ScheduleWorker не должен создаваться — "
            "он живёт со страницей, а не с окном",
        )
        self.assertEqual(host._workers, [],
                         "воркер не должен попадать в host._workers")

    def test_schedule_read_synchronously(self):
        self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        host = _PlainHost(self.dir)
        fake_info = {"j-mock": {"scheduled": True, "next_run": "2026-10-03"}}
        with mock.patch(
            "core.scheduler.schedule_info_for_container",
            return_value=fake_info,
        ) as sic:
            page = BackupPage(host)
        self.addCleanup(self._dispose, page, host)

        self.assertTrue(sic.called, "schedule_info_for_container не вызван")
        self.assertEqual(page._schedule_info, fake_info,
                         "результат не применён к self._schedule_info")
        self.assertIsNone(page._schedule_worker)


class TestDeleteWorkInBackground(_TmpMixin):


    def test_qwidget_host_uses_worker(self):
        host = _QHost(self.dir)
        page, container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [
                {"title": "Daily"},
                {"title": "Weekly"},
            ],
        }])
        work_id = container["works"][0]["id"]

        launched = []
        with mock.patch(
            "workers.schedule_worker.ScheduleRemoveWorker"
        ) as worker_cls, mock.patch(
            "core.scheduler.remove_scheduled_task_by_name"
        ) as sync_remove, mock.patch(
            "ui.backup_page.QMessageBox.question",
            return_value=YES_BUTTON,
        ):
            worker_cls.return_value = mock.MagicMock()
            with mock.patch.object(
                page, "_launch_background_worker",
                side_effect=lambda w: (launched.append(w), True)[1],
            ):
                page._delete_work(work_id)

        self.assertTrue(launched, "воркер не запущен на QWidget-хосте")
        sync_remove.assert_not_called()

    def test_plain_host_uses_sync_fallback(self):
        host = _PlainHost(self.dir)
        page, container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [
                {"title": "Daily"},
                {"title": "Weekly"},
            ],
        }])
        work_id = container["works"][0]["id"]

        with mock.patch(
            "core.scheduler.remove_scheduled_task_by_name"
        ) as sync_remove, mock.patch.object(
            page, "_launch_background_worker", return_value=False,
        ), mock.patch(
            "ui.backup_page.QMessageBox.question",
            return_value=YES_BUTTON,
        ):
            sync_remove.return_value = True
            page._delete_work(work_id)

        self.assertGreaterEqual(
            sync_remove.call_count, 2,
            "синхронный fallback не снял регистрации",
        )

    def test_worker_receives_all_job_names(self):

        host = _QHost(self.dir)
        page, container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [
                {"title": "Daily"},
                {"title": "Weekly"},
            ],
        }])
        work_id = container["works"][0]["id"]

        names_seen = []
        with mock.patch(
            "workers.schedule_worker.ScheduleRemoveWorker"
        ) as worker_cls, mock.patch(
            "ui.backup_page.QMessageBox.question", return_value=YES_BUTTON,
        ):
            def _capture(names):
                names_seen.append(names)
                return mock.MagicMock()
            worker_cls.side_effect = _capture
            with mock.patch.object(
                page, "_launch_background_worker", return_value=True,
            ):
                page._delete_work(work_id)

        self.assertEqual(len(names_seen), 1,
                         "воркер должен создаваться ровно один раз")
        self.assertEqual(len(names_seen[0]), 2,
                         "у работы два задания — воркер должен получить два имени")


class TestDeleteJobInBackground(_TmpMixin):
    def test_uses_worker(self):
        host = _QHost(self.dir)
        page, container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        job_id = container["works"][0]["jobs"][0]["id"]

        launched = []
        with mock.patch(
            "workers.schedule_worker.ScheduleRemoveWorker"
        ) as worker_cls, mock.patch(
            "core.scheduler.remove_scheduled_task_by_name"
        ) as sync_remove, mock.patch(
            "ui.backup_page.QMessageBox.question", return_value=YES_BUTTON,
        ):
            worker_cls.return_value = mock.MagicMock()
            with mock.patch.object(
                page, "_launch_background_worker",
                side_effect=lambda w: (launched.append(w), True)[1],
            ):
                page._delete_job(job_id)

        self.assertTrue(launched, "воркер удаления не запущен")
        sync_remove.assert_not_called()


class TestScheduleJobInBackground(_TmpMixin):
    def test_uses_create_worker(self):
        host = _QHost(self.dir)
        page, container = self._make_page(host, works=[{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        job_id = container["works"][0]["jobs"][0]["id"]

        fake_dlg = mock.MagicMock()
        fake_dlg.exec.return_value = 1
        fake_dlg.result_schedule.return_value = {
            "enabled": True, "frequency": "daily",
            "time": "03:00", "interval": 1,
        }

        launched = []
        with mock.patch(
            "ui.scheduler_dialog.ScheduleDialog", return_value=fake_dlg,
        ), mock.patch(
            "workers.schedule_worker.ScheduleCreateWorker",
        ) as create_cls, mock.patch(
            "core.scheduler.create_scheduled_task",
        ) as sync_create:
            create_cls.return_value = mock.MagicMock()
            with mock.patch.object(
                page, "_launch_background_worker",
                side_effect=lambda w: (launched.append(w), True)[1],
            ):
                page._schedule_job(job_id)

        self.assertTrue(launched, "воркер создания задачи не запущен")
        sync_create.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
