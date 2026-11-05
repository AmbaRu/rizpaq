from __future__ import annotations

import os
import re
import subprocess
import time


from core.engine_path import (
    EnginePathError,
    drop_substitutes,
    rewrite_cmd,
)
from core.proc_health import (
    Liveness,
    effective_stall_timeout,
    make_cpu_reader,
)

from PySide6.QtCore import QThread, Signal


PERCENT_RE = re.compile(rb"(\d{1,3}(?:[.,]\d+)?)\s*%")


OF_RE = re.compile(rb"(\d+)\s+of\s+(\d+)")


SPEED_RE = re.compile(
    rb"(?:@\s*)?(\d+(?:[.,]\d+)?)\s*(B|KB|MB|GB|TB)/s",
    re.IGNORECASE,
)


ETA_RE = re.compile(rb"\d+(?:[.,]\d+)?%\s+(\d{2}:\d{2}:\d{2})")


ADD_FILES_RE = re.compile(
    rb"Add\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+([\d.]+)\s+"
)


ADD_DIRS_RE = re.compile(rb"\(([\d.]+)\s+dirs\)")


EXTRACT_INFO_RE = re.compile(
    rb"Extract\s+([\d.]+)\s+bytes\s+\(([^)]+)\)\s+in\s+([\d.]+)\s+files\s+\(([\d.]+)\s+folders?\)",
    re.IGNORECASE,
)


DEFAULT_STALL_TIMEOUT = 90
STALL_TIMEOUT = DEFAULT_STALL_TIMEOUT


BUSY_STALL_MULTIPLIER = 30


POLL_INTERVAL = 0.05


_PASSWORD_PROMPT = re.compile(rb"Enter AES password", re.IGNORECASE)


def popen_kwargs() -> dict:

    kw = {}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kw


