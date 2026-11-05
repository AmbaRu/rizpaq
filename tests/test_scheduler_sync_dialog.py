from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.scheduler_sync_dialog import SchedulerSyncDialog


_WORK = {"id": "work-1", "title": "Docs"}
_JOB_ENABLED = {
    "id": "job-1",
    "title": "Daily",
    "schedule": {"enabled": True, "frequency": "daily",
                 "time": "02:00", "interval": 1},
}
_JOB_DISABLED = {
    "id": "job-2",
    "title": "Weekly",
    "schedule": {"enabled": False},
}
_ORPHAN = {"name": "Rizpaq_ghost_00000000_deadbeef",
           "status": "", "next_run": ""}


def _actions(add=None, disable=None, remove=None) -> dict:

    return {
        "add": list(add or []),
        "disable": list(disable or []),
        "remove": list(remove or []),
    }


def _make_dialog(actions=None) -> SchedulerSyncDialog:
    actions = actions if actions is not None else _actions()
    with mock.patch("core.scheduler.compute_sync_actions",
                    return_value=actions):
        dlg = SchedulerSyncDialog("D:/tasks.rzp", {})
    return dlg


class TestDialogConstruction(unittest.TestCase):
    def test_creates_without_actions(self):
        dlg = _make_dialog()
        self.assertIsNone(dlg._add_list)
        self.assertIsNone(dlg._disable_list)
        self.assertIsNone(dlg._remove_list)
        self.assertEqual(dlg.result_stats(),
                         {"added": 0, "disabled": 0, "removed": 0,
                          "failed": 0})
        dlg.close()

    def test_add_section_creates_list(self):
        dlg = _make_dialog(_actions(add=[(_WORK, _JOB_ENABLED)]))
        self.assertIsNotNone(dlg._add_list)
        self.assertEqual(dlg._add_list.count(), 1)
        self.assertIsNone(dlg._disable_list)
        self.assertIsNone(dlg._remove_list)
        dlg.close()

    def test_disable_section_creates_list(self):
        dlg = _make_dialog(_actions(disable=[(_WORK, _JOB_DISABLED)]))
        self.assertIsNotNone(dlg._disable_list)
        self.assertEqual(dlg._disable_list.count(), 1)
        dlg.close()

    def test_remove_section_creates_list(self):
        dlg = _make_dialog(_actions(remove=[_ORPHAN]))
        self.assertIsNotNone(dlg._remove_list)
        self.assertEqual(dlg._remove_list.count(), 1)
        dlg.close()

    def test_all_three_sections(self):
        dlg = _make_dialog(_actions(
            add=[(_WORK, _JOB_ENABLED)],
            disable=[(_WORK, _JOB_DISABLED)],
            remove=[_ORPHAN],
        ))
        self.assertIsNotNone(dlg._add_list)
        self.assertIsNotNone(dlg._disable_list)
        self.assertIsNotNone(dlg._remove_list)
        self.assertEqual(dlg._add_list.count(), 1)
        self.assertEqual(dlg._disable_list.count(), 1)
        self.assertEqual(dlg._remove_list.count(), 1)
        dlg.close()

    def test_empty_sections_are_not_shown(self):

        dlg = _make_dialog(_actions(add=[(_WORK, _JOB_ENABLED)]))
        self.assertIsNone(dlg._disable_list)
        self.assertIsNone(dlg._remove_list)
        dlg.close()


