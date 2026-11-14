



























































































































































from __future__ import annotations

import os
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox

from core.parser import parse_create_stats, parse_info_stat
from core.password_store import set_password
from core.incomplete_archive import incomplete_archive_action
from core.tasks import (
    ACTION_TEST,
    ACTION_CROP,
    ACTION_CONSOLIDATE,
    ACTION_SFX,
    ACTION_INFO,
    ACTION_PASSWORD,
    ACTION_CHECKPASSWORD,
    CONTAINER_NAME,
    ContainerLockBusy,
    JOB_FIELDS,
    add_job,
    add_work,
    container_path,
    empty_container,
    find_job,
    find_work,
    job_to_runnable_settings,
    load_container,
    scheduler_task_name,
    update_container,
    update_job,
    update_job_meta,
    update_work,
)

                                                                    
                                                                  
                                                                  
from core.archive_naming import default_dest as _default_dest
from core.archive_naming import has_non_latin as _has_non_latin
from core.archive_naming import make_latin_name as _make_latin_name

                                                          
                                                                     
                                                                
                                        
from core import archive_index
from core import index_refresh

                                                                 
                                                                 
                                      
from core.headless import _build_log_header, _write_task_log

                                                                   
                                                               
                                           
from core.zpaq_cli import looks_like_busy_error

from ui.archive_check_dialog import ArchiveCheckDialog
from ui.archive_create_dialog import ArchiveCreateDialog
from ui.archive_done_dialog import ArchiveDoneDialog
from ui.archive_info_dialog import ArchiveInfoDialog
from ui.archive_progress_dialog import ArchiveProgressDialog
from ui.archive_work_dialog import ArchiveWorkDialog
from ui.extract_progress_dialog import ExtractProgressDialog
from ui.i18n import tr
from ui.test_modes import mode_label as test_mode_label
from ui.qt_compat import (
    K_FS,
    K_FS_ARC,
    K_FS_DIR,
    K_FS_FILE,
    K_FS_UNI_ARC,
    KIND_ROLE,
    PASSWORD_ECHO,
    TCOL,
    USER_ROLE,
    YES_BUTTON,
    YES_NO_BUTTONS,
    multipart_pattern,
)
from ui.test_progress_dialog import TestProgressDialog
from workers import (
    ExtractFolderBatchWorker,
    Par2CreateWorker,
    ScheduleCreateWorker,
    StreamingListWorker,
    ZpaqWorker,
)

_TEST_LOG_LIMIT = 20000
_TEST_TAIL = 2000
_CREATE_LOG_LIMIT = 20000

                                                                   
                                                              
_WORK_FIELDS = (
    "sources",
    "dest",
    "only_masks",
    "not_masks",
    "comment",
)


def offer_latin_rename(path: str, parent):
    pass













    if not path:
        return path
    if "?" in str(path):
                                                                 
                                               
        return path
    if not _has_non_latin(Path(path).stem):
        return path
    new_path = _make_latin_name(path)
    ans = QMessageBox.question(
        parent,
        tr("create.nonlatin_title"),
        tr("open.nonlatin_offer_text", old=Path(path).name, new=Path(new_path).name),
        YES_NO_BUTTONS,
    )
    if ans != YES_BUTTON:
        return None
    try:
        os.rename(path, new_path)
    except OSError as exc:
        QMessageBox.warning(
            parent,
            tr("create.nonlatin_title"),
            tr("open.nonlatin_rename_failed", error=str(exc)),
        )
        return None
    return new_path


def _fmt_time_hms(t: str) -> str:
    t = (t or "").strip()
    if not t:
        return ""
    parts = t.split(":")
    if len(parts) == 2:
        t += ":00"
    return t


def _esc(value: object) -> str:
    return str(value).replace("{", "{{").replace("}", "}}")


