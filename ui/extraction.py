


















from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMessageBox,
)

from core.paths import (
    directory_not_empty,
    is_temp_path,
    is_top_level_drive,
    sanitize_filename,
)
from core.temp_cleanup import remove_temp_dir
from ui.fs_actions import open_file_external
from ui.i18n import tr
from ui.qt_compat import YES_BUTTON, YES_NO_BUTTONS


class ExtractionMixin:
    pass

                                                                              
    def _ui_folder_started(self, total: int) -> None:
        pass

    def _ui_folder_tick(self, i: int, total: int, path: str) -> None:
        pass

    def _ui_folder_batch_started(self) -> None:
        pass

    def _ui_folder_percent(self, pct: int) -> None:
        pass

    def _ui_file_started(self, name: str = "") -> None:
        pass

    def _ui_extract_finished(self, ok: bool, total: int, msg: str) -> None:
        pass

                                                                          
    def _latest_entry_for_path(self, path: str):
        c = [
            e
            for e in self.entries
            if e.path == path and not e.is_dir and e.flag != "-"
        ]
        if not c:
            return None

        return max(c, key=lambda x: (x.version or 0, x.datetime))

    def _extract_file_entry(self, entry):
        if not self.archive_path or not entry:
            return

        base = sanitize_filename(Path(entry.path).name)
        stem, suffix = os.path.splitext(base)
        proposed = (
            f"{stem}_v{entry.version}{suffix}"
            if entry.version is not None
            else base
        )

        initial_dir = self._initial_extract_dir()

        dest, _ = QFileDialog.getSaveFileName(
            self,
            tr("extract.dialog.save_file_title"),
            str(initial_dir / proposed),
        )
        if not dest:
            return

        dest_str = str(dest).strip()

        if dest_str.endswith(":") or dest_str.endswith(("/", "\\")):
            base_path = dest_str.rstrip("/\\")
            dest_path = (
                Path(base_path + "\\" + proposed)
                if base_path.endswith(":")
                else Path(base_path) / proposed
            )
        else:
            dest_path = Path(dest_str)
            if dest_path.is_dir():
                dest_path = dest_path / proposed

        if dest_path.is_dir():
            dest_path = dest_path.with_name(dest_path.name + "_file")

        if dest_path.exists():
            ans = QMessageBox.question(
                self,
                tr("extract.dialog.file_exists_title"),
                tr("extract.dialog.file_exists_text", path=dest_path),
                YES_NO_BUTTONS,
            )
            if ans != YES_BUTTON:
                return

        if dest_path.parent.is_dir():
            self.last_extract_dir = dest_path.parent

        self.statusBar().showMessage(tr("status.extract_file", name=entry.name))
        self._start_extract_file_worker(entry, str(dest_path))

    def _open_arc_file_entry(self, entry):
        pass

        if not self.archive_path or not entry:
            return

        try:
            tmp_dir = tempfile.mkdtemp(prefix="rizpaq_open_")
        except OSError:
            QMessageBox.critical(
                self, tr("open.title"), tr("open.tmp_failed")
            )
            return

                                                                
                                                                   
        dest = str(Path(tmp_dir) / sanitize_filename(Path(entry.path).name))
        self.statusBar().showMessage(tr("status.opening", name=entry.name))
        self._start_extract_file_worker(entry, dest, open_after=True)

    def _open_extracted_if_ok(self, result, dest: str):
        pass
                                                                        
                                                                         
                                                                     
                                                                 
        if result.get("cancelled"):
            remove_temp_dir(Path(dest).parent)
            return
        if result.get("kind") != "extract_file" or not result.get("success"):
            remove_temp_dir(Path(dest).parent)
            return
        if not open_file_external(dest):
            QMessageBox.warning(
                self,
                tr("open.title"),
                tr("open.failed", name=Path(dest).name),
            )
                                                                 
            remove_temp_dir(Path(dest).parent)

    def _extract_folder_ask_version(self, folder_path: str):
        text, ok = QInputDialog.getText(
            self,
            tr("extract.dialog.version_title"),
            tr("extract.dialog.version_text"),
        )
        if ok and text.strip():
            self._extract_folder(folder_path, text.strip())

    def _extract_folder(self, folder_path: str, version_text: Optional[str]):
        if not self.archive_path or folder_path is None:
            return

        initial_dir = self._initial_extract_dir()

        dest_parent = QFileDialog.getExistingDirectory(
            self,
            tr("extract.dialog.choose_folder_title"),
            str(initial_dir),
        )
        if not dest_parent:
            return

        dest_parent_path = Path(dest_parent)

        if dest_parent_path.is_file():
            dest_parent_path = dest_parent_path.parent

        try:
            dest_parent_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("extract.dialog.error_title"),
                tr(
                    "extract.dialog.cannot_use_folder",
                    path=dest_parent_path,
                    error=exc,
                ),
            )
            return

        self.last_extract_dir = dest_parent_path

        if is_top_level_drive(folder_path):
            drive_letter = folder_path.strip().rstrip("/")[0].upper()

            direct_path = str(dest_parent_path)
            subfolder_path = str(dest_parent_path / drive_letter)

            ans = QMessageBox.question(
                self,
                tr("extract.dialog.top_level_title"),
                tr(
                    "extract.dialog.top_level_text",
                    inner=folder_path,
                    direct=direct_path,
                    subfolder=subfolder_path,
                ),
                YES_NO_BUTTONS,
            )

            dest_folder = (
                dest_parent_path
                if ans == YES_BUTTON
                else dest_parent_path / drive_letter
            )

            if dest_folder.is_file():
                dest_folder = dest_parent_path / (drive_letter + "_folder")

            if dest_folder.exists() and directory_not_empty(dest_folder):
                a2 = QMessageBox.question(
                    self,
                    tr("extract.dialog.folder_not_empty_title"),
                    tr("extract.dialog.folder_not_empty_text", path=dest_folder),
                    YES_NO_BUTTONS,
                )
                if a2 != YES_BUTTON:
                    return
        else:
            folder_name = sanitize_filename(
                folder_path.rstrip("/").split("/")[-1] or folder_path
            )
            dest_folder = dest_parent_path / folder_name

            if dest_folder.is_file():
                dest_folder = dest_parent_path / (folder_name + "_folder")

            if dest_folder.exists():
                ans = QMessageBox.question(
                    self,
                    tr("extract.dialog.folder_exists_title"),
                    tr("extract.dialog.folder_exists_text", path=dest_folder),
                    YES_NO_BUTTONS,
                )

                if ans != YES_BUTTON:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_folder = dest_parent_path / f"{folder_name}_{ts}"

        try:
            dest_folder.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("extract.dialog.error_title"),
                tr(
                    "extract.dialog.cannot_create_folder",
                    path=dest_folder,
                    error=exc,
                ),
            )
            return

        if not dest_folder.is_dir():
            QMessageBox.critical(
                self,
                tr("extract.dialog.error_title"),
                tr("extract.dialog.cannot_prepare_folder", path=dest_folder),
            )
            return

                                                                     
        version: Optional[object] = None

        if version_text:
            s = str(version_text).strip()

            if s:
                try:
                    version = int(s)
                    if version <= 0:
                        version = None
                except ValueError:
                    if len(s) == 10:
                        s += " 23:59:59"
                    version = s

                                                                          
        if version is None:
            self.statusBar().showMessage(
                tr(
                    "status.extract_folder_batch",
                    path=folder_path.rstrip("/") or folder_path,
                )
            )
            self._start_extract_folder_batch_worker(
                folder_path, None, str(dest_folder)
            )
            return

                                                                         
        entries = self._collect_folder_entries(folder_path, version)

        if not entries:
            QMessageBox.warning(
                self,
                tr("extract.dialog.no_files_title"),
                tr(
                    "extract.dialog.no_files_text",
                    folder=folder_path,
                    version=version_text or tr("extract.dialog.version_latest"),
                ),
            )
            return

        prefix = folder_path.rstrip("/") + "/"
        tasks = []

        for entry in entries:
            rel = (
                entry.path[len(prefix):]
                if entry.path.startswith(prefix)
                else entry.path.split("/")[-1]
            )

            if not rel:
                continue

            tasks.append(
                (
                    entry.path,
                    entry.version,
                    str(dest_folder / rel.replace("/", os.sep)),
                )
            )

        if not tasks:
            QMessageBox.warning(
                self,
                tr("extract.dialog.no_files_title"),
                tr("extract.dialog.no_files_build"),
            )
            return

        self.statusBar().showMessage(
            tr(
                "status.extract_folder_version",
                version=version,
                path=folder_path.rstrip("/") or folder_path,
                count=len(tasks),
            )
        )
        self._start_extract_folder_worker(tasks, dest_folder)

    def _collect_folder_entries(self, folder_path: str, version):
        prefix = folder_path.rstrip("/") + "/"
        chosen: dict = {}

        for entry in self.entries:
            if entry.is_dir or entry.flag == "-" or not entry.path.startswith(prefix):
                continue

            if isinstance(version, int):
                if entry.version is None or entry.version > version:
                    continue
            elif isinstance(version, str):
                if entry.datetime > version:
                    continue

            old = chosen.get(entry.path)

            if old is None:
                chosen[entry.path] = entry
            elif (entry.version or 0, entry.datetime) > (
                old.version or 0,
                old.datetime,
            ):
                chosen[entry.path] = entry

        return list(chosen.values())

    def _on_extract_done(self, result):
        kind = result.get("kind")

                                                                          
        if result.get("cancelled"):
            if kind == "extract_file":
                output = result.get("output", "")
                if output:
                    self.log_output(output)
            elif kind == "extract_folder_batch":
                log = result.get("log", "")
                if log:
                    self.log_output(log)
            elif kind == "extract_folder":
                error_logs = result.get("error_logs", [])
                if error_logs:
                    self.log_output("\n\n".join(error_logs))

            total = result.get("total")
            if total is None:
                total = 1 if kind == "extract_file" else 0

            cancelled_text = tr("status.extract_cancelled")

            self.statusBar().showMessage(cancelled_text)
            self._ui_extract_finished(False, int(total), cancelled_text)
            return

                                                                               
        if kind == "extract_file":
            output = result.get("output", "")
            if output:
                self.log_output(output)

            if result.get("success"):
                dest = result.get("dest", "")

                if dest:
                    parent = Path(dest).parent
                    if parent.is_dir() and not is_temp_path(parent):
                        self.last_extract_dir = parent
                        self._remember_extract_dir()

                self.statusBar().showMessage(tr("status.extracted_to", dest=dest))
                self._ui_extract_finished(True, 1, dest or "")
            else:
                error_text = tr("status.extract_file_error")

                self.statusBar().showMessage(error_text)
                self._ui_extract_finished(False, 1, error_text)
                QMessageBox.critical(
                    self,
                    tr("extract.dialog.extract_error_title"),
                    (output or "")[:5000],
                )

        elif kind == "extract_folder_batch":
            log = result.get("log", "")
            if log:
                self.log_output(log)

            dest = result.get("dest_folder", "")

            if result.get("ok"):
                if dest:
                    dp = Path(dest)
                    if dp.is_dir():
                        self.last_extract_dir = dp.parent if dp.parent != dp else dp
                self._remember_extract_dir()

                self.statusBar().showMessage(
                    tr("status.extract_folder_done", dest=dest)
                )
                self._ui_extract_finished(True, 0, dest or "")
            else:
                error_text = tr("status.extract_folder_error")

                self.statusBar().showMessage(error_text)
                self._ui_extract_finished(False, 0, error_text)
                QMessageBox.warning(
                    self,
                    tr("extract.dialog.extract_folder_error_title"),
                    (log or tr("extract.dialog.extract_folder_error_fallback"))[:5000],
                )

        elif kind == "extract_folder":
            ok = result.get("ok", 0)
            total = result.get("total", 0)
            dest = result.get("dest_folder", "")
            errors = result.get("errors", [])
            error_logs = result.get("error_logs", [])

            if dest:
                dp = Path(dest)
                if dp.is_dir():
                    self.last_extract_dir = dp.parent if dp.parent != dp else dp

            if ok == total and self.last_extract_dir:
                self._remember_extract_dir()

            if error_logs:
                self.log_output("\n\n".join(error_logs))

            if ok == total:
                self.statusBar().showMessage(
                    tr("status.extract_folder_done", dest=dest)
                )
                self._ui_extract_finished(True, total, dest or "")
            else:
                self.statusBar().showMessage(
                    tr("status.extract_folder_with_errors")
                )

                msg = tr(
                    "extract.dialog.extract_with_errors_text",
                    ok=ok,
                    total=total,
                    folder=dest,
                )

                if errors:
                    msg += tr("extract.dialog.errors_label") + "\n"
                    msg += "\n".join(errors[:20])

                    if len(errors) > 20:
                        msg += "\n" + tr(
                            "extract.dialog.extract_with_errors_more",
                            count=len(errors) - 20,
                        )

                self._ui_extract_finished(
                    False,
                    total,
                    tr("status.extract_folder_with_errors"),
                )
                QMessageBox.warning(
                    self,
                    tr("extract.dialog.extract_with_errors_title"),
                    msg[:5000],
                )

                                                                            
    def _on_salvage_archive(self):
        pass






        if self.mode != "archive" or self.archive_path is None:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return

        from ui.salvage_dialog import SalvageOptionsDialog

        dlg = SalvageOptionsDialog(
            archive_name=Path(self.archive_path).name, parent=self
        )
        if dlg.exec() != SalvageOptionsDialog.Accepted:
            return

        dest = QFileDialog.getExistingDirectory(
            self,
            tr("salvage.choose_folder_title"),
            str(self._initial_extract_dir()),
        )
        if not dest:
            return

        self._start_salvage_worker(dest, dlg.ram_gb())

    def _on_salvage_done(self, result):
        pass




        log = result.get("log", "")
        if log:
            self.log_output(log)

        dest = result.get("dest_folder", "")

        if result.get("cancelled"):
            cancelled_text = tr("status.extract_cancelled")
            self.statusBar().showMessage(cancelled_text)
            self._ui_extract_finished(False, 0, cancelled_text)
            return

        if result.get("ok"):
            if dest:
                dp = Path(dest)
                if dp.is_dir():
                    self.last_extract_dir = dp.parent if dp.parent != dp else dp
                    self._remember_extract_dir()

            self.statusBar().showMessage(tr("salvage.status_done", dest=dest))
            self._ui_extract_finished(True, 0, dest or "")
            QMessageBox.information(
                self,
                tr("salvage.done_title"),
                tr("salvage.done_text", dest=dest),
            )
        else:
            self.statusBar().showMessage(tr("salvage.status_partial"))
            self._ui_extract_finished(False, 0, tr("salvage.status_partial"))

            msg = tr("salvage.partial_text", dest=dest)
            tail = (log or "").strip().splitlines()[-15:]
            if tail:
                msg += "\n\n" + "\n".join(tail)

            QMessageBox.warning(
                self,
                tr("salvage.partial_title"),
                msg[:5000],
            )

    def _initial_extract_dir(self):
        last = getattr(self, "last_extract_dir", None)

        if last and Path(last).is_dir():
            return Path(last)

        if self.archive_path and Path(self.archive_path).parent.is_dir():
            return Path(self.archive_path).parent

        if self.fs_path and self.fs_path.is_dir():
            return self.fs_path

        return Path.home()
