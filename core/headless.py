
















































































from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

                                                                      
              
from core.password_store import get_password, set_password
from core.incomplete_archive import incomplete_archive_action
from core.tasks import (
    ACTION_TEST,
    ContainerLockBusy,
    PAR2_REASON_BY_STATE,
    TEST_MODE_SYNC,
    _now,
    load_container,
    update_container,
    update_job_meta,
    update_work,
    find_job,
    job_to_runnable_settings,
)
from core.zpaq_cli import looks_like_busy_error

_HEADLESS_OPS = ("--test", "--extract-here", "--create", "--task")


def is_headless_op(args: list) -> bool:
    pass







    if not args:
        return False
    return str(args[0]).strip() in _HEADLESS_OPS


def _init_language() -> None:
    pass





    try:
        from ui.config_bridge import _load_cfg
        from ui.i18n import detect_language, set_language

        cfg = _load_cfg()
        lang = getattr(cfg, "language", None)
        if not lang:
            lang = detect_language()
        set_language(lang, notify=False)
    except Exception:
        pass


def _zpaq_bin():
    pass







    zpaq = os.environ.get("ZPAQ_BIN")
    if zpaq:
        return zpaq
    try:
        from core.config import load as _load_cfg

        cfg = _load_cfg()
        if getattr(cfg, "zpaq_path", None) and os.path.isfile(cfg.zpaq_path):
            return cfg.zpaq_path
    except Exception:
        pass
    return "zpaqfranz"


def _make_progress_window(title: str):
    pass






    from PySide6.QtWidgets import QDialog, QVBoxLayout

    from ui.extract_progress import ExtractProgressBar

    class _HeadlessProgress(QDialog):
        def __init__(self, t: str):
            super().__init__()
            self.setWindowTitle(t)
            self.setModal(False)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.bar = ExtractProgressBar()
            layout.addWidget(self.bar)
            self.resize(560, 110)
            self.bar.setVisible(True)
            self.bar.setFixedHeight(80)

    return _HeadlessProgress(title)


def run_headless(args: list) -> int:
    pass
    _init_language()
    op = str(args[0]).strip()
    if op == "--test":
        if len(args) < 2:
            return 1
        return _headless_test(str(args[1]))
    if op == "--extract-here":
        if len(args) < 2:
            return 1
        return _headless_extract_here(str(args[1]))
    if op == "--create":
        sources = [str(a) for a in args[1:] if str(a).strip()]
        if not sources:
            return 1
        return _headless_create(sources)
    if op == "--task":
                                                                   
                                                                         
                                             
        return _headless_task(list(args[1:]))
    return 1


                                                                   
def _headless_test(archive: str) -> int:
    from PySide6.QtWidgets import QApplication, QMessageBox

    from ui.archive_actions import offer_latin_rename
    from ui.i18n import tr
    from workers import ZpaqWorker

    archive = offer_latin_rename(archive, None)
    if not archive:
        return 0

    zpaq = _zpaq_bin()
    password = get_password(archive)
    cmd = [zpaq, "t", archive]
    if password:
        cmd += ["-key", password]

    win = _make_progress_window(tr("test.title"))
    win.show()
    win.bar.begin_file(Path(archive).name)

    def on_result(result):
        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ok = rc == 0
        try:
            win.bar.finish(ok, 0, Path(archive).name)
        except Exception:
            pass
        name = Path(archive).name
        if ok:
            QMessageBox.information(win, tr("test.title"), tr("test.ok", name=name))
        else:
            tail = output.strip()[-2000:]
            QMessageBox.warning(
                win, tr("test.title"), tr("test.fail", name=name) + "\n\n" + tail
            )
        QApplication.quit()

    worker = ZpaqWorker("test", cmd, {"path": archive})
    worker.result.connect(on_result)
    try:
        worker.percent.connect(win.bar.set_percent)
    except Exception:
        pass
    worker.start()
    return QApplication.instance().exec()


                                                                           
