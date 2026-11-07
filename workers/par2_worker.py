


























































from __future__ import annotations

import os

from PySide6.QtCore import QThread, Signal

from core import par2_ops


class Par2CreateWorker(QThread):
    pass

    done = Signal(dict)
                                                                     
                                                                    
                                                                
    line_received = Signal(str)

    def __init__(
        self,
        bin_path: str,
        archive_path: str,
        options: dict = None,
        unchanged_size=None,
        parent=None,
    ):
        super().__init__(parent)
        self._bin_path = bin_path
        self._archive_path = str(archive_path)
        self._options = dict(options or {})
        self._unchanged_size = unchanged_size

        self._cancel = False
        self._proc = None

                                                                             

    def cancel_request(self):
        pass






        self._cancel = True
        proc = self._proc
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass

                                                                             

    def run(self):
        result = {
            "ok": False,
            "cancelled": False,
            "state": par2_ops.STATE_FAILED,
            "log": "",
            "recorded_size": None,
            "archive_path": self._archive_path,
            "skipped": False,
        }

                                                                    
                                                                    
                                                                      
        try:
            res = par2_ops.refresh_par2_set(
                self._bin_path,
                self._archive_path,
                redundancy=self._opt("redundancy", 5),
                memory_mb=self._opt("memory_mb"),
                threads=self._opt("threads"),
                block_size=self._opt("block_size"),
                recursion=bool(self._opt("recursion")),
                skip_if_unchanged=self._unchanged_size is not None,
                unchanged_size=self._unchanged_size,
                register=self._register_proc,
                on_line=self.line_received.emit,
            )
            result.update(
                ok=bool(res.ok),
                state=res.state,
                log=res.log or "",
                recorded_size=res.recorded_size,
                skipped=bool(res.skipped),
            )
        except Exception as exc:
                                                                          
                                                                
            result["state"] = par2_ops.STATE_FAILED
            result["log"] = f"{type(exc).__name__}: {exc}"

        result["cancelled"] = bool(self._cancel)
        if self._cancel:
                                                                      
                                           
            result["ok"] = False

        self.done.emit(result)

                                                                            

    def _opt(self, key, default=None):
        pass





        value = self._options.get(key, default)
        if value is None or value == "":
            return default
        try:
            if int(value) <= 0:
                return default
        except (TypeError, ValueError):
            return default
        return value

    def _register_proc(self, proc):
        pass
        self._proc = proc
        if self._cancel:
                                                                
            try:
                proc.kill()
            except Exception:
                pass


class Par2VerifyWorker(QThread):
    pass













    done = Signal(dict)

    def __init__(self, bin_path: str, archive_path: str, parent=None):
        super().__init__(parent)
        self._bin_path = bin_path
        self._archive_path = str(archive_path)

        self._cancel = False
        self._proc = None

    def cancel_request(self):
        pass
        self._cancel = True
        proc = self._proc
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass

    def run(self):
                                                                      
                                                                
        try:
            par2_path = par2_ops.par2_main_name(self._archive_path)
        except Exception as exc:
            self.done.emit({
                "ok": False,
                "cancelled": False,
                "state": par2_ops.STATE_FAILED,
                "log": f"{type(exc).__name__}: {exc}",
                "recorded_size": None,
                "archive_path": self._archive_path,
                "par2_path": "",
            })
            return

        result = {
            "ok": False,
            "cancelled": False,
            "state": par2_ops.STATE_FAILED,
            "log": "",
            "recorded_size": None,
            "archive_path": self._archive_path,
            "par2_path": par2_path,
        }

        try:
            res = par2_ops.verify_parset(
                self._bin_path, par2_path, register=self._register_proc
            )
            result.update(
                ok=bool(res.ok),
                state=res.state,
                log=res.log or "",
                recorded_size=res.recorded_size,
            )
        except Exception as exc:
            result["log"] = f"{type(exc).__name__}: {exc}"

        result["cancelled"] = bool(self._cancel)
        if self._cancel:
            result["ok"] = False
        self.done.emit(result)

    def _register_proc(self, proc):
        self._proc = proc
        if self._cancel:
            try:
                proc.kill()
            except Exception:
                pass


class Par2RepairWorker(QThread):
    pass

















    done = Signal(dict)

    def __init__(self, bin_path: str, archive_path: str,
                 recorded_size: int, parent=None):
        super().__init__(parent)
        self._bin_path = bin_path
        self._archive_path = str(archive_path)
        self._recorded_size = int(recorded_size)

        self._cancel = False
        self._proc = None

    def cancel_request(self):
        self._cancel = True
        proc = self._proc
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass

    def run(self):
        result = {
            "ok": False,
            "cancelled": False,
            "state": par2_ops.STATE_FAILED,
            "log": "",
            "archive_path": self._archive_path,
            "recorded_size": self._recorded_size,
            "actual_size": None,
        }
                                                                  
                                                                    
                                                
        try:
            try:
                result["actual_size"] = os.path.getsize(self._archive_path)
            except OSError:
                pass

            res = par2_ops.repair_parset(
                self._bin_path,
                par2_ops.par2_main_name(self._archive_path),
                archive_path=self._archive_path,
                recorded_size=self._recorded_size,
                register=self._register_proc,
            )
            result.update(ok=bool(res.ok), state=res.state, log=res.log or "")
        except Exception as exc:
            result["log"] = f"{type(exc).__name__}: {exc}"
            result["state"] = par2_ops.STATE_FAILED

        result["cancelled"] = bool(self._cancel)
        if self._cancel:
            result["ok"] = False
        self.done.emit(result)

    def _register_proc(self, proc):
        self._proc = proc
