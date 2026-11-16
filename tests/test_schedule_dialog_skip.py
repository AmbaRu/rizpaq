                       










from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication              

_APP = QApplication.instance() or QApplication(sys.argv)

from ui import i18n              
from ui.scheduler_dialog import ScheduleDialog              

i18n.set_language("ru", notify=False)


def _daily(skip=None):
    schedule = {
        "enabled": True,
        "frequency": "daily",
        "interval": 1,
        "time": "02:00",
    }
    if skip is not None:
        schedule["skip_unchanged"] = skip
    return schedule


class SkipUnchangedDialogTest(unittest.TestCase):
    def _dialog(self, schedule):
        dlg = ScheduleDialog(initial_schedule=schedule)
        self.addCleanup(dlg.deleteLater)
        return dlg

    def test_checked_flag_is_saved(self):
        dlg = self._dialog(_daily())
        dlg._skip_changed_cb.setChecked(True)
        dlg._validate_and_accept()

        result = dlg.result_schedule()
        self.assertEqual(result["frequency"], "daily")
        self.assertTrue(result["skip_unchanged"])

    def test_unchecked_flag_is_not_stored(self):
        dlg = self._dialog(_daily())
        dlg._validate_and_accept()

        self.assertNotIn("skip_unchanged", dlg.result_schedule())

    def test_flag_is_restored(self):
        dlg = self._dialog(_daily(skip=True))
        self.assertTrue(dlg._skip_changed_cb.isChecked())

    def test_continuous_hides_the_option(self):
        dlg = self._dialog({
            "enabled": True,
            "frequency": "continuous",
            "interval": 5,
        })
        self.assertTrue(dlg._skip_changed_cb.isHidden())
        self.assertTrue(dlg._skip_changed_hint.isHidden())

        dlg._rb_daily.setChecked(True)
        dlg._update_ui_state()
        self.assertFalse(dlg._skip_changed_cb.isHidden())
        self.assertFalse(dlg._skip_changed_hint.isHidden())

    def test_continuous_does_not_store_the_flag(self):
        dlg = self._dialog({
            "enabled": True,
            "frequency": "continuous",
            "interval": 5,
        })
                                                                  
                                                      
        dlg._skip_changed_cb.setChecked(True)
        dlg._validate_and_accept()

        self.assertNotIn("skip_unchanged", dlg.result_schedule())

    def test_check_job_hides_and_ignores_the_option(self):
        pass
        dlg = ScheduleDialog(
            initial_schedule=_daily(), allow_skip_unchanged=False
        )
        self.addCleanup(dlg.deleteLater)

        self.assertTrue(dlg._skip_changed_cb.isHidden())
        dlg._skip_changed_cb.setChecked(True)
        dlg._validate_and_accept()

        self.assertNotIn("skip_unchanged", dlg.result_schedule())


if __name__ == "__main__":
    unittest.main(verbosity=2)
