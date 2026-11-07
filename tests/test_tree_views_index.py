


























from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QTreeWidgetItem              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language              

set_language("ru", notify=False)

from ui.qt_compat import K_FS, K_FS_ARC, KIND_ROLE, TCOL, USER_ROLE              
from ui.tree_views import ArchiveTree              
from core.models import ArchiveEntry              


def _entry(path: str, is_dir: bool = False) -> ArchiveEntry:
    return ArchiveEntry(
        path=path, size=1, datetime="", version=None, flag="+", is_dir=is_dir,
    )


def _make_tree(self) -> ArchiveTree:
    pass
    tree = ArchiveTree()
    self.addCleanup(tree.deleteLater)
    return tree


def _put_arc_node(tree: ArchiveTree, arc_path: str = "D:/x.zpaq") -> QTreeWidgetItem:
    pass
    item = QTreeWidgetItem(["🗜 x.zpaq"])
    item.setData(TCOL, USER_ROLE, arc_path)
    item.setData(TCOL, KIND_ROLE, K_FS_ARC)
    tree.addTopLevelItem(item)
    tree._arc_items[arc_path] = item
    return item


class TestSubtreeIndex(unittest.TestCase):
    def test_build_indexes_every_folder(self):
        tree = _make_tree(self)
        _put_arc_node(tree)
        tree.build_archive_subtree("D:/x.zpaq", [
            _entry("a/b/c.txt"),
            _entry("a/d.txt"),
            _entry("only.txt"),
        ])
        idx = tree._arc_subtree_index.get("D:/x.zpaq")
        self.assertIsNotNone(idx, "индекс не создан")
        self.assertIn("a", idx)
        self.assertIn("a/b", idx)
                                                       
        self.assertNotIn("a/d.txt", idx)
        self.assertNotIn("only.txt", idx)

    def test_build_indexes_directory_entries(self):
        pass
        tree = _make_tree(self)
        _put_arc_node(tree)
        tree.build_archive_subtree("D:/x.zpaq", [
            _entry("emptydir", is_dir=True),
        ])
        idx = tree._arc_subtree_index["D:/x.zpaq"]
        self.assertIn("emptydir", idx)

    def test_find_under_uses_index(self):
        tree = _make_tree(self)
        arc = _put_arc_node(tree)
        tree.build_archive_subtree("D:/x.zpaq", [_entry("a/b/c.txt")])

        found_a = tree._arc_find_under(arc, "a")
        self.assertIsNotNone(found_a)
        self.assertEqual(found_a.data(TCOL, USER_ROLE), "a")

        found_b = tree._arc_find_under(arc, "a/b")
        self.assertIsNotNone(found_b)
        self.assertEqual(found_b.data(TCOL, USER_ROLE), "a/b")

    def test_find_under_missing_returns_none(self):
        tree = _make_tree(self)
        arc = _put_arc_node(tree)
        tree.build_archive_subtree("D:/x.zpaq", [_entry("a/b/c.txt")])
        self.assertIsNone(tree._arc_find_under(arc, "no_such_folder"))

    def test_find_under_without_index_returns_none(self):
        pass




        tree = _make_tree(self)
        arc = _put_arc_node(tree)
                                            
        self.assertIsNone(tree._arc_find_under(arc, "a"))

    def test_rebuild_replaces_index(self):
        pass
        tree = _make_tree(self)
        arc = _put_arc_node(tree)

        tree.build_archive_subtree("D:/x.zpaq", [_entry("old/a.txt")])
        self.assertIsNotNone(tree._arc_find_under(arc, "old"),
                             "первый индекс не построен")

        tree.build_archive_subtree("D:/x.zpaq", [_entry("new/b.txt")])
        self.assertIsNone(
            tree._arc_find_under(arc, "old"),
            "старый индекс не сброшен при пересборке",
        )
        self.assertIsNotNone(tree._arc_find_under(arc, "new"))

    def test_rebuild_after_arc_node_missing_clears_index(self):
        pass




        tree = _make_tree(self)
                                                              
        tree._arc_subtree_index["D:/ghost.zpaq"] = {"x": object()}

        tree.build_archive_subtree("D:/ghost.zpaq", [_entry("a/b.txt")])
        self.assertNotIn(
            "D:/ghost.zpaq", tree._arc_subtree_index,
            "индекс для отсутствующего узла архива должен быть сброшен",
        )


class TestIndexCleanupOnRebuild(unittest.TestCase):
    pass

    def test_build_fs_roots_clears_index(self):
        tree = _make_tree(self)
        tree._arc_subtree_index["D:/x.zpaq"] = {"a": object()}
                                                                      
        with mock.patch("ui.tree_views.windows_drives",
                        return_value=["C:\\", "D:\\"]):
            tree.build_fs_roots()
        self.assertEqual(tree._arc_subtree_index, {},
                         "build_fs_roots должен сбросить индекс: "
                         "self.clear() уничтожает узлы, а индекс — ссылки "
                         "на них")

    def test_ensure_loaded_clears_index_for_removed_arcs(self):
        pass



        tmp = Path(tempfile.mkdtemp(prefix="rizpaq_tv_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
                                                        
        (tmp / "x.zpaq").write_bytes(b"x")

        tree = _make_tree(self)
        fs_node = QTreeWidgetItem(["📂"])
        fs_node.setData(TCOL, USER_ROLE, str(tmp))
        fs_node.setData(TCOL, KIND_ROLE, K_FS)
        tree.addTopLevelItem(fs_node)

        tree._fill(fs_node)
        arc_path = str(tmp / "x.zpaq")
        self.assertIn(arc_path, tree._arc_items,
                      "тест-подготовка сломана: узел архива не появился")

                                         
        tree._arc_subtree_index[arc_path] = {"a": object()}

                                                     
        tree._ensure_loaded(fs_node)

        self.assertNotIn(
            arc_path, tree._arc_subtree_index,
            "_ensure_loaded снёс arc-узел, но индекс для него остался "
            "— это ссылки на уничтоженные C++-объекты",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
