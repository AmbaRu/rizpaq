from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.archive_actions import ArchiveActionsMixin


class _Host(ArchiveActionsMixin):

    zpaq_available = True
    zpaq_bin = "zpaqfranz"

    def __init__(self, backup_page=None):
        self.backup_page = backup_page
        self.status_messages = []

        self.calls = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        self.status_messages.append(text)


    def _run_job(self, work_id, job_id):
        self.calls.append(("run", work_id, job_id))

    def _edit_job(self, work_id, job_id):
        self.calls.append(("edit", work_id, job_id))


class _FakeBackupPage:

    def __init__(self, selected=None, raises=False):
        self._selected = selected
        self._raises = raises

    def selected_job(self):
        if self._raises:
            raise RuntimeError("boom")
        return self._selected


class _FakeBackupPageNoMethod:

    pass


class TestSelectedBackupJob(unittest.TestCase):


    def test_none_when_page_missing(self):
        host = _Host(backup_page=None)
        self.assertIsNone(host._selected_backup_job())

    def test_none_when_page_has_no_method(self):
        host = _Host(backup_page=_FakeBackupPageNoMethod())
        self.assertIsNone(host._selected_backup_job())

    def test_none_when_method_raises(self):
        page = _FakeBackupPage(raises=True)
        host = _Host(backup_page=page)
        self.assertIsNone(host._selected_backup_job())

    def test_none_when_method_returns_none(self):
        page = _FakeBackupPage(selected=None)
        host = _Host(backup_page=page)
        self.assertIsNone(host._selected_backup_job())

    def test_returns_selection_from_page(self):
        selected = {"work_id": "w1", "job_id": "j1"}
        page = _FakeBackupPage(selected=selected)
        host = _Host(backup_page=page)
        self.assertEqual(host._selected_backup_job(), selected)


class TestRunTask(unittest.TestCase):


    def test_runs_selected_job(self):
        page = _FakeBackupPage(selected={"work_id": "w1", "job_id": "j1"})
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information") as info:
            host._on_run_task()

        self.assertEqual(host.calls, [("run", "w1", "j1")])
        info.assert_not_called()

    def test_shows_message_when_nothing_selected(self):
        page = _FakeBackupPage(selected=None)
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information") as info:
            host._on_run_task()

        self.assertEqual(host.calls, [], "без выделения запускать нечего")
        info.assert_called_once()

    def test_shows_message_when_page_missing(self):
        host = _Host(backup_page=None)

        with mock.patch.object(QMessageBox, "information") as info:
            host._on_run_task()

        self.assertEqual(host.calls, [])
        info.assert_called_once()

    def test_absorbs_clicked_bool(self):
        page = _FakeBackupPage(selected={"work_id": "w1", "job_id": "j1"})
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information"):
            host._on_run_task(False)

        self.assertEqual(host.calls, [("run", "w1", "j1")])

    def test_no_warning_if_page_raises(self):

        page = _FakeBackupPage(raises=True)
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information") as info:
            host._on_run_task()

        self.assertEqual(host.calls, [])
        info.assert_called_once()


class TestEditTask(unittest.TestCase):


    def test_edits_selected_job(self):
        page = _FakeBackupPage(selected={"work_id": "w1", "job_id": "j1"})
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information") as info:
            host._on_edit_task()

        self.assertEqual(host.calls, [("edit", "w1", "j1")])
        info.assert_not_called()

    def test_shows_message_when_nothing_selected(self):
        page = _FakeBackupPage(selected=None)
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information") as info:
            host._on_edit_task()

        self.assertEqual(host.calls, [])
        info.assert_called_once()

    def test_absorbs_clicked_bool(self):
        page = _FakeBackupPage(selected={"work_id": "w1", "job_id": "j1"})
        host = _Host(backup_page=page)

        with mock.patch.object(QMessageBox, "information"):
            host._on_edit_task(False)

        self.assertEqual(host.calls, [("edit", "w1", "j1")])


class TestSplitSettingsWorkJob(unittest.TestCase):

    def _host(self):
        return _Host(backup_page=None)

    def test_work_fields_go_to_work(self):
        host = self._host()
        work_fields, _job = host._split_settings_work_job({
            "sources": ["D:/a"],
            "dest": "D:/b.zpaq",
            "password": "pw",
            "only_masks": ["*.txt"],
            "not_masks": ["*.bak"],
            "comment": "weekly",
        })
        self.assertEqual(work_fields["sources"], ["D:/a"])
        self.assertEqual(work_fields["dest"], "D:/b.zpaq")
        self.assertEqual(work_fields["only_masks"], ["*.txt"])
        self.assertEqual(work_fields["not_masks"], ["*.bak"])
        self.assertEqual(work_fields["comment"], "weekly")
        self.assertEqual(work_fields["password"], "pw")

    def test_job_fields_go_to_job(self):
        host = self._host()
        _work, job = host._split_settings_work_job({
            "sources": ["D:/a"],
            "dest": "D:/b.zpaq",
            "level_key": "m5",
            "level": ["-m5"],
            "verify": "full",
            "vss": True,
            "task_log_mode": "full",
        })
        self.assertEqual(job["level_key"], "m5")
        self.assertEqual(job["level"], ["-m5"])
        self.assertEqual(job["verify"], "full")
        self.assertTrue(job["vss"])
        self.assertEqual(job["task_log_mode"], "full")

    def test_password_absent_when_not_set(self):

        host = self._host()
        work_fields, _ = host._split_settings_work_job({
            "sources": ["D:/a"],
            "dest": "D:/b.zpaq",
        })
        self.assertNotIn("password", work_fields)

    def test_missing_password_in_settings_does_not_crash(self):
        host = self._host()
        work_fields, _job = host._split_settings_work_job({})
        self.assertEqual(work_fields["sources"], [])
        self.assertEqual(work_fields["dest"], "")
        self.assertNotIn("password", work_fields)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
