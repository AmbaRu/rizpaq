from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.paths import find_extracted_path, merge_tree
from core.proc_health import Liveness, effective_stall_timeout, make_cpu_reader


from core.engine_path import (
    EnginePathError,
    discard_staging_if_empty,
    make_staging,
    move_to_dest,
    needs_staging,
)
from workers.streaming import (
    BUSY_STALL_MULTIPLIER,
    DEFAULT_STALL_TIMEOUT,
    StreamingZpaqThread,
    popen_kwargs,
)


STALL_TIMEOUT = DEFAULT_STALL_TIMEOUT


PROC_POLL_INTERVAL = 0.1


MAX_ERROR_LOGS = 10
MAX_ERROR_LOG_CHARS = 4000


def _read_until_exit(proc, cancelled):
    fd = proc.stdout.fileno()
    try:
        os.set_blocking(fd, False)
    except Exception:


        pass

    stall_used = effective_stall_timeout(DEFAULT_STALL_TIMEOUT, STALL_TIMEOUT)
    liv = Liveness(
        make_cpu_reader(proc),
        stall_timeout=stall_used,
        busy_timeout=stall_used * BUSY_STALL_MULTIPLIER,
    )
    chunks = []
    note = ""

    def drain():

        while True:
            try:
                rest = os.read(fd, 65536)
            except OSError:
                return
            if not rest:
                return
            chunks.append(rest)

    while True:
        if cancelled():
            try:
                proc.kill()
            except Exception:
                pass
            drain()
            break

        try:
            chunk = os.read(fd, 65536)
        except OSError:
            chunk = b""

        if chunk:
            chunks.append(chunk)
            liv.note_data()
            continue

        if proc.poll() is not None:
            drain()
            break

        if liv.verdict().stalled:
            note = (
                "движок не отвечал: " + liv.describe()
                + ". Извлечение прервано, чтобы окно не ждало вечно."
            )
            try:
                proc.kill()
            except Exception:
                pass
            drain()
            break

        time.sleep(PROC_POLL_INTERVAL)

    try:
        proc.wait(timeout=5)
    except Exception:
        pass

    return proc.returncode, b"".join(chunks), note


class ExtractFileWorker(StreamingZpaqThread):


    worker_started = Signal()
    done = Signal(dict)

    def __init__(self, zpaq, archive, password, inner, version, dest, parent=None):


        self.real_dest = dest


        self.staged = ""
        self.staged_path = ""

        target = dest
        if needs_staging(dest):
            try:
                self.staged_path = make_staging(dest)
                target = self.staged_path
                self.staged = "1"
            except EnginePathError as exc:


                cmd = [zpaq, "l", archive]
                super().__init__(cmd, parent)
                self.dest = dest
                self._prepare_error = f"ERROR: {exc}\n"
                return

        cmd = [zpaq, "x", archive]

        if password:
            cmd += ["-key", password]


        cmd.append(inner)

        if isinstance(version, int):
            cmd += ["-until", str(version)]

        cmd += ["-to", target]

        super().__init__(cmd, parent)
        self.dest = dest

    def run(self):
        self.worker_started.emit()

        if getattr(self, "_prepare_error", ""):
            self.done.emit(
                {
                    "kind": "extract_file",
                    "success": False,
                    "cancelled": False,
                    "output": self._prepare_error,
                    "dest": self.real_dest,
                    "staged": "",
                }
            )
            return

        rc, text = self._run_stream()

        moved = True
        note = ""
        left = ""

        if self.staged_path and rc == 0 and not self._cancel:
            moved, note = move_to_dest(self.staged_path, self.real_dest)
            if moved:
                self.staged = ""
        elif self.staged_path:


            if not discard_staging_if_empty(self.staged_path):
                left = self.staged_path
                note = (
                    f"извлечение не удалось, но файл мог остаться частично — "
                    f"он здесь: {self.staged_path}"
                )
        else:
            moved = rc == 0 and not self._cancel

        if note:
            text = (text + "\n" if text else "") + "[rizpaq] " + note

        success = rc == 0 and not self._cancel and moved

        self.done.emit(
            {
                "kind": "extract_file",
                "success": success,
                "cancelled": bool(self._cancel),
                "output": text,


                "dest": self.real_dest,


                "staged": left or (self.staged_path if not moved else ""),
            }
        )