def _headless_extract_here(archive: str) -> int:
    from PySide6.QtWidgets import QApplication, QMessageBox

    from ui.archive_actions import offer_latin_rename
    from ui.i18n import tr
    from workers import ExtractFolderBatchWorker

    archive = offer_latin_rename(archive, None)
    if not archive:
        return 0

    zpaq = _zpaq_bin()
    password = get_password(archive)
    dest = os.path.dirname(archive) or "."

    win = _make_progress_window(tr("menu.unpack"))
    win.show()
    win.bar.begin_file(Path(archive).name)

    def on_done(result):
        ok = bool(result.get("ok"))
        log = result.get("log", "") or ""
        try:
            win.bar.finish(ok, 0, dest)
        except Exception:
            pass
        if ok:
            QMessageBox.information(
                win,
                tr("menu.unpack"),
                tr("status.extract_folder_done", dest=dest),
            )
        else:
            tail = (log or tr("extract.dialog.extract_folder_error_fallback")).strip()[
                -2000:
            ]
            QMessageBox.warning(
                win, tr("extract.dialog.extract_folder_error_title"), tail
            )
        QApplication.quit()

    worker = ExtractFolderBatchWorker(zpaq, archive, password, "", None, dest)
    worker.done.connect(on_done)
    try:
        worker.percent.connect(win.bar.set_percent)
    except Exception:
        pass
    worker.start()
    return QApplication.instance().exec()


                                                                     
def _build_create_cmd(zpaq_bin, settings, srcs, dest, password):
    pass














    cmd = [zpaq_bin, "a", dest] + list(srcs)
                                                                    
                                                                   
                                                       
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
    return cmd


def _build_test_cmd(zpaq_bin, dest, password, test_mode, tmp_dir=None, sources=None):
    pass







































    mode = str(test_mode or "full").strip().lower()
    if mode == "verify_fs":
                                                                   
                                                                
                                                        
        cmd = [zpaq_bin, "v", dest]
    elif mode == "sync":
                                                             
                                                                    
                                                                     
                                                               
        cmd = [zpaq_bin, "sync", dest] + [str(s) for s in (sources or [])]
    else:
        cmd = [zpaq_bin, "t", dest]
        if mode == "checksum":
            cmd += ["-all", "-checksum"]
        elif mode == "verify":
            cmd += ["-verify"]
        elif mode == "paranoid":
            cmd += ["-verify", "-paranoid"]
            if tmp_dir:
                cmd += ["-to", str(tmp_dir)]
                                                                  
                                                   
    if password:
        cmd += ["-key", password]
    return cmd


def _headless_create(sources: list) -> int:
    pass






    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

    from core.archive_naming import default_dest as _default_dest
    from core.archive_naming import has_non_latin as _has_non_latin
    from core.archive_naming import make_latin_name as _make_latin_name
    from ui.archive_create_dialog import ArchiveCreateDialog
    from ui.i18n import tr
    from ui.qt_compat import YES_BUTTON, YES_NO_BUTTONS
    from workers import ZpaqWorker

    zpaq = _zpaq_bin()
    default_dest = _default_dest(sources[0])
    if _has_non_latin(Path(default_dest).stem):
        default_dest = _make_latin_name(default_dest, avoid_existing=False)

    dlg = ArchiveCreateDialog(sources, default_dest, parent=None)
    if dlg.exec() != QDialog.Accepted:
        return 0

    settings = dlg.result_settings()
    if not settings or not settings.get("dest"):
        return 0

    srcs = settings.get("sources") or sources
    if not srcs:
        return 0

    dest = settings["dest"]
    password = settings.get("password")

    if _has_non_latin(Path(dest).stem) and "?" not in dest:
        new_dest = _make_latin_name(dest)
        ans = QMessageBox.question(
            None,
            tr("create.nonlatin_title"),
            tr(
                "create.nonlatin_create_text",
                old=Path(dest).name,
                new=Path(new_dest).name,
            ),
            YES_NO_BUTTONS,
        )
        if ans != YES_BUTTON:
            return 0
        dest = new_dest

    if settings.get("chunk") and "?" not in dest:
        p = Path(dest)
        dest = str(p.parent / (p.stem + "_????" + (p.suffix or ".zpaq")))

    cmd = _build_create_cmd(zpaq, settings, srcs, dest, password)

                                                                        
                                                              
    existed_before = Path(dest).is_file()

    win = _make_progress_window(tr("create.dialog_title"))
    win.show()
    win.bar.begin_file(Path(dest).name)

    def on_result(result):
        rc = result.get("rc", 1)
        output = result.get("output", "") or ""
        ok = rc == 0
        busy = (not ok) and looks_like_busy_error(output)
        try:
            win.bar.finish(ok, 0, Path(dest).name)
        except Exception:
            pass
        if ok:
            if password:
                set_password(dest, password)
            QMessageBox.information(
                win,
                tr("create.dialog_title"),
                tr("create.done", name=Path(dest).name),
            )
        elif busy:
                                                              
                                                    
            QMessageBox.information(
                win,
                tr("create.busy_title"),
                tr("create.busy_text", name=Path(dest).name),
            )
        else:
            tail = output.strip()[-2000:]
            QMessageBox.warning(win, tr("create.error_title"), tail)
            _handle_incomplete_headless(win, dest, existed_before, output)
        QApplication.quit()

    worker = ZpaqWorker("create", cmd, {"dest": dest, "password": password})
    worker.result.connect(on_result)
    try:
        worker.percent.connect(win.bar.set_percent)
    except Exception:
        pass
    worker.start()
    return QApplication.instance().exec()