class TestListItems(unittest.TestCase):
    def test_items_are_checked_by_default(self):
        dlg = _make_dialog(_actions(
            add=[(_WORK, _JOB_ENABLED)],
            remove=[_ORPHAN],
        ))
        item_add = dlg._add_list.item(0)
        item_rem = dlg._remove_list.item(0)
        self.assertEqual(item_add.checkState(), Qt.Checked)
        self.assertEqual(item_rem.checkState(), Qt.Checked)
        dlg.close()

    def test_item_payload_is_entry(self):

        dlg = _make_dialog(_actions(
            add=[(_WORK, _JOB_ENABLED)],
            remove=[_ORPHAN],
        ))
        payload_add = dlg._add_list.item(0).data(Qt.UserRole)
        self.assertEqual(payload_add, (_WORK, _JOB_ENABLED))
        payload_rem = dlg._remove_list.item(0).data(Qt.UserRole)
        self.assertEqual(payload_rem, _ORPHAN)
        dlg.close()

    def test_label_for_add_is_work_slash_job(self):
        dlg = _make_dialog(_actions(add=[(_WORK, _JOB_ENABLED)]))
        text = dlg._add_list.item(0).text()
        self.assertIn("Docs", text)
        self.assertIn("Daily", text)
        dlg.close()

    def test_label_for_orphan_is_name(self):
        dlg = _make_dialog(_actions(remove=[_ORPHAN]))
        text = dlg._remove_list.item(0).text()
        self.assertIn("Rizpaq_ghost", text)
        dlg.close()

    def test_format_entry_handles_missing_titles(self):

        text = SchedulerSyncDialog._format_entry(
            ({"id": "w", "title": ""}, {"id": "j", "title": ""}),
            kind="add",
        )
        self.assertTrue(text)
        dlg_close = SchedulerSyncDialog._format_entry({}, kind="remove")
        self.assertTrue(dlg_close)


class TestCheckedEntries(unittest.TestCase):
    def test_returns_only_checked(self):
        dlg = _make_dialog(_actions(add=[
            (_WORK, _JOB_ENABLED),
            (_WORK, {"id": "job-3", "title": "Monthly",
                     "schedule": {"enabled": True, "frequency": "monthly",
                                  "time": "03:00", "interval": 1}}),
        ]))

        dlg._add_list.item(1).setCheckState(Qt.Unchecked)
        checked = dlg._checked_entries(dlg._add_list)
        self.assertEqual(len(checked), 1)
        self.assertEqual(checked[0], (_WORK, _JOB_ENABLED))
        dlg.close()

    def test_none_list_gives_empty(self):
        dlg = _make_dialog()
        self.assertEqual(dlg._checked_entries(None), [])
        dlg.close()

    def test_all_checked_gives_all(self):
        dlg = _make_dialog(_actions(remove=[_ORPHAN,
                                            {"name": "Rizpaq_x_00000000_00000000"}]))
        checked = dlg._checked_entries(dlg._remove_list)
        self.assertEqual(len(checked), 2)
        dlg.close()


