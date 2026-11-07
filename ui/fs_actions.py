













from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QUrl, QFile
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QInputDialog, QMessageBox

from core.password_store import get_password, set_password
from core.paths import is_inside as _is_inside
from core.paths import is_root as _is_root
from core.paths import nearest_existing as _nearest_existing
from core.paths import retarget_path as _retarget_path
from core.paths import same_name, valid_filename
from ui.i18n import tr
from ui.qt_compat import (
    K_FS_ARC,
    K_FS_DIR,
    K_FS_FILE,
    YES_BUTTON,
    YES_NO_BUTTONS,
)


def open_file_external(path: str) -> bool:
    pass



    try:
        return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))))
    except Exception:
        return False


def _move_to_trash(path: str) -> bool:
    pass

    try:
        res = QFile.moveToTrash(path)
    except Exception:
        return False
    if isinstance(res, tuple):
        return bool(res[0]) if res else False
    return bool(res)


class FsActionsMixin:
    pass

                                                                       
    def _open_fs_path(self, path: str):
        pass
        if not path:
            return
        p = Path(path)
        if not p.is_file():
            return
        if not open_file_external(path):
            QMessageBox.warning(
                self, tr("open.title"), tr("open.failed", name=p.name)
            )

    def _delete_fs_path(self, path: str):
        pass
        if not path:
            return
        p = Path(path)
        if _is_root(p):
            QMessageBox.warning(self, tr("delete.title"), tr("delete.cannot_root"))
            return
        if not (p.exists() or p.is_symlink()):
            return

        name = p.name or str(p)
        ans = QMessageBox.question(
            self,
            tr("delete.title"),
            tr("delete.confirm", name=name),
            YES_NO_BUTTONS,
        )
        if ans != YES_BUTTON:
            return

        if not _move_to_trash(str(p)):
            QMessageBox.warning(
                self, tr("delete.title"), tr("delete.failed", name=name)
            )
            return
        self._after_fs_delete(p)

    def _delete_table_current(self):
        pass
        kind, payload = self._row_payload()
        if kind not in (K_FS_DIR, K_FS_FILE, K_FS_ARC):
            return
        if payload:
            self._delete_fs_path(str(payload))

                                                                       
    def _rename_fs_path(self, path: str):
        pass
        if not path:
            return
        p = Path(path)
        if _is_root(p) or not p.exists():
            return

        name, ok = QInputDialog.getText(
            self,
            tr("rename.title"),
            tr("rename.prompt", name=p.name),
            text=p.name,
        )
        if not ok:
            return
        new_name = (name or "").strip()
        if not new_name or new_name == p.name:
            return
        if not valid_filename(new_name):
            QMessageBox.warning(self, tr("rename.title"), tr("rename.invalid"))
            return

        new_full = p.parent / new_name
                                                                          
        if new_full.exists() and not same_name(str(new_full), str(p)):
            QMessageBox.warning(
                self, tr("rename.title"), tr("rename.exists", name=new_name)
            )
            return

        try:
            os.rename(p, new_full)
        except OSError as exc:
            QMessageBox.warning(
                self, tr("rename.title"), tr("rename.failed", error=str(exc))
            )
            return
        self._after_fs_rename(p, new_full)

    def _rename_table_current(self):
        pass
        kind, payload = self._row_payload()
        if kind not in (K_FS_DIR, K_FS_FILE, K_FS_ARC):
            return
        if payload:
            self._rename_fs_path(str(payload))

                                                                           
    def _after_fs_rename(self, old: Path, new: Path):
        parent = new.parent

                                                                           
                                                                        
        if self.archive_path:
            retargeted = _retarget_path(self.archive_path, old, new)
            if retargeted:
                self._retarget_archive_state(self.archive_path, str(retargeted))

        if self.mode == "fs" and self.fs_path is not None:
            new_fs = _retarget_path(self.fs_path, old, new)
            if new_fs and Path(new_fs).is_dir():
                                                              
                self.navigate_fs(Path(new_fs))
                return
            if same_name(str(parent), str(self.fs_path)):
                self._populate_right_fs()

        try:
            self.tree.select_fs_path(parent)
        except Exception:
            pass

    def _retarget_archive_state(self, old_arc: str, new_arc: str):
        pass
                                                        
        try:
            stored = get_password(old_arc)
            if stored:
                set_password(new_arc, stored)
                set_password(old_arc, None)
        except Exception:
            pass

        cached = self._arc_cache.pop(old_arc, None)
        if cached is not None:
            self._arc_cache[new_arc] = cached

        if self.archive_path and same_name(self.archive_path, old_arc):
            self.archive_path = new_arc
            self.password = cached.get("password") if cached else None
            self._nav_key = (new_arc, self.archive_inner or "")

                                                                           
        try:
            self.tree._arc_items.pop(old_arc, None)
        except Exception:
            pass

        self._update_chrome()

                                                                           
    def _after_fs_delete(self, p: Path):
        parent = p.parent if p.parent != p else None

        arc_gone = self.archive_path and (
            same_name(self.archive_path, str(p)) or _is_inside(self.archive_path, p)
        )
        fs_gone = self.mode == "fs" and self.fs_path is not None and (
            same_name(str(self.fs_path), str(p))
            or _is_inside(str(self.fs_path), p)
        )

                                                                         
                   
        if arc_gone:
            for k in [
                k
                for k in list(self._arc_cache)
                if same_name(k, str(p)) or _is_inside(k, p)
            ]:
                self._arc_cache.pop(k, None)

        if arc_gone or fs_gone:
            target = _nearest_existing(parent) if parent is not None else None
            self._show_fs(target or Path.home())
            return

                                                                       
        if (
            self.mode == "fs"
            and self.fs_path is not None
            and parent is not None
            and same_name(str(self.fs_path), str(parent))
        ):
            self._populate_right_fs()

        if parent is not None:
            try:
                self.tree.select_fs_path(parent)
            except Exception:
                pass
