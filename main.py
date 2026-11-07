#!/usr/bin/env python3

































































































from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

                                                           
try:
    _HERE = Path(__file__).resolve().parent
except NameError:
    _HERE = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path.cwd()
    )
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


                                                                              
def _bundled_zpaq():
    pass
    if not getattr(sys, "frozen", False):
        return None
    name = "zpaqfranz.exe" if os.name == "nt" else "zpaqfranz"
    base = os.path.dirname(sys.executable)
    cand = os.path.join(base, name)
    if os.path.isfile(cand):
        return cand
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand2 = os.path.join(meipass, name)
        if os.path.isfile(cand2):
            return cand2
    return None


if not os.environ.get("ZPAQ_BIN"):
    _bz = _bundled_zpaq()
    if _bz:
        os.environ["ZPAQ_BIN"] = _bz


                                                                              
def _bundled_7z():
    pass
    name = "7z.exe"
                                       
    if not getattr(sys, "frozen", False):
        cand = _HERE / name
        if cand.is_file():
            return str(cand)
        return None

                                                     
    base = os.path.dirname(sys.executable)
    cand = os.path.join(base, name)
    if os.path.isfile(cand):
        return cand
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand2 = os.path.join(meipass, name)
        if os.path.isfile(cand2):
            return cand2
    return None


if not os.environ.get("SEVEN_ZIP_BIN"):
    _b7z = _bundled_7z()
    if _b7z:
        os.environ["SEVEN_ZIP_BIN"] = _b7z


                                                                              
def _bundled_par2():
    pass











    name = "par2.exe"
    if not getattr(sys, "frozen", False):
        cand = _HERE / name
        if cand.is_file():
            return str(cand)
        return None

    base = os.path.dirname(sys.executable)
    cand = os.path.join(base, name)
    if os.path.isfile(cand):
        return cand
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand2 = os.path.join(meipass, name)
        if os.path.isfile(cand2):
            return cand2
    return None


if not os.environ.get("PAR2_BIN"):
    _bpar2 = _bundled_par2()
    if _bpar2:
        os.environ["PAR2_BIN"] = _bpar2


                                                                              
def _find_icon():
    pass
    name = "app.ico"
    base = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else str(_HERE)
    )
    candidates = [os.path.join(base, name)]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, name))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _has_console() -> bool:
    pass






    try:
        return bool(sys.stdin is not None and sys.stdin.isatty())
    except Exception:
        return False


def _report_fatal(error_text: str) -> None:
    pass






    try:
        from core.config import write_error_log

        log_file = write_error_log(error_text)
    except Exception:
        log_file = None

    try:
        sys.stderr.write("=" * 70 + "\n")
        sys.stderr.write(error_text)
        sys.stderr.write("=" * 70 + "\n")
        if log_file:
            sys.stderr.write("Лог: " + str(log_file) + "\n")
        sys.stderr.flush()
    except Exception:
        pass

    if _has_console():
        try:
            if log_file:
                input("Лог сохранён в: " + str(log_file))
            else:
                input("Нажми Enter для выхода...")
        except Exception:
            pass


def main():
    args = sys.argv[1:]

                                                                               
                                                                           
     
                                                                           
                                                                           
                                                                        
                                                                          
                                                                        
                                                 
     
                                                                        
                                                                          
                                      
                                                                               
    if args and str(args[0]).strip() == "--task":
        from core.headless import _headless_task

        rc = _headless_task(list(args[1:]))
        sys.exit(rc)

                                                                               
    try:
        from PySide6.QtGui import QFont, QIcon
        from PySide6.QtWidgets import QApplication, QMessageBox
        from ui.palette import apply_theme
        from ui.main_window import MainWindow
    except Exception:
                                                                       
                                                                          
        _report_fatal(traceback.format_exc())
        sys.exit(1)

    app = QApplication(sys.argv)
                                                                         
                                                                         
                                                                            
    try:
        app.setFont(QFont("Segoe UI", 9))
    except Exception:
        pass
    try:
                                                              
                                                            
                                                              
                                                      
        try:
            from ui.config_bridge import _load_cfg
            apply_theme(app, _load_cfg().skin)
        except Exception:
            apply_theme(app)
    except Exception:
        traceback.print_exc()

    icon_path = _find_icon()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

                                                                             
    from core.headless import is_headless_op, run_headless
    if is_headless_op(args):
        rc = run_headless(args)
        sys.exit(rc)

                                                                             
     
                                 
                                                                    
                                                                     
                                                                    
                                            
     
                                                                      
                                                                     
                                                                 
    from core.cli import find_archive_arg, handle_cli_command
    from core.single_instance import SERVER_NAME, SingleInstance

    si = SingleInstance()
    if si.try_send_to_existing(args):
        sys.exit(0)

                                                                   
                                                                     
                                                                       
                                                               
    if not si.listen():
                                                                        
                                                                       
                                                         
        try:
            from core.config import write_error_log
            write_error_log(
                "single_instance: QLocalServer.listen() failed for "
                f"{SERVER_NAME!r}; running without IPC."
            )
        except Exception:
            pass

                                                                              
                                                                  
                                                                      
                                                                       
                                                                     
                                                                    
    try:
        from core.temp_cleanup import cleanup_stale_temp

        _stale = cleanup_stale_temp()
        if _stale:
            print(f"Rizpaq: cleaned {len(_stale)} stale temp dir(s)")
    except Exception:
        pass

                                                                             
                                                                    
                                                                     
                                                                   
                                                                   
                                                          
                                                                       
             
    try:
        from core.config import load as _cfg_load

        _associations_done = bool(
            getattr(_cfg_load(), "associations_asked", False)
        )
    except Exception:
                                                                 
        _associations_done = True

    if not _associations_done:
        try:
            from core.file_association import (
                is_registered,
                is_rzp_registered,
                register,
            )

            need_zpaq = not is_registered()
            need_rzp = not is_rzp_registered()
            if need_zpaq or need_rzp:
                register()
        except Exception:
            pass

                                                               
                                                                   
                                                                  
                                  
        try:
            from core.config import update as _cfg_update
            _cfg_update(associations_asked=True)
        except Exception:
            pass

    try:
                                                                     
                                                                  
                                                               
                                                                     
        window = MainWindow()
        window.show()

        from PySide6.QtCore import QTimer

                                                                      
                                                                   
                                                                      
                                                             
                                                                    
                                                                     
        try:
            QTimer.singleShot(800, window.show_startup_digest)
        except Exception:
            pass

                                                                 
                                                                         
                                                                         
                                                                    
        try:
            QTimer.singleShot(1500, window.start_update_check)
        except Exception:
            pass

                                                                    
                                                  
        si.setParent(window)

                                                                    
                                                                 
                                                                    
                                                                      
                                                                     
                      
        si.connect_command_receiver(
            lambda a: handle_cli_command(window, a)
        )

                                                                   
                                                                           
        if find_archive_arg(args):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda a=args: handle_cli_command(window, a))

        rc = app.exec()
    except Exception:
        error_text = traceback.format_exc()
                                                                 
                                                                       
                                                           
        log_file = None
        try:
            from core.config import write_error_log

            log_file = write_error_log(error_text)
        except Exception:
            pass

        if log_file:
            try:
                print("Rizpaq: лог ошибок -> " + str(log_file))
            except Exception:
                pass

        try:
            QMessageBox.critical(None, "Ошибка запуска Rizpaq", error_text)
        except Exception:
            pass
        rc = 1

    sys.exit(rc)


if __name__ == "__main__":
    main()
