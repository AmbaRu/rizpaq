





from __future__ import annotations

import unittest
from unittest import mock

from PySide6.QtWidgets import QMessageBox

from core import scheduler
from core import tasks as tasks_mod
from ui import stale_scheduler


class _Parent:
    def tasks_dir(self):
        return r"D:\Backup"


class TestStaleStartup(unittest.TestCase):
    def setUp(self):
        stale_scheduler._reset_for_tests()
        self.addCleanup(stale_scheduler._reset_for_tests)

    def test_recreates_when_user_agrees(self):
        task = {"name": "Rizpaq_b_old_12345678", "command": "python main.py --task x"}
        work = {"id": "w", "title": "RIZPAQ"}
        job = {"id": "j", "title": "Задание", "schedule": {"enabled": True,
               "frequency": "hourly", "interval": 1, "time": "00:00"}}
        container = {"works": [{"id": "w", "jobs": [job]}]}

        with mock.patch.object(stale_scheduler.sys, "frozen", True, create=True), \
             mock.patch.object(scheduler, "find_stale_runner_tasks", return_value=[task]), \
             mock.patch.object(scheduler, "container_task_map",
                               return_value={task["name"]: (work, job)}), \
             mock.patch.object(scheduler, "create_scheduled_task",
                               return_value=True) as create, \
             mock.patch.object(tasks_mod, "load_container", return_value=container), \
             mock.patch.object(tasks_mod, "container_path", return_value="p.rzp"), \
             mock.patch.object(stale_scheduler.QMessageBox, "question",
                               return_value=QMessageBox.Yes), \
             mock.patch.object(stale_scheduler.QMessageBox, "information") as info:
            stale_scheduler.check_on_startup(_Parent())

        create.assert_called_once()
        info.assert_called_once()

    def test_start_check_uses_background_worker(self):
        from ui.stale_scheduler import start_check

        with mock.patch.object(stale_scheduler.sys, "frozen", True, create=True), \
             mock.patch("workers.stale_worker.StaleTaskWorker") as worker_cls:
            start_check(_Parent())
            worker_cls.assert_called_once()
            worker_cls.return_value.start.assert_called_once()
            start_check(_Parent())
            worker_cls.assert_called_once()                      

    def test_skipped_on_second_call(self):
        with mock.patch.object(stale_scheduler.sys, "frozen", True, create=True), \
             mock.patch.object(scheduler, "find_stale_runner_tasks",
                               return_value=[]) as find:
            stale_scheduler.check_on_startup(_Parent())
            stale_scheduler.check_on_startup(_Parent())
            find.assert_called_once()


if __name__ == "__main__":
    unittest.main()
