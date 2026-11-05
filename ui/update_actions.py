from __future__ import annotations

import os
import time

from PySide6.QtWidgets import QApplication, QMessageBox

from core import updater
from ui.app_info import APP_VERSION, APP_VERSION_FULL
from ui.config_bridge import _load_cfg, _merge_cfg
from ui.i18n import tr
from ui.qt_compat import YES_BUTTON
from ui.update_dialog import UpdateDialog
from workers.update_worker import UpdateCheckWorker


CHECK_INTERVAL_SECONDS = 24 * 60 * 60


class UpdateActionsMixin:


    def _update_cfg(self):
        try:
            return self._cfg or _load_cfg()
        except Exception:
            return None

    def _update_url(self) -> str:
        cfg = self._update_cfg()
        return str(getattr(cfg, "update_url", None)
                   or updater.DEFAULT_MANIFEST_URL)

    def _drop_update_worker(self, worker) -> None:
        if getattr(self, "_update_worker", None) is worker:
            self._update_worker = None
        workers = getattr(self, "_workers", None)
        if workers is not None:
            try:
                if worker in workers:
                    workers.remove(worker)
            except Exception:
                pass


        try:
            worker.deleteLater()
        except Exception:
            pass


    def start_update_check(self, manual: bool = False) -> bool:
        running = getattr(self, "_update_worker", None)
        try:
            if running is not None and running.isRunning():
                return False
        except Exception:
            pass

        cfg = self._update_cfg()
        if not manual:
            if not bool(getattr(cfg, "update_check_enabled", True)):
                return False
            last = getattr(cfg, "last_update_check", None)
            try:
                if last and int(time.time()) - int(last) < CHECK_INTERVAL_SECONDS:
                    return False
            except (TypeError, ValueError):
                pass

        if manual:
            try:
                self.statusBar().showMessage(tr("update.checking"))
            except Exception:
                pass

        worker = UpdateCheckWorker(self._update_url(), APP_VERSION, parent=self)
        worker.done.connect(
            lambda result, m=manual: self._on_update_check_done(result, m)
        )
        worker.finished.connect(
            lambda w=worker: self._drop_update_worker(w)
        )
        workers = getattr(self, "_workers", None)
        if workers is not None:
            try:
                workers.append(worker)
            except Exception:
                pass
        self._update_worker = worker
        worker.start()
        return True

    def _on_update_check_done(self, result: dict, manual: bool) -> None:


        if getattr(self, "_closing", False):
            return


        try:
            _merge_cfg(last_update_check=int(time.time()))
        except Exception:
            pass
        cfg_now = self._update_cfg()
        if cfg_now is not None:
            try:
                cfg_now.last_update_check = int(time.time())
            except Exception:
                pass

        if not result.get("ok"):
            if manual:
                QMessageBox.warning(
                    self, tr("update.error_title"),
                    tr("update.check_error", error=result.get("error") or ""),
                )
            return

        info = result.get("info") or {}
        if not result.get("newer"):
            if manual:
                QMessageBox.information(
                    self, tr("update.title"),
                    tr("update.latest", version=APP_VERSION_FULL),
                )
            return

        cfg = self._update_cfg()
        skipped = getattr(cfg, "skipped_version", None)
        if not manual and skipped and str(skipped) == str(
                info.get("version") or ""):
            return

        self._show_update_dialog(info, manual)


    def _show_update_dialog(self, info: dict, manual: bool) -> None:
        if getattr(self, "_closing", False):
            return
        existing = getattr(self, "_update_dialog", None)
        try:
            if existing is not None and existing.isVisible():
                existing.raise_()
                existing.activateWindow()
                return
        except Exception:
            pass

        cfg = self._update_cfg()
        dlg = UpdateDialog(
            info,
            APP_VERSION_FULL,
            install_supported=updater.is_frozen(),
            auto_check=bool(getattr(cfg, "update_check_enabled", True)),
            parent=self,
        )
        dlg.ready_to_install.connect(
            lambda inf, path, d=dlg: self._install_update(d, inf, path)
        )
        dlg.skip_requested.connect(self._on_update_skipped)
        dlg.auto_check_changed.connect(self._on_auto_check_changed)
        dlg.finished.connect(lambda _r, d=dlg: self._forget_update_dialog(d))
        self._update_dialog = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _forget_update_dialog(self, dlg) -> None:
        if getattr(self, "_update_dialog", None) is dlg:
            self._update_dialog = None

    def _on_update_skipped(self, version: str) -> None:
        if not version:
            return
        try:
            _merge_cfg(skipped_version=str(version))
        except Exception:
            pass
        cfg = self._update_cfg()
        if cfg is not None:
            try:
                cfg.skipped_version = str(version)
            except Exception:
                pass
        try:
            self.statusBar().showMessage(tr("update.skipped", version=version))
        except Exception:
            pass

    def _on_auto_check_changed(self, enabled: bool) -> None:
        try:
            _merge_cfg(update_check_enabled=bool(enabled))
        except Exception:
            pass
        cfg = getattr(self, "_cfg", None)
        if cfg is not None:
            try:
                cfg.update_check_enabled = bool(enabled)
            except Exception:
                pass


    def _install_update(self, dialog, info: dict, zip_path: str) -> None:
        discard = getattr(dialog, "discard_download", None)
        if not updater.is_frozen():
            QMessageBox.information(
                self, tr("update.title"),
                tr("update.install_only_built"),
            )
            if callable(discard):
                discard()
            return

        answer = QMessageBox.question(
            self, tr("update.title"),
            tr("update.confirm_install", version=info.get("version") or ""),
        )
        if answer != YES_BUTTON:


            if callable(discard):
                discard()
            return

        try:
            script, _temp = updater.prepare_update(
                zip_path,
                install_path=updater.install_dir(),
                wait_pid=os.getpid(),
            )
            updater.launch_updater(script)
        except Exception as exc:
            QMessageBox.critical(
                self, tr("update.error_title"),
                tr("update.install_error", error=f"{type(exc).__name__}: {exc}"),
            )
            if callable(discard):
                discard()
            return


        if callable(discard):
            discard()

        try:
            dialog.accept()
        except Exception:
            pass
        app = QApplication.instance()
        if app is not None:
            app.quit()
