

































from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt              
from PySide6.QtWidgets import QApplication, QTreeWidgetItem              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language, tr              

set_language("ru", notify=False)

import ui.source_select_window as ssw              
from ui.source_select_window import _PATH_ROLE              


class _Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_ss_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _make_files(self, count: int, prefix: str = "file"):
        for i in range(count):
            (self.tmp / f"{prefix}_{i:03d}.txt").write_text("x", encoding="utf-8")

    def _make_dirs(self, count: int, prefix: str = "dir"):
        for i in range(count):
            (self.tmp / f"{prefix}_{i:03d}").mkdir()

    def _root_item(self) -> QTreeWidgetItem:
        item = QTreeWidgetItem(["root"])
        item.setData(0, _PATH_ROLE, str(self.tmp))
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Unchecked)
        return item

    def _window(self) -> ssw.SourceSelectWindow:
        w = ssw.SourceSelectWindow()
        self.addCleanup(w.deleteLater)
        return w


class TestNoTruncation(_Case):
    def test_small_folder_shows_all(self):
        self._make_files(5)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 100):
            w._load_children(item)
                                    
        self.assertEqual(item.childCount(), 5)

    def test_exactly_at_limit_no_note(self):
        self._make_files(10)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 10):
            w._load_children(item)
                                                           
        self.assertEqual(item.childCount(), 10)
        for i in range(item.childCount()):
            self.assertIsNotNone(item.child(i).data(0, _PATH_ROLE))


class TestTruncation(_Case):
    def test_caps_children_to_limit(self):
        self._make_files(15)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 10):
            w._load_children(item)
                               
        self.assertEqual(item.childCount(), 11)

    def test_note_is_not_an_entry(self):
        pass



        self._make_files(15)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 10):
            w._load_children(item)
        note = item.child(item.childCount() - 1)
        self.assertIsNone(note.data(0, _PATH_ROLE),
                          "у заглушки не должно быть _PATH_ROLE")
        self.assertEqual(note.flags(), Qt.NoItemFlags,
                         "заглушка не должна быть интерактивной")

    def test_note_text_names_hidden_count(self):
        pass






        self._make_files(15)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 10):
            w._load_children(item)
        note = item.child(item.childCount() - 1)
        text = note.text(0)
        self.assertTrue(text.strip(), "текст заглушки пуст")
        self.assertNotIn("table.truncated", text,
                         "в заглушке сырой ключ локали вместо перевода")
                                                                            
        self.assertIn("10", text, "в заглушке нет числа показанных")
        self.assertIn("15", text, "в заглушке нет числа скрытых")

    def test_dirs_come_before_files(self):
        pass
        self._make_dirs(3)
        self._make_files(15)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 8):
            w._load_children(item)
        texts = [item.child(i).text(0) for i in range(item.childCount())]
        dir_positions = [i for i, t in enumerate(texts) if t.startswith("📂")]
        file_positions = [i for i, t in enumerate(texts) if t.startswith("📄")]
        self.assertTrue(dir_positions, "подпапки не попали в дерево")
        if file_positions:
            self.assertLess(
                max(dir_positions), min(file_positions),
                "файл оказался раньше подпапки — подпапки в приоритете",
            )


class TestScandirCalledOnce(_Case):
    def test_no_list_materialization(self):
        pass












        self._make_files(5)
        item = self._root_item()
        w = self._window()
        real_scandir = os.scandir
        calls: list = []

        def counting(path):
            calls.append(path)
            return real_scandir(path)

        with mock.patch.object(ssw.os, "scandir", side_effect=counting), \
             mock.patch.object(ssw, "MAX_CHILDREN", 100):
            w._load_children(item)

        self.assertEqual(
            len(calls), 1,
            "scandir должен вызываться один раз: итерация напрямую, "
            "а не list() + повторный обход",
        )


class TestBlockChangedReset(_Case):
    def test_block_changed_false_after_normal_run(self):
        self._make_files(3)
        item = self._root_item()
        w = self._window()
        with mock.patch.object(ssw, "MAX_CHILDREN", 100):
            w._load_children(item)
        self.assertFalse(w._block_changed)

    def test_block_changed_false_after_oserror(self):
        pass




        item = self._root_item()

        def boom(path):
            raise OSError("нет доступа")

        w = self._window()
        with mock.patch.object(ssw.os, "scandir", side_effect=boom):
            w._load_children(item)

        self.assertFalse(
            w._block_changed,
            "_block_changed остался True после OSError — "
            "следующий _on_item_changed будет молча проигнорирован",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
