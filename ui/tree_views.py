from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.paths import same_name, windows_drives
from ui.i18n import tr
from ui.qt_compat import (
    ARC_OWNER_ROLE,
    K_ARC,
    K_FS,
    K_FS_ARC,
    K_FS_UNI_ARC,
    K_PLACE,
    KIND_ROLE,
    PLACEHOLDER,
    TCOL,
    USER_ROLE,
)


UNI_EXTS = (".zip", ".7z", ".rar")


class ArchiveTree(QTreeWidget):
    fs_selected = Signal(str)
    arc_selected = Signal(str, str)
    arc_open_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel(tr("tree.header"))
        self.setAlternatingRowColors(True)


        self._arc_items: dict = {}


        self._arc_subtree_index: dict = {}
        self._block_depth = 0

        self.itemExpanded.connect(self._on_expanded)
        self.currentItemChanged.connect(self._on_current)
        self.itemClicked.connect(self._on_clicked)


    @contextmanager
    def _blocked(self):
        self._block_depth += 1
        if self._block_depth == 1:
            self.blockSignals(True)
        try:
            yield
        finally:
            self._block_depth -= 1
            if self._block_depth == 0:
                self.blockSignals(False)


    def build_fs_roots(self) -> None:
        with self._blocked():
            self.clear()
            self._arc_items.clear()


            self._arc_subtree_index.clear()
            if os.name == "nt":
                for root in windows_drives():
                    letter = root[0].upper()
                    node = QTreeWidgetItem([tr("tree.drive", letter=letter)])
                    node.setData(TCOL, USER_ROLE, root)
                    node.setData(TCOL, KIND_ROLE, K_FS)
                    self.addTopLevelItem(node)
                    self._add_placeholder(node)
            else:
                node = QTreeWidgetItem(["/"])
                node.setData(TCOL, USER_ROLE, "/")
                node.setData(TCOL, KIND_ROLE, K_FS)
                self.addTopLevelItem(node)
                self._add_placeholder(node)

    def _add_placeholder(self, node: QTreeWidgetItem) -> None:
        ph = QTreeWidgetItem(["⏳"])
        ph.setData(TCOL, USER_ROLE, PLACEHOLDER)
        ph.setData(TCOL, KIND_ROLE, K_PLACE)
        node.addChild(ph)

    def _has_expandable(self, path: str) -> bool:

        try:
            with os.scandir(path) as it:
                for e in it:
                    try:
                        if e.is_dir() and not e.name.startswith("."):
                            return True
                        name_low = e.name.lower()
                        if name_low.endswith(".zpaq") or name_low.endswith(UNI_EXTS):
                            return True
                    except OSError:
                        continue
        except OSError:
            pass
        return False

    def _fill(self, node: QTreeWidgetItem) -> None:

        path = node.data(TCOL, USER_ROLE)
        dirs, arcs = [], []
        try:
            with os.scandir(path) as it:
                for e in it:
                    try:
                        if e.is_dir() and not e.name.startswith("."):
                            dirs.append((e.name, e.path))
                        else:
                            name_low = e.name.lower()
                            if name_low.endswith(".zpaq"):
                                arcs.append((e.name, e.path, False))
                            elif name_low.endswith(UNI_EXTS):
                                arcs.append((e.name, e.path, True))
                    except OSError:
                        continue
        except OSError:
            dirs, arcs = [], []

        dirs.sort(key=lambda x: os.path.normcase(x[0]))
        arcs.sort(key=lambda x: os.path.normcase(x[0]))

        with self._blocked():
            for name, full in dirs:
                child = QTreeWidgetItem([f"📂 {name}"])
                child.setData(TCOL, USER_ROLE, full)
                child.setData(TCOL, KIND_ROLE, K_FS)
                node.addChild(child)
                if self._has_expandable(full):
                    self._add_placeholder(child)

            for name, full, is_uni in arcs:
                kind = K_FS_UNI_ARC if is_uni else K_FS_ARC
                child = QTreeWidgetItem([f"🗜 {name}"])
                child.setData(TCOL, USER_ROLE, full)
                child.setData(TCOL, KIND_ROLE, kind)
                node.addChild(child)
                self._arc_items[full] = child
                self._add_placeholder(child)

    def _ensure_loaded(self, node: QTreeWidgetItem) -> None:
        if node.data(TCOL, KIND_ROLE) != K_FS:
            return
        with self._blocked():

            while node.childCount():
                child = node.child(0)
                if child.data(TCOL, KIND_ROLE) in (K_FS_ARC, K_FS_UNI_ARC):
                    arc_path = child.data(TCOL, USER_ROLE)
                    self._arc_items.pop(arc_path, None)


                    self._arc_subtree_index.pop(arc_path, None)
                node.removeChild(child)
        self._fill(node)

    def _find_child_fs(self, node: QTreeWidgetItem, name: str):
        for i in range(node.childCount()):
            c = node.child(i)
            if c.data(TCOL, KIND_ROLE) != K_FS:
                continue
            text = c.text(0)
            clean = text[2:] if text.startswith("📂 ") else text
            if same_name(clean, name):
                return c
        return None

    def _find_child_arc(self, node: Optional[QTreeWidgetItem], arc_path: str):
        if node is None:
            return None
        for i in range(node.childCount()):
            c = node.child(i)
            if (
                c.data(TCOL, KIND_ROLE) in (K_FS_ARC, K_FS_UNI_ARC)
                and same_name(c.data(TCOL, USER_ROLE), arc_path)
            ):
                return c
        return None


    def _fs_root_and_rel(self, path: Path):
        try:
            path = path.resolve()
        except OSError:
            pass
        if os.name == "nt" and path.drive:
            root_str = path.drive + "\\"
            root = None
            for i in range(self.topLevelItemCount()):
                t = self.topLevelItem(i)
                if same_name(t.data(TCOL, USER_ROLE), root_str):
                    root = t
                    break
            if root is None:
                return None, ()
            try:
                rel = path.relative_to(root_str).parts
            except ValueError:
                rel = ()
            return root, rel
        root = self.topLevelItem(0) if self.topLevelItemCount() else None
        if root is None:
            return None, ()
        rel = path.parts[1:] if path.parts and path.parts[0] in ("/", "") else path.parts
        return root, rel

    def _ensure_fs_path_expanded(self, path: Path):
        root, rel = self._fs_root_and_rel(path)
        if root is None:
            return None
        node = root
        self.expandItem(node)
        self._ensure_loaded(node)
        for part in rel:
            child = self._find_child_fs(node, part)
            if child is None:
                return node
            node = child
            self.expandItem(node)
            self._ensure_loaded(node)
        return node


    def select_fs_path(self, path: Path) -> None:
        with self._blocked():
            node = self._ensure_fs_path_expanded(path)
            if node is not None:
                self.setCurrentItem(node)
                self.scrollToItem(node)

    def reveal_archive(self, arc_path: str) -> None:
        parent_dir = Path(arc_path).parent
        with self._blocked():
            fs_node = self._ensure_fs_path_expanded(parent_dir)
            arc_node = self._find_child_arc(fs_node, arc_path)
            if arc_node is None:
                return
            self._arc_items[arc_path] = arc_node
            self.expandItem(arc_node)
            self.setCurrentItem(arc_node)
            self.scrollToItem(arc_node)

    def select_archive_inner(self, arc_path: str, inner: str) -> None:
        with self._blocked():
            arc = self._arc_items.get(arc_path)
            if arc is None:
                return
            if not inner:
                target = arc
            else:
                target = self._arc_find_under(arc, inner)
            if target is None:
                return
            p = target.parent()
            while p is not None:
                self.expandItem(p)
                p = p.parent()
            self.setCurrentItem(target)
            self.scrollToItem(target)

    def _arc_find_under(self, arc: QTreeWidgetItem, inner: str):
        try:
            arc_path = arc.data(TCOL, USER_ROLE)
        except Exception:
            return None
        if not arc_path:
            return None
        per_arc = self._arc_subtree_index.get(arc_path)
        if not per_arc:
            return None
        return per_arc.get(inner)


    def build_archive_subtree(self, arc_path: str, entries: list) -> None:
        arc = self._arc_items.get(arc_path)


        self._arc_subtree_index.pop(arc_path, None)

        if arc is None:
            return
        with self._blocked():
            while arc.childCount():
                arc.removeChild(arc.child(0))

            folders = {""}
            for e in entries:
                p = e.path
                if e.is_dir:
                    folders.add(p)
                if "/" in p:
                    parent = p.rsplit("/", 1)[0]
                else:
                    parent = ""
                while parent:
                    folders.add(parent)
                    if "/" not in parent:
                        break
                    parent = parent.rsplit("/", 1)[0]

            items = {"": arc}
            for folder in sorted(folders, key=lambda x: (x.count("/"), x.lower())):
                if folder == "":
                    continue
                parent = folder.rsplit("/", 1)[0] if "/" in folder else ""
                parent_item = items.get(parent, arc)
                name = folder.split("/")[-1] or folder
                item = QTreeWidgetItem([f"📂 {name}"])
                item.setData(TCOL, USER_ROLE, folder)
                item.setData(TCOL, KIND_ROLE, K_ARC)
                item.setData(TCOL, ARC_OWNER_ROLE, arc_path)
                parent_item.addChild(item)
                items[folder] = item

            self.expandItem(arc)


            self._arc_subtree_index[arc_path] = items


    def _on_expanded(self, node: QTreeWidgetItem) -> None:
        kind = node.data(TCOL, KIND_ROLE)
        if kind == K_FS:
            self._ensure_loaded(node)
        elif kind in (K_FS_ARC, K_FS_UNI_ARC):
            if node.childCount() == 1 and node.child(0).data(TCOL, KIND_ROLE) == K_PLACE:
                self.arc_open_requested.emit(node.data(TCOL, USER_ROLE))

    def _on_current(self, current: Optional[QTreeWidgetItem], _previous) -> None:
        self._emit_for(current)

    def _on_clicked(self, node: QTreeWidgetItem, _column: int) -> None:
        self._emit_for(node)

    def _emit_for(self, node: Optional[QTreeWidgetItem]) -> None:
        if node is None:
            return
        kind = node.data(TCOL, KIND_ROLE)
        if kind == K_FS:
            self.fs_selected.emit(node.data(TCOL, USER_ROLE))
        elif kind in (K_FS_ARC, K_FS_UNI_ARC):
            self.arc_selected.emit(node.data(TCOL, USER_ROLE), "")
        elif kind == K_ARC:
            owner = node.data(TCOL, ARC_OWNER_ROLE)
            inner = node.data(TCOL, USER_ROLE)
            self.arc_selected.emit(owner, inner or "")
