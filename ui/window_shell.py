from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from ui import skins
from ui.app_info import APP_NAME, APP_VERSION_FULL
from ui.config_bridge import _load_cfg, _save_cfg
from ui.i18n import tr
from ui.qt_compat import YES_BUTTON, YES_NO_BUTTONS


_SHUTDOWN_TIMEOUT_MS = 8000


def _is_alive(worker) -> bool:

    try:
        return bool(worker.isRunning())
    except Exception:
        return False


class WindowShellMixin:


    def _on_about(self):


        c_header = skins.color("TEXT_HEADER")
        c_accent = skins.color("ACCENT")
        c_main = skins.color("TEXT_MAIN")
        c_border = skins.color("BORDER_SOFT")
        c_muted = skins.color("TEXT_MUTED")

        title = tr("about.title", app_name=APP_NAME)
        text = (
            f"<h2 style='margin:0 0 2px 0; color:{c_header};'>"
            f"{APP_NAME}"
            "</h2>"
            f"<p style='margin:0 0 12px 0; color:{c_accent}; font-weight:600;'>"
            f"{tr('about.version', app_version=APP_VERSION_FULL)}"
            "</p>"
            f"<p style='margin:0 0 8px 0; line-height:1.45; color:{c_main};'>"
            f"{tr('about.description')}"
            "</p>"
            f"<hr style='border:none; border-top:1px solid {c_border}; margin:10px 0;'>"
            f"<p style='margin:0; color:{c_muted}; font-size:11px; line-height:1.5;'>"
            f"{tr('about.engine')}<br>"
            f"{tr('about.ui')}"
            "</p>"
        )
        QMessageBox.about(self, title, text)


    def _update_title(self):
        if self.mode == "archive" and self.archive_path:
            self.setWindowTitle(
                f"{APP_NAME} v{APP_VERSION_FULL} — "
                f"{Path(self.archive_path).name}"
            )
        elif self.fs_path:
            self.setWindowTitle(
                f"{APP_NAME} v{APP_VERSION_FULL} — {self.fs_path}"
            )
        else:
            self.setWindowTitle(f"{APP_NAME} v{APP_VERSION_FULL}")


    def _show_fs(self, path):
        self.mode = "fs"
        self.tree.build_fs_roots()
        self.navigate_fs(path)


    def _running_workers(self) -> list:

        out = []
        for w in list(getattr(self, "_workers", []) or []):
            if _is_alive(w):
                out.append(w)
        return out

    def _shutdown_workers(
        self,
        workers: list,
        timeout_ms: int = _SHUTDOWN_TIMEOUT_MS,
    ) -> list:
        for w in workers:
            try:
                w.cancel_request()
            except Exception:
                pass

        deadline = time.monotonic() + timeout_ms / 1000.0
        alive = list(workers)

        while alive and time.monotonic() < deadline:


            QApplication.processEvents()
            alive = [w for w in alive if _is_alive(w)]
            if alive:
                time.sleep(0.02)


        if alive:
            QApplication.processEvents()
            alive = [w for w in alive if _is_alive(w)]

        for w in workers:
            if w not in alive:
                try:
                    w.deleteLater()
                except Exception:
                    pass

        try:
            self._workers = [
                w
                for w in (getattr(self, "_workers", []) or [])
                if w in alive
            ]
        except Exception:
            pass

        return alive

    def _confirm_close_with_busy_workers(self) -> bool:
        running = self._running_workers()
        if not running:
            return True

        ans = QMessageBox.question(
            self,
            tr("close.busy_title"),
            tr("close.busy_text", count=len(running)),
            YES_NO_BUTTONS,
        )
        if ans != YES_BUTTON:
            return False

        stuck = self._shutdown_workers(running)
        if stuck:
            QMessageBox.warning(
                self,
                tr("close.busy_title"),
                tr("close.busy_stuck", count=len(stuck)),
            )
            return False

        return True


    def _discard_transcode_temp_dir(self):
        cleanup = getattr(self, "_cleanup_transcode_temp_dir", None)
        if callable(cleanup):
            try:
                cleanup()
            except Exception:
                pass


    def closeEvent(self, ev):


        self._closing = True
        if not self._confirm_close_with_busy_workers():
            self._closing = False
            ev.ignore()
            return


        self._discard_transcode_temp_dir()

        try:
            cfg = _load_cfg()

            try:
                cfg.zpaq_path = (
                    self.zpaq_bin
                    if self.zpaq_bin and os.path.isfile(self.zpaq_bin)
                    else cfg.zpaq_path
                )
            except Exception:
                pass

            try:
                cfg.latest_only = bool(self.latest_only_action.isChecked())
            except Exception:
                pass

            try:
                if self.mode == "fs" and self.fs_path and Path(self.fs_path).is_dir():
                    cfg.last_fs_path = str(self.fs_path)
            except Exception:
                pass

            try:
                if self.last_extract_dir and Path(self.last_extract_dir).is_dir():
                    cfg.last_extract_dir = str(self.last_extract_dir)
            except Exception:
                pass

            try:
                g = self.geometry()
                cfg.window_geometry = [g.x(), g.y(), g.width(), g.height()]
                cfg.window_maximized = bool(self.isMaximized())
            except Exception:
                pass


            try:
                cfg.right_sort_column = getattr(self, "_right_sort_column", None)
                cfg.right_sort_desc = getattr(self, "_right_sort_desc", False)
            except Exception:
                pass


            try:
                cfg.last_close = int(time.time())
            except Exception:
                pass

            _save_cfg(cfg)
        except Exception:
            pass
        super().closeEvent(ev)