def _decode_line(raw: bytes) -> str:
    if not raw:
        return ""
    for enc in ("utf-8", "cp1251", "cp866", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def _parse_european_number(raw: bytes) -> int:
    try:
        text = raw.decode("ascii", "replace").strip()
        return int(text.replace(".", ""))
    except (ValueError, AttributeError):
        return 0


def _extract_percent(chunk: bytes) -> int:
    best = -1
    for m in PERCENT_RE.finditer(chunk):
        try:
            val_str = m.group(1).decode("ascii", "replace").replace(",", ".")
            v = int(float(val_str))
        except Exception:
            v = -1
        if 0 <= v <= 100:
            best = v
    if best >= 0:
        return best

    for m in OF_RE.finditer(chunk):
        try:
            a = int(m.group(1))
            b = int(m.group(2))
        except Exception:
            continue
        if b > 0:
            best = int(a * 100 // b)
    return best


def _extract_speed(chunk: bytes) -> str:
    matches = list(SPEED_RE.finditer(chunk))
    if matches:
        m = matches[-1]
        try:
            val = m.group(1).decode("ascii", "replace").replace(",", ".")
            unit = m.group(2).decode("ascii", "replace").upper()
            return f"{val} {unit}/s"
        except Exception:
            pass
    return ""


def _extract_eta(chunk: bytes) -> str:
    matches = list(ETA_RE.finditer(chunk))
    if matches:
        try:
            return matches[-1].group(1).decode("ascii", "replace")
        except Exception:
            pass
    return ""


def _extract_add_info(chunk: bytes):
    m_files = ADD_FILES_RE.search(chunk)
    m_dirs = ADD_DIRS_RE.search(chunk)
    files = None
    dirs = None
    if m_files:
        files = _parse_european_number(m_files.group(1))
    if m_dirs:
        dirs = _parse_european_number(m_dirs.group(1))
    if files is not None or dirs is not None:
        return files, dirs
    return None, None


def _extract_extract_info(chunk: bytes):
    m = EXTRACT_INFO_RE.search(chunk)
    if not m:
        return None, None, None, ""
    try:
        bytes_total = _parse_european_number(m.group(1))
        files_total = _parse_european_number(m.group(3))
        dirs_total = _parse_european_number(m.group(4))
        bytes_text = m.group(2).decode("ascii", "replace").strip()
        return files_total, dirs_total, bytes_total, bytes_text
    except Exception:
        return None, None, None, ""


class StreamingZpaqThread(QThread):

    percent = Signal(int)
    progress_info = Signal(dict)
    line_received = Signal(str)

    def __init__(self, cmd, parent=None, cwd=None):
        super().__init__(parent)
        self.cmd = cmd
        self.cwd = cwd
        self._cancel = False
        self._proc = None

    def cancel_request(self):
        self._cancel = True
        p = self._proc
        if p is not None:
            try:
                p.kill()
            except Exception:
                pass

    def _run_stream(self):
        try:
            cmd, prep_cwd, subs = rewrite_cmd(self.cmd)
        except EnginePathError as exc:


            return 1, f"ERROR: {exc}\n"
        except Exception:

            cmd, prep_cwd, subs = list(self.cmd), None, []


        run_cwd = self.cwd or prep_cwd

        try:
            return self._stream_with(cmd, run_cwd)
        finally:
            drop_substitutes(subs)

    def _stream_with(self, cmd, run_cwd):

        chunks = []
        rc = 1
        tail_note = ""


        stalled = False
        p = None

        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=run_cwd,
                **popen_kwargs(),
            )
            self._proc = p
            fd = p.stdout.fileno()


            stall_used = effective_stall_timeout(
                DEFAULT_STALL_TIMEOUT, STALL_TIMEOUT)
            liv = Liveness(make_cpu_reader(p),
                           stall_timeout=stall_used,
                           busy_timeout=stall_used * BUSY_STALL_MULTIPLIER)


            try:
                os.set_blocking(fd, False)
            except Exception:
                pass

            last_pct = -1
            last_speed = ""
            last_eta = ""
            files_total = None
            dirs_total = None
            bytes_total = None
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
                        stalled = True
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
                chunks.append(chunk)

                line_buf += chunk
                while True:


                    m = re.search(rb"[\r\n]", line_buf)
                    if not m:
                        break
                    raw_line = line_buf[: m.start()]
                    line_buf = line_buf[m.end():]
                    if raw_line.strip():
                        self.line_received.emit(_decode_line(raw_line))

                val = _extract_percent(chunk)
                if 0 <= val <= 100 and val != last_pct:
                    last_pct = val
                    self.percent.emit(val)

                info = {}
                changed = False

                speed = _extract_speed(chunk)
                if speed and speed != last_speed:
                    last_speed = speed
                    info["speed"] = speed
                    changed = True

                eta = _extract_eta(chunk)
                if eta and eta != last_eta:
                    last_eta = eta
                    info["eta"] = eta
                    changed = True

                f, d = _extract_add_info(chunk)
                if f is not None and f != files_total:
                    files_total = f
                    dirs_total = d
                    info["files_total"] = f
                    if d is not None:
                        info["dirs_total"] = d
                    changed = True

                ef, ed, eb, _eb_text = _extract_extract_info(chunk)
                if ef is not None and ef != files_total:
                    files_total = ef
                    info["files_total"] = ef
                    changed = True


                if ed is not None and ed != dirs_total:
                    dirs_total = ed
                    info["dirs_total"] = ed
                    changed = True
                if eb is not None and eb != bytes_total:
                    bytes_total = eb
                    info["bytes_total"] = eb
                    changed = True

                if changed:
                    self.progress_info.emit(info)

            if line_buf.strip():
                self.line_received.emit(_decode_line(line_buf))

            rc = p.wait()


            if stalled:
                if _PASSWORD_PROMPT.search(b"".join(chunks[-6:])):
                    tail_note = (
                        "\n[rizpaq] zpaqfranz запросил пароль и ждал ввода. "
                        "Обычно это значит, что движок не смог открыть файл: "
                        "путь содержит нелатинские символы, а на этом томе "
                        "недоступны короткие имена 8.3."
                    )
                else:
                    tail_note = (
                        f"\n[rizpaq] движок не вывел ничего "
                        f"{int(stall_used)} с при живом процессе — "
                        f"работа прервана."
                    )
        except Exception as exc:
            rc = 1


            tail_note = f"\n[rizpaq] внутренняя ошибка чтения вывода: {exc!r}"
        finally:


            if p is not None:
                try:
                    if p.stdout is not None:
                        p.stdout.close()
                except Exception:
                    pass

        data = b"".join(chunks)
        try:
            text = data.decode("utf-8", "replace")
        except Exception:
            text = ""
        if tail_note:
            text += tail_note
        return rc, text
