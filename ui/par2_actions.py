from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QDialog, QMessageBox

from ui.i18n import tr
from ui.par2_set_dialog import Par2SetDialog, last_options, remember_options
from ui.par2_verify_dialog import (
    Par2CreateDialog,
    Par2RepairDialog,
    Par2VerifyDialog,
)

from core.container_lock import ContainerLockBusy
from core.tasks import (
    PAR2_REASON_BY_STATE,
    _now,
    update_container,
    update_job_meta,
    update_work,
)
from ui.presentation import format_size
from workers import Par2CreateWorker, Par2RepairWorker, Par2VerifyWorker


class Par2ActionsMixin:


    def _par2_current_target(self):
        from ui.qt_compat import KIND_ROLE, TCOL, USER_ROLE
        from ui.qt_compat import K_FS_ARC


        table = getattr(self, "table", None)
        if table is not None:
            try:
                rows = sorted({idx.row() for idx in table.selectedIndexes()})
            except Exception:
                rows = []
            for r in rows:
                try:
                    item = table.item(r, 0)
                    if item is None:
                        continue
                    if item.data(KIND_ROLE) != K_FS_ARC:
                        continue
                    payload = item.data(USER_ROLE)
                except Exception:
                    continue
                if payload:
                    return str(payload)

        tree = getattr(self, "tree", None)
        if tree is not None:
            try:
                item = tree.currentItem()
                if item is not None:
                    if item.data(TCOL, KIND_ROLE) == K_FS_ARC:
                        payload = item.data(TCOL, USER_ROLE)
                        if payload:
                            return str(payload)
            except Exception:
                pass

        return str(getattr(self, "archive_path", "") or "")

    def _par2_target_from_menu(self):
        current = self._par2_current_target()
        if current:
            return current

        from PySide6.QtWidgets import QFileDialog


        path, _ = QFileDialog.getOpenFileName(
            self, tr("par2.pick_archive"), "", tr("create.filter")
        )
        return str(path or "")

    def _par2_menu_create(self):
        target = self._par2_target_from_menu()
        if not target:
            return
        from ui.test_modes import has_par2_for

        self._start_par2_create(target, recreate=has_par2_for(target))

    def _par2_menu_verify(self):

        target = self._par2_target_from_menu()
        if not target:
            return
        self._start_par2_verify(target)

    def _par2_menu_repair(self):

        target = self._par2_target_from_menu()
        if not target:
            return
        self._start_par2_repair(target)

    def _refresh_par2_menu(self):
        from ui.test_modes import has_par2_for

        create = getattr(self, "_par2_menu_create_action", None)
        verify = getattr(self, "_par2_menu_verify_action", None)
        repair = getattr(self, "_par2_menu_repair_action", None)
        actions = [a for a in (create, verify, repair) if a is not None]


        arc = self._par2_current_target()
        if not arc:


            for act in actions:
                act.setEnabled(True)
            return

        has_set = has_par2_for(arc)

        if create is not None:


            create.setEnabled(True)


            create.setText(tr("par2.recreate_now" if has_set
                              else "par2.create_now"))
        if verify is not None:
            verify.setEnabled(has_set)
        if repair is not None:
            repair.setEnabled(has_set)

    def _par2_job_for(self, archive_path: str):
        try:
            container, _path = self._load_container()
        except Exception:
            return None, {}, None
        if not container:
            return None, {}, None

        target = os.path.normcase(os.path.abspath(str(archive_path or "")))
        for work in container.get("works") or []:
            dest = str(work.get("dest") or "")
            if not dest:
                continue
            if os.path.normcase(os.path.abspath(dest)) != target:
                continue
            work_id = str(work.get("id") or "")
            for job in work.get("jobs") or []:
                if not job.get("par2_enabled"):
                    continue
                raw = job.get("par2_options")
                options = dict(raw) if isinstance(raw, dict) else {}
                job_id = str(job.get("id") or "")
                return (
                    {"work_id": work_id, "job_id": job_id},
                    options,
                    work.get("par2_size"),
                )
        return None, {}, None

    def _start_par2_create(self, archive_path: str,
                           recreate: bool = False) -> bool:
        try:
            from core.par2_ops import (
                default_options,
                find_par2,
                par2_main_name,
            )
            from ui.test_modes import has_par2_for

            if not archive_path or not os.path.isfile(archive_path):
                self._par2_note(tr("par2.verify_missing"), archive_path)
                return False

            par2_bin = find_par2()
            if not par2_bin:
                self._par2_note(tr("par2.not_found"), archive_path)
                return False

            if has_par2_for(archive_path):
                if not recreate:


                    self._par2_note(tr("par2.already_exists"),
                                    archive_path)
                    return False

                name = Path(archive_path).name
                answer = QMessageBox.question(
                    self,
                    tr("par2.recreate_title"),
                    tr("par2.recreate_text", name=name),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    self._par2_note(tr("par2.cancelled"), archive_path)
                    return False


                try:
                    self._remove_par2_set(archive_path)
                except Exception as exc:
                    self._par2_note(
                        tr("par2.recreate_blocked", error=str(exc)),
                        archive_path,
                    )
                    return False

            job_context, job_options, _known = self._par2_job_for(archive_path)
            name = Path(archive_path).name


            prefill = job_options or last_options()
            if not prefill:
                prefill = default_options()

            set_dlg = Par2SetDialog(name, prefill, self)
            if set_dlg.exec() != QDialog.Accepted:
                set_dlg.deleteLater()
                self._par2_note(tr("par2.cancelled"), archive_path)
                return False
            options = set_dlg.options()
            remember_options(options)
            set_dlg.deleteLater()

            dlg = Par2CreateDialog(name, self)
            self._par2_create_dialog = dlg


            dlg.finished.connect(
                lambda *_a, _d=dlg: self._release_create_dialog(_d)
            )

            worker = Par2CreateWorker(
                par2_bin, archive_path, options=options
            )
            dlg.cancelRequested.connect(worker.cancel_request)
            worker.done.connect(
                lambda r, c=job_context: self._on_par2_done(c, r, dlg)
            )
            worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

            dlg.show()
            self._workers.append(worker)
            self._par2_worker = worker
            worker.start()
            return True
        except Exception as exc:
            try:
                self._par2_note(
                    tr("par2.verify_failed",
                       error=f"{type(exc).__name__}: {exc}"),
                    archive_path,
                )
            except Exception:
                pass
            return False

    def _release_create_dialog(self, dialog):

        if getattr(self, "_par2_create_dialog", None) is dialog:
            self._par2_create_dialog = None

    def _start_par2_worker(
        self,
        job_context: dict,
        archive_path: str,
        par2_fallback: dict = None,
        dialog=None,
    ) -> bool:
        try:
            if not archive_path:
                return False
            if not os.path.isfile(archive_path):
                return False

            from core.par2_ops import find_par2

            par2_bin = find_par2()
            if not par2_bin:
                self._par2_note(tr("par2.not_found"), archive_path)
                return False

            enabled, options, known_size = self._par2_settings(job_context)
            if par2_fallback:


                enabled = bool(par2_fallback.get("enabled"))
                options = dict(par2_fallback.get("options") or {})
            if not enabled:
                return False

            worker = Par2CreateWorker(
                par2_bin,
                archive_path,
                options=options,
                unchanged_size=known_size,
            )
            worker.done.connect(
                lambda r, c=job_context, d=dialog:
                    self._on_par2_done(c, r, d)
            )
            worker.finished.connect(
                lambda w=worker: self._cleanup_worker(w)
            )
            if dialog is not None:


                try:
                    dialog.begin_par2_stage(Path(archive_path).name)
                    worker.line_received.connect(dialog.append_output)
                except Exception:
                    pass

            self._workers.append(worker)
            self._par2_worker = worker
            worker.start()
            return True
        except Exception:


            return False


    def _par2_settings(self, job_context: dict):
        try:
            container, _path = self._load_container()
        except Exception:
            return False, {}, None
        if not container:
            return False, {}, None

        if not job_context:
            return False, {}, None

        work_id = str(job_context.get("work_id") or "")
        job_id = str(job_context.get("job_id") or "")

        for work in container.get("works") or []:
            if work_id and str(work.get("id")) != work_id:
                continue
            known_size = work.get("par2_size")
            for job in work.get("jobs") or []:
                if job_id and str(job.get("id")) != job_id:
                    continue
                options = job.get("par2_options")
                return (
                    bool(job.get("par2_enabled")),
                    dict(options) if isinstance(options, dict) else {},
                    known_size if isinstance(known_size, int) else None,
                )
        return False, {}, None


    def _on_par2_done(self, job_context: dict, result: dict,
                       dialog=None):
        self._par2_worker = None

        archive_path = result.get("archive_path") or ""
        ok = bool(result.get("ok"))
        cancelled = bool(result.get("cancelled"))
        log = result.get("log") or ""
        recorded_size = result.get("recorded_size")
        skipped = bool(result.get("skipped"))

        if log:
            try:
                self.log_output(f"[par2] {log}")
            except Exception:
                pass

        if ok and not cancelled and recorded_size is not None:
            self._save_par2_marker(job_context, recorded_size)


        verdict_key = "par2.created_ok"
        verdict_ok = ok
        if cancelled:
            verdict_key = "par2.cancelled"
            verdict_ok = False
        elif skipped:
            verdict_key = "par2.create_skipped"
            verdict_ok = False
        elif not ok:
            verdict_key = "par2.create_failed"
            verdict_ok = False

        if dialog is not None and hasattr(dialog, "finish_verdict"):
            detail = ""
            if isinstance(recorded_size, int) and recorded_size > 0:
                detail = tr("par2.verify_size",
                             size=format_size(recorded_size))
            try:
                dialog.finish_verdict(verdict_ok, tr(verdict_key), log,
                                      detail)
            except Exception as exc:
                try:
                    self.log_output(
                        f"[par2] окно создания не показало итог: {exc}"
                    )
                except Exception:
                    pass
        elif dialog is not None:


            try:
                if cancelled:
                    dialog.finish(True, tr("par2.cancelled"), stay=True)
                elif ok and skipped:
                    dialog.finish(True, tr("par2.create_skipped"),
                                  stay=True)
                elif ok:
                    dialog.finish(True, tr(
                        "par2.created_ok",
                        name=Path(archive_path).name
                        if archive_path else ""), stay=True)
                else:
                    dialog.finish(False, tr(
                        "par2.create_failed", error=_last_line(log)),
                        stay=True)
            except Exception:


                pass

        if cancelled:
            self._par2_note(tr("par2.cancelled"), archive_path)
            return


        if ok and skipped:
            self._par2_note(tr("par2.create_skipped"), archive_path)
            return

        if ok:
            self._par2_note(
                tr("par2.created_ok", name=Path(archive_path).name
                   if archive_path else ""),
                archive_path,
            )
            return

        self._par2_note(
            tr("par2.create_failed", error=_last_line(log)), archive_path
        )


    def _save_par2_marker(self, job_context: dict, size: int):
        try:
            container, path = self._load_container()
            if not container or not path:
                return
            work_id = str(job_context.get("work_id") or "")
            if not work_id:
                return

            def mutate(c):
                update_work(
                    c, work_id,
                    par2_size=int(size),
                    par2_created=_now(),
                )

            try:
                update_container(path, mutate)
            except ContainerLockBusy:
                pass
        except Exception:
            pass


    def _par2_note(self, text: str, archive_path: str):
        name = Path(archive_path).name if archive_path else ""
        try:
            self.statusBar().showMessage(
                "PAR2: " + text + (f" ({name})" if name else "")
            )
        except Exception:
            pass


    def _release_verify_dialog(self, dialog):
        if getattr(self, "_par2_verify_dialog", None) is dialog:
            self._par2_verify_dialog = None

    def _par2_refuse(self, archive_path: str, text_key: str,
                     warn: bool = False) -> bool:
        self._par2_note(tr(text_key), archive_path)
        try:
            from PySide6.QtWidgets import QMessageBox

            title = tr("par2.quick_check")
            text = tr(text_key)
            if warn:
                QMessageBox.warning(self, title, text)
            else:
                QMessageBox.information(self, title, text)
        except Exception:
            pass
        return False

    def _start_par2_verify(self, archive_path: str, job_context: dict = None):
        try:
            from core.par2_ops import find_par2, par2_main_name

            par2_bin = find_par2()
            if not par2_bin:
                return self._par2_refuse(
                    archive_path, "backup.reason_full.par2_failed", warn=True
                )

            par2_path = par2_main_name(archive_path)
            if not os.path.isfile(par2_path):
                return self._par2_refuse(
                    archive_path, "backup.reason_full.par2_missing"
                )


            name = Path(archive_path).name if archive_path else ""
            dlg = Par2VerifyDialog(name, self)
            self._par2_verify_dialog = dlg


            dlg.finished.connect(
                lambda *_args, _d=dlg: self._release_verify_dialog(_d)
            )

            worker = Par2VerifyWorker(par2_bin, archive_path)


            dlg.cancelRequested.connect(worker.cancel_request)
            worker.done.connect(
                lambda r, c=job_context: self._on_par2_verify_done(c, r, dlg)
            )
            worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

            dlg.show()
            self._workers.append(worker)
            self._par2_verify_worker = worker
            worker.start()
            return True
        except Exception as exc:


            try:
                self._par2_note(
                    tr("par2.verify_failed", error=f"{type(exc).__name__}: {exc}"),
                    archive_path,
                )
            except Exception:
                pass
            return False

    def _on_par2_verify_done(self, job_context: dict, result: dict,
                             dialog=None):
        from core.par2_ops import (
            STATE_BROKEN,
            STATE_DAMAGED,
            STATE_MISSING,
            STATE_OK,
            STATE_UNREPAIRABLE,
        )

        self._par2_verify_worker = None

        archive_path = result.get("archive_path") or ""
        state = result.get("state")
        log = result.get("log") or ""
        name = Path(archive_path).name if archive_path else ""

        if log:
            try:
                self.log_output(f"[par2] {log}")
            except Exception:
                pass


        verdict_key = "test.title"
        verdict_ok = False


        verdict_extra = {}
        if result.get("cancelled"):
            verdict_key = "par2.cancelled"
        elif state == STATE_OK:
            verdict_key = "par2.verify_ok"
            verdict_ok = True
        elif state == STATE_DAMAGED:
            recorded = result.get("recorded_size")
            actual = None
            if _par2_set_is_stale(archive_path, recorded):
                try:
                    actual = os.path.getsize(archive_path)
                except OSError:
                    actual = None
            if actual is not None and isinstance(recorded, int):
                verdict_key = "par2.verify_stale"
                verdict_extra = {"recorded": recorded, "actual": actual}
            else:
                verdict_key = "par2.verify_damaged"
        elif state == STATE_UNREPAIRABLE:
            verdict_key = "par2.verify_unrepairable"
        elif state == STATE_MISSING:
            verdict_key = "par2.verify_missing"
        elif state == STATE_BROKEN:
            verdict_key = "par2.verify_broken"

        if dialog is not None:


            detail = ""
            recorded = result.get("recorded_size")
            if isinstance(recorded, int) and recorded > 0:
                detail = tr("par2.verify_size", size=format_size(recorded))
            try:
                dialog.finish_verdict(
                    verdict_ok,
                    tr(verdict_key, name=name, **verdict_extra),
                    log, detail,
                )
            except Exception as exc:


                try:
                    self.log_output(
                        f"[par2] окно проверки не показало вердикт: {exc}"
                    )
                except Exception:
                    pass

        if result.get("cancelled"):
            self._par2_note(tr("par2.cancelled"), archive_path)
            return


        if job_context:
            status = "ok" if state == STATE_OK else "error"
            reason = None if state == STATE_OK else PAR2_REASON_BY_STATE.get(state)
            try:


                self._update_job_meta_after_run(
                    job_context, status, reason=reason, output=log)
            except Exception:
                pass

        if state == STATE_OK:
            self._par2_note(tr("par2.verify_ok", name=name), archive_path)
            return

        if state == STATE_DAMAGED:


            if verdict_extra:
                self._par2_note(
                    tr("par2.verify_stale", **verdict_extra), archive_path
                )
            else:
                self._par2_note(tr("par2.verify_damaged"), archive_path)
            return

        if state == STATE_UNREPAIRABLE:


            self._par2_note(tr("par2.verify_unrepairable"), archive_path)
            return

        if state == STATE_MISSING:
            self._par2_note(tr("par2.verify_missing"), archive_path)
            return

        if state == STATE_BROKEN:
            self._par2_note(tr("par2.verify_broken"), archive_path)
            return

        self._par2_note(
            tr("par2.create_failed", error=_last_line(log)), archive_path
        )


    def _start_par2_repair(self, archive_path: str):
        from core.par2_ops import (
            STATE_BROKEN,
            STATE_DAMAGED,
            STATE_MISSING,
            STATE_OK,
            STATE_UNREPAIRABLE,
            find_par2,
            par2_main_name,
            verify_parset,
        )

        name = Path(archive_path).name if archive_path else ""


        dlg = Par2RepairDialog(name, self)
        self._par2_repair_dialog = dlg


        dlg.finished.connect(
            lambda *_args, _d=dlg: self._release_repair_dialog(_d)
        )

        def refuse(verdict, ok=False):
            self._par2_note(verdict, archive_path)
            try:
                dlg.finish_verdict(ok, verdict)
            except Exception:
                pass
            return False

        try:
            par2_bin = find_par2()
            if not par2_bin:
                return refuse(tr("par2.not_found"))

            par2_path = par2_main_name(archive_path)
            if not os.path.isfile(par2_path):
                return refuse(tr("par2.verify_missing"))

            res = verify_parset(par2_bin, par2_path)
            if res.state in (STATE_MISSING, STATE_BROKEN):
                return refuse(tr("par2.verify_broken"))
            if res.state == STATE_UNREPAIRABLE:


                return refuse(tr("par2.repair_impossible"))
            if res.state != STATE_DAMAGED:

                return refuse(tr("par2.repair_not_needed"), ok=True)
            if res.recorded_size is None:
                return refuse(tr("par2.repair_no_size"))

            try:
                actual = os.path.getsize(archive_path)
            except OSError:
                return refuse(tr("par2.verify_missing"))

            if actual != int(res.recorded_size):


                return refuse(
                    tr("par2.repair_stale",
                       actual=actual, recorded=int(res.recorded_size))
                )

            answer = QMessageBox.question(
                self,
                tr("par2.repair_confirm_title"),


                tr("par2.repair_confirm_same_size"
                   if actual == int(res.recorded_size)
                   else "par2.repair_confirm_text",
                   name=name,
                   actual=actual,
                   recorded=int(res.recorded_size)),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return refuse(tr("par2.cancelled"), ok=True)

            dlg.begin_repair()

            worker = Par2RepairWorker(
                par2_bin, archive_path, recorded_size=res.recorded_size
            )
            dlg.cancelRequested.connect(worker.cancel_request)
            worker.done.connect(lambda r: self._on_par2_repair_done(r, dlg))
            worker.finished.connect(
                lambda w=worker: self._cleanup_worker(w)
            )

            self._workers.append(worker)
            self._par2_repair_worker = worker
            worker.start()
            return True
        except Exception as exc:
            return refuse(
                tr("par2.verify_failed",
                   error=f"{type(exc).__name__}: {exc}")
            )

    def _release_repair_dialog(self, dialog):

        if getattr(self, "_par2_repair_dialog", None) is dialog:
            self._par2_repair_dialog = None

    def _on_par2_repair_done(self, result: dict, dialog=None):
        self._par2_repair_worker = None

        archive_path = result.get("archive_path") or ""
        log = result.get("log") or ""

        if log:
            try:
                self.log_output(f"[par2] {log}")
            except Exception:
                pass

        if result.get("cancelled"):
            verdict = tr("par2.cancelled")
        elif result.get("ok"):
            verdict = tr("par2.repair_ok")
        else:
            verdict = tr("par2.repair_failed", error=_last_line(log))

        if dialog is not None:
            try:
                dialog.finish_verdict(bool(result.get("ok")), verdict, log)
            except Exception as exc:
                try:
                    self.log_output(
                        f"[par2] окно восстановления не показало итог: {exc}"
                    )
                except Exception:
                    pass

        if result.get("cancelled"):
            self._par2_note(tr("par2.cancelled"), archive_path)
            return

        if result.get("ok"):
            self._par2_note(tr("par2.repair_ok"), archive_path)
            try:
                self._on_refresh()
            except Exception:
                pass


            try:
                self._refresh_index_after_create(archive_path)
            except Exception:
                pass
            return

        self._par2_note(
            tr("par2.repair_failed", error=_last_line(log)), archive_path
        )


    def _remove_par2_set(self, archive_path: str) -> int:
        try:
            from core.par2_ops import remove_par2_set

            return len(remove_par2_set(archive_path))
        except Exception:
            return 0


def _par2_set_is_stale(archive_path: str, recorded_size) -> bool:
    if not archive_path or not isinstance(recorded_size, int):
        return False
    if recorded_size <= 0:
        return False
    try:
        actual = os.path.getsize(archive_path)
    except OSError:
        return False
    return actual != recorded_size


def _last_line(text: str) -> str:

    for line in reversed((text or "").splitlines()):
        line = line.strip()
        if line:
            return line[:120]
    return "причина неизвестна"
