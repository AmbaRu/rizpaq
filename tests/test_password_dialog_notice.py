













from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QTimer              
from PySide6.QtWidgets import (              
    QApplication,
    QMainWindow,
    QPlainTextEdit,
)

from ui import i18n              
from ui.app_services import AppServicesMixin              
from ui.archive_loader import ArchiveLoaderMixin              
from ui.operation_notice import NOTICE_DELAY_MS              

_APP = QApplication.instance() or QApplication([])
i18n.set_language("ru", notify=False)


def _pump(ms: int) -> None:
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        _APP.processEvents()
        time.sleep(0.005)


class _Loader(AppServicesMixin, ArchiveLoaderMixin, QMainWindow):
    pass

    def __init__(self):
        QMainWindow.__init__(self)
        self._busy_base = ""
        self._busy_n = 0
        self._busy_depth = 0
        self._notice = None
        self._wait_cursor = False
        self._busy_timer = QTimer(self)
        self._busy_timer.setInterval(350)
        self._busy_timer.timeout.connect(self._tick_busy)
        self.log = QPlainTextEdit()
        self.tree = SimpleNamespace(build_archive_subtree=lambda *a: None)
        self.mode = "archive"
        self.archive_path = ""
        self.password = ""
        self.cache = {}

    def _cache(self, path):
        return self.cache.setdefault(
            path, {"entries": None, "loaded": False, "info_loaded": False}
        )

    def _cancel_long_operations(self):
        pass

    def _refresh_status_for_current_mode(self):
        pass

    def navigate_fs(self, path):
        pass

    def close(self):
        if self._notice is not None:
            self._notice.hide_notice()
        self._busy_timer.stop()
        super().close()

    _on_streaming_list_result = ArchiveLoaderMixin._on_streaming_list_result


def _result(tail: str) -> dict:
    return {
        "path": "C:/Backup/arc_reps_001.zpaq",
        "make_active": True,
        "inner": "",
        "file_stamp": None,
        "rc": 1,
        "cancelled": False,
        "entries": [],
        "report": None,
        "tail": tail,
    }


class TestPasswordDialogOnTop(unittest.TestCase):
    def setUp(self):
        self.loader = _Loader()
        self.addCleanup(self.loader.close)
        self.loader._start_busy("Чтение arc_reps_001.zpaq")
        _pump(NOTICE_DELAY_MS + 100)
        self.assertTrue(
            self.loader._notice.isVisible(), "окно операции должно быть видно"
        )

    def test_password_prompt_is_not_covered(self):
        seen = []

        class FakeInputDialog:
            @staticmethod
            def getText(parent, title, label, echo):
                seen.append(parent._notice.isVisible())
                seen.append(parent._notice.is_visible_notice())
                return "", False

        with patch("ui.archive_loader.QInputDialog", FakeInputDialog):
            self.loader._on_streaming_list_result(_result("PASSWORD REQUIRED"))

        self.assertEqual(
            seen[0], False,
            "диалог пароля перекрыт окошком «идёт операция» — пароль не ввести",
        )
        self.assertEqual(
            seen[1], True, "индикатор должен быть лишь временно спрятан"
        )
        self.assertEqual(self.loader._busy_depth, 0, "busy не снят после диалога")

    def test_error_box_is_not_covered(self):
        seen = []

        class FakeMessageBox:
            @staticmethod
            def critical(parent, title, text):
                seen.append(parent._notice.isVisible())

            @staticmethod
            def warning(parent, title, text):
                seen.append(parent._notice.isVisible())

        with patch("ui.archive_loader.QMessageBox", FakeMessageBox):
            self.loader._on_streaming_list_result(_result("archive is broken"))

        self.assertEqual(
            seen, [False], "сообщение об ошибке перекрыто окошком операции"
        )
        self.assertEqual(self.loader._busy_depth, 0)


if __name__ == "__main__":
    unittest.main()
