













from __future__ import annotations

import sys
import tempfile
import time
import unittest
from contextlib import nullcontext
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

from ui import archive_loader, extraction, i18n              
from ui.app_services import AppServicesMixin              
from ui.archive_loader import ArchiveLoaderMixin              
from ui.extraction import ExtractionMixin              
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


class _ExtractHost(ExtractionMixin):
    pass

    def __init__(self, archive_path, password=None):
        self.archive_path = str(archive_path)
        self.password = password
        self._arc_cache = {}
        self.stored = []

    def _cache(self, path):
        return self._arc_cache.setdefault(path, {"password": None})

    def _modal_dialog(self):
        return nullcontext()


class TestExtractionPasswordPrompt(unittest.TestCase):
    def _host(self, data=b"", password=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "arc.zpaq"
        if data:
            path.write_bytes(data)
        return _ExtractHost(path, password)

    def test_plain_archive_does_not_ask(self):
        host = self._host(b"7kSt" + b"\0" * 32)
        with patch.object(
            host, "_ask_archive_password", return_value=True
        ) as ask:
            self.assertTrue(host._ensure_extract_password())
        ask.assert_not_called()

    def test_known_password_does_not_ask(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32, password="pw")
        with patch.object(
            host, "_ask_archive_password", return_value=True
        ) as ask:
            self.assertTrue(host._ensure_extract_password())
        ask.assert_not_called()

    def test_encrypted_archive_asks_and_stores(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32)

        with patch.object(
            extraction.QInputDialog, "getText", return_value=("pw", True)
        ), patch.object(extraction, "set_password") as store:
            self.assertTrue(host._ensure_extract_password())

        self.assertEqual(host.password, "pw")
        self.assertEqual(host._cache(host.archive_path)["password"], "pw")
        store.assert_called_once_with(host.archive_path, "pw")

    def test_cancelled_prompt_aborts_extraction(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32)

        with patch.object(
            extraction.QInputDialog, "getText", return_value=("", False)
        ), patch.object(extraction, "set_password") as store:
            self.assertFalse(host._ensure_extract_password())

        self.assertIsNone(host.password)
        store.assert_not_called()

    def test_password_failure_retries(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32)
        called = []

        with patch.object(
            host, "_ask_archive_password", return_value=True
        ) as ask:
            handled = host._maybe_retry_extract_with_password(
                {
                    "kind": "extract_file",
                    "success": False,
                    "output": "42267! Password required, use -key",
                },
                lambda: called.append("retry"),
            )

        self.assertTrue(handled)
        self.assertEqual(called, ["retry"])
        ask.assert_called_once_with()

    def test_success_does_not_retry(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32)
        called = []

        with patch.object(
            host, "_ask_archive_password", return_value=True
        ) as ask:
            handled = host._maybe_retry_extract_with_password(
                {
                    "kind": "extract_file",
                    "success": True,
                    "output": "Password required",
                },
                lambda: called.append("retry"),
            )

        self.assertFalse(handled)
        self.assertEqual(called, [])
        ask.assert_not_called()

    def test_ordinary_key_word_does_not_retry(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32)
        called = []

        with patch.object(
            host, "_ask_archive_password", return_value=True
        ) as ask:
            handled = host._maybe_retry_extract_with_password(
                {
                    "kind": "extract_file",
                    "success": False,
                    "output": "monkey.txt: file not found",
                },
                lambda: called.append("retry"),
            )

        self.assertFalse(handled)
        self.assertEqual(called, [])
        ask.assert_not_called()

    def test_password_retry_returns_false_without_retry_callable(self):
        host = self._host(b"\x01\x02\x03\x04" + b"\0" * 32)

        with patch.object(
            host, "_ask_archive_password", return_value=True
        ) as ask:
            handled = host._maybe_retry_extract_with_password(
                {
                    "kind": "extract_folder_batch",
                    "ok": False,
                    "log": "zpaqfranz error: password incorrect",
                },
                None,
            )

        self.assertFalse(handled)
        ask.assert_not_called()

    def test_multipart_mask_checks_first_volume(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        (folder / "arc_0001.zpaq").write_bytes(
            b"\x01\x02\x03\x04" + b"\0" * 32
        )
        host = _ExtractHost(folder / "arc_????.zpaq")

        self.assertTrue(host._archive_is_encrypted())


class _CacheHost:
    def __init__(self):
        self._arc_cache = {}

    _cache = ArchiveLoaderMixin._cache


class TestNoStoredPasswordHydration(unittest.TestCase):
    pass

    def test_cache_starts_without_password(self):
        host = _CacheHost()
        entry = host._cache("C:/Backup/arc_0001.zpaq")

        self.assertIsNone(entry["password"])

    def test_reopening_cache_does_not_add_password(self):
        host = _CacheHost()
        first = host._cache("C:/Backup/arc_0001.zpaq")
        first["password"] = "session"
        second = host._cache("C:/Backup/arc_0001.zpaq")

        self.assertIs(second, first)
        self.assertEqual(second["password"], "session")


class _InfoHost:
    pass

    def __init__(self):
        self.archive_path = "C:/Backup/arc.zpaq"
        self.password = None
        self._arc_cache = {}
        self.info_calls = []
        self.retries = []
        self.stopped = 0

    _cache = ArchiveLoaderMixin._cache
    _on_worker_result = ArchiveLoaderMixin._on_worker_result
    _password_attempt = ArchiveLoaderMixin._password_attempt
    _reset_password_attempts = ArchiveLoaderMixin._reset_password_attempts

    def log_output(self, text):
        pass

    def _modal_dialog(self):
        return nullcontext()

    def _handle_info_result(self, path, rc, output):
        self.info_calls.append((path, rc, output))

    def _stop_busy(self):
        self.stopped += 1

    def _open_pending_dialogs(self, path):
        pass

    def _load_info(self, path, quiet=False):
        self.retries.append((path, quiet))


class TestInfoPasswordPrompt(unittest.TestCase):
    def _result(self):
        return {
            "kind": "info",
            "rc": 2,
            "output": "42267! Password required, use -key",
            "context": {"path": "C:/Backup/arc.zpaq", "quiet": True},
        }

    def test_password_error_asks_and_retries(self):
        host = _InfoHost()
        with patch.object(
            archive_loader.QInputDialog, "getText", return_value=("pw", True)
        ) as ask, patch.object(archive_loader, "set_password") as store:
            host._on_worker_result(self._result())

        ask.assert_called_once()
        store.assert_called_once_with("C:/Backup/arc.zpaq", "pw")
        self.assertEqual(host.password, "pw")
        self.assertEqual(host._cache(host.archive_path)["password"], "pw")
        self.assertEqual(host.retries, [("C:/Backup/arc.zpaq", True)])
        self.assertEqual(host.info_calls, [])
        self.assertEqual(host.stopped, 1)

    def test_cancelled_prompt_does_not_retry(self):
        host = _InfoHost()
        with patch.object(
            archive_loader.QInputDialog, "getText", return_value=("", False)
        ), patch.object(archive_loader, "set_password") as store:
            host._on_worker_result(self._result())

        self.assertEqual(host.retries, [])
        self.assertEqual(host.info_calls, [])
        self.assertEqual(host.stopped, 1)
        store.assert_not_called()

    def test_ordinary_failure_does_not_ask(self):
        host = _InfoHost()
        result = self._result()
        result["output"] = "some unrelated error"
        with patch.object(
            archive_loader.QInputDialog, "getText", return_value=("pw", True)
        ) as ask:
            host._on_worker_result(result)

        ask.assert_not_called()
        self.assertEqual(len(host.info_calls), 1)
        self.assertEqual(host.retries, [])

    def test_after_three_failures_shows_error_instead_of_looping(self):
        host = _InfoHost()
        with patch.object(
            archive_loader.QInputDialog, "getText", return_value=("pw", True)
        ) as ask, patch.object(archive_loader, "set_password"), patch.object(
            archive_loader.QMessageBox, "critical"
        ) as critical:
            for _ in range(3):
                host._on_worker_result(self._result())

            ask.reset_mock()
            host._on_worker_result(self._result())

        ask.assert_not_called()
        critical.assert_called_once()
        self.assertEqual(len(host.retries), 3)

    def test_success_resets_attempts(self):
        host = _InfoHost()
        with patch.object(
            archive_loader.QInputDialog, "getText", return_value=("pw", True)
        ), patch.object(archive_loader, "set_password"):
            host._on_worker_result(self._result())

        result = self._result()
        result["rc"] = 0
        result["output"] = "2 versions, 2 files"
        host._on_worker_result(result)

        self.assertIsNone(
            host._password_attempts.get("C:/Backup/arc.zpaq")
        )


if __name__ == "__main__":
    unittest.main()
