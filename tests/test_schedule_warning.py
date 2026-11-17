


from __future__ import annotations

import unittest
from datetime import datetime
from unittest import mock

from ui.schedule_warning import confirm_schedule_conflicts

NOW = datetime(2026, 11, 17, 12, 0)

CONTAINER = {
    "works": [{
        "id": "w", "title": "RIZPAQ", "dest": "F:/a.zpaq",
        "jobs": [
            {"id": "j1", "title": "Первое", "action": "backup",
             "schedule": {"enabled": True, "frequency": "hourly",
                          "interval": 1, "time": "00:00"}},
            {"id": "j2", "title": "Второе", "action": "backup",
             "schedule": {"enabled": True, "frequency": "hourly",
                          "interval": 1, "time": "00:00"}},
        ],
    }]
}
WORK = CONTAINER["works"][0]
JOB = WORK["jobs"][0]


class TestConfirmScheduleConflicts(unittest.TestCase):
    def test_user_declines(self):
        with mock.patch("ui.schedule_warning.QMessageBox.question",
                        return_value=mock.Mock()), \
             mock.patch("core.schedule_conflicts.datetime") as dt:
            dt.now.return_value = NOW
                                                                   
            self.assertFalse(confirm_schedule_conflicts(
                None, CONTAINER, WORK, JOB, JOB["schedule"]
            ))

    def test_user_accepts(self):
        from PySide6.QtWidgets import QMessageBox

        with mock.patch("ui.schedule_warning.QMessageBox.question",
                        return_value=QMessageBox.Yes), \
             mock.patch("core.schedule_conflicts.datetime") as dt:
            dt.now.return_value = NOW
            self.assertTrue(confirm_schedule_conflicts(
                None, CONTAINER, WORK, JOB, JOB["schedule"]
            ))

    def test_no_conflict_no_dialog(self):
        other = {"works": [{"id": "w", "title": "X", "dest": "F:/other.zpaq",
                            "jobs": [dict(JOB)]}]}
        with mock.patch("ui.schedule_warning.QMessageBox.question") as ask:
            self.assertTrue(confirm_schedule_conflicts(
                None, other, other["works"][0], other["works"][0]["jobs"][0],
                JOB["schedule"]
            ))
            ask.assert_not_called()


if __name__ == "__main__":
    unittest.main()
