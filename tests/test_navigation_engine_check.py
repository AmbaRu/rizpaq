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


from ui.i18n import set_language

set_language("ru", notify=False)

from ui.navigation import NavigationMixin


class _Host(NavigationMixin):

    def __init__(self, zpaq: bool = True, seven_zip: bool = True):
        self.zpaq_available = zpaq
        self.seven_zip_available = seven_zip
        self.archive_path = None
        self.archive_inner = ""
        self.mode = "fs"
        self._activated = []
        self._loaded = []


    def _activate_archive(self, key):
        self._activated.append(key)

    def _cache(self, key):
        return {"loaded": False, "info_loaded": False, "entries": []}

    def _load_archive_list(self, path, make_active=False, inner=""):
        self._loaded.append((path, make_active, inner))

    def _load_info(self, path):
        pass

    def navigate_archive(self, inner, from_tree=False):
        pass

    def statusBar(self):
        return self


class TestCheckArchiveEngine(unittest.TestCase):


    def test_zip_requires_7z(self):
        h = _Host(seven_zip=False)
        with mock.patch.object(QMessageBox, "warning") as warn:
            self.assertFalse(h._check_archive_engine("D:/x.zip"))
        warn.assert_called_once()

    def test_zip_passes_with_7z(self):
        h = _Host(seven_zip=True)
        with mock.patch.object(QMessageBox, "warning") as warn:
            self.assertTrue(h._check_archive_engine("D:/x.zip"))
        warn.assert_not_called()

    def test_7z_and_rar_require_7z(self):
        for ext in (".7z", ".rar"):
            with self.subTest(ext=ext):
                h = _Host(seven_zip=False)
                with mock.patch.object(QMessageBox, "warning") as warn:
                    self.assertFalse(h._check_archive_engine(f"D:/x{ext}"))
                warn.assert_called_once()

    def test_zpaq_requires_zpaqfranz(self):
        h = _Host(zpaq=False)
        with mock.patch.object(QMessageBox, "warning") as warn:
            self.assertFalse(h._check_archive_engine("D:/x.zpaq"))
        warn.assert_called_once()

    def test_zpaq_passes_with_zpaqfranz(self):
        h = _Host(zpaq=True)
        with mock.patch.object(QMessageBox, "warning") as warn:
            self.assertTrue(h._check_archive_engine("D:/x.zpaq"))
        warn.assert_not_called()

    def test_unknown_extension_passes(self):
        h = _Host(zpaq=False, seven_zip=False)
        with mock.patch.object(QMessageBox, "warning") as warn:
            self.assertTrue(h._check_archive_engine("D:/x.tar.gz"))
        warn.assert_not_called()

    def test_case_insensitive_extension(self):

        h = _Host(seven_zip=False)
        with mock.patch.object(QMessageBox, "warning"):
            self.assertFalse(h._check_archive_engine("D:/x.ZIP"))

        h = _Host(zpaq=False)
        with mock.patch.object(QMessageBox, "warning"):
            self.assertFalse(h._check_archive_engine("D:/x.ZPAQ"))


class TestTreeClickStopsOnMissingEngine(unittest.TestCase):


    def test_zip_click_without_7z_does_not_load(self):
        h = _Host(seven_zip=False)
        with mock.patch.object(QMessageBox, "warning") as warn:
            h._on_tree_arc_selected("D:/x.zip", "")
        self.assertEqual(h._activated, [], "_activate_archive вызвана без 7z")
        self.assertEqual(h._loaded, [], "_load_archive_list вызвана без 7z")
        warn.assert_called_once()

    def test_zip_click_with_7z_loads(self):
        h = _Host(seven_zip=True)
        with mock.patch.object(QMessageBox, "warning") as warn:
            h._on_tree_arc_selected("D:/x.zip", "")
        self.assertEqual(h._activated, ["D:/x.zip"])
        self.assertEqual(h._loaded, [("D:/x.zip", True, "")])
        warn.assert_not_called()

    def test_zpaq_click_without_zpaqfranz_does_not_load(self):
        h = _Host(zpaq=False)
        with mock.patch.object(QMessageBox, "warning"):
            h._on_tree_arc_selected("D:/x.zpaq", "")
        self.assertEqual(h._activated, [])
        self.assertEqual(h._loaded, [])

    def test_empty_path_does_nothing(self):
        h = _Host(seven_zip=False)
        with mock.patch.object(QMessageBox, "warning") as warn:
            h._on_tree_arc_selected("", "")
        self.assertEqual(h._activated, [])
        self.assertEqual(h._loaded, [])
        warn.assert_not_called()


class TestTreeExpandStopsOnMissingEngine(unittest.TestCase):


    def test_zip_expand_without_7z_does_not_load(self):
        h = _Host(seven_zip=False)
        with mock.patch.object(QMessageBox, "warning") as warn:
            h._on_tree_arc_open_requested("D:/x.zip")
        self.assertEqual(h._loaded, [], "_load_archive_list вызвана без 7z")
        warn.assert_called_once()

    def test_zip_expand_with_7z_loads(self):
        h = _Host(seven_zip=True)
        with mock.patch.object(QMessageBox, "warning") as warn:
            h._on_tree_arc_open_requested("D:/x.zip")
        self.assertEqual(h._loaded, [("D:/x.zip", False, "")])
        warn.assert_not_called()

    def test_zpaq_expand_without_zpaqfranz_does_not_load(self):
        h = _Host(zpaq=False)
        with mock.patch.object(QMessageBox, "warning"):
            h._on_tree_arc_open_requested("D:/x.zpaq")
        self.assertEqual(h._loaded, [])


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