def _handle_incomplete_headless(win, dest, existed_before, output):
    pass









    from PySide6.QtWidgets import QMessageBox

    from ui.i18n import tr

    action = incomplete_archive_action(dest, existed_before)
    if action["action"] == "none":
        return
    name = Path(dest).name
    if action["action"] == "delete":
        try:
            Path(dest).unlink()
        except OSError as exc:
            QMessageBox.warning(
                win,
                tr("create.error_title"),
                tr("create.incomplete_delete_error", name=name, error=str(exc)),
            )
            return
        QMessageBox.information(
            win,
            tr("create.incomplete_title"),
            tr("create.incomplete_deleted", name=name),
        )
        return
    tail = (output or "").strip()[-2000:]
    QMessageBox.warning(
        win,
        tr("create.incomplete_title"),
        tr("create.incomplete_text") + ("\n\n" + tail if tail else ""),
    )


                                                                                 
def _write_temp_error(text: str) -> None:
    pass






    try:
        temp_log = Path(tempfile.gettempdir()) / "rizpaq_task_error.log"
        with open(temp_log, "a", encoding="utf-8") as f:
            f.write(f"--- Rizpaq task error {datetime.now().isoformat(timespec='seconds')} ---\n")
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
            f.write("=" * 50 + "\n\n")
    except Exception:
        pass


def _headless_par2_verify(dest: str) -> tuple:
    pass









    from core import par2_ops

    par2_bin = par2_ops.find_par2()
    if not par2_bin:
        return 1, "[par2] par2.exe не найден, проверка невозможна\n", par2_ops.STATE_FAILED

    par2_path = par2_ops.par2_main_name(dest)
    if not os.path.isfile(par2_path):
        return 1, (
            "[par2] набор не создан рядом с архивом — проверять нечего\n"
            f"[par2] ожидался файл: {par2_path}\n"
        ), par2_ops.STATE_MISSING

    res = par2_ops.verify_parset(par2_bin, par2_path)

    tail = [ln for ln in (res.log or "").splitlines() if ln.strip()]
    body = "\n".join(tail[-12:]) if tail else ""

    if res.state == par2_ops.STATE_OK:
        return 0, (
            "[par2] набор проверен, архив цел\n"
            f"[par2] защищает {res.recorded_size} байт\n"
        ), res.state
    if res.state == par2_ops.STATE_DAMAGED:
                                                                  
                                                                     
                                                                        
                                                                        
                           
        return 0, (
            "[par2] АРХИВ ПОВРЕЖДЁН, восстановление возможно\n" + body + "\n"
        ), res.state
    if res.state == par2_ops.STATE_UNREPAIRABLE:
                                                                 
                                                                   
                                                             
        return 1, (
            "[par2] АРХИВ ПОВРЕЖДЁН, ИЗБЫТОЧНОСТИ НЕ ХВАТИТ — "
            "ВОССТАНОВЛЕНИЕ НЕВОЗМОЖНО\n" + body + "\n"
        ), res.state

    reason = {
        par2_ops.STATE_MISSING: "набор не найден",
        par2_ops.STATE_BROKEN: "набор повреждён и не читается",
    }.get(res.state, "проверка не удалась")
    return 1, f"[par2] {reason}\n" + body + "\n", res.state


