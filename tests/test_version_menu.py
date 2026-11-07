
























from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QCoreApplication, QEvent              
from PySide6.QtGui import QActionGroup              
from PySide6.QtWidgets import QApplication, QMenu, QWidget              

from core.models import ArchiveVersion              
from ui.version_menu import VersionMenuMixin              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))



def _versions(n: int = 5) -> list:
    return [
        ArchiveVersion(
            number=i,
            date="2026-01-01",
            time="12:00:00",
            added=1,
            removed=0,
            bytes_added=100,
            comment=f"rev {i}",
        )
        for i in range(1, n + 1)
    ]


class _Harness(VersionMenuMixin, QWidget):
    pass

    def __init__(self):
        QWidget.__init__(self)
        self._versions_menu = QMenu(self)
        self.mode = "archive"
        self.archive_path = "C:/test.zpaq"
        self.versions = _versions()
        self.version_slice = 2
        self.convert_action = None
        self.entries = []
        self._on_version_slice = lambda n: None
        self._populate_right_archive = lambda: None

    def statusBar(self):                                
        return None


def _count_action_groups(widget: QWidget) -> int:
    pass
    count = 0
    stack = list(widget.children())
    while stack:
        obj = stack.pop()
        if isinstance(obj, QActionGroup):
            count += 1
        stack.extend(obj.children())
    return count


class TestVersionsMenuLeak(unittest.TestCase):
    def setUp(self):
        self.win = _Harness()

    def tearDown(self):
        self.win.deleteLater()
                                                                      
                                                                     
                                                                     
                                                            
        self._drain_events()

    def test_repeated_rebuild_does_not_accumulate_action_groups(self):
        pass







        self._drain_events()
        before = _count_action_groups(self.win)

        for _ in range(50):
            self.win._rebuild_versions_menu()

        self._drain_events()
        after = _count_action_groups(self.win)

        self.assertLessEqual(
            after - before,
            2,
            f"утечка QActionGroup: было {before}, стало {after} после 50 вызовов",
        )

    @staticmethod
    def _drain_events() -> None:
        pass






        for _ in range(3):
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_action_group_is_deleted_later(self):
        pass
        self.win._rebuild_versions_menu()
        self._drain_events()
        first = self.win._ver_group
        self.assertIsNotNone(first)

        self.win._rebuild_versions_menu()
        self._drain_events()

        self.assertIsNot(first, self.win._ver_group, "создана новая группа")
        self.assertEqual(
            _count_action_groups(self.win),
            1,
            "старая группа должна быть удалена, остаться может только новая",
        )

    def test_rebuild_works_without_archive(self):
        pass
        self.win.mode = "fs"
        self.win.archive_path = None
        self.win._rebuild_versions_menu()
        self._drain_events()
        self.assertEqual(_count_action_groups(self.win), 0)

    def test_none_menu_is_safe(self):
        pass
        self.win._versions_menu = None
        self.win._rebuild_versions_menu()                     

    def test_menu_populated_with_actions(self):
        pass
        self.win.version_slice = 3
        self.win._rebuild_versions_menu()
        self._drain_events()

        actions = self.win._versions_menu.actions()
                                               
        self.assertEqual(len(actions), 7)
        self.assertTrue(actions[0].isCheckable())
        self.assertIsNone(actions[0].data())
        self.assertEqual(actions[2].data(), 1)
        self.assertTrue(actions[2].isChecked() is False)
        self.assertTrue(actions[4].isChecked(), "v3 должен быть отмечен")

    def test_group_is_exclusive(self):
        self.win._rebuild_versions_menu()
        self._drain_events()
        self.assertTrue(self.win._ver_group.isExclusive())


if __name__ == "__main__":
    unittest.main()
