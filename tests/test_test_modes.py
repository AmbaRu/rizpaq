
























from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMenu, QWidget              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from core.tasks import TEST_MODES              
from ui.i18n import set_language, tr              

set_language("ru", str(ROOT / "locales"))

from ui.qt_compat import KIND_ROLE, TCOL, USER_ROLE              
from ui.test_modes import (              
    combo_entries,
    has_par2_for,
    menu_entries,
    mode_label,
)


class _Item:
    pass

    def __init__(self, path, kind):
        self._path = path
        self._kind = kind

    def data(self, col, role):
        if col != TCOL:
            return None
        if role == USER_ROLE:
            return self._path
        if role == KIND_ROLE:
            return self._kind
        return None


class _MenuHost(QWidget):
    pass







    def __init__(self):
        QWidget.__init__(self)
        self.archive_path = None
        self.calls = []
        self.captured = None

                           
    def _enter_archive(self, path):
        self.calls.append(("open", path))

    def _on_create_archive_paths(self, sources):
        self.calls.append(("create", sources))

    def _on_test_archive(self, path, mode, *a, **k):
        self.calls.append(("test", path, mode))

    def _start_par2_repair(self, path):
        self.calls.append(("repair", path))

    def _rename_fs_path(self, path):
        self.calls.append(("rename", path))

    def _delete_fs_path(self, path):
        self.calls.append(("delete", path))

    def _on_archive_info(self):
        self.calls.append(("info",))

    def _exec_menu(self, menu, pos):
        self.captured = menu

                     
    def build(self, path, from_table=False):
        self.archive_path = path
        item = _Item(path, "fs_arc")
        if from_table:
            from ui.table_events import TableEventsMixin as M
        else:
            from ui.tree_events import TreeEventsMixin as M
        M._fs_archive_context_menu(self, item, None)
        return self.captured


class _FakeViewport:
    def mapToGlobal(self, pos):
        return pos


class _FakeTable:
    pass

    def __init__(self):
        self._viewport = _FakeViewport()

    def viewport(self):
        return self._viewport

    def rowAt(self, _y):
        return 0

    def selectRow(self, _row):
        pass


class _Pos:
    def __init__(self):
        self._x = 5
        self._y = 7

    def x(self):
        return self._x

    def y(self):
        return self._y


class _TableHost(_MenuHost):
    pass






    def __init__(self):
        QWidget.__init__(self)
        self.archive_path = None
        self.calls = []
        self.table = _FakeTable()
        self._payload = None

    def _row_payload(self):
        return self._payload

    def build(self, path, from_table=False):
        from ui.qt_compat import K_FS_ARC
        from ui.table_events import TableEventsMixin

        self.archive_path = path
        self._payload = (K_FS_ARC, path)
                                                                      
                                                                 
                                                                 
                                        
        TableEventsMixin._on_table_context_menu(self, _Pos())
        return self.captured


class TestModeListIsSingleSource(unittest.TestCase):
    pass






    def test_menu_modes_match_core(self):
        self.assertEqual([m for m, _ in menu_entries()], list(TEST_MODES))

    def test_combo_modes_match_core(self):
        self.assertEqual([m for m, _ in combo_entries()], list(TEST_MODES))

    def test_par2_is_present(self):
        pass
        self.assertIn("par2", [m for m, _ in menu_entries()])

    def test_verify_is_present(self):
        pass





        self.assertIn("verify", [m for m, _ in menu_entries()])

    def test_labels_are_not_empty(self):
        for mode, label in menu_entries():
            with self.subTest(mode=mode):
                self.assertTrue(label.strip())

    def test_menu_and_combo_labels_differ(self):
        pass






        menu = dict(menu_entries())
        combo = dict(combo_entries())
        self.assertNotEqual(menu["full"], combo["full"])

    def test_mode_label_falls_back(self):
        pass
        label = mode_label("что-то_неизвестное")
        self.assertEqual(label, tr("test.title"))

    def test_mode_label_known(self):
        self.assertEqual(mode_label("full"), tr("menu.test.full"))


class TestHasPar2For(unittest.TestCase):
    pass

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_haspar2_"))
        self.arch = self.dir / "backup.zpaq"
        self.arch.write_bytes(b"Z" * 1024)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.dir, ignore_errors=True)

    def test_false_without_set(self):
        self.assertFalse(has_par2_for(str(self.arch)))

    def test_true_with_set(self):
        (self.dir / "backup.zpaq.par2").write_bytes(b"P")
        self.assertTrue(has_par2_for(str(self.arch)))

    def test_false_for_empty_path(self):
        self.assertFalse(has_par2_for(""))

    def test_false_for_missing_archive(self):
        pass
        self.assertFalse(has_par2_for(str(self.dir / "нет.zpaq")))


