













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
    _stored_password = ArchiveLoaderMixin._stored_password


class TestStoredPasswordHydration(unittest.TestCase):
    def test_cache_takes_stored_password(self):
        host = _CacheHost()
        with patch.object(
            archive_loader, "get_password", return_value="stored"
        ):
            entry = host._cache("C:/Backup/arc_0001.zpaq")

        self.assertEqual(entry["password"], "stored")

    def test_cache_tries_multipart_mask(self):
        host = _CacheHost()

        def fake_get(path):
            return "mask-pw" if "?" in path else None

        with patch.object(
            archive_loader, "get_password", side_effect=fake_get
        ) as get:
            entry = host._cache("C:/Backup/arc_0001.zpaq")

        self.assertEqual(entry["password"], "mask-pw")
        self.assertGreaterEqual(get.call_count, 2)

    def test_cache_without_stored_password(self):
        host = _CacheHost()
        with patch.object(archive_loader, "get_password", return_value=None):
            entry = host._cache("C:/Backup/plain.zpaq")

        self.assertIsNone(entry["password"])


if __name__ == "__main__":
    unittest.main()
