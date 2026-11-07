
















from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from core.zpaq_cli import check_zpaq, safe_cmdline
from ui.config_bridge import _merge_cfg
from ui.i18n import tr
from ui.qt_compat import WAIT_CURSOR, YES_BUTTON, YES_NO_BUTTONS


class AppServicesMixin:
    pass

                                                                          
    def _verify_zpaq(self):
        if check_zpaq(self.zpaq_bin):
            self.zpaq_available = True
            return
        ans = QMessageBox.question(
            self,
            tr("zpaq.verify_title"),
            tr("zpaq.verify_text", bin=self.zpaq_bin),
            YES_NO_BUTTONS,
        )
        if ans == YES_BUTTON:
            self._choose_zpaq_path()
        else:
            self.statusBar().showMessage(tr("status.no_zpaq_mode"))

    def _choose_zpaq_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("zpaq.choose_title"),
            "",
            tr("zpaq.choose_filter"),
        )
        if not path:
            return
        self.zpaq_bin = path
        self.zpaq_available = check_zpaq(path)
        if self.zpaq_available:
            _merge_cfg(zpaq_path=path)
            self.statusBar().showMessage(tr("status.zpaq_found", path=path))
        else:
            self.statusBar().showMessage(tr("status.zpaq_not_started", path=path))

                                                                        
    def _verify_7z(self):
        pass
        from core.universal_ops import check_7z, find_7z
        
        if not self.seven_zip_bin:
            self.seven_zip_bin = find_7z()
            
        if self.seven_zip_bin and check_7z(self.seven_zip_bin):
            self.seven_zip_available = True
            return
            
        self.seven_zip_available = False
                                                                            
                                                             
                                                           

    def _choose_7z_path(self):
        pass
        from core.universal_ops import check_7z
        
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("zpaq.seven_zip_choose_title"),
            "",
            tr("zpaq.choose_filter"),
        )
        if not path:
            return
            
        self.seven_zip_bin = path
        self.seven_zip_available = check_7z(path)
        
        if self.seven_zip_available:
            _merge_cfg(seven_zip_path=path)
            self.statusBar().showMessage(tr("status.seven_zip_found", path=path))
        else:
            self.seven_zip_bin = ""
            _merge_cfg(seven_zip_path="")
            self.statusBar().showMessage(tr("status.seven_zip_not_started", path=path))

                                                                         
    def log_command(self, cmd: list):
        self.log.appendPlainText("$ " + safe_cmdline(cmd, self.password))

    def log_output(self, text: str):
        if text:
            self.log.appendPlainText(text)

                                                                          
    def _start_busy(self, base_text: str):
        pass










        self._busy_base = base_text
        self._busy_n = 0
        self._busy_depth = getattr(self, "_busy_depth", 0) + 1

        self.statusBar().showMessage(base_text)
        if not self._busy_timer.isActive():
            self._busy_timer.start()

        self._ensure_notice()
        try:
            if self._busy_depth == 1:
                self._notice.show_notice(base_text)
            else:
                                                                        
                self._notice.update_step(base_text)
        except Exception:
            pass

        if not getattr(self, "_wait_cursor", False):
            QApplication.setOverrideCursor(WAIT_CURSOR)
            self._wait_cursor = True

    def _stop_busy(self):
        self._busy_depth = max(0, getattr(self, "_busy_depth", 1) - 1)

        if self._busy_depth > 0:
                                                         
            return

        self._busy_timer.stop()
        if getattr(self, "_wait_cursor", False):
            QApplication.restoreOverrideCursor()
            self._wait_cursor = False
        try:
            if getattr(self, "_notice", None) is not None:
                self._notice.hide_notice()
        except Exception:
            pass

    def _ensure_notice(self) -> None:
        pass
        if getattr(self, "_notice", None) is not None:
            return
        try:
            from ui.operation_notice import OperationNotice

            self._notice = OperationNotice(parent=self, cancel_enabled=True)
            self._notice.cancelRequested.connect(self._on_notice_cancel)
        except Exception:
            self._notice = None

    def _on_notice_cancel(self) -> None:
        pass
        try:
            self._cancel_long_operations()
        except Exception:
            pass

    def _tick_busy(self):
        self._busy_n = (self._busy_n + 1) % 4
                                                                    
                                                        
        shown = self.statusBar().currentMessage()
        if not shown or shown.startswith(self._busy_base):
            self.statusBar().showMessage(self._busy_base + "." * (self._busy_n + 1))

    def _refresh_status_for_current_mode(self):
        try:
            if self.mode == "fs":
                if self.fs_path is not None:
                    self.statusBar().showMessage(
                        tr("status.folder", path=self.fs_path)
                    )
            elif self.mode == "archive" and self.archive_path:
                self.statusBar().showMessage(
                    f"{Path(self.archive_path).name} :: {self.archive_inner or '/'}"
                )
        except Exception:
            pass

                                                                           
    def _remember_extract_dir(self):

        try:
            if self.last_extract_dir:
                _merge_cfg(last_extract_dir=str(self.last_extract_dir))
        except Exception:
            pass

                                                                           
    def _on_open_manual(self):
        pass






        from core.help_docs import open_manual

        ok, what = open_manual()
        if ok:
            return
                                                                                
        QMessageBox.warning(
            self,
            tr("menu.help.guide"),
            tr("manual.not_found", path=what or "."),
        )