class ExtractFolderBatchWorker(StreamingZpaqThread):


    worker_started = Signal()
    done = Signal(dict)

    def __init__(
        self,
        zpaq,
        archive,
        password,
        inner_prefix,
        version,
        dest_folder,
        parent=None,
    ):
        self.zpaq = zpaq
        self.archive = archive
        self.password = password
        self.inner_prefix = inner_prefix or ""
        self.version = version
        self.dest_folder = dest_folder


        self.cmd = self._build_cmd(self.dest_folder)

        super().__init__(self.cmd, parent)

    def _build_cmd(self, out_dir):
        cmd = [self.zpaq, "x", self.archive]

        if self.password:
            cmd += ["-key", self.password]

        pat = (self.inner_prefix.rstrip("/") + "/*") if self.inner_prefix else "*"
        cmd += ["-only", pat]

        if isinstance(self.version, int):
            cmd += ["-until", str(self.version)]

        cmd += ["-to", str(out_dir)]

        return cmd

    def _layout_diagnostics(self, root: Path) -> str:
        lines = []

        try:
            entries = sorted(root.rglob("*"))

            for p in entries[:50]:
                try:
                    lines.append("   " + str(p.relative_to(root)))
                except Exception:
                    lines.append("   " + str(p))

            if len(entries) > 50:
                lines.append(f"   ... ({len(entries) - 50} more)")
        except Exception:
            pass

        return "\n".join(lines)

    def run(self):
        self.worker_started.emit()

        dest = Path(self.dest_folder)
        staging = None

        log = ""
        ok = False
        cancelled = False

        try:
            if dest.exists() and dest.is_file():
                raise NotADirectoryError(f"Destination is a file: {dest}")

            dest.mkdir(parents=True, exist_ok=True)


            try:
                staging = Path(
                    tempfile.mkdtemp(
                        prefix="rizpaq_batch_",
                        dir=str(dest.parent),
                    )
                )
            except Exception:
                staging = Path(tempfile.mkdtemp(prefix="rizpaq_batch_"))

            self.cmd = self._build_cmd(staging)

            rc, log = self._run_stream()
            cancelled = bool(self._cancel)

            if not cancelled and rc == 0:
                if self.inner_prefix:
                    source = find_extracted_path(
                        staging,
                        self.inner_prefix,
                        want_dir=True,
                    )

                    if source is None:


                        try:
                            has_any = any(staging.iterdir())
                        except Exception:
                            has_any = False

                        if not has_any:
                            ok = True
                            log += (
                                "\n[layout] no files extracted "
                                "(the folder is empty or no data matched)."
                            )
                        else:
                            log += (
                                "\n[layout] extracted folder for "
                                f"'{self.inner_prefix}' was not found "
                                "in temporary output."
                            )

                            listing = self._layout_diagnostics(staging)
                            if listing:
                                log += "\n[layout] temporary content:\n" + listing
                    else:
                        merge_tree(source, dest)
                        ok = True
                else:

                    merge_tree(staging, dest)
                    ok = True

            elif not cancelled:
                log += f"\n[layout] zpaqfranz return code: {rc}"

        except Exception as exc:
            log += f"\n[layout] error: {exc}"

        finally:
            if staging is not None:


                if ok or cancelled:
                    shutil.rmtree(staging, ignore_errors=True)
                else:
                    log += (
                        "\n[layout] temporary data kept: " + str(staging)
                        + "\n[layout] files that could not be placed into "
                          "the destination are still there; move them "
                          "yourself or delete this folder."
                    )

        self.done.emit(
            {
                "kind": "extract_folder_batch",
                "ok": ok,
                "cancelled": cancelled,
                "dest_folder": str(dest),


                "staging": (
                    str(staging) if (staging and not (ok or cancelled)) else ""
                ),
                "log": log,
            }
        )


class ExtractFolderWorker(QThread):


    worker_started = Signal(int)
    tick = Signal(int, int, str)
    done = Signal(dict)

    def __init__(self, zpaq, archive, password, tasks, dest_folder, parent=None):
        super().__init__(parent)

        self.zpaq = zpaq
        self.archive = archive
        self.password = password
        self.tasks = tasks
        self.dest_folder = dest_folder

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

    def run(self):
        total = len(self.tasks)
        self.worker_started.emit(total)

        ok = 0
        errors = []
        error_logs = []

        for i, (inner, version, dest) in enumerate(self.tasks):
            if self._cancel:
                break

            cmd = [self.zpaq, "x", self.archive]

            if self.password:
                cmd += ["-key", self.password]


            cmd.append(inner)

            if isinstance(version, int):
                cmd += ["-until", str(version)]

            cmd += ["-to", dest]

            self.tick.emit(i, total, inner)

            try:
                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    **popen_kwargs(),
                )
                self._proc = p
                rc, out, note = _read_until_exit(p, lambda: self._cancel)
            except Exception as exc:


                rc = 1
                out = f"ERROR: {exc}".encode("utf-8", "replace")
                note = ""

            if note:
                out += ("\n[rizpaq] " + note).encode("utf-8", "replace")

            if rc == 0:
                ok += 1
            else:
                errors.append(inner)
                if out and len(error_logs) < MAX_ERROR_LOGS:
                    error_logs.append(
                        out.decode("utf-8", "replace")[:MAX_ERROR_LOG_CHARS]
                    )

        self.done.emit(
            {
                "kind": "extract_folder",
                "ok": ok,
                "total": total,
                "dest_folder": str(self.dest_folder),
                "errors": errors,
                "error_logs": error_logs,
                "cancelled": bool(self._cancel),
            }
        )


class ExtractSalvageWorker(StreamingZpaqThread):


    worker_started = Signal()
    done = Signal(dict)

    def __init__(
        self,
        zpaq,
        archive,
        password,
        dest_folder,
        ram_gb=None,
        parent=None,
    ):
        self.zpaq = zpaq
        self.archive = archive
        self.password = password
        self.dest_folder = str(dest_folder)
        self.ram_gb = ram_gb


        self.cmd = self._build_cmd(self.dest_folder)

        super().__init__(self.cmd, parent)

    def _build_cmd(self, out_dir):
        cmd = [self.zpaq, "xx", self.archive]

        if self.password:
            cmd += ["-key", self.password]


        cmd.append("-force")

        if self.ram_gb:
            cmd += ["-ramsize", f"{int(self.ram_gb)}GB"]

        cmd += ["-to", str(out_dir)]

        return cmd

    def run(self):
        self.worker_started.emit()

        dest = Path(self.dest_folder)

        try:
            dest.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.done.emit(
                {
                    "kind": "extract_salvage",
                    "ok": False,
                    "cancelled": False,
                    "rc": -1,
                    "log": f"ERROR: {exc}\n",
                    "dest_folder": self.dest_folder,
                }
            )
            return

        rc, log = self._run_stream()
        cancelled = bool(self._cancel)


        ok = rc == 0 and not cancelled

        self.done.emit(
            {
                "kind": "extract_salvage",
                "ok": ok,
                "cancelled": cancelled,
                "rc": int(rc),
                "log": log,
                "dest_folder": self.dest_folder,
            }
        )