def _headless_par2(rzp_path: str, work: dict, job: dict,
                    dest: str, settings: dict) -> str:
    pass















    from core import par2_ops

    header = "\n[par2] создание набора защиты от повреждений\n"

    par2_bin = par2_ops.find_par2()
    if not par2_bin:
        return header + "par2.exe не найден, набор не создан\n"

    options = settings.get("par2_options")
    options = dict(options) if isinstance(options, dict) else {}
    known_size = work.get("par2_size")
    if not isinstance(known_size, int):
        known_size = None

    try:
        res = par2_ops.refresh_par2_set(
            par2_bin,
            dest,
            redundancy=options.get("redundancy") or 5,
            memory_mb=options.get("memory_mb"),
            threads=options.get("threads"),
            block_size=options.get("block_size"),
            recursion=bool(options.get("recursion")),
            skip_if_unchanged=known_size is not None,
            unchanged_size=known_size,
        )
    except Exception as exc:
        return header + f"ошибка набора: {type(exc).__name__}: {exc}\n"

    if not res.ok:
                                                                       
                                                          
        tail = (res.log or "").strip().splitlines()
        return header + "набор НЕ создан: " + (
            tail[-1][:200] if tail else "причина неизвестна"
        ) + "\n"

    if res.recorded_size is not None:
        work_id = str(work.get("id") or "")
        if work_id:
            try:
                def _mark(c: dict) -> None:
                    update_work(
                        c, work_id,
                        par2_size=int(res.recorded_size),
                        par2_created=_now(),
                    )

                try:
                    update_container(rzp_path, _mark)
                except ContainerLockBusy:
                    pass
            except Exception:
                pass

    if "не изменился" in (res.log or ""):
        return header + "архив не изменился, набор остался в силе\n"
    return header + f"набор создан, защищает {res.recorded_size} байт\n"