class TestApplyAndAccept(unittest.TestCase):

    def _run_apply(self, dlg):
        with mock.patch.object(QMessageBox, "information"), \
             mock.patch.object(QMessageBox, "warning"):
            dlg._apply_and_accept()

    def test_empty_actions_calls_nothing(self):
        dlg = _make_dialog()
        with mock.patch("core.scheduler.create_scheduled_task") as c, \
             mock.patch("core.scheduler.remove_scheduled_task") as r, \
             mock.patch("core.scheduler.remove_scheduled_task_by_name") as rb:
            self._run_apply(dlg)
        c.assert_not_called()
        r.assert_not_called()
        rb.assert_not_called()
        self.assertEqual(dlg.result_stats(),
                         {"added": 0, "disabled": 0, "removed": 0,
                          "failed": 0})
        dlg.close()

    def test_add_calls_create_scheduled_task(self):
        dlg = _make_dialog(_actions(add=[(_WORK, _JOB_ENABLED)]))
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=True) as c, \
             mock.patch("core.scheduler.remove_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name"):
            self._run_apply(dlg)
        c.assert_called_once()
        args, _kwargs = c.call_args

        self.assertEqual(args[0], "D:/tasks.rzp")
        self.assertEqual(args[1], _WORK)
        self.assertEqual(args[2], _JOB_ENABLED)
        self.assertEqual(args[3], _JOB_ENABLED["schedule"])
        self.assertEqual(dlg.result_stats()["added"], 1)
        dlg.close()

    def test_disable_calls_remove_scheduled_task(self):
        dlg = _make_dialog(_actions(disable=[(_WORK, _JOB_DISABLED)]))
        with mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task",
                        return_value=True) as r, \
             mock.patch("core.scheduler.remove_scheduled_task_by_name"):
            self._run_apply(dlg)
        r.assert_called_once_with(_WORK, _JOB_DISABLED)
        self.assertEqual(dlg.result_stats()["disabled"], 1)
        dlg.close()

    def test_remove_calls_remove_by_name(self):
        dlg = _make_dialog(_actions(remove=[_ORPHAN]))
        with mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name",
                        return_value=True) as rb:
            self._run_apply(dlg)
        rb.assert_called_once_with(_ORPHAN["name"])
        self.assertEqual(dlg.result_stats()["removed"], 1)
        dlg.close()

    def test_order_remove_then_add_then_disable(self):
        dlg = _make_dialog(_actions(
            add=[(_WORK, _JOB_ENABLED)],
            disable=[(_WORK, _JOB_DISABLED)],
            remove=[_ORPHAN],
        ))
        calls: list = []

        def _rec_remove_by_name(name):
            calls.append(("remove_by_name", name))
            return True

        def _rec_create(rzp, work, job, sched):
            calls.append(("create", job.get("id")))
            return True

        def _rec_remove(work, job):
            calls.append(("remove", job.get("id")))
            return True

        with mock.patch("core.scheduler.remove_scheduled_task_by_name",
                        side_effect=_rec_remove_by_name), \
             mock.patch("core.scheduler.create_scheduled_task",
                        side_effect=_rec_create), \
             mock.patch("core.scheduler.remove_scheduled_task",
                        side_effect=_rec_remove):
            self._run_apply(dlg)

        kinds = [c[0] for c in calls]
        self.assertEqual(kinds, ["remove_by_name", "create", "remove"])
        dlg.close()

    def test_unchecked_items_are_skipped(self):

        dlg = _make_dialog(_actions(add=[
            (_WORK, _JOB_ENABLED),
            (_WORK, {"id": "job-3", "title": "Monthly",
                     "schedule": {"enabled": True, "frequency": "monthly",
                                  "time": "03:00", "interval": 1}}),
        ]))
        dlg._add_list.item(1).setCheckState(Qt.Unchecked)
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=True) as c, \
             mock.patch("core.scheduler.remove_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name"):
            self._run_apply(dlg)
        c.assert_called_once()
        self.assertEqual(dlg.result_stats()["added"], 1)
        dlg.close()

    def test_failed_create_counts_as_failed(self):
        dlg = _make_dialog(_actions(add=[(_WORK, _JOB_ENABLED)]))
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=False), \
             mock.patch("core.scheduler.remove_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name"):
            self._run_apply(dlg)
        stats = dlg.result_stats()
        self.assertEqual(stats["added"], 0)
        self.assertEqual(stats["failed"], 1)
        dlg.close()

    def test_exception_counts_as_failed_but_does_not_break_others(self):
        dlg = _make_dialog(_actions(add=[
            (_WORK, _JOB_ENABLED),
            (_WORK, {"id": "job-3", "title": "Monthly",
                     "schedule": {"enabled": True, "frequency": "monthly",
                                  "time": "03:00", "interval": 1}}),
        ]))
        real_create = mock.Mock()

        def _side(rzp, work, job, sched):
            if job.get("id") == "job-1":
                raise RuntimeError("boom")
            real_create(rzp, work, job, sched)
            return True

        with mock.patch("core.scheduler.create_scheduled_task",
                        side_effect=_side), \
             mock.patch("core.scheduler.remove_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name"):
            self._run_apply(dlg)
        stats = dlg.result_stats()
        self.assertEqual(stats["added"], 1)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(real_create.call_count, 1)
        dlg.close()

    def test_accept_is_called(self):
        dlg = _make_dialog()
        with mock.patch.object(dlg, "accept") as acc, \
             mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name"):
            self._run_apply(dlg)
        acc.assert_called_once()
        dlg.close()


class TestOrphanEntryPayload(unittest.TestCase):
    def test_orphan_entry_payload_is_dict(self):
        dlg = _make_dialog(_actions(remove=[_ORPHAN]))
        payload = dlg._remove_list.item(0).data(Qt.UserRole)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("name"), _ORPHAN["name"])
        dlg.close()

    def test_orphan_without_name_is_counted_failed(self):
        dlg = _make_dialog(_actions(remove=[
            {"status": "", "next_run": ""},
            _ORPHAN,
        ]))
        with mock.patch("core.scheduler.remove_scheduled_task_by_name",
                        return_value=True) as rb, \
             mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task"):
            with mock.patch.object(QMessageBox, "information"), \
                 mock.patch.object(QMessageBox, "warning"):
                dlg._apply_and_accept()

        rb.assert_called_once_with(_ORPHAN["name"])
        stats = dlg.result_stats()
        self.assertEqual(stats["removed"], 1)
        self.assertEqual(stats["failed"], 1)
        dlg.close()


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
