                       





from __future__ import annotations

import os
import sqlite3
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QDialog, QWidget              

_APP = QApplication.instance() or QApplication(sys.argv)

from ui import i18n              

i18n.set_language("ru", notify=False)

from core import archive_catalog              
from core import archive_index as idx              
from core import config as config_mod              
from core.models import ArchiveEntry              
from workers.catalog_worker import CatalogWorker              


def _entry(path: str) -> ArchiveEntry:
    return ArchiveEntry(
        path=path,
        size=10,
        datetime="2026-10-31 12:00:00",
        version=None,
        flag="+",
        is_dir=False,
    )


def _touch(path: Path, data: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


                                                                          


class ScanRootsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_catalog_scan_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def test_finds_nested_archives_and_ignores_other_files(self):
        _touch(self._tmp / "a.zpaq")
        _touch(self._tmp / "sub" / "b.ZPAQ")
        _touch(self._tmp / "sub" / "note.txt")
        _touch(self._tmp / "sub" / "c.zip")

        got = archive_catalog.scan_roots([str(self._tmp)])
        names = sorted(Path(r["path"]).name for r in got)
        self.assertEqual(names, ["a.zpaq", "b.ZPAQ"])

    def test_skips_recycle_bin_and_system_volume(self):
        _touch(self._tmp / "$Recycle.Bin" / "old.zpaq")
        _touch(self._tmp / "System Volume Information" / "sys.zpaq")
        _touch(self._tmp / "keep.zpaq")

        got = archive_catalog.scan_roots([str(self._tmp)])
        self.assertEqual([Path(r["path"]).name for r in got], ["keep.zpaq"])

    def test_multipart_parts_grouped_into_one_mask(self):
        _touch(self._tmp / "backup_0001.zpaq", b"aa")
        _touch(self._tmp / "backup_0002.zpaq", b"bbb")

        got = archive_catalog.scan_roots([str(self._tmp)])
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0]["path"].endswith("backup_????.zpaq"))
        self.assertEqual(got[0]["parts"], 2)
        self.assertEqual(got[0]["size"], 5)

    def test_root_can_be_archive_file(self):
        arc = self._tmp / "single.zpaq"
        _touch(arc)
        got = archive_catalog.scan_roots([str(arc)])
        self.assertEqual([r["path"] for r in got], [str(arc)])

    def test_missing_root_reported_without_raising(self):
        errors = []
        got = archive_catalog.scan_roots(
            [str(self._tmp / "nope")],
            on_error=lambda path, exc: errors.append((path, exc)),
        )
        self.assertEqual(got, [])
        self.assertEqual(len(errors), 1)

    def test_stop_request_ends_scan(self):
        _touch(self._tmp / "a.zpaq")
        calls = {"n": 0}

        def stop():
            calls["n"] += 1
            return True

        got = archive_catalog.scan_roots([str(self._tmp)], should_stop=stop)
        self.assertEqual(got, [])
        self.assertGreaterEqual(calls["n"], 1)

    def test_on_found_called_for_each_archive(self):
        _touch(self._tmp / "a.zpaq")
        _touch(self._tmp / "b.zpaq")
        seen = []
        archive_catalog.scan_roots(
            [str(self._tmp)], on_found=seen.append)
        self.assertEqual(len(seen), 2)


                                                                           


