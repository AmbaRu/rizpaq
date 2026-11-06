from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

_APP = QApplication.instance() or QApplication(sys.argv)

from ui import i18n

i18n.set_language("ru", notify=False)

from ui.i18n import tr
from ui.global_search_dialog import GlobalSearchDialog
from ui.menu_actions import MenuActionsMixin
from ui.version_menu import VersionMenuMixin

from core import archive_index as idx
from core import search as core_search
from core.models import ArchiveEntry


def _entry(
    path: str,
    size: int = 100,
    version=None,
    flag: str = "+",
    is_dir: bool = False,
    dt: str = "2026-10-09 12:00:00",
) -> ArchiveEntry:
    return ArchiveEntry(
        path=path,
        size=size,
        datetime=dt,
        version=version,
        flag=flag,
        is_dir=is_dir,
    )


class TestSearchAll(unittest.TestCase):


    def test_empty_query_returns_no_results(self):
        archives = [
            ("C:/arc1.zpaq", [_entry("d:/tax/docs.xlsx")]),
        ]
        self.assertEqual(core_search.search_all("", archives), [])
        self.assertEqual(core_search.search_all("   ", archives), [])

    def test_matches_across_archives(self):
        archives = [
            ("C:/arc1.zpaq", [_entry("d:/tax/docs.xlsx"), _entry("d:/other.bin")]),
            ("C:/arc2.zpaq", [_entry("d:/tax/extra.txt")]),
        ]
        res = core_search.search_all("tax", archives)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["archive"], "C:/arc1.zpaq")
        self.assertEqual(res[0]["path"], "d:/tax/docs.xlsx")
        self.assertEqual(res[0]["size"], 100)
        self.assertEqual(res[0]["version"], None)
        self.assertEqual(res[1]["archive"], "C:/arc2.zpaq")

    def test_no_match(self):
        archives = [("C:/arc1.zpaq", [_entry("d:/x.txt")])]
        self.assertEqual(core_search.search_all("zzz", archives), [])

    def test_glob_query(self):
        archives = [("C:/arc1.zpaq", [_entry("d:/tax/x.TXT")])]
        res = core_search.search_all("*.txt", archives)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["path"], "d:/tax/x.TXT")

    def test_none_entries_skipped(self):
        archives = [
            ("C:/arc1.zpaq", None),
            ("C:/arc2.zpaq", [_entry("d:/tax/x.txt")]),
        ]
        res = core_search.search_all("tax", archives)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["archive"], "C:/arc2.zpaq")


class TestListArchives(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_glob_idx_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.path = self._tmp / "archive_index.sqlite"
        idx._set_index_path_for_tests(self.path)
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)

    def test_empty_index_lists_nothing(self):
        self.assertEqual(idx.list_archives(), [])

    def test_stored_archives_listed(self):
        idx.store_entries("C:/arc1.zpaq", 111, 222, [_entry("d:/a.txt")])
        idx.store_entries("C:/arc2.zpaq", 111, 222, [_entry("d:/b.txt")])

        idx.store_entries("C:/backup_????.zpaq", 111, 222, [_entry("d:/c.txt")])
        got = idx.list_archives()
        paths = sorted(a["path"] for a in got)
        self.assertEqual(paths, ["C:/arc1.zpaq", "C:/arc2.zpaq"])
        self.assertEqual(got[0]["entries_count"], 1)


class _Host(QWidget, MenuActionsMixin):


    def __init__(self):
        QWidget.__init__(self)
        self.opened = []

    def _enter_archive(self, path: str) -> None:
        self.opened.append(path)


class GlobalSearchDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_glob_dlg_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.path = self._tmp / "archive_index.sqlite"
        idx._set_index_path_for_tests(self.path)
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)

        idx.store_entries("C:/arc1.zpaq", 111, 222, [_entry("d:/tax/docs.xlsx")])
        idx.store_entries("C:/arc2.zpaq", 111, 222, [_entry("d:/other/inn.txt")])

        self.dlg = GlobalSearchDialog()
        self.addCleanup(self.dlg.close)
        self.addCleanup(self.dlg._timer.stop)

    def tearDown(self):
        self.dlg.close()

    def _type(self, text: str) -> None:
        self.dlg.search_edit.setText(text)
        self.dlg._timer.stop()
        self.dlg._apply_search()

    def test_open_clears_results(self):
        self.dlg.open()
        self.assertEqual(self.dlg.results.rowCount(), 0)
        self.assertEqual(self.dlg.search_edit.text(), "")

    def test_query_populates_flat_results(self):
        self.dlg.open()
        self._type("tax")
        self.assertEqual(self.dlg.results.rowCount(), 1)
        self.assertEqual(self.dlg.results.item(0, 0).text(), "C:/arc1.zpaq")
        self.assertEqual(self.dlg.results.item(0, 1).text(), "d:/tax/docs.xlsx")

    def test_no_query_no_results(self):
        self.dlg.open()
        self._type("tax")
        self.assertEqual(self.dlg.results.rowCount(), 1)
        self._type("   ")
        self.assertEqual(self.dlg.results.rowCount(), 0)

    def test_no_match_shows_not_found(self):
        self.dlg.open()
        self._type("zzz")
        self.assertEqual(self.dlg.results.rowCount(), 0)
        self.assertIn("по запросу", self.dlg.count_label.text())

    def test_double_click_emits_archive_requested(self):
        self.dlg.open()
        self._type("tax")
        self.assertEqual(self.dlg.results.rowCount(), 1)
        self.dlg.results.selectRow(0)
        captured = mock.Mock()
        self.dlg.archive_requested.connect(captured)
        self.dlg._on_result_double_clicked(0, 0)
        captured.assert_called_once_with("C:/arc1.zpaq")

    def test_global_archive_requested_opens_archive(self):
        host = _Host()
        MenuActionsMixin._on_global_archive_requested(host, "C:/arc1.zpaq")
        self.assertEqual(host.opened, ["C:/arc1.zpaq"])


class GlobalSearchResultLimitTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_glob_limit_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        idx._set_index_path_for_tests(self._tmp / "archive_index.sqlite")
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)
        self.dlg = GlobalSearchDialog()
        self.addCleanup(self.dlg.close)
        self.addCleanup(self.dlg._timer.stop)

    def test_rows_capped_and_message_says_shown_of(self):
        from ui.global_search_dialog import _MAX_RESULT_ROWS

        entries = [_entry(f"d:/many/file{i:05d}.txt") for i in range(
            _MAX_RESULT_ROWS + 250
        )]
        idx.store_entries("C:/big.zpaq", 1, 2, entries)

        self.dlg.search_edit.setText("file")
        self.dlg._timer.stop()
        self.dlg._apply_search()

        self.assertEqual(self.dlg.results.rowCount(), _MAX_RESULT_ROWS)
        self.assertIn(str(_MAX_RESULT_ROWS), self.dlg.count_label.text())
        self.assertIn(str(len(entries)), self.dlg.count_label.text())

    def test_index_read_once_per_dialog(self):
        idx.store_entries("C:/arc1.zpaq", 1, 2, [_entry("d:/tax/a.txt")])

        with mock.patch.object(
            self.dlg, "_collect_archives", wraps=self.dlg._collect_archives
        ) as collect:
            for text in ("tax", "tax/a", "a.txt"):
                self.dlg.search_edit.setText(text)
                self.dlg._timer.stop()
                self.dlg._apply_search()
        self.assertEqual(collect.call_count, 1)


        self.dlg.reset_search()
        self.assertIsNone(self.dlg._archives)


_MENU_STUBS = (
    "_build_profile_menu",
    "_build_skin_menu",
    "_change_language",
    "_choose_7z_path",
    "_choose_zpaq_path",
    "_focus_search",
    "_on_about",
    "_on_archive_info",
    "_on_compare_versions",
    "_on_convert_current_to_zpaq",
    "_on_create_archive_current",
    "_on_edit_task",
    "_on_open_archive_dialog",
    "_on_open_association_dialog",
    "_on_open_manual",
    "_on_open_scheduler",
    "_on_refresh",
    "_on_run_task",
    "_on_salvage_archive",
    "_on_test_archive",
    "_on_toggle_latest",
    "_on_unpack_all",
    "_par2_menu_create",
    "_par2_menu_repair",
    "_par2_menu_verify",
    "_rebuild_unpack_menu",
    "_refresh_par2_menu",
)


class _MenuHost(QMainWindow, MenuActionsMixin, VersionMenuMixin):
    pass


for _name in _MENU_STUBS:
    setattr(_MenuHost, _name, lambda self, *a, **k: None)


class GlobalSearchMenuTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
        self.host = _MenuHost()
        self.addCleanup(self.host.deleteLater)

    def test_action_enabled_without_open_archive(self):
        self.host._create_actions()
        self.assertTrue(self.host.global_search_action.isEnabled())

    def test_action_stays_enabled_when_archive_dependent_actions_off(self):
        self.host._create_actions()

        self.host._set_archive_dependent_actions(False)
        self.assertTrue(self.host.global_search_action.isEnabled())

    def test_action_opens_dialog(self):
        self.host._create_actions()
        with mock.patch(
            "ui.global_search_dialog.GlobalSearchDialog"
        ) as dlg_cls:
            self.host.global_search_action.trigger()
        dlg_cls.return_value.reset_search.assert_called_once()
        dlg_cls.return_value.exec.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
