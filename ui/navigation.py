





from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.config_bridge import _merge_cfg
from ui.i18n import tr
from ui.qt_compat import multipart_pattern


class NavigationMixin:
    pass

                                                                               

    def _check_archive_engine(self, arc_path: str) -> bool:
        pass

































        arc_low = str(arc_path or "").lower()

        if arc_low.endswith((".zip", ".7z", ".rar")):
            if not getattr(self, "seven_zip_available", False):
                QMessageBox.warning(
                    self,
                    tr("zpaq.not_found_title"),
                    tr("zpaq.seven_zip_not_found_text"),
                )
                return False
            return True

        if arc_low.endswith(".zpaq"):
            if not getattr(self, "zpaq_available", False):
                QMessageBox.warning(
                    self,
                    tr("zpaq.not_found_title"),
                    tr("zpaq.not_found_text"),
                )
                return False
            return True

        return True

                                                                      

    def _update_chrome(self):
        self.crumb.update_state(
            self.mode,
            self.fs_path,
            Path(self.archive_path).name if self.archive_path else "",
            self.archive_inner or "",
        )
        self._update_title()

    def navigate_fs(self, path, from_tree=False):
        path = Path(path)

        if self.mode == "fs" and self.fs_path is not None and path == self.fs_path:
                                                                         
                                                                               
            if from_tree:
                self._populate_right_fs()
            return

        self.mode = "fs"
        self.fs_path = path
        self._nav_key = ("fs", str(path))

        self.search_bar.setVisible(False)
        self.search_edit.clear()
        self._search_query = ""
        self._last_search_archive = None

        self._rebuild_versions_menu()
        self._populate_right_fs()
        self._update_chrome()

        self.statusBar().showMessage(tr("status.folder", path=path))

        if not from_tree:
            self.tree.select_fs_path(path)

    def navigate_archive(self, inner, from_tree=False):
        inner = inner or ""

        if self.archive_path is None:
            return

        key = (self.archive_path, inner)

        if self.mode == "archive" and self._nav_key == key:
                                                                        
            self._rebuild_versions_menu()
            return

        self._nav_key = key
        self.mode = "archive"
        self.archive_inner = inner

        self.search_bar.setVisible(True)

        if self.archive_path != self._last_search_archive:
            self.search_edit.clear()
            self._search_query = ""
            self._last_search_archive = self.archive_path

        self._rebuild_versions_menu()
        self._populate_right_archive()
        self._update_chrome()

        label = inner or "/"
        self.statusBar().showMessage(
            f"{Path(self.archive_path).name} :: {label}"
        )

        if not from_tree:
            self.tree.select_archive_inner(self.archive_path, inner)

    def _go_up(self):
        if self.mode == "fs":
            p = self.fs_path
            if p is None or p == p.parent:
                return
            self.navigate_fs(p.parent)
        else:
            inner = self.archive_inner or ""
            if inner:
                parent = "/".join(inner.split("/")[:-1])
                self.navigate_archive(parent)
            elif self.archive_path:
                self.navigate_fs(Path(self.archive_path).parent)

    def _on_backspace(self):
        fw = QApplication.focusWidget()
        if fw is self.log:
            return
        self._go_up()

    def _on_refresh(self):
        if self.mode == "fs":
            self._populate_right_fs()
            self.statusBar().showMessage(tr("status.updated", path=self.fs_path))
        elif self.archive_path:
            self._load_archive_list(
                self.archive_path,
                make_active=True,
                inner=self.archive_inner,
            )

    def _on_toggle_latest(self):
        _merge_cfg(latest_only=bool(self.latest_only_action.isChecked()))

        if self.mode == "archive":
            self._populate_right_archive()

    def _on_tree_fs_selected(self, path: str):
        self.navigate_fs(Path(path), from_tree=True)

    def _on_tree_arc_selected(self, arc_path: str, inner: str):
        pass



















        if not arc_path:
            return

                                                                
                                                                     
                                      
        if not self._check_archive_engine(arc_path):
            return

        key = multipart_pattern(arc_path)

        if key != self.archive_path:
            self._activate_archive(key)

            c = self._cache(key)
            if not c["loaded"]:
                self._load_archive_list(key, make_active=True, inner=inner)
                return

            if not c["info_loaded"]:
                self._load_info(key)

        self.navigate_archive(inner, from_tree=True)

    def _on_tree_arc_open_requested(self, arc_path: str):
        pass







        if not arc_path:
            return

        if not self._check_archive_engine(arc_path):
            return

        key = multipart_pattern(arc_path)
        c = self._cache(key)
        if c["loaded"]:
                                                          
                                                                
            try:
                self.tree.build_archive_subtree(key, c["entries"])
            except Exception:
                pass
            return

        self._load_archive_list(key, make_active=False, inner="")