class CatalogSqlTests(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_catalog_sql_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.path = self._tmp / "archive_index.sqlite"
        idx._set_index_path_for_tests(self.path)
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)

    def test_empty_catalog(self):
        self.assertEqual(idx.catalog_list(), [])

    def test_upsert_and_indexed_flag(self):
        idx.catalog_upsert("C:/a.zpaq", 10, 20)
        row = idx.catalog_list()[0]
        self.assertFalse(row["indexed"])
        self.assertFalse(row["missing"])

        idx.store_entries("C:/a.zpaq", 20, 10, [_entry("d:/x.txt")])
        row = idx.catalog_list()[0]
        self.assertTrue(row["indexed"])
        self.assertEqual(row["entries_count"], 1)

    def test_stale_listing_is_not_indexed(self):
        idx.store_entries("C:/a.zpaq", 999, 10, [_entry("d:/x.txt")])
        idx.catalog_upsert("C:/a.zpaq", 10, 20)
        self.assertFalse(idx.catalog_list()[0]["indexed"])

    def test_mark_scanned_flags_only_missing_inside_roots(self):
        idx.catalog_upsert("C:/root/old.zpaq", 1, 2)
        idx.catalog_upsert("C:/root/new.zpaq", 1, 2)
        idx.catalog_upsert("C:/other/keep.zpaq", 1, 2)

        missing = idx.catalog_mark_scanned(
            ["C:/root"], ["C:/root/new.zpaq"])
        self.assertEqual(missing, 1)

        by_path = {r["path"]: r for r in idx.catalog_list()}
        self.assertTrue(by_path["C:/root/old.zpaq"]["missing"])
        self.assertFalse(by_path["C:/root/new.zpaq"]["missing"])
        self.assertFalse(by_path["C:/other/keep.zpaq"]["missing"])

    def test_upsert_clears_missing(self):
        idx.catalog_upsert("C:/root/a.zpaq", 1, 2)
        idx.catalog_mark_scanned(["C:/root"], [])
        self.assertTrue(idx.catalog_list()[0]["missing"])
        idx.catalog_upsert("C:/root/a.zpaq", 1, 2)
        self.assertFalse(idx.catalog_list()[0]["missing"])

    def test_forget_removes_only_catalog_row(self):
        idx.store_entries("C:/a.zpaq", 20, 10, [_entry("d:/x.txt")])
        idx.catalog_upsert("C:/a.zpaq", 10, 20)
        idx.catalog_forget("C:/a.zpaq")
        self.assertEqual(idx.catalog_list(), [])
                                                              
        self.assertEqual(idx.list_archives()[0]["path"], "C:/a.zpaq")

    def test_catalog_survives_schema_migration(self):
        idx.catalog_upsert("C:/a.zpaq", 1, 2)
        idx.store_entries("C:/a.zpaq", 2, 1, [_entry("d:/x.txt")])
        idx.close()

                                                                     
        conn = sqlite3.connect(str(self.path))
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()

        rows = idx.catalog_list()
        self.assertEqual([r["path"] for r in rows], ["C:/a.zpaq"])
                                                  
        self.assertEqual(idx.list_archives(), [])


                                                                          


class CatalogConfigTests(unittest.TestCase):
    def test_defaults(self):
        s = config_mod.Settings()
        self.assertIsNone(s.catalog_roots)
        self.assertTrue(s.catalog_index_on_scan)

    def test_from_dict_coerces(self):
        s = config_mod._from_dict({
            "catalog_roots": ["C:/a", "  ", 5, "D:/b"],
            "catalog_index_on_scan": False,
        })
        self.assertEqual(s.catalog_roots, ["C:/a", "D:/b"])
        self.assertFalse(s.catalog_index_on_scan)

    def test_empty_list_is_preserved(self):
        s = config_mod._from_dict({"catalog_roots": []})
        self.assertEqual(s.catalog_roots, [])

    def test_garbage_gives_none(self):
        s = config_mod._from_dict({"catalog_roots": "C:/a"})
        self.assertIsNone(s.catalog_roots)


                                                                          


class CatalogWorkerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_catalog_worker_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        idx._set_index_path_for_tests(self._tmp / "archive_index.sqlite")
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)
        self.roots = self._tmp / "data"
        _touch(self.roots / "a.zpaq")
        _touch(self.roots / "sub" / "b.zpaq")

    def test_scan_without_indexing_writes_catalog(self):
        w = CatalogWorker([str(self.roots)], zpaq_bin="", index_on_scan=False)
        results = []
        w.done.connect(results.append)
        w.run()

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["ok"])
        paths = sorted(r["path"] for r in idx.catalog_list())
        self.assertEqual(len(paths), 2)

    def test_cancelled_before_scan_emits_done(self):
        w = CatalogWorker([str(self.roots)], zpaq_bin="", index_on_scan=False)
        w.cancel_request()
        results = []
        w.done.connect(results.append)
        w.run()
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["cancelled"])


                                                                          


class CatalogDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_catalog_dlg_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        idx._set_index_path_for_tests(self._tmp / "archive_index.sqlite")
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)

        from ui.archive_catalog_dialog import ArchiveCatalogDialog

        self.ArchiveCatalogDialog = ArchiveCatalogDialog

        patcher = mock.patch.object(config_mod, "update")
        self.config_update = patcher.start()
        self.addCleanup(patcher.stop)

        idx.catalog_upsert("C:/root/a.zpaq", 2048, 1_700_000_000_000_000_000)
        idx.store_entries(
            "C:/root/a.zpaq", 1_700_000_000_000_000_000, 2048,
            [_entry("d:/x.txt")])

        self.dlg = ArchiveCatalogDialog(
            roots=["C:/root"], index_on_scan=True, zpaq_bin="")
        self.addCleanup(self.dlg.close)

    def test_table_shows_catalog(self):
        self.assertEqual(self.dlg.table.rowCount(), 1)
        self.assertEqual(
            self.dlg.table.item(0, 0).text(), "C:/root/a.zpaq")
        self.assertEqual(self.dlg.table.item(0, 4).text(), "да")
        self.assertEqual(self.dlg.table.item(0, 3).text(), "1")

    def test_open_selected_archive_accepts(self):
        self.dlg.table.selectRow(0)
        self.dlg._on_open()
        self.assertEqual(self.dlg.chosen_path(), "C:/root/a.zpaq")
        self.assertEqual(self.dlg.result(), QDialog.Accepted)

    def test_double_click_opens(self):
        self.dlg.table.selectRow(0)
        self.dlg._on_double_clicked(0, 0)
        self.assertEqual(self.dlg.chosen_path(), "C:/root/a.zpaq")

    def test_missing_file_is_not_opened(self):
        idx.catalog_mark_scanned(["C:/root"], [])
        self.dlg._reload()
        self.dlg.table.selectRow(0)
        with mock.patch(
            "ui.archive_catalog_dialog.QMessageBox.warning"
        ) as warning:
            self.dlg._on_open()
        warning.assert_called_once()
        self.assertEqual(self.dlg.chosen_path(), "")

    def test_forget_selected_removes_row(self):
        self.dlg.table.selectRow(0)
        self.dlg._on_forget()
        self.assertEqual(self.dlg.table.rowCount(), 0)
        self.assertEqual(idx.catalog_list(), [])

    def test_no_roots_warns_instead_of_scanning(self):
        dlg = self.ArchiveCatalogDialog(roots=[], zpaq_bin="")
        self.addCleanup(dlg.close)
        with mock.patch(
            "ui.archive_catalog_dialog.QMessageBox.information"
        ) as info:
            dlg._on_scan()
        info.assert_called_once()
        self.assertIsNone(dlg._worker)

    def test_add_and_remove_roots_persist(self):
        self.dlg._on_add_roots = lambda: None
        self.dlg._roots = self.dlg._dedup_roots(
            self.dlg._roots + ["D:/backups"])
        self.dlg._fill_roots()
        self.dlg._persist()
        self.config_update.assert_called_once_with(
            catalog_roots=["C:/root", "D:/backups"],
            catalog_index_on_scan=True,
        )

    def test_index_toggle_persists(self):
        self.config_update.reset_mock()
        self.dlg.index_check.setChecked(False)
        self.config_update.assert_called_once_with(
            catalog_roots=["C:/root"],
            catalog_index_on_scan=False,
        )


                                                                          


class CatalogMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("ru", notify=False)

    def setUp(self):
        from tests.test_global_search import _MenuHost

        self.host = _MenuHost()
        self.addCleanup(self.host.deleteLater)

    def test_action_exists_and_enabled_without_archive(self):
        self.host._create_actions()
        self.assertTrue(self.host.all_archives_action.isEnabled())

    def test_handler_opens_dialog_and_archive(self):
        host = QWidget()

        class _Cfg:
            catalog_roots = ["C:/root"]
            catalog_index_on_scan = True

        host._cfg = _Cfg()
        host.zpaq_bin = "zpaqfranz"
        host.opened = []
        host._enter_archive = lambda path: host.opened.append(path)

        dlg = mock.Mock()
        dlg.exec.return_value = QDialog.Accepted
        dlg.chosen_path.return_value = "C:/root/a.zpaq"

        from ui import menu_actions

        with mock.patch(
            "ui.archive_catalog_dialog.ArchiveCatalogDialog",
            return_value=dlg,
        ):
            menu_actions.MenuActionsMixin._on_show_all_archives(host)

        self.assertEqual(host.opened, ["C:/root/a.zpaq"])
        dlg.exec.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
