































from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from core.paths import windows_drives
from ui.i18n import tr

                                                                    
                                                              
                                                                  
                          
MAX_CHILDREN = 1000

_PATH_ROLE = Qt.UserRole + 100


class SourceSelectWindow(QDialog):
    pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("source_select.title"))
        self.resize(540, 430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(tr("source_select.tree_header"))
        self.tree.setAlternatingRowColors(True)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._block_changed = False
        self._build_roots()

    def _build_roots(self):
        self._block_changed = True
        self.tree.clear()
        if os.name == "nt":
            roots = windows_drives()
        else:
            roots = ["/"]
        for root in roots:
            label = root
            if os.name == "nt" and root:
                label = tr("tree.drive", letter=root[0].upper())
            item = QTreeWidgetItem([label])
            item.setData(0, _PATH_ROLE, root)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            self.tree.addTopLevelItem(item)
            self._add_placeholder(item)
        self._block_changed = False

    def _add_placeholder(self, item: QTreeWidgetItem):
        ph = QTreeWidgetItem(["..."])
        ph.setData(0, _PATH_ROLE, None)
        ph.setFlags(Qt.NoItemFlags)
        item.addChild(ph)

    def _has_placeholder(self, item: QTreeWidgetItem) -> bool:
        for i in range(item.childCount()):
            if item.child(i).data(0, _PATH_ROLE) is None:
                return True
        return False

    def _on_item_expanded(self, item: QTreeWidgetItem):
        if self._has_placeholder(item):
            self._load_children(item)

    def _load_children(self, item: QTreeWidgetItem):
        pass












        path = item.data(0, _PATH_ROLE)
        if not path:
            return
        self._block_changed = True
        try:
            while item.childCount():
                item.removeChild(item.child(0))

            dirs, files = [], []
            try:
                with os.scandir(path) as it:
                    for e in it:
                        try:
                            if e.is_dir():
                                dirs.append((e.name, e.path))
                            else:
                                files.append((e.name, e.path))
                        except OSError:
                            continue
            except OSError:
                                                                    
                                                                    
                                                                    
                             
                return

            dirs.sort(key=lambda x: os.path.normcase(x[0]))
            files.sort(key=lambda x: os.path.normcase(x[0]))

            total = len(dirs) + len(files)
            parent_check = item.checkState(0)
            shown = 0

                                                               
                                                                
                                                                
                               
            for name, full in dirs:
                if shown >= MAX_CHILDREN:
                    break
                child = QTreeWidgetItem([f"📂 {name}"])
                child.setData(0, _PATH_ROLE, full)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, parent_check)
                item.addChild(child)
                self._add_placeholder(child)
                shown += 1

            for name, full in files:
                if shown >= MAX_CHILDREN:
                    break
                child = QTreeWidgetItem([f"📄 {name}"])
                child.setData(0, _PATH_ROLE, full)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, parent_check)
                item.addChild(child)
                shown += 1

            if total > shown:
                                                                               
                                                                             
                                                                            
                                                                         
                                                                              
                                                                         
                                                             
                note = QTreeWidgetItem(
                    [tr("table.truncated", max=shown, count=total)]
                )
                note.setData(0, _PATH_ROLE, None)
                note.setFlags(Qt.NoItemFlags)
                item.addChild(note)
        finally:
            self._block_changed = False

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        if self._block_changed:
            return
        if item.data(0, _PATH_ROLE) is None:
            return
        self._block_changed = True
        check = item.checkState(0)
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, _PATH_ROLE) is not None:
                child.setCheckState(0, check)
        self._block_changed = False
        self._update_parents(item)

    def _update_parents(self, item: QTreeWidgetItem):
        self._block_changed = True
        parent = item.parent()
        while parent is not None:
            states = [
                parent.child(i).checkState(0)
                for i in range(parent.childCount())
                if parent.child(i).data(0, _PATH_ROLE) is not None
            ]
            if not states:
                parent.setCheckState(0, Qt.Unchecked)
            elif all(s == Qt.Checked for s in states):
                parent.setCheckState(0, Qt.Checked)
            elif all(s == Qt.Unchecked for s in states):
                parent.setCheckState(0, Qt.Unchecked)
            else:
                parent.setCheckState(0, Qt.PartiallyChecked)
            parent = parent.parent()
        self._block_changed = False

    def selected_paths(self) -> list:
        paths = []
        for i in range(self.tree.topLevelItemCount()):
            self._collect_paths(self.tree.topLevelItem(i), paths)
        return paths

    def _collect_paths(self, item: QTreeWidgetItem, paths: list):
        path = item.data(0, _PATH_ROLE)
        if path is None:
            return
        check = item.checkState(0)
        if check == Qt.Checked:
            if self._all_children_checked(item):
                paths.append(str(path))
            else:
                for i in range(item.childCount()):
                    self._collect_paths(item.child(i), paths)
        elif check == Qt.PartiallyChecked:
            for i in range(item.childCount()):
                self._collect_paths(item.child(i), paths)

    def _all_children_checked(self, item: QTreeWidgetItem) -> bool:
        if item.childCount() == 0:
            return True
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, _PATH_ROLE) is None:
                continue
            if child.checkState(0) != Qt.Checked:
                return False
        return True