class ArchiveActionsMixin:
    pass

                                                                          

    def _tasks_dir(self):
        pass






        page = getattr(self, "backup_page", None)
        if page is not None:
            getter = getattr(page, "tasks_dir", None)
            if callable(getter):
                try:
                    return getter()
                except Exception:
                    pass
        cfg = getattr(self, "_cfg", None)
        if cfg is None:
            return None
        try:
            value = getattr(cfg, "tasks_dir", None)
        except Exception:
            return None
        return str(value) if value else None

    def _load_container(self):
        pass
        folder = self._tasks_dir()
        if not folder:
            return None, None
        path = container_path(folder)
        try:
            return load_container(path), path
        except Exception:
            return None, None

    def _show_container_busy(self, path) -> None:
        pass







        try:
            QMessageBox.information(
                self,
                tr("container.lock_busy_title"),
                tr("container.lock_busy_text", path=str(path)),
            )
        except Exception:
            pass

    def _show_container_save_error(self, path, exc) -> None:
        pass





        try:
            QMessageBox.warning(
                self,
                tr("task.save_title"),
                tr("backup.save_error", error=str(exc)),
            )
        except Exception:
            pass

                                                                        

    def _offer_nonlatin_rename(self, path: str):
        return offer_latin_rename(path, self)

    def _enter_archive(self, path):
        if not path:
            return
        path = str(Path(path))
        path = self._offer_nonlatin_rename(path)
        if not path:
            return

        if str(path).lower().endswith((".zip", ".7z", ".rar")):
            if not self.seven_zip_available:
                QMessageBox.warning(
                    self, tr("zpaq.not_found_title"), tr("zpaq.seven_zip_not_found_text")
                )
                return
        else:
            if not self.zpaq_available:
                QMessageBox.warning(
                    self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
                )
                return

        try:
            self.tree.reveal_archive(path)
        except Exception:
            pass
        self._load_archive_list(path, make_active=True, inner="")

    def _on_set_password(self):
        if self.archive_path is None:
            self.statusBar().showMessage(tr("status.archive_password_first"))
            return
        pw, ok = QInputDialog.getText(
            self,
            tr("dialog.password.set_title"),
            tr("dialog.password.set_text", name=Path(self.archive_path).name),
            PASSWORD_ECHO,
            self.password or "",
        )
        if not ok:
            return
        self._cache(self.archive_path)["password"] = pw or None
        set_password(self.archive_path, pw or None)
        self.password = pw or None
        self._load_archive_list(
            self.archive_path, make_active=True, inner=self.archive_inner
        )

                                                                             

    def _open_info_dialog(self, path: str) -> None:
        c = self._cache(path)
        dlg = ArchiveInfoDialog(
            path,
            c.get("summary"),
            c.get("versions"),
            bool(c.get("password")),
            parent=self,
        )
        self._start_dedup_worker(path, dlg)
        dlg.exec()

    def _start_dedup_worker(self, path: str, dlg) -> None:
        pass


















        try:
            pw = self._cache(path).get("password")
            cmd = [self.zpaq_bin, "i", str(path), "-stat"]
            if pw:
                cmd += ["-key", pw]
            worker = ZpaqWorker("info_stat", cmd, {"path": str(path)})
            worker.result.connect(
                lambda res, d=dlg: self._on_dedup_stats(d, res)
            )
            worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
            self._workers.append(worker)
            worker.start()
        except Exception:
            pass

    def _on_dedup_stats(self, dlg, result: dict) -> None:
        pass
        try:
            if not result or result.get("rc", 1) != 0:
                return
            stat = parse_info_stat(result.get("output", "") or "")
            if not stat:
                return
            dlg.set_dedup_stats(stat.get("uncompressed"))
        except Exception:
            pass

    def _on_archive_info(self):
        if self.archive_path is None:
            self.statusBar().showMessage(tr("status.archive_password_first"))
            return

        c = self._cache(self.archive_path)
        if c.get("info_loaded"):
            self._open_info_dialog(self.archive_path)
            return

        self._pending_info_path = self.archive_path
        self.statusBar().showMessage(tr("status.archive_info_requested"))
        self._load_info(self.archive_path)

                                                                    

    def _resolve_sync_sources(self, sources, job_context, archive_path) -> list:
        pass










        srcs = [str(s) for s in (sources or []) if str(s).strip()]
        if srcs:
            return srcs
        if job_context:
            try:
                container, _path = self._load_container()
                if container is not None:
                    found = find_job(
                        container, str(job_context.get("job_id") or "")
                    )
                    if found is not None:
                        work, _job = found
                        srcs = [
                            str(s)
                            for s in (work.get("sources") or [])
                            if str(s).strip()
                        ]
            except Exception:
                srcs = []
        if srcs:
            return srcs
        start = ""
        try:
            if archive_path:
                start = str(Path(archive_path).parent)
        except Exception:
            start = ""
        folder = QFileDialog.getExistingDirectory(
            self, tr("sync.choose_folder"), start
        )
        return [folder] if folder else []

    def _on_test_archive(
        self,
        path=None,
        mode="full",
        from_create=False,
        job_context=None,
        password=None,
        sources=None,
    ):
        pass

























        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

                                                                       
                                                                      
                                                                         
                                                                         
                                                                         
                      
        if str(mode) == "par2":
            self._start_par2_verify(arc, job_context=job_context)
            return

        arc = self._offer_nonlatin_rename(str(arc))
        if not arc:
            return
        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

        if not from_create:
            self._create_report = None

        arc = str(arc)

                                                                     
                                                                     
                                                                     
                                                  
        if password:
            pw = password
            try:
                self._cache(arc)["password"] = pw
            except Exception:
                pass
        else:
            pw = self._cache(arc).get("password")

        cmd = [self.zpaq_bin, "t", arc]
        tmp = None
        if mode == "sync":
                                                                       
                                                                 
                                                                  
                                          
            srcs = self._resolve_sync_sources(sources, job_context, arc)
            if not srcs:
                self.statusBar().showMessage(tr("sync.no_sources"))
                return
            cmd = [self.zpaq_bin, "sync", arc] + srcs
        elif mode == "verify_fs":
                                                                       
            cmd = [self.zpaq_bin, "v", arc]
        elif mode == "checksum":
            cmd += ["-all", "-checksum"]
        elif mode == "verify":
            cmd += ["-verify"]
        elif mode == "paranoid":
            try:
                tmp = tempfile.mkdtemp(prefix="rizpaq_test_")
            except OSError:
                tmp = None
            cmd += ["-verify", "-paranoid"]
            if tmp:
                cmd += ["-to", tmp]
        if pw:
            cmd += ["-key", pw]

        self.log_command(cmd)

        dlg = TestProgressDialog(
            Path(arc).name, test_mode_label(mode), parent=self
        )
        self._test_progress_dialog = dlg
        try:
            dlg.cancelRequested.connect(self._cancel_long_operations)
        except Exception:
            pass

        worker = ZpaqWorker(
            "test",
            cmd,
            {
                "path": arc,
                "tmp": tmp,
                "from_create": from_create,
                                                                    
                                                                
                "job_context": dict(job_context) if job_context else None,
                                                                    
                                                                 
                "mode": mode,
            },
        )
        worker.result.connect(self._on_test_result)
        try:
            worker.percent.connect(dlg.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(dlg.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(dlg.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_test_result(self, result):
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        tmp = ctx.get("tmp")
        from_create = bool(ctx.get("from_create"))
        cancelled = bool(result.get("cancelled"))
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

        if tmp:
            try:
                shutil.rmtree(tmp, ignore_errors=True)
            except Exception:
                pass

                                                                       
                                                                   
                                                                   
         
                                                                      
                                                                     
                                                    
        if job_context and not cancelled:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output)

        if output:
            if len(output) > _TEST_LOG_LIMIT:
                self.log_output("…\n" + output[-_TEST_LOG_LIMIT:])
            else:
                self.log_output(output)

        dlg = getattr(self, "_test_progress_dialog", None)
        self._test_progress_dialog = None

        if dlg is not None:
            if cancelled:
                dlg.finish(False, tr("status.extract_cancelled"))
                dlg.accept()
            else:
                dlg.finish(rc == 0, name)
                if rc == 0 or from_create:
                    dlg.accept()

        if from_create and getattr(self, "_create_report", None):
            self._create_report["test_rc"] = rc
            self._request_create_report()
            return

        if cancelled:
            self.statusBar().showMessage(tr("status.cancel_requested"))
            return

        if str(ctx.get("mode") or "") == "sync":
            self._on_sync_done(rc, output, name)
            return

        if rc == 0:
            self.statusBar().showMessage(tr("test.ok", name=name))
            QMessageBox.information(self, tr("test.title"), tr("test.ok", name=name))
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("test.fail", name=name))
            QMessageBox.warning(
                self, tr("test.title"), tr("test.fail", name=name) + "\n\n" + tail
            )

    def _on_sync_done(self, rc: int, output: str, name: str) -> None:
        pass









        if rc == 0:
            self.statusBar().showMessage(tr("sync.ok", name=name))
            QMessageBox.information(
                self, tr("sync.title"), tr("sync.ok", name=name)
            )
            return
        tail = output.strip()[-_TEST_TAIL:]
        if rc == 2:
            self.statusBar().showMessage(tr("sync.diff", name=name))
            QMessageBox.warning(
                self,
                tr("sync.title"),
                tr("sync.diff", name=name) + "\n\n" + tail,
            )
            return
        self.statusBar().showMessage(tr("sync.fail", name=name))
        QMessageBox.warning(
            self,
            tr("sync.title"),
            tr("sync.fail", name=name) + "\n\n" + tail,
        )

                                                                              

    def _run_crop(self, path: str, job_context: dict):
        pass





        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

                                             
        ans = QMessageBox.question(
            self,
            tr("crop.dialog_title"),
            tr("crop.confirm_text", name=Path(arc).name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        cmd = [self.zpaq_bin, "crop", arc, "-kill", "-to", arc]

        self.log_command(cmd)

        worker = ZpaqWorker(
            "crop",
            cmd,
            {
                "path": arc,
                "from_create": False,
                "job_context": dict(job_context) if job_context else None,
            },
        )
        worker.result.connect(self._on_crop_result)
        try:
            worker.percent.connect(self._crop_progress.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(self._crop_progress.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._crop_progress.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_crop_result(self, result):
        pass
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

        if job_context:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output
            )

        if output:
            self.log_output(output)

        if rc == 0:
            self.statusBar().showMessage(tr("crop.ok", name=name))
            QMessageBox.information(
                self, tr("crop.title"), tr("crop.ok", name=name)
            )
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("crop.fail", name=name))
            QMessageBox.warning(
                self,
                tr("crop.title"),
                tr("crop.fail", name=name) + "\n\n" + tail,
            )

                                                                                          

    def _run_consolidate(self, path: str, job_context: dict):
        pass






        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

                                                       
        ans = QMessageBox.question(
            self,
            tr("consolidate.dialog_title"),
            tr("consolidate.confirm_text", name=Path(arc).name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        cmd = [self.zpaq_bin, "consolidate", arc, "-to", arc]

        self.log_command(cmd)

        worker = ZpaqWorker(
            "consolidate",
            cmd,
            {
                "path": arc,
                "from_create": False,
                "job_context": dict(job_context) if job_context else None,
            },
        )
        worker.result.connect(self._on_consolidate_result)
        try:
            worker.percent.connect(self._consolidate_progress.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(self._consolidate_progress.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._consolidate_progress.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_consolidate_result(self, result):
        pass
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

        if job_context:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output
            )

        if output:
            self.log_output(output)

        if rc == 0:
            self.statusBar().showMessage(tr("consolidate.ok", name=name))
            QMessageBox.information(
                self, tr("consolidate.title"), tr("consolidate.ok", name=name)
            )
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("consolidate.fail", name=name))
            QMessageBox.warning(
                self,
                tr("consolidate.title"),
                tr("consolidate.fail", name=name) + "\n\n" + tail,
            )

                                                                        

    def _run_sfx(self, path: str, job_context: dict):
        pass






        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

        sfx_dest = str(Path(arc).with_suffix(".exe"))

                                                     
        ans = QMessageBox.question(
            self,
            tr("sfx.dialog_title"),
            tr("sfx.confirm_text", name=Path(arc).name, sfx=Path(sfx_dest).name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        cmd = [self.zpaq_bin, "sfx", arc, sfx_dest]

        self.log_command(cmd)

        worker = ZpaqWorker(
            "sfx",
            cmd,
            {
                "path": arc,
                "from_create": False,
                "job_context": dict(job_context) if job_context else None,
            },
        )
        worker.result.connect(self._on_sfx_result)
        try:
            worker.percent.connect(self._sfx_progress.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(self._sfx_progress.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._sfx_progress.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_sfx_result(self, result):
        pass
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

        if job_context:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output
            )

        if output:
            self.log_output(output)

        if rc == 0:
            self.statusBar().showMessage(tr("sfx.ok", name=name))
            QMessageBox.information(
                self, tr("sfx.title"), tr("sfx.ok", name=name)
            )
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("sfx.fail", name=name))
            QMessageBox.warning(
                self,
                tr("sfx.title"),
                tr("sfx.fail", name=name) + "\n\n" + tail,
            )

                                                                                 

    def _run_info(self, path: str, job_context: dict):
        pass




        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

        cmd = [self.zpaq_bin, "i", arc, "-comment"]

        self.log_command(cmd)

        worker = ZpaqWorker(
            "info",
            cmd,
            {
                "path": arc,
                "from_create": False,
                "job_context": dict(job_context) if job_context else None,
            },
        )
        worker.result.connect(self._on_info_result)
        try:
            worker.percent.connect(self._info_progress.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(self._info_progress.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._info_progress.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_info_result(self, result):
        pass
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

        if job_context:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output
            )

        if output:
            self.log_output(output)

        if rc == 0:
            self.statusBar().showMessage(tr("info.ok", name=name))
            QMessageBox.information(
                self, tr("info.title"), tr("info.ok", name=name)
            )
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("info.fail", name=name))
            QMessageBox.warning(
                self,
                tr("info.title"),
                tr("info.fail", name=name) + "\n\n" + tail,
            )

                                                                                       

    def _run_password(self, path: str, job_context: dict, settings: dict):
        pass




        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

        if "?" in arc:
                                                                         
                                                                        
                                                              
            QMessageBox.warning(
                self,
                tr("password.dialog_title"),
                tr("password.multipart_unsupported"),
            )
            return

        old_pw = str(settings.get("password") or "").strip()
        new_pw = str(settings.get("new_password") or "").strip()
        if not old_pw or not new_pw:
            QMessageBox.warning(
                self,
                tr("password.dialog_title"),
                tr("password.confirm_text_missing"),
            )
            return

                                                                    
                                                                     
        p = Path(arc)
        target = str(p.with_name(p.stem + ".new" + (p.suffix or ".zpaq")))

                                                                     
        ans = QMessageBox.question(
            self,
            tr("password.dialog_title"),
            tr("password.confirm_text", name=p.name, sfx=Path(target).name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        cmd = [
            self.zpaq_bin, "password", arc, target,
            "-key", old_pw, "-key2", new_pw, "-force",
        ]

        self.log_command(cmd)

        worker = ZpaqWorker(
            "password",
            cmd,
            {
                "path": arc,
                "target": target,
                "new_password": new_pw,
                "from_create": False,
                "job_context": dict(job_context) if job_context else None,
            },
        )
        worker.result.connect(self._on_password_result)
        try:
            worker.percent.connect(self._password_progress.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(self._password_progress.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._password_progress.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_password_result(self, result):
        pass
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        target = ctx.get("target", "")
        new_pw = str(ctx.get("new_password") or "")
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

                                                                    
                                                                    
                                                                   
        if target:
            if rc == 0:
                try:
                    os.replace(target, path)
                except OSError as exc:
                    rc = 1
                    output = (output or "") + (
                        "\nERROR: cannot replace the archive with the "
                        f"re-encrypted copy: {exc}\n"
                    )
                else:
                    try:
                        self._cache(path)["password"] = new_pw or None
                    except Exception:
                        pass
                                                                  
                                                                      
                                                  
                    try:
                        set_password(path, new_pw or None)
                    except Exception:
                        pass
                    try:
                        self._on_refresh()
                    except Exception:
                        pass
            else:
                try:
                    os.remove(target)
                except OSError:
                    pass

        if job_context:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output
            )

        if output:
            self.log_output(output)

        if rc == 0:
            self.statusBar().showMessage(tr("password.ok", name=name))
            QMessageBox.information(
                self, tr("password.title"), tr("password.ok", name=name)
            )
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("password.fail", name=name))
            QMessageBox.warning(
                self,
                tr("password.title"),
                tr("password.fail", name=name) + "\n\n" + tail,
            )

                                                                                               

    def _run_checkpassword(self, path: str, job_context: dict, settings: dict):
        pass




        arc = multipart_pattern(path or self.archive_path)
        if not arc:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        arc = str(arc)

        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

        pw = str(settings.get("password") or "").strip()
        if not pw:
            QMessageBox.warning(
                self,
                tr("checkpassword.dialog_title"),
                tr("checkpassword.confirm_text_missing"),
            )
            return

        cmd = [self.zpaq_bin, "checkpassword", arc, "-key", pw]

        self.log_command(cmd)

        worker = ZpaqWorker(
            "checkpassword",
            cmd,
            {
                "path": arc,
                "from_create": False,
                "job_context": dict(job_context) if job_context else None,
            },
        )
        worker.result.connect(self._on_checkpassword_result)
        try:
            worker.percent.connect(self._checkpassword_progress.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(self._checkpassword_progress.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._checkpassword_progress.append_output)
        except Exception:
            pass

        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_checkpassword_result(self, result):
        pass
        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        path = ctx.get("path", "")
        job_context = ctx.get("job_context")
        name = Path(path).name if path else ""

        if job_context:
            status = "ok" if rc == 0 else "error"
            self._update_job_meta_after_run(
                job_context, status, rc=rc, output=output
            )

        if output:
            self.log_output(output)

        if rc == 0:
            self.statusBar().showMessage(tr("checkpassword.ok", name=name))
            QMessageBox.information(
                self, tr("checkpassword.title"), tr("checkpassword.ok", name=name)
            )
        else:
            tail = output.strip()[-_TEST_TAIL:]
            self.statusBar().showMessage(tr("checkpassword.fail", name=name))
            QMessageBox.warning(
                self,
                tr("checkpassword.title"),
                tr("checkpassword.fail", name=name) + "\n\n" + tail,
            )

                                                               

    def _compute_changed_counts(self):
        pv = defaultdict(set)
        for e in self.entries:
            ver = getattr(e, "version", None)
            path = getattr(e, "path", None)
            if ver is not None and path:
                pv[path].add(ver)

        nums = sorted({v.number for v in self.versions})
        prev_of = {nums[i]: nums[i - 1] for i in range(1, len(nums))}
        changed = {n: 0 for n in nums}
        for path, vers in pv.items():
            for n in vers:
                prev = prev_of.get(n)
                if prev is not None and prev in vers:
                    changed[n] += 1
        return changed

    def _get_changed_counts(self):
        if getattr(self, "_changed_cache_arc", None) != self.archive_path:
            try:
                self._changed_counts = self._compute_changed_counts()
            except Exception:
                self._changed_counts = {}
            self._changed_cache_arc = self.archive_path
        return getattr(self, "_changed_counts", {})

    def _rebuild_unpack_menu(self):
        menu = self._unpack_ver_menu
        menu.clear()
        has_archive = (
            self.mode == "archive"
            and self.archive_path is not None
            and bool(self.versions)
        )
                                                                   
                                                                    
        has_salvage = (
            self.mode == "archive" and self.archive_path is not None
        )
        try:
            self._unpack_all_action.setEnabled(has_archive)
        except Exception:
            pass
        menu.setEnabled(has_archive or has_salvage)
        try:
            self._salvage_action.setEnabled(has_salvage)
        except Exception:
            pass
        if not has_archive:
            return

        changed_map = self._get_changed_counts()
        for v in sorted(self.versions, key=lambda x: x.number):
            label = f"v{v.number}"
            date = (getattr(v, "date", "") or "").strip()
            time = _fmt_time_hms(getattr(v, "time", ""))
            if date:
                label += f" · {date}"
            if time:
                label += f" {time}"
            added = getattr(v, "added", None)
            removed = getattr(v, "removed", None)
            changed = changed_map.get(v.number)
            counts = []
            if added is not None:
                counts.append(f"+{added}")
            if changed is not None:
                counts.append(f"~{changed}")
            if removed is not None:
                counts.append(f"−{removed}")
            if counts:
                label += " · " + " ".join(counts)
            a = menu.addAction(label)
            a.triggered.connect(
                lambda checked=False, n=v.number: self._on_unpack_version(n)
            )

    def _on_unpack_version(self, n):
        if self.mode != "archive" or self.archive_path is None:
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        dest = QFileDialog.getExistingDirectory(
            self, tr("extract.dialog.choose_folder_title")
        )
        if not dest:
            return
        self._start_extract_folder_batch_worker("", n, dest)

    def _on_unpack_all(self):
        if (
            self.mode != "archive"
            or self.archive_path is None
            or not self.versions
        ):
            self.statusBar().showMessage(tr("status.test_only_archive"))
            return
        base = QFileDialog.getExistingDirectory(
            self, tr("extract.dialog.choose_folder_title")
        )
        if not base:
            return
        self._unpack_queue = [
            (v.number, str(Path(base) / f"v{v.number}"))
            for v in sorted(self.versions, key=lambda x: x.number)
        ]
        self._unpack_base = base
        self._unpack_next()

    def _unpack_next(self):
        if not getattr(self, "_unpack_queue", None):
            return
        n, dest = self._unpack_queue.pop(0)
        try:
            Path(dest).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        worker = ExtractFolderBatchWorker(
            self.zpaq_bin, self.archive_path, self.password, "", n, dest
        )
                                                                      
                                                                       
                                                                   
                                                  
        worker.worker_started.connect(self._ui_folder_batch_started)
        worker.percent.connect(self._ui_folder_percent)
        try:
            worker.progress_info.connect(self._ui_extract_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(self._ui_extract_output)
        except Exception:
            pass
        worker.done.connect(self._on_unpack_step_done)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_unpack_step_done(self, result):
        ok = bool(result.get("ok"))
        if not ok:
            self._unpack_queue = []
            log = result.get("log", "") or ""
            self._ui_extract_finished(
                False, 0, log or tr("status.extract_folder_error")
            )
            QMessageBox.warning(
                self,
                tr("extract.dialog.extract_folder_error_title"),
                (log or tr("extract.dialog.extract_folder_error_fallback"))[:5000],
            )
            return
        if self._unpack_queue:
            self._unpack_next()
            return
        base = getattr(self, "_unpack_base", "")
        self._ui_extract_finished(True, 0, base)
        self.statusBar().showMessage(tr("status.unpack_all_done", dest=base))
        QMessageBox.information(
            self, tr("menu.unpack"), tr("status.unpack_all_done", dest=base)
        )

                                                                  

    def _selected_table_sources(self) -> list:
        tbl = getattr(self, "table", None)
        if tbl is None:
            return []
        paths = []
        try:
            rows = sorted({idx.row() for idx in tbl.selectedIndexes()})
            for r in rows:
                it = tbl.item(r, 0)
                if it is None:
                    continue
                kind = it.data(KIND_ROLE)
                if kind not in (K_FS_DIR, K_FS_FILE, K_FS_ARC):
                    continue
                payload = it.data(USER_ROLE)
                if payload:
                    paths.append(str(payload))
        except Exception:
            return []
        return paths

    def _selected_tree_sources(self) -> list:
        pass







        tree = getattr(self, "tree", None)
        if tree is None:
            return []
        try:
            item = tree.currentItem()
        except Exception:
            return []
        if item is None:
            return []
        try:
            kind = item.data(TCOL, KIND_ROLE)
            payload = item.data(TCOL, USER_ROLE)
        except Exception:
            return []
        if kind in (K_FS, K_FS_ARC, K_FS_UNI_ARC) and payload:
            return [str(payload)]
        return []

    def _on_create_archive_current(self):
        pass







        if self.mode == "fs":
            sel = self._selected_table_sources()
            if sel:
                self._start_create_archive(sel)
                return

        tree_sel = self._selected_tree_sources()
        if tree_sel:
            self._start_create_archive(tree_sel)
            return

        sources = []
        if self.mode == "fs" and self.fs_path:
            sources = [str(self.fs_path)]
        elif self.archive_path:
            sources = [str(Path(self.archive_path).parent)]
        if not sources:
            self.statusBar().showMessage(tr("create.no_source"))
            return
        self._start_create_archive(sources)

    def _on_create_archive_paths(self, paths):
        if not paths:
            self.statusBar().showMessage(tr("create.no_source"))
            return
        self._start_create_archive([str(p) for p in paths])

                                                                     

    def _copy_archive_to_folder(self, dest: str, copy_dir: str) -> str:
        try:
            target_dir = Path(copy_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return str(exc)
        src = Path(dest)
        if "?" in src.name:
            files = sorted(src.parent.glob(src.name))
        else:
            files = [src] if src.exists() else []
        if not files:
            return "archive file not found"
        errors = []
        for f in files:
            try:
                dst = target_dir / f.name
                if dst.resolve() == f.resolve():
                    continue
                shutil.copy2(str(f), str(dst))
            except Exception as exc:
                errors.append(f"{f.name}: {exc}")
        return "; ".join(errors)

                                                                       

    def _run_job(self, work_id: str, job_id: str):
        pass




















        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return

        container, _path = self._load_container()
        if container is None:
            QMessageBox.warning(
                self, tr("task.run_title"), tr("task.no_tasks_dir")
            )
            return

        found = find_job(container, str(job_id))
        if found is None:
            QMessageBox.warning(
                self, tr("task.run_title"), tr("task.job_not_found")
            )
            return

        work, job = found
        settings = job_to_runnable_settings(work, job)

        if not settings.get("dest"):
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.dest_required")
            )
            return

        action = str(settings.get("action") or "backup").strip().lower()
        job_context = {"work_id": str(work_id), "job_id": str(job_id)}

        if action == ACTION_TEST:
                                                                    
                                                                  
                                                                 
                                                               
                             
            self._on_test_archive(
                path=settings.get("dest"),
                mode=str(settings.get("test_mode") or "full"),
                from_create=False,
                job_context=job_context,
                password=settings.get("password"),
            )
            return

        if action == ACTION_CROP:
                                                                   
                                                                     
            self._run_crop(
                path=settings.get("dest"),
                job_context=job_context,
            )
            return

        if action == ACTION_CONSOLIDATE:
                                                                         
            self._run_consolidate(
                path=settings.get("dest"),
                job_context=job_context,
            )
            return

        if action == ACTION_SFX:
                                                                    
            self._run_sfx(
                path=settings.get("dest"),
                job_context=job_context,
            )
            return

        if action == ACTION_INFO:
                                                            
            self._run_info(
                path=settings.get("dest"),
                job_context=job_context,
            )
            return

        if action == ACTION_PASSWORD:
                                                           
            self._run_password(
                path=settings.get("dest"),
                job_context=job_context,
                settings=settings,
            )
            return

        if action == ACTION_CHECKPASSWORD:
                                                                   
            self._run_checkpassword(
                path=settings.get("dest"),
                job_context=job_context,
                settings=settings,
            )
            return

                                       
        if not settings.get("sources"):
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.no_source")
            )
            return

        self._run_create_from_settings(settings, job_context=job_context)

                                                                               

    def _edit_job(self, work_id: str, job_id: str):
        pass

























        container, path = self._load_container()
        if container is None:
            QMessageBox.warning(
                self, tr("task.edit_title"), tr("task.no_tasks_dir")
            )
            return

        found = find_job(container, str(job_id))
        if found is None:
            QMessageBox.warning(
                self, tr("task.edit_title"), tr("task.job_not_found")
            )
            return

        work, job = found
        settings = job_to_runnable_settings(work, job)
        action = str(settings.get("action") or "backup").strip().lower()

        if action == ACTION_TEST:
            dlg = ArchiveCheckDialog(
                work,
                parent=self,
                initial_settings=settings,
                edit_work_id=str(work_id),
                edit_job_id=str(job_id),
            )
            if dlg.exec() != QDialog.Accepted:
                return
                                                                 
                                                              
            return

                                    
        sources = settings.get("sources") or []
        if not sources:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.no_source")
            )
            return

        default_dest = settings.get("dest") or _default_dest(sources[0])
        if _has_non_latin(Path(default_dest).stem):
            default_dest = _make_latin_name(default_dest, avoid_existing=False)

        dlg = ArchiveCreateDialog(
            sources,
            default_dest,
            parent=self,
            initial_settings=settings,
            edit_work_id=str(work_id),
            edit_job_id=str(job_id),
        )
        if dlg.exec() != QDialog.Accepted:
            return

        new_settings = dlg.result_settings()
        if not new_settings or not new_settings.get("dest"):
            return

                                                                   
                 
        work_fields, job_fields = self._split_settings_work_job(new_settings)

        result = {"error": None}

        def mutate(c):
            if update_work(c, str(work_id), **work_fields) is None:
                result["error"] = "work_not_found"
                return
            if update_job(c, str(job_id), **job_fields) is None:
                result["error"] = "job_not_found"
                return

        try:
            update_container(path, mutate)
        except ContainerLockBusy:
            self._show_container_busy(path)
            return
        except Exception as exc:
            self._show_container_save_error(path, exc)
            return

        if result["error"]:
            QMessageBox.warning(
                self, tr("task.edit_title"), tr("task.job_not_found")
            )
            return

        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass

        self._run_create_from_settings(
            new_settings,
            job_context={"work_id": str(work_id), "job_id": str(job_id)},
        )

                                                                              

    def _edit_work(self, work_id: str):
        pass











        container, path = self._load_container()
        if container is None:
            QMessageBox.warning(
                self, tr("work.edit_title"), tr("task.no_tasks_dir")
            )
            return

        work = find_work(container, str(work_id))
        if work is None:
            QMessageBox.warning(
                self, tr("work.edit_title"), tr("task.job_not_found")
            )
            return

        dlg = ArchiveWorkDialog(work, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        settings = dlg.result_settings()
        if not settings:
            return

        self._save_edited_work(settings, str(work_id))

    def _save_edited_work(self, settings: dict, work_id: str) -> bool:
        pass




























        container, path = self._load_container()
        if container is None or path is None:
            QMessageBox.warning(
                self, tr("work.edit_title"), tr("task.no_tasks_dir")
            )
            return False

        work = find_work(container, str(work_id))
        if work is None:
            QMessageBox.warning(
                self, tr("work.edit_title"), tr("task.job_not_found")
            )
            return False

                                                                    
                                                                      
                            
        old_names = []
        for job in work.get("jobs") or []:
            nm = self._task_name_for(container, work_id, str(job.get("id") or ""))
            old_names.append((str(job.get("id") or ""), nm))

                                  
        fields = {
            "sources": list(settings.get("sources") or []),
            "dest": str(settings.get("dest") or ""),
            "comment": str(settings.get("comment") or ""),
            "only_masks": list(settings.get("only_masks") or []),
            "not_masks": list(settings.get("not_masks") or []),
        }
        wt = str(settings.get("work_title") or "").strip()
        if wt:
            fields["title"] = wt

                                                                      
        password_action = str(settings.get("password_action") or "keep").lower()
        if password_action == "set":
            fields["password"] = str(settings.get("password") or "")
        elif password_action == "clear":
            fields["password"] = ""                                       

        result = {"error": None, "new_names": {}}

        def mutate(c):
            if update_work(c, str(work_id), **fields) is None:
                result["error"] = "work_not_found"
                return
                                                               
                                                                  
                                    
            for job_id, _old in old_names:
                nm = self._task_name_for(c, work_id, job_id)
                result["new_names"][job_id] = nm

        try:
            update_container(path, mutate)
        except ContainerLockBusy:
            self._show_container_busy(path)
            return False
        except Exception as exc:
            self._show_container_save_error(path, exc)
            return False

        if result["error"]:
            QMessageBox.warning(
                self, tr("work.edit_title"), tr("task.job_not_found")
            )
            return False

                                                                    
                                                                    
                                              
        for job_id, old_name in old_names:
            if not old_name:
                continue
            new_name = result["new_names"].get(job_id, "")
            if new_name and new_name != old_name:
                try:
                    from core.scheduler import remove_scheduled_task_by_name
                    remove_scheduled_task_by_name(old_name)
                except Exception:
                    pass

        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass

        return True

                                                                                    

    def _on_add_job_to_work(self, work_id: str):
        pass














        container, path = self._load_container()
        if container is None:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("task.no_tasks_dir")
            )
            return

        work = find_work(container, str(work_id))
        if work is None:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("task.job_not_found")
            )
            return

        sources = list(work.get("sources") or [])
        if not sources:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.no_source")
            )
            return
        default_dest = work.get("dest") or _default_dest(sources[0])
        if _has_non_latin(Path(default_dest).stem):
            default_dest = _make_latin_name(default_dest, avoid_existing=False)

        initial = {
            "sources": sources,
            "dest": work.get("dest") or "",
            "comment": work.get("comment") or "",
            "only_masks": list(work.get("only_masks") or []),
            "not_masks": list(work.get("not_masks") or []),
            "level_key": "m2",
            "task_log_mode": "short",
                                                                  
                                               
            "work_title": work.get("title") or "",
        }

        dlg = ArchiveCreateDialog(
            sources,
            default_dest,
            parent=self,
            initial_settings=initial,
            add_to_work_id=str(work_id),
        )
        if dlg.exec() != QDialog.Accepted:
            return

        new_settings = dlg.result_settings()
        if not new_settings or not new_settings.get("dest"):
            return

        work_fields, job_fields = self._split_settings_work_job(new_settings)

        def mutate(c):
            update_work(c, str(work_id), **work_fields)
            add_job(c, str(work_id), job_fields)

        try:
            update_container(path, mutate)
        except ContainerLockBusy:
            self._show_container_busy(path)
            return
        except Exception as exc:
            self._show_container_save_error(path, exc)
            return

        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass

    def _on_add_check_to_work(self, work_id: str):
        pass


















        container, path = self._load_container()
        if container is None:
            QMessageBox.warning(
                self, tr("check.dialog_title"), tr("task.no_tasks_dir")
            )
            return

        work = find_work(container, str(work_id))
        if work is None:
            QMessageBox.warning(
                self, tr("check.dialog_title"), tr("task.job_not_found")
            )
            return

        if not work.get("dest"):
            QMessageBox.warning(
                self, tr("check.dialog_title"), tr("check.dest_missing")
            )
            return

        dlg = ArchiveCheckDialog(
            work,
            parent=self,
            add_to_work_id=str(work_id),
        )
        if dlg.exec() != QDialog.Accepted:
            return

                                                          
                                                                       
                                                                
                                                           
        _ = path                                                 

    def _on_add_check_par2_to_work(self, work_id: str):
        pass








        container, path = self._load_container()
        if container is None:
            QMessageBox.warning(
                self, tr("check.dialog_title"), tr("task.no_tasks_dir")
            )
            return

        work = find_work(container, str(work_id))
        if work is None:
            QMessageBox.warning(
                self, tr("check.dialog_title"), tr("task.job_not_found")
            )
            return

        if not work.get("dest"):
            QMessageBox.warning(
                self, tr("check.dialog_title"), tr("check.dest_missing")
            )
            return

        dlg = ArchiveCheckDialog(
            work,
            parent=self,
            initial_settings={"test_mode": "par2"},
            add_to_work_id=str(work_id),
        )
        if dlg.exec() != QDialog.Accepted:
            return

        _ = path

                                                                            

    def _split_settings_work_job(self, settings: dict) -> tuple:
        pass






























        password = settings.get("password")
        work_fields = {
            "sources": list(settings.get("sources") or []),
            "dest": settings.get("dest") or "",
            "only_masks": list(settings.get("only_masks") or []),
            "not_masks": list(settings.get("not_masks") or []),
            "comment": settings.get("comment") or "",
        }
        if password:
            work_fields["password"] = password

                                                                    
                                                            
                                                                
                                     
        if "work_title" in settings:
            wt = str(settings.get("work_title") or "").strip()
            if wt:
                work_fields["title"] = wt

        job_fields = {}
                                                                   
                                                                  
                                                                  
                                                                      
                                                                     
                           
         
                                                                     
                                                                      
                                                                
        for key in JOB_FIELDS:
            if key in settings:
                job_fields[key] = settings.get(key)

                                                                  
                                                                   
                                                   
        if "title" in settings:
            job_fields["title"] = settings.get("title")

        return work_fields, job_fields

                                                                               

    def _save_new_job(self, settings: dict, work_id=None) -> bool:
        pass































        folder = self._tasks_dir()
        if not folder:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("task.no_tasks_dir")
            )
            return False

        path = container_path(folder)

        work_fields, job_fields = self._split_settings_work_job(settings)

                                                               
                                                               
        result = {"work": None, "job": None, "error": None}

        def mutate(c):
            if work_id:
                work = find_work(c, str(work_id))
                if work is None:
                    result["error"] = "work_not_found"
                    return
                                                                 
                                                                   
                update_work(c, str(work_id), **work_fields)
                job = add_job(c, str(work_id), job_fields)
                if job is None:
                    result["error"] = "add_job_failed"
                    return
                                                                       
                result["work"] = find_work(c, str(work_id)) or work
                result["job"] = job
            else:
                                                                  
                                           
                wf = dict(work_fields)

                                                                    
                                                                  
                                                                    
                                                                      
                         
                 
                                                                         
                                                                         
                work_title = str(wf.pop("title", "") or "").strip()
                if not work_title:
                    dest = str(wf.get("dest") or "")
                    work_title = Path(dest).stem if dest else ""
                if not work_title:
                    srcs = wf.get("sources") or []
                    work_title = Path(srcs[0]).name if srcs else "Работа"

                password = wf.pop("password", None)
                work = add_work(
                    c,
                    title=work_title,
                    sources=wf.get("sources") or [],
                    dest=wf.get("dest") or "",
                    password=password,
                    only_masks=wf.get("only_masks") or [],
                    not_masks=wf.get("not_masks") or [],
                    comment=wf.get("comment") or "",
                )

                job = add_job(c, work["id"], job_fields)
                if job is None:
                    result["error"] = "add_job_failed"
                    return
                result["work"] = work
                result["job"] = job

        try:
            update_container(path, mutate)
        except ContainerLockBusy:
            self._show_container_busy(path)
            return False
        except Exception as exc:
            self._show_container_save_error(path, exc)
            return False

        if result["error"] == "work_not_found":
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("task.job_not_found")
            )
            return False
        if result["error"] == "add_job_failed":
            QMessageBox.warning(
                self, tr("task.save_title"),
                tr("task.save_error", error="add_job failed"),
            )
            return False

        work = result["work"]
        job = result["job"]
        if work is None or job is None:
            return False

                                                                    
                                                              
                                      
        self._apply_schedule(work, job, settings.get("schedule"))

        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass

        return True

    def _save_edited_job(self, settings: dict, work_id: str, job_id: str) -> bool:
        pass































        container, path = self._load_container()
        if container is None or path is None:
            QMessageBox.warning(
                self, tr("task.edit_title"), tr("task.no_tasks_dir")
            )
            return False

                                                                        
                                                                      
                                
        old_task_name = self._task_name_for(container, work_id, job_id)

        work_fields, job_fields = self._split_settings_work_job(settings)

        result = {"error": None, "new_task_name": ""}

        def mutate(c):
            if update_work(c, str(work_id), **work_fields) is None:
                result["error"] = "work_not_found"
                return
            if update_job(c, str(job_id), **job_fields) is None:
                result["error"] = "job_not_found"
                return
                                                                    
                                            
            result["new_task_name"] = self._task_name_for(c, work_id, job_id)

        try:
            update_container(path, mutate)
        except ContainerLockBusy:
            self._show_container_busy(path)
            return False
        except Exception as exc:
            self._show_container_save_error(path, exc)
            return False

        if result["error"]:
            QMessageBox.warning(
                self, tr("task.edit_title"), tr("task.job_not_found")
            )
            return False

                                                                      
                                                                   
                                                
        new_task_name = result["new_task_name"]
        if old_task_name and new_task_name and old_task_name != new_task_name:
            try:
                from core.scheduler import remove_scheduled_task_by_name
                remove_scheduled_task_by_name(old_task_name)
            except Exception:
                pass

                                                                     
                                                                       
                                                             
        schedule = settings.get("schedule")
        if schedule is not None:
                                                                        
                                                                
            container_now, _ = self._load_container()
            if container_now is not None:
                work = find_work(container_now, str(work_id))
                found = find_job(container_now, str(job_id))
                if work is not None and found is not None:
                    self._apply_schedule(work, found[1], schedule)

        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass

        return True

    @staticmethod
    def _task_name_for(container: dict, work_id: str, job_id: str) -> str:
        pass







        try:
            work = find_work(container, str(work_id))
            found = find_job(container, str(job_id))
            if work is None or found is None:
                return ""
            return scheduler_task_name(work, found[1])
        except Exception:
            return ""

    def _apply_schedule(self, work: dict, job: dict, schedule) -> None:
        pass






















        if schedule is None:
            return

        try:
            folder = self._tasks_dir()
            path = container_path(folder) if folder else None
        except Exception:
            path = None

        if path is None:
            return

        worker = ScheduleCreateWorker(path, work, job, schedule)
        worker.done.connect(
            lambda ok, err, s=schedule: self._on_schedule_apply_done(ok, err, s)
        )
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_schedule_apply_done(self, ok: bool, error_text: str, schedule) -> None:
        pass
















                                                                 
                                                                     
        if not schedule or not schedule.get("enabled"):
            return

        if ok:
            try:
                self.statusBar().showMessage(
                    tr("scheduler.scheduled_ok", path=CONTAINER_NAME)
                )
            except Exception:
                pass
            return

        try:
            text = tr("scheduler.scheduled_failed")
            if error_text:
                text = text + "\n\n" + error_text
            QMessageBox.warning(self, tr("scheduler.title"), text)
        except Exception:
            pass

                                                                              

    def _selected_backup_job(self):
        pass




        page = getattr(self, "backup_page", None)
        if page is None:
            return None
        getter = getattr(page, "selected_job", None)
        if not callable(getter):
            return None
        try:
            return getter()
        except Exception:
            return None

    def _on_run_task(self, *_args):
        pass






        selected = self._selected_backup_job()
        if selected is None:
            QMessageBox.information(
                self, tr("task.run_title"), tr("task.select_job_first")
            )
            return
        self._run_job(selected["work_id"], selected["job_id"])

    def _on_edit_task(self, *_args):
        pass




        selected = self._selected_backup_job()
        if selected is None:
            QMessageBox.information(
                self, tr("task.edit_title"), tr("task.select_job_first")
            )
            return
        self._edit_job(selected["work_id"], selected["job_id"])

                                                                                 

    def _run_create_from_settings(self, settings: dict, job_context=None):
        pass














        srcs = settings.get("sources") or []
        if not srcs:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.no_source")
            )
            return
        dest = settings["dest"]
        password = settings.get("password")

        if _has_non_latin(Path(dest).stem) and "?" not in dest:
            new_dest = _make_latin_name(dest)
            ans = QMessageBox.question(
                self,
                tr("create.nonlatin_title"),
                tr(
                    "create.nonlatin_create_text",
                    old=Path(dest).name,
                    new=Path(new_dest).name,
                ),
                YES_NO_BUTTONS,
            )
            if ans != YES_BUTTON:
                return
            dest = new_dest

        if settings.get("chunk") and "?" not in dest:
            p = Path(dest)
            dest = str(p.parent / (p.stem + "_????" + (p.suffix or ".zpaq")))

        is_update = "?" not in dest and Path(dest).exists()
        verify_mode = settings.get("verify") or ""

        cwd = None
        strip_base = settings.get("strip_base_path")
        if strip_base:
            cwd = strip_base
            srcs = ["*"]

        cmd = [self.zpaq_bin, "a", dest] + srcs
                                                                 
                                                                 
                                                                     
                                        
        cmd.append("-open")
        for flag in settings.get("level", []) or []:
            cmd.append(flag)
        if settings.get("hash"):
            cmd.append(settings["hash"])
        comment = settings.get("comment")
        if comment:
            cmd += ["-comment", comment]
        for m in settings.get("only_masks", []) or []:
            cmd += ["-only", m]
        for m in settings.get("not_masks", []) or []:
            cmd += ["-not", m]

        if settings.get("longpath"):
            if srcs and "*" not in srcs:
                cmd.append("-longpath")

        if settings.get("date"):
            cmd.append("-date")
        if settings.get("norecursion"):
            cmd.append("-norecursion")
        if settings.get("forcewindows"):
            cmd.append("-forcewindows")
        if settings.get("force_xls"):
            cmd.append("-xls")
        if settings.get("nochecksum"):
            cmd.append("-nochecksum")
        if settings.get("nodedup"):
            cmd.append("-nodedup")
        if settings.get("vss"):
            cmd.append("-vss")
        if settings.get("checkspace"):
            cmd += ["-checksize", settings["checkspace"]]
        if settings.get("noonedrive"):
            cmd.append("-noonedrive")
        if settings.get("ignore"):
            cmd.append("-ignore")
        if settings.get("errorlog"):
            cmd += ["-errorlog", settings["errorlog"]]
        if settings.get("shutdown"):
            cmd.append("-shutdown")
        if settings.get("sfx"):
            cmd += ["-sfx", settings["sfx"]]
        if settings.get("chunk"):
            cmd += ["-chunk", settings["chunk"]]
        if password:
            cmd += ["-key", password]

        self.log_command(cmd)

        archive_name = Path(dest).name
        progress_dlg = ArchiveProgressDialog(archive_name, parent=self)
        self._archive_progress_dialog = progress_dlg

        worker = ZpaqWorker(
            "create",
            cmd,
            {
                "dest": dest,
                "password": password,
                "test_after": bool(verify_mode),
                "test_mode": verify_mode,
                "is_update": is_update,
                "copy": settings.get("copy") or "",
                "params_rows": settings.get("params_rows") or [],
                "job_context": dict(job_context) if job_context else None,
                                                                    
                                                                     
                                                              
                                                                   
                                                                       
                "par2": {
                    "enabled": bool(settings.get("par2_enabled")),
                    "options": dict(settings.get("par2_options") or {}),
                },
            },
            cwd=cwd,
        )
        self._archive_create_worker = worker
        worker.result.connect(self._on_create_result)
        try:
            worker.percent.connect(progress_dlg.set_percent)
        except Exception:
            pass
        try:
            worker.progress_info.connect(progress_dlg.update_info)
        except Exception:
            pass
        try:
            worker.line_received.connect(progress_dlg.append_output)
        except Exception:
            pass

        progress_dlg.cancelRequested.connect(self._on_archive_progress_cancel)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        progress_dlg.show()
        worker.start()

    def _on_archive_progress_cancel(self):
        worker = getattr(self, "_archive_create_worker", None)
        if worker is not None:
            try:
                worker.cancel_request()
            except Exception:
                pass
                                                                     
                                                                     
                                                                 
                          
        par2_worker = getattr(self, "_par2_worker", None)
        if par2_worker is not None:
            try:
                par2_worker.cancel_request()
            except Exception:
                pass
        try:
            self.statusBar().showMessage(tr("status.cancel_requested"))
        except Exception:
            pass

    def _start_create_archive(self, sources):
        pass
        if not self.zpaq_available:
            QMessageBox.warning(
                self, tr("zpaq.not_found_title"), tr("zpaq.not_found_text")
            )
            return
        self._create_report = None
        default_dest = _default_dest(sources[0])
        if _has_non_latin(Path(default_dest).stem):
            default_dest = _make_latin_name(default_dest, avoid_existing=False)
        dlg = ArchiveCreateDialog(
            sources, default_dest, parent=self
        )
        if dlg.exec() != QDialog.Accepted:
            return
        settings = dlg.result_settings()
        if not settings or not settings.get("dest"):
            return
        self._run_create_from_settings(settings)

                                                                           

    def _request_create_report(self):
        pass



        rep = getattr(self, "_create_report", None)
        if not rep:
            return

        dest = rep.get("dest")
        if not dest:
            self._show_create_report()
            return

        c = self._cache(dest)
        if c.get("info_loaded"):
            self._show_create_report()
            return

        self._pending_create_report = rep
        self._create_report = None
        self._load_info(dest, quiet=True)

    def _show_create_report(self):
        pass
        rep = getattr(self, "_create_report", None) or getattr(
            self, "_pending_create_report", None
        )
        self._create_report = None
        self._pending_create_report = None
        if not rep:
            return

        dest = rep.get("dest")
        c = self._cache(dest) if dest else {}
        dlg = ArchiveDoneDialog(
            rep,
            c.get("summary"),
            c.get("versions") or [],
            parent=self,
        )
        dlg.exec()

    def _on_create_result(self, result):
        pass











        try:
            self._stop_busy()
        except Exception:
            pass

        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ctx = result.get("context", {})
        dest = ctx.get("dest", "")
        password = ctx.get("password")
        test_after = bool(ctx.get("test_after"))
        cancelled = bool(result.get("cancelled"))
        name = Path(dest).name if dest else ""
        job_context = ctx.get("job_context")

                                                                   
                                                                    
                                                                  
                           
        if cancelled:
            job_status = ""
        elif rc == 0:
            job_status = "ok"
        elif looks_like_busy_error(output):
            job_status = "busy"
        else:
            job_status = "error"

        if job_context and job_status:
            self._update_job_meta_after_run(
                job_context, job_status, rc=rc, output=output)

                                                                    
                                                                 
                                                             
                                                                  
                                                      
                                                                    
                                                       
        if job_status == "ok" and dest and "?" not in dest:
            self._refresh_index_after_create(dest, password)

        if output:
            if len(output) > _CREATE_LOG_LIMIT:
                self.log_output("…\n" + output[-_CREATE_LOG_LIMIT:])
            else:
                self.log_output(output)

        progress_dlg = getattr(self, "_archive_progress_dialog", None)
        self._archive_progress_dialog = None
        self._archive_create_worker = None

        if progress_dlg is not None:
            if cancelled:
                progress_dlg.finish(False, tr("status.cancel_requested"))
                progress_dlg.accept()
            elif rc != 0:
                progress_dlg.finish(rc == 0, name)
                                                                      
                                                                      
                                                                
                                                                       

        if cancelled:
            self.statusBar().showMessage(tr("status.cancel_requested"))
            self._handle_incomplete_archive(dest, bool(ctx.get("is_update")),
                                            output)
            self._cleanup_transcode_temp_dir()
            return

        if rc == 0:
            self.statusBar().showMessage(tr("create.done", name=name))
                                                                   
                                                                    
                                                                   
                                                                     
                                                                  
                                                                   
                                                                    
                                                     
             
                                                                    
                                                                      
                                                                      
            started_par2 = False
            try:
                started_par2 = self._start_par2_worker(
                    job_context, dest, ctx.get("par2"),
                    dialog=progress_dlg,
                )
            except Exception:
                started_par2 = False
            if progress_dlg is not None and not started_par2:
                progress_dlg.finish(True, name)
            try:
                self.tree.reveal_archive(dest)
            except Exception:
                pass
            try:
                self._on_refresh()
            except Exception:
                pass

            stats = parse_create_stats(output)
            self._create_report = {
                "dest": dest,
                "is_update": bool(ctx.get("is_update")),
                "ok": True,
                "params_rows": ctx.get("params_rows") or [],
                "test_rc": None,
                "stats": stats,
            }
            try:
                if password:
                    self._cache(dest)["password"] = password
                    set_password(dest, password)
            except Exception:
                pass

            copy_dir = ctx.get("copy") or ""
            if copy_dir:
                err = self._copy_archive_to_folder(dest, copy_dir)
                if err:
                    QMessageBox.warning(
                        self,
                        tr("create.copy_title"),
                        tr("create.copy_error", dir=copy_dir, error=_esc(err)),
                    )
                else:
                    self.statusBar().showMessage(tr("create.copy_done", dir=copy_dir))

            if test_after:
                                                                     
                                                                      
                                                                    
                                                                      
                                                            
                self._cleanup_transcode_temp_dir()
                self._on_test_archive(
                    dest, ctx.get("test_mode") or "full", from_create=True
                )
                return

            self._request_create_report()
            self._cleanup_transcode_temp_dir()
            return

                         
        if job_status == "busy":
                                                                   
                                                                
                                                                 
                                                        
            self._create_report = None
            self.statusBar().showMessage(tr("create.busy_status", name=name))
            QMessageBox.information(
                self,
                tr("create.busy_title"),
                tr("create.busy_text", name=name),
            )
            self._cleanup_transcode_temp_dir()
            return

                                         
        self._create_report = None
        tail = output.strip()[-_TEST_TAIL:]
        self.statusBar().showMessage(tr("create.error_title"))
        QMessageBox.warning(
            self, tr("create.error_title"), tail or tr("create.error_title")
        )
        self._handle_incomplete_archive(dest, bool(ctx.get("is_update")),
                                        output)
        self._cleanup_transcode_temp_dir()

    def _update_job_meta_after_run(self, job_context: dict, status: str,
                                   reason: str = None, rc=None, output=None):
        pass



























        try:
            container, path = self._load_container()
            if container is None or path is None:
                return
            job_id = str(job_context.get("job_id") or "")
            if not job_id:
                return

                                                                    
                                                                   
            work = job = None
            try:
                found = find_job(container, job_id)
                if found is not None:
                    work, job = found
            except Exception:
                pass

            def mutate(c):
                update_job_meta(c, job_id, status, reason=reason)

            try:
                update_container(path, mutate)
            except ContainerLockBusy:
                                                        
                pass

                                                                  
                                                                 
                                                                    
                                                                     
            self._write_run_log_record(
                str(path), job_id, status, rc, output)

                                                                     
                                                                        
                                                    
            if work is not None and job is not None:
                self._notify_job_result(work, job, status, reason)
        except Exception:
            pass

        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass

    def _notify_job_result(self, work: dict, job: dict, status: str,
                           reason=None) -> None:
        pass







        try:
            from core import config as config_mod
            from core import notify as notify_mod

            cfg = config_mod.load()
            notify_mod.notify_job_async(
                cfg,
                work,
                job,
                status,
                reason=str(reason or ""),
                archive=str((work or {}).get("dest") or ""),
            )
        except Exception:
            pass

    def _write_run_log_record(self, rzp_path: str, job_id: str, status: str,
                              rc, output):
        pass










        try:
            container = load_container(rzp_path)
            if container is None:
                return
            found = find_job(container, job_id)
            if found is None:
                return
            work, job = found
            mode = str(job.get("task_log_mode") or "short")
            if mode == "none":
                return
            rc_out = int(rc) if rc is not None else (
                0 if status == "ok" else 1)
            header = _build_log_header(rzp_path, work, job, rc_out)
            _write_task_log(
                rzp_path, header, output or "",
                mode=mode, rc=rc_out, busy=(status == "busy"),
            )
        except Exception:
            pass

                                                                        

    def _refresh_index_after_create(self, dest: str, password=None):
        pass









        zpaq = getattr(self, "zpaq_bin", None)
        if not zpaq:
            return
        stamp = index_refresh.file_stamp(dest)
        if stamp is None:
            return

        cmd = index_refresh.build_list_cmd(zpaq, dest, password)
        ctx = {
            "path": dest,
            "file_stamp": stamp,
            "index_refresh": True,
        }
        worker = StreamingListWorker(cmd, context=ctx)
        worker.result.connect(self._on_index_refresh_result)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _on_index_refresh_result(self, result: dict):
        pass






        try:
            ctx = result.get("context") or {}
            if not ctx.get("index_refresh"):
                return
            if result.get("rc") != 0:
                return
            entries = result.get("entries") or []
            if not entries:
                return
            path = ctx.get("path")
            stamp = ctx.get("file_stamp")
            if not path or not stamp:
                return
            current = index_refresh.file_stamp(path)
            if current != stamp:
                return
            archive_index.store_entries(
                str(path), stamp[0], stamp[1], entries)
        except Exception:
                                                          
            pass

    def _handle_incomplete_archive(self, dest, is_update, output):
        pass






        p = Path(dest)
        action = incomplete_archive_action(str(p), bool(is_update))
        if action["action"] == "none":
            return
        if action["action"] == "delete":
            try:
                p.unlink()
            except OSError as exc:
                QMessageBox.warning(
                    self, tr("create.error_title"),
                    tr("create.incomplete_delete_error",
                       name=p.name, error=str(exc)),
                )
                return
            self.statusBar().showMessage(
                tr("create.incomplete_deleted", name=p.name))
            return
        tail = (output or "").strip()[-2000:]
        QMessageBox.warning(
            self,
            tr("create.incomplete_title"),
            tr("create.incomplete_text") + ("\n\n" + tail if tail else ""),
        )

                                                                             

    def _extract_universal_dialog(self, path):
        dest = QFileDialog.getExistingDirectory(
            self, tr("extract.dialog.choose_folder_title")
        )
        if not dest:
            return

        from workers.universal_worker import UniversalExtractWorker

        worker = UniversalExtractWorker(
            self.seven_zip_bin, path, dest, self.password
        )

        dlg = ExtractProgressDialog(parent=self)
        dlg.begin_file(Path(path).name)

        worker.percent.connect(dlg.set_percent)
        worker.progress_info.connect(dlg.update_info)
        worker.line_received.connect(dlg.append_output)
        dlg.cancelRequested.connect(worker.cancel_request)

        def on_done(result):
            ok = result.get("ok")
            log = result.get("log", "")
            cancelled = result.get("cancelled")

            if cancelled:
                dlg.finish(False, tr("status.extract_cancelled"))
                dlg.accept()
                self.statusBar().showMessage(tr("status.cancel_requested"))
                return

            dlg.finish(ok, dest if ok else tr("status.extract_folder_error"))
            dlg.accept()

            if ok:
                self.statusBar().showMessage(tr("status.extract_folder_done", dest=dest))
                QMessageBox.information(
                    self, tr("menu.unpack"), tr("status.extract_folder_done", dest=dest)
                )
            else:
                self.statusBar().showMessage(tr("status.extract_folder_error"))
                QMessageBox.warning(
                    self,
                    tr("extract.dialog.extract_folder_error_title"),
                    (log or tr("extract.dialog.extract_folder_error_fallback"))[:5000],
                )

        worker.done.connect(on_done)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _convert_universal_to_zpaq(self, path):
        pass


        default_dest = _default_dest(path)
        if _has_non_latin(Path(default_dest).stem):
            default_dest = _make_latin_name(default_dest, avoid_existing=False)

        dlg = ArchiveCreateDialog([path], default_dest, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        settings = dlg.result_settings()
        if not settings or not settings.get("dest"):
            return

        try:
            temp_dir = tempfile.mkdtemp(prefix="rizpaq_transcode_")
        except Exception as exc:
            QMessageBox.critical(
                self, tr("create.error_title"), f"Failed to create temp dir: {exc}"
            )
            return

        settings["sources"] = [temp_dir]
        settings["strip_base_path"] = temp_dir
        self._temp_cleanup_dir = temp_dir

        from workers.universal_worker import UniversalExtractWorker

        worker = UniversalExtractWorker(
            self.seven_zip_bin, path, temp_dir, self.password
        )

        dlg_extract = ExtractProgressDialog(parent=self)
        dlg_extract.begin_file(Path(path).name)

        worker.percent.connect(dlg_extract.set_percent)
        worker.progress_info.connect(dlg_extract.update_info)
        worker.line_received.connect(dlg_extract.append_output)
        dlg_extract.cancelRequested.connect(worker.cancel_request)

        def on_extract_done(result):
            ok = result.get("ok")
            log = result.get("log", "")
            cancelled = result.get("cancelled")

            if cancelled:
                dlg_extract.finish(False, tr("status.extract_cancelled"))
                dlg_extract.accept()
                shutil.rmtree(temp_dir, ignore_errors=True)
                self._temp_cleanup_dir = None
                self.statusBar().showMessage(tr("status.cancel_requested"))
                return

            if not ok:
                dlg_extract.finish(False, tr("context.convert_extract_failed"))
                dlg_extract.accept()
                shutil.rmtree(temp_dir, ignore_errors=True)
                self._temp_cleanup_dir = None
                QMessageBox.warning(
                    self,
                    tr("create.error_title"),
                    tr("context.convert_extract_failed") + "\n\n" + log[:2000]
                )
                return

            dlg_extract.finish(True, tr("create.dialog_title"))
            dlg_extract.accept()
            self._run_create_from_settings(settings)

        worker.done.connect(on_extract_done)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _cleanup_transcode_temp_dir(self):
        temp_dir = getattr(self, "_temp_cleanup_dir", None)
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self._temp_cleanup_dir = None