class TestArchiveContextMenu(unittest.TestCase):
    pass

    def setUp(self):
        import shutil

        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_menu_test_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.arch = self.dir / "backup.zpaq"
        self.arch.write_bytes(b"Z" * 1024)
        self.host = _MenuHost()
        self.host.set = None

    def _menu(self, from_table=False):
        if from_table:
            host = _TableHost()
            return host, host.build(str(self.arch), from_table=True)
        return self.host, self.host.build(str(self.arch))

    def _test_menu(self, menu):
        for act in menu.actions():
            if act.menu() is not None and act.text() == tr("menu.test"):
                return act.menu()
        return None

    def _restore(self, menu):
        return [a for a in menu.actions()
                if a.text() == tr("par2.repair")]

                                                                    
    def test_tree_has_five_modes(self):
        _host, menu = self._menu()
        sub = self._test_menu(menu)
        self.assertIsNotNone(sub, "подменю «Проверка» не найдено")
        self.assertEqual([a.data() for a in sub.actions()],
                         list(TEST_MODES))

    def test_table_has_five_modes(self):
        _host, menu = self._menu(from_table=True)
        sub = self._test_menu(menu)
        self.assertIsNotNone(sub, "подменю «Проверка» не найдено")
        self.assertEqual([a.data() for a in sub.actions()],
                         list(TEST_MODES))

    def test_mode_triggers_host_with_mode(self):
        _host, menu = self._menu()
        sub = self._test_menu(menu)
        target = next(a for a in sub.actions() if a.data() == "par2")
        target.trigger()
        self.assertIn(("test", str(self.arch), "par2"), self.host.calls)

    def test_each_mode_passes_own_code(self):
        pass






        _host, menu = self._menu()
        sub = self._test_menu(menu)
        for act in sub.actions():
            with self.subTest(mode=act.data()):
                self.host.calls.clear()
                act.trigger()
                self.assertEqual(self.host.calls[-1][2], act.data())

                                                                            
    def test_restore_hidden_without_set(self):
        _host, menu = self._menu()
        self.assertEqual(self._restore(menu), [])

    def test_restore_shown_with_set(self):
        (self.dir / "backup.zpaq.par2").write_bytes(b"P")
        _host, menu = self._menu()
        self.assertEqual(len(self._restore(menu)), 1)

    def test_table_restore_shown_with_set(self):
        pass
        (self.dir / "backup.zpaq.par2").write_bytes(b"P")
        host = _TableHost()
        menu = host.build(str(self.arch), from_table=True)
        self.assertEqual(len(self._restore(menu)), 1)

    def test_restore_triggers_host_with_path(self):
        (self.dir / "backup.zpaq.par2").write_bytes(b"P")
        _host, menu = self._menu()
        self._restore(menu)[0].trigger()
        self.assertIn(("repair", str(self.arch)), self.host.calls)


class TestCheckDialogUsesSharedList(unittest.TestCase):
    pass

    def test_combo_matches_list(self):
        from ui.archive_check_dialog import ArchiveCheckDialog

        dlg = ArchiveCheckDialog({"title": "W", "sources": ["D:/a"],
                                  "dest": "D:/a.zpaq", "jobs": []})
        self.addCleanup(dlg.deleteLater)
        combo = dlg._mode_combo
        codes = [combo.itemData(i) for i in range(combo.count())]
        self.assertEqual(codes, list(TEST_MODES))


class TestNoHardcodedModeLists(unittest.TestCase):
    pass








    FILES = (
        "ui/tree_events.py",
        "ui/table_events.py",
        "ui/menu_actions.py",
    )

    def test_no_mode_literals(self):
        for rel in self.FILES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(file=rel):
                for mode in TEST_MODES:
                    needle = f'"{mode}"'
                    self.assertNotIn(
                        needle, text,
                        f"{rel} содержит свой список режимов ({needle}). "
                        f"Режимы берутся из ui.test_modes.",
                    )

    def test_archive_actions_has_no_labels_dict(self):
        pass




        text = (ROOT / "ui" / "archive_actions.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("mode_labels = {", text)


if __name__ == "__main__":
    unittest.main()
