
















































from __future__ import annotations

import os
import re
import subprocess
import time

from PySide6.QtCore import QThread, Signal

from core.engine_path import EnginePathError, drop_substitutes, rewrite_cmd
from core.parser import ParseReport, parse_csv_line_reported
from core.proc_health import Liveness, effective_stall_timeout, make_cpu_reader
from core.zpaq_cli import decode_bytes

                                                              
                                                                  
                                                            
                                                             
                                                                
                                                                  
                                             
                                                                      
                                                                
DEFAULT_STALL_TIMEOUT = 90
STALL_TIMEOUT = DEFAULT_STALL_TIMEOUT
BUSY_STALL_MULTIPLIER = 30
POLL_INTERVAL = 0.05

                                                                 
                                                                  
TAIL_LIMIT = 16384


def _popen_kwargs() -> dict:
    pass
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kw


class StreamingListWorker(QThread):
    pass







    result = Signal(dict)

    def __init__(self, cmd, context=None, parent=None, cwd=None):
        super().__init__(parent)
        self._cmd = list(cmd)
        self._context = dict(context or {})
        self._cwd = cwd
        self._cancel = False
        self._proc = None

                                                                             

    def cancel_request(self):
        pass






        self._cancel = True
        p = self._proc
        if p is not None:
            try:
                p.kill()
            except Exception:
                pass

                                                                            

    def run(self):
        pass













        try:
            cmd, prep_cwd, subs = rewrite_cmd(self._cmd)
        except EnginePathError as exc:
            self.result.emit(self._make_result(
                rc=1, entries=[], report=ParseReport(),
                tail=f"ERROR: {exc}\n",
            ))
            return
        except Exception:
                                                       
            cmd, prep_cwd, subs = list(self._cmd), None, []

        run_cwd = self._cwd or prep_cwd

        try:
            rc, entries, report, tail = self._stream_with(cmd, run_cwd)
        except Exception as exc:
            rc, entries, report = 1, [], ParseReport()
            tail = f"ERROR: {exc}\n"
        finally:
            drop_substitutes(subs)

        self.result.emit(self._make_result(
            rc=rc, entries=entries, report=report, tail=tail,
        ))

    def _make_result(self, rc, entries, report, tail) -> dict:
        pass
        out = dict(self._context)
        out["rc"] = int(rc)
        out["cancelled"] = bool(self._cancel)
        out["entries"] = entries
        out["report"] = report
        out["tail"] = tail
        return out

                                                                            

    def _stream_with(self, cmd, run_cwd):
        pass










        entries: list = []
        report = ParseReport()
        tail_buf = bytearray()

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=run_cwd,
            **_popen_kwargs(),
        )
        self._proc = p

        try:
            fd = p.stdout.fileno()

            stall_used = effective_stall_timeout(
                DEFAULT_STALL_TIMEOUT, STALL_TIMEOUT)
            liv = Liveness(
                make_cpu_reader(p),
                stall_timeout=stall_used,
                busy_timeout=stall_used * BUSY_STALL_MULTIPLIER,
            )

            try:
                os.set_blocking(fd, False)
            except Exception:
                pass

            line_buf = b""

            while True:
                if self._cancel:
                    try:
                        p.kill()
                    except Exception:
                        pass
                    break

                if p.poll() is None:
                    liv.verdict()
                    if liv.stalled:
                        try:
                            p.kill()
                        except Exception:
                            pass
                        break

                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    chunk = b""

                if not chunk:
                    if p.poll() is not None:
                                                         
                        try:
                            rest = os.read(fd, 65536)
                            if rest:
                                chunk = rest
                        except OSError:
                            chunk = b""
                        if not chunk:
                            break
                    else:
                                                                         
                                                          
                        time.sleep(POLL_INTERVAL)
                        continue

                liv.note_data()

                                                                       
                                                                       
                                                                  
                                           
                tail_buf.extend(chunk)
                if len(tail_buf) > TAIL_LIMIT:
                    del tail_buf[: len(tail_buf) - TAIL_LIMIT]

                                                                        
                                                                          
                         
                line_buf += chunk
                while True:
                                                                 
                                                                      
                                                                      
                                                                      
                                                                        
                                                                     
                                                               
                    m = re.search(rb"[\r\n]", line_buf)
                    if m is None:
                        break
                    raw_line = line_buf[: m.start()]
                    line_buf = line_buf[m.end():]
                    if not raw_line.strip():
                        continue
                    entry = parse_csv_line_reported(
                        decode_bytes(raw_line), report
                    )
                    if entry is not None:
                        entries.append(entry)

                                                   
            if line_buf.strip():
                entry = parse_csv_line_reported(
                    decode_bytes(bytes(line_buf)), report
                )
                if entry is not None:
                    entries.append(entry)

            rc = p.wait()
        finally:
            try:
                if p.stdout is not None:
                    p.stdout.close()
            except Exception:
                pass
            self._proc = None

        tail = decode_bytes(bytes(tail_buf))
        return rc, entries, report, tail