def _write_task_log(rzp_path: str, header: str, log: str,
                    mode: str = "short", rc: int = 0,
                    busy: bool = False, note: str = "") -> None:
    pass




















    if mode == "none":
        return
    try:
        log_path = Path(str(rzp_path) + ".log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(header + "\n")
                                                                 
                                                                          
                                                                        
                                                                         
                                                                       
                                          
            if note:
                f.write(note if note.endswith("\n") else note + "\n")
            if mode == "full":
                if log:
                    f.write(log)
            elif mode == "short":
                if rc == 0:
                    f.write("Status: OK\n")
                elif busy:
                    f.write("Status: BUSY (another zpaqfranz is running)\n")
                else:
                    f.write(f"Status: ERROR (rc={rc})\n")
                    if log:
                                                                                
                        clean_log = log.replace("\r", "\n")
                        lines = [ln for ln in clean_log.splitlines() if ln.strip()]
                        tail = "\n".join(lines[-10:])
                        f.write("--- Last output lines ---\n")
                        f.write(tail + "\n")
            f.write("=" * 50 + "\n\n")
    except Exception:
        pass


def _parse_task_args(rest: list) -> tuple:
    pass









    if not rest:
        return "", ""
    rzp_path = str(rest[0]).strip()
    job_id = ""
    i = 1
    while i < len(rest):
        arg = str(rest[i]).strip()
        if arg == "--job" and i + 1 < len(rest):
            job_id = str(rest[i + 1]).strip()
            break
        i += 1
    return rzp_path, job_id


def _headless_task(rest: list) -> int:
    pass
































    from core.zpaq_cli import run_zpaq, safe_cmdline

                             
    rzp_path, job_id = _parse_task_args(rest)
    if not rzp_path:
        _write_temp_error(
            f"Rizpaq: --task без пути к контейнеру. "
            f"Аргументы: {rest!r}\n"
        )
        return 1
    if not job_id:
                                                                  
                                                                
        _write_temp_error(
            f"Rizpaq: --task без --job. Файл: {rzp_path}. "
            f"Аргументы: {rest!r}\n"
        )
        return 1

                                                                    
                                                                   
                                                    
     
                                                                   
                                                                   
                                       
    try:
        container = load_container(rzp_path)
    except Exception as exc:
        _write_temp_error(
            f"Rizpaq: не удалось прочитать контейнер {rzp_path}: "
            f"{type(exc).__name__}: {exc}\n"
        )
        return 1

                             
    found = find_job(container, job_id)
    if found is None:
        _write_temp_error(
            f"Rizpaq: в контейнере {rzp_path} нет задания с id={job_id!r}. "
            f"Возможно, контейнер отредактировали после регистрации задачи "
            f"в Планировщике, и запись указывает на устаревший id.\n"
        )
        return 1

    work, job = found
    settings = job_to_runnable_settings(work, job)

    action = str(settings.get("action") or "backup").strip().lower()

    srcs = settings.get("sources") or []
    if action != ACTION_TEST and not srcs:
                                                               
                                                            
        header = _build_log_header(rzp_path, work, job, 1)
        _write_task_log(rzp_path, header, "No sources specified in job.",
                        "full", 1)
        return 1
                                                                  
                                                                 
                                                                 
    if (
        action == ACTION_TEST
        and str(settings.get("test_mode") or "").strip().lower() == TEST_MODE_SYNC
        and not srcs
    ):
        header = _build_log_header(rzp_path, work, job, 1)
        _write_task_log(rzp_path, header, "No sources specified for sync.",
                        "full", 1)
        return 1
    dest = settings.get("dest")
    if not dest:
        header = _build_log_header(rzp_path, work, job, 1)
        _write_task_log(rzp_path, header, "No destination specified in job.",
                        "full", 1)
        return 1

    password = settings.get("password")
    zpaq = _zpaq_bin()
    log_mode = settings.get("task_log_mode") or "short"

    rename_note = ""

                                                                           
                                                                        
                                                         
    from core.archive_naming import has_non_latin as _has_non_latin
    from core.archive_naming import make_latin_name as _make_latin_name

    if _has_non_latin(Path(dest).stem) and "?" not in dest:
        old_name = Path(dest).name
        dest = _make_latin_name(dest)
                                                                        
                                                                             
                                
        rename_note = (
            f"\n[rizpaq] destination renamed for engine compatibility: "
            f"'{old_name}' -> '{Path(dest).name}'\n"
        )

                                                   
    tmp_dir = None                                              
    cmd = None
    par2_mode = (action == ACTION_TEST
                 and str(settings.get("test_mode") or "").strip().lower()
                 == "par2")
    par2_note = ""
    par2_reason = None                                                
    try:
        if par2_mode:
                                                                   
                                                                  
                                                                      
                                                             
            cmd = None
            rc, log, par2_state = _headless_par2_verify(dest)
                                                                       
                                                                   
                                                                     
                                
            par2_note = log
                                                                        
                                                                       
                                                                  
                                                                    
                                         
            from core import par2_ops                                                      

            ok = par2_state == par2_ops.STATE_OK
            if not ok:
                par2_reason = PAR2_REASON_BY_STATE.get(par2_state)
        elif action == ACTION_TEST:
            test_mode = settings.get("test_mode") or "full"
            if str(test_mode).strip().lower() == "paranoid":
                                                                  
                                                                   
                                                                       
                                                      
                try:
                    tmp_dir = tempfile.mkdtemp(prefix="rizpaq_task_test_")
                except OSError:
                    tmp_dir = None
            cmd = _build_test_cmd(zpaq, dest, password, test_mode, tmp_dir, srcs)
        elif action == ACTION_CROP:
                                                                
                                                            
                                                            
            cmd = [zpaq_bin, "crop", dest, "-kill", "-to", dest]
        elif action == ACTION_CONSOLIDATE:
                                                                         
                                                          
            cmd = [zpaq_bin, "consolidate", dest, "-to", dest]
        elif action == ACTION_SFX:
                                                                    
                                                       
                                                                 
            sfx_dest = str(Path(dest).with_suffix(".exe"))
            cmd = [zpaq_bin, "sfx", dest, sfx_dest]
        elif action == ACTION_INFO:
                                                            
                                                                
            cmd = [zpaq_bin, "i", dest, "-comment"]
        elif action == ACTION_PASSWORD:
                                                           
                                                                                                 
                                                                            
            old_pw = password or ""
            new_pw = str(settings.get("new_password") or "").strip()
            if not old_pw or not new_pw:
                                               
                rc, log_out = 1, "ERROR: password change requires both old and new password\n"
                ok = False
                                                                                      
                                                             
                cmd = None
            else:
                sfx_dest = str(Path(dest).with_suffix(".zpaq"))
                cmd = [zpaq_bin, "password", dest, sfx_dest, "-key", old_pw, "-key2", new_pw]
        elif action == ACTION_CHECKPASSWORD:
                                                                   
                                                 
            cmd = [zpaq_bin, "checkpassword", dest, "-key", password or ""]
        else:
                                                                
            if settings.get("chunk") and "?" not in dest:
                p = Path(dest)
                dest = str(p.parent / (p.stem + "_????" + (p.suffix or ".zpaq")))
            cmd = _build_create_cmd(zpaq, settings, srcs, dest, password)

                                                            
        if not par2_mode:
            if cmd is not None:
                rc, log = run_zpaq(cmd)
                ok = rc == 0
                                                                              
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    if rename_note:
        log = rename_note + (log or "")

                                                             
                                                                   
                                                      
    busy = (not ok) and looks_like_busy_error(log or "")

                                                  
                                                          
                                                                 
                                
     
                                                            
                                                                 
                                                              
                                                                   
                                               
     
                                                                     
                                                               
                                                                  
    try:
        if ok:
            status = "ok"
        elif busy:
            status = "busy"
        else:
            status = "error"

        def _mutate(c: dict) -> None:
                                                                   
                                                                 
                                                                      
                                         
            update_job_meta(c, job_id, status, reason=par2_reason)

        try:
            update_container(rzp_path, _mutate)
        except ContainerLockBusy:
                                                                
                                                                 
                                                              
                                              
            pass
    except Exception:
        pass

                                               
    if ok and password:
        try:
            set_password(dest, password)
        except Exception:
            pass

                                                                     
                                                        
     
                                                                         
                                                                          
                                                                     
                                                                        
                                                 
    if ok and action != ACTION_TEST and settings.get("par2_enabled"):
                                                                   
                                                                        
                                                                    
         
                                                                      
                                                                  
                                                                    
                    
        par2_note = _headless_par2(rzp_path, work, job, dest, settings)

                                                           
     
                                                                 
                                                                    
                                                                      
                                                                   
                                                                      
                                                                   
                                                                
                                                                     
                                                  
    if ok and action != ACTION_TEST:
        try:
            from core import index_refresh
            index_refresh.refresh_index_sync(zpaq, dest, password)
        except Exception:
            pass

                                                   
    log_header = _build_log_header(rzp_path, work, job, rc,
                                   password, cmd=cmd)
    _write_task_log(rzp_path, log_header, log, log_mode, rc, busy=busy,
                    note=par2_note)

                                                                
                                                             
    if not ok and not busy:
        try:
            temp_log = Path(tempfile.gettempdir()) / "rizpaq_task_error.log"
            with open(temp_log, "a", encoding="utf-8") as f:
                f.write(log_header + "\n" + (log or "") + "\n\n")
        except Exception:
            pass

    return 0 if ok else 1


def _build_log_header(rzp_path: str, work: dict, job: dict,
                      rc: int, password=None, cmd=None) -> str:
    pass













    from core.tasks import job_to_runnable_settings                                

    lines = [
        f"--- Rizpaq task run {datetime.now()} ---",
        f"Task file: {rzp_path}",
        f"Work id:   {work.get('id','')}",
        f"Work:      {work.get('title','')}",
        f"Job id:    {job.get('id','')}",
        f"Job:       {job.get('title','')}",
        f"Action:    {job.get('action','backup')}",
    ]
    if cmd:
        try:
            lines.append(f"Command:   {safe_cmdline(cmd, password)}")
        except Exception:
            pass
    else:
                                                                      
                                                                
                                                                 
        try:
            _ = job_to_runnable_settings(work, job)                       
        except Exception:
            pass
    lines.append(f"Return code: {rc}")
    return "\n".join(lines)
