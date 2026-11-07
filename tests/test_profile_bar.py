














from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language, tr              

set_language("ru", notify=False)

from ui.profile_bar import ProfileBar              
from ui.profile_bridge import PROFILES              


class _Host:
    pass








    def __init__(self, profile: str = "archive"):
        self._profile = profile
        self.profile_calls = 0

    def current_profile(self) -> str:
        self.profile_calls += 1
        return self._profile


class _BarCase(unittest.TestCase):
    def _make(self, profile: str = "archive"):
        host = _Host(profile)
        bar = ProfileBar(host=host)
                                                                      
                                                                     
        self.addCleanup(bar.deleteLater)
        return host, bar

    @staticmethod
    def _checked(bar) -> dict:
        return {code: btn.isChecked() for code, btn in bar._profile_buttons.items()}

    @staticmethod
    def _action_state(bar) -> dict:
        pass
        return {
            btn.text(): btn.property("active")
            for btn, *_ in bar._action_buttons
        }


class TestRebuildByPassedProfile(_BarCase):
    pass

    def test_initial_uses_host_profile(self):
        pass
        _host, bar = self._make("archive")
        checked = self._checked(bar)
        self.assertTrue(checked["archive"])
        self.assertFalse(checked["backup"])

    def test_rebuild_with_explicit_profile_overrides_host(self):
        pass







        host, bar = self._make("archive")
                                                                    
        self.assertTrue(self._checked(bar)["archive"])

        bar.rebuild("backup")

        checked = self._checked(bar)
        self.assertFalse(checked["archive"],
                         "сегмент archive должен быть погашен")
        self.assertTrue(checked["backup"],
                        "сегмент backup должен быть подсвечен")

    def test_rebuild_with_explicit_profile_affects_actions(self):
        pass





        _host, bar = self._make("archive")
        bar.rebuild("backup")

        state = self._action_state(bar)
        create_label = tr("menu.file.create_archive")
        run_label = tr("task.run_menu")
        self.assertIn(create_label, state)
        self.assertIn(run_label, state)
        self.assertEqual(state[create_label], "false",
                         "«Создать архив» должна быть неактивна в профиле backup")
        self.assertEqual(state[run_label], "true",
                         "«Запустить задание» должна быть активна в профиле backup")

    def test_rebuild_archive_actions_reversed(self):
        pass
        _host, bar = self._make("backup")
        bar.rebuild("archive")
        state = self._action_state(bar)
        self.assertEqual(state[tr("menu.file.create_archive")], "true")
        self.assertEqual(state[tr("task.run_menu")], "false")

    def test_rebuild_without_argument_uses_host(self):
        host, bar = self._make("backup")
        bar.rebuild()
        checked = self._checked(bar)
        self.assertTrue(checked["backup"])
        self.assertFalse(checked["archive"])

    def test_rebuild_with_invalid_profile_falls_back_to_host(self):
        pass



        host, bar = self._make("backup")
        bar.rebuild("no_such_profile")
        checked = self._checked(bar)
        self.assertTrue(checked["backup"],
                        "неизвестный профиль должен привести к host-профилю")
        self.assertFalse(checked["archive"])


class TestRebuildIdempotent(_BarCase):
    pass

    def test_second_rebuild_with_same_profile(self):
        host, bar = self._make("archive")
        bar.rebuild("backup")
        bar.rebuild("backup")
        checked = self._checked(bar)
        self.assertTrue(checked["backup"])
        self.assertFalse(checked["archive"])

    def test_switch_back_and_forth(self):
        host, bar = self._make("archive")
        for profile in ("backup", "archive", "backup", "archive"):
            bar.rebuild(profile)
            checked = self._checked(bar)
            self.assertTrue(checked[profile],
                            f"после rebuild({profile!r}) должен быть подсвечен {profile}")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
