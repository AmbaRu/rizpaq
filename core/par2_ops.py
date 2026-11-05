from __future__ import annotations

import os
import re
import string
import subprocess
import sys
import threading
from pathlib import Path
from typing import List, NamedTuple, Optional

from core.zpaq_cli import decode_bytes


STATE_OK = "ok"

STATE_DAMAGED = "damaged"


STATE_UNREPAIRABLE = "unrepairable"

STATE_MISSING = "missing"

STATE_BROKEN = "broken"

STATE_FAILED = "failed"


DAMAGED_STATES = (STATE_DAMAGED, STATE_UNREPAIRABLE)


class Par2Result(NamedTuple):

    ok: bool
    state: str
    log: str = ""
    recorded_size: Optional[int] = None


    skipped: bool = False

    @property
    def damaged(self) -> bool:
        return self.state in DAMAGED_STATES

    @property
    def repairable(self) -> bool:

        return self.state == STATE_DAMAGED

    @property
    def has_set(self) -> bool:

        return self.state in (STATE_OK,) + DAMAGED_STATES


def find_par2() -> Optional[str]:
    env_bin = os.environ.get("PAR2_BIN")
    if env_bin and os.path.isfile(env_bin):
        return env_bin

    if not getattr(sys, "frozen", False):
        try:
            here = Path(__file__).resolve().parent.parent
            cand = here / "par2.exe"
            if cand.is_file():
                return str(cand)
        except Exception:
            pass
    return None


def check_par2(bin_path: str) -> bool:

    if not bin_path or not os.path.isfile(bin_path):
        return False
    try:
        res = subprocess.run(
            [bin_path, "-V"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return res.returncode == 0
    except Exception:
        return False


_VOL_RE = re.compile(r"\.vol\d+\+\d+\.par2$", re.IGNORECASE)


def default_options() -> dict:
    return {
        "redundancy": 5,
        "block_size": None,
        "block_count": None,
        "recursion": False,
        "uniform": False,
    }


def par2_main_name(archive_path: str) -> str:
    return str(archive_path) + ".par2"


def par2_set_files(archive_path: str) -> List[str]:
    main = par2_main_name(archive_path)
    out: List[str] = []
    if os.path.isfile(main):
        out.append(main)

    folder = os.path.dirname(main) or "."
    archive_base = os.path.basename(str(archive_path))
    try:
        names = os.listdir(folder)
    except OSError:
        return out

    for name in names:
        if name == os.path.basename(main):
            continue
        if _TEMP_MARK in name:
            continue
        if _VOL_RE.search(name) and name.startswith(archive_base):
            out.append(os.path.join(folder, name))

    out.sort()
    return out


def remove_par2_set(archive_path: str) -> List[str]:
    removed: List[str] = []
    for path in par2_set_files(archive_path):
        try:
            os.remove(path)
            removed.append(path)
        except OSError:
            continue
    return removed


_MAX_SET_PATH = 240


class SubstLetter:

    def __init__(self, folder: str):
        self.folder = folder
        self.letter: Optional[str] = None


        self.required = False
        self.failed = False

    def __enter__(self) -> Optional[str]:
        self.required = needs_subst(self.folder)
        if not self.required:
            return None
        if os.name != "nt":


            self.required = False
            return None

        for letter in string.ascii_uppercase:
            drive = letter + ":"


            if os.path.exists(drive):
                continue
            try:
                res = subprocess.run(
                    ["subst", drive, self.folder],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    stdin=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except Exception:
                continue
            if res.returncode == 0:
                self.letter = drive
                return drive

        self.failed = True
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.letter:
            try:
                subprocess.run(
                    ["subst", self.letter, "/d"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    stdin=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except Exception:
                pass
            self.letter = None
        return False


def needs_subst(folder: str) -> bool:
    name = os.path.basename(str(folder).rstrip("\\/")) or "x"
    probe = os.path.join(str(folder), name + ".zpaq.vol127+35.par2")
    return len(probe) > _MAX_SET_PATH


def _popen_kwargs() -> dict:

    kw = {}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kw


def _kill(proc) -> None:

    try:
        proc.kill()
    except Exception:
        pass


def _run(bin_path: str, args: List[str], timeout: int, register=None,
         on_line=None):
    try:
        proc = subprocess.Popen(
            [bin_path] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            **_popen_kwargs(),
        )
    except Exception as exc:
        return "error", f"{type(exc).__name__}: {exc}"

    if callable(register):
        try:
            register(proc)
        except Exception:
            pass

    if on_line is None:
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill(proc)
            try:
                out, _ = proc.communicate(timeout=10)
            except Exception:
                out = b""
            return "timeout", decode_bytes(out or b"")
        except Exception as exc:
            _kill(proc)
            return "error", f"{type(exc).__name__}: {exc}"

        return proc.returncode, decode_bytes(out)

    lines: List[str] = []

    def _pump() -> None:
        try:
            for raw in iter(proc.stdout.readline, b""):
                text = decode_bytes(raw).strip("\r\n")
                if text:
                    lines.append(text)
                try:
                    on_line(text)
                except Exception:

                    pass
        except Exception:
            pass

    pump = threading.Thread(target=_pump, daemon=True)
    pump.start()
    try:
        proc.wait(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        _kill(proc)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        rc = "timeout"
    except Exception:
        _kill(proc)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        rc = "error"
    pump.join(timeout=5)
    return rc, "\n".join(lines)


_SIZE_RE = re.compile(
    r"total size of the data files is\s+([0-9,]+)\s*bytes", re.IGNORECASE
)


def read_recorded_size(log: str) -> Optional[int]:
    if not log:
        return None
    m = _SIZE_RE.search(log)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", "").replace(" ", ""))
    except ValueError:
        return None


_RE_OK = re.compile(r"All files are correct", re.IGNORECASE)
_RE_DAMAGED = re.compile(r"-\s*damaged", re.IGNORECASE)
_RE_TARGET_MISSING = re.compile(r"-\s*missing", re.IGNORECASE)
_RE_REPAIR_POSSIBLE = re.compile(r"Repair is possible", re.IGNORECASE)
_RE_REPAIR_IMPOSSIBLE = re.compile(r"Repair is not possible", re.IGNORECASE)
_RE_SET_UNREADABLE = re.compile(
    r"Unable to load|Cannot load|is not a valid par2 file|"
    r"Cannot find|does not exist|No files could be found",
    re.IGNORECASE,
)


def classify_verify_log(log: str) -> Optional[str]:
    if not log:
        return None


    if _RE_OK.search(log):
        return STATE_OK


    if _RE_DAMAGED.search(log):


        if _RE_REPAIR_IMPOSSIBLE.search(log):
            return STATE_UNREPAIRABLE
        if _RE_REPAIR_POSSIBLE.search(log):
            return STATE_DAMAGED


        return STATE_UNREPAIRABLE


    if _RE_TARGET_MISSING.search(log):
        return STATE_MISSING


    if _RE_SET_UNREADABLE.search(log):
        return STATE_BROKEN

    return None


def _classify_verify(rc, log: str) -> Par2Result:
    by_log = classify_verify_log(log)
    if by_log == STATE_OK:
        return Par2Result(True, STATE_OK, log, read_recorded_size(log))
    if by_log in DAMAGED_STATES:
        return Par2Result(
            False, by_log, log, read_recorded_size(log)
        )
    if by_log in (STATE_MISSING, STATE_BROKEN):
        return Par2Result(False, by_log, log, read_recorded_size(log))


    if rc == 0:
        return Par2Result(True, STATE_OK, log, read_recorded_size(log))
    if rc == 1:
        return Par2Result(
            False, STATE_DAMAGED, log, read_recorded_size(log)
        )
    if rc == 3:

        return Par2Result(False, STATE_MISSING, log)
    if rc == 2:


        return Par2Result(False, STATE_UNREPAIRABLE, log,
                          read_recorded_size(log))
    return Par2Result(False, STATE_FAILED, log)


def create_parset(
    bin_path: str,
    archive_path: str,
    *,
    redundancy: int = 5,
    memory_mb: Optional[int] = None,
    threads: Optional[int] = None,
    block_size: Optional[int] = None,
    recursion: bool = False,
    set_name: Optional[str] = None,
    timeout: int = 3600,
    register=None,
    on_line=None,
) -> Par2Result:
    if not bin_path or not os.path.isfile(bin_path):
        return Par2Result(False, STATE_FAILED, "par2 не найден")


    subst = SubstLetter(os.path.dirname(str(archive_path)) or ".")
    with subst as drive:
        target = str(archive_path)
        if drive:
            target = os.path.join(drive + "\\",
                                  os.path.basename(str(archive_path)))

        args: List[str] = ["create"]
        args.append(f"-r{max(1, int(redundancy))}")
        if memory_mb:
            args.append(f"-m{int(memory_mb)}")
        if threads:
            args.append(f"-t{int(threads)}")
        if block_size:
            args.append(f"-s{int(block_size)}")
        if recursion:
            args.append("-R")
        if set_name:
            name = str(set_name)
            if drive:
                name = os.path.join(drive + "\\",
                                    os.path.basename(name))
            args += ["-a", name]
        args.append(target)

        rc, log = _run(bin_path, args, timeout, register=register,
                       on_line=on_line)
        subst_failed = subst.failed

    if rc == 0:
        return Par2Result(True, STATE_OK, log)


    if subst.failed:
        log = (
            f"[rizpaq] путь слишком длинный: Windows не дала укоротить его "
            f"через subst ({len(str(archive_path))} символов, предел около "
            f"260). Набор создан не будет.\n" + (log or "")
        )

    if rc == 3 and "already exists" in (log or ""):
        return Par2Result(False, STATE_FAILED, log)
    if rc == 3 and "must specify a list of files" in (log or ""):


        return Par2Result(False, STATE_MISSING, log)
    if rc == "timeout":
        return Par2Result(False, STATE_FAILED, "превышено время ожидания")
    if rc == "error":
        return Par2Result(False, STATE_FAILED, log)
    return Par2Result(False, STATE_FAILED, log)


def verify_parset(
    bin_path: str,
    par2_path: str,
    timeout: int = 3600,
    register=None,
) -> Par2Result:
    if not bin_path or not os.path.isfile(bin_path):
        return Par2Result(False, STATE_FAILED, "par2 не найден")
    if not par2_path or not os.path.isfile(par2_path):
        return Par2Result(False, STATE_MISSING, "набор не найден")

    rc, log = _run(
        bin_path, ["v", "-v", str(par2_path)], timeout, register=register
    )
    if rc == "timeout":
        return Par2Result(False, STATE_FAILED, "превышено время ожидания")
    if rc == "error":
        return Par2Result(False, STATE_FAILED, log)
    return _classify_verify(rc, log)


def repair_parset(
    bin_path: str,
    par2_path: str,
    *,
    archive_path: Optional[str] = None,
    recorded_size: Optional[int] = None,
    timeout: int = 7200,
    register=None,
) -> Par2Result:
    if not bin_path or not os.path.isfile(bin_path):
        return Par2Result(False, STATE_FAILED, "par2 не найден")
    if not par2_path or not os.path.isfile(par2_path):
        return Par2Result(False, STATE_MISSING, "набор не найден")

    if not archive_path or recorded_size is None:
        return Par2Result(
            False,
            STATE_FAILED,
            "восстановление заблокировано: неизвестно, какому состоянию "
            "архива соответствует набор (нужны путь к архиву и размер, "
            "записанный в наборе)",
        )

    try:
        actual = os.path.getsize(archive_path)
    except OSError:
        return Par2Result(
            False, STATE_MISSING, "файл архива не найден"
        )

    if actual > int(recorded_size):
        return Par2Result(
            False,
            STATE_FAILED,
            "восстановление заблокировано: архив больше, чем набор. "
            f"Архив {actual} байт, набор рассчитан на {int(recorded_size)} "
            "байт. Набор устарел: восстановление по нему откатит архив "
            "на прежнюю версию и удалит последнюю. Сначала пересоздайте "
            "набор для текущего архива.",
        )


    folder = os.path.dirname(str(par2_path)) or "."
    subst = SubstLetter(folder)
    with subst as drive:
        target = par2_path
        if drive:
            target = os.path.join(drive + "\\", os.path.basename(par2_path))
        rc, log = _run(bin_path, ["r", str(target)], timeout, register=register)


        subst_failed = subst.failed

    if rc == 0:
        return Par2Result(True, STATE_OK, log)
    if subst_failed:
        log = (
            "[rizpaq] восстановление невозможно: путь слишком длинный, "
            "Windows не дала укоротить его через subst. Проверка набора "
            "работает, а починить им файл не выйдет.\n" + (log or "")
        )
    if rc == 1:
        return Par2Result(False, STATE_DAMAGED, log)
    if rc == "timeout":
        return Par2Result(False, STATE_FAILED, "превышено время ожидания")
    return Par2Result(False, STATE_FAILED, log)


def set_is_stale(archive_path: str, recorded_size: Optional[int]) -> Optional[bool]:
    if recorded_size is None:
        return None
    try:
        actual = os.path.getsize(archive_path)
    except OSError:
        return None
    return actual > int(recorded_size)


_TEMP_MARK = ".rizpaq-new"


def par2_temp_set_name(archive_path: str) -> str:

    return str(archive_path) + _TEMP_MARK + ".par2"


def _temp_set_files(archive_path: str) -> List[str]:
    temp_main = par2_temp_set_name(archive_path)
    folder = os.path.dirname(temp_main) or "."
    base = os.path.basename(temp_main)
    stem = os.path.splitext(base)[0]
    out: List[str] = []
    try:
        names = os.listdir(folder)
    except OSError:
        return out
    for name in names:
        if name == base:
            out.append(os.path.join(folder, name))
            continue
        if _VOL_RE.search(name) and name.startswith(stem):
            out.append(os.path.join(folder, name))
    return sorted(out)


def cleanup_orphans(archive_path: str) -> List[str]:
    removed: List[str] = []
    for path in _temp_set_files(archive_path):
        try:
            os.remove(path)
            removed.append(path)
        except OSError:
            continue
    return removed


def refresh_par2_set(
    bin_path: str,
    archive_path: str,
    *,
    redundancy: int = 5,
    memory_mb: Optional[int] = None,
    threads: Optional[int] = None,
    block_size: Optional[int] = None,
    recursion: bool = False,
    skip_if_unchanged: bool = True,
    unchanged_size: Optional[int] = None,
    register=None,
    on_line=None,
) -> Par2Result:
    if not bin_path or not os.path.isfile(bin_path):
        return Par2Result(False, STATE_FAILED, "par2 не найден")
    if not archive_path or not os.path.isfile(archive_path):
        return Par2Result(False, STATE_MISSING, "файл архива не найден")

    try:
        size_before = os.path.getsize(archive_path)
    except OSError as exc:
        return Par2Result(
            False, STATE_MISSING, f"не удалось прочитать архив: {exc}"
        )

    if skip_if_unchanged and unchanged_size is not None:
        if size_before == int(unchanged_size):
            return Par2Result(
                True, STATE_OK,
                "архив не изменился, набор остаётся в силе",
                recorded_size=size_before,
                skipped=True,
            )


    cleanup_orphans(archive_path)

    created = create_parset(
        bin_path,
        archive_path,
        redundancy=redundancy,
        memory_mb=memory_mb,
        threads=threads,
        block_size=block_size,
        recursion=recursion,
        set_name=par2_temp_set_name(archive_path),
        register=register,
        on_line=on_line,
    )
    if not created.ok:


        cleanup_orphans(archive_path)
        return created

    try:
        size_after = os.path.getsize(archive_path)
    except OSError:
        size_after = None

    if size_after != size_before:

        cleanup_orphans(archive_path)
        return Par2Result(
            False,
            STATE_FAILED,
            "архив изменился во время создания набора, набор не создан. "
            "Ничего не изменено, следующий запуск создаст набор заново.",
            recorded_size=size_after,
        )


    remove_par2_set(archive_path)


    renamed = 0
    for path in _temp_set_files(archive_path):
        folder_path = os.path.dirname(path) or "."
        name = os.path.basename(path)
        if _TEMP_MARK not in name:
            continue
        target_name = name.replace(_TEMP_MARK, "", 1)
        try:
            os.replace(path, os.path.join(folder_path, target_name))
            renamed += 1
        except OSError:


            continue

    if renamed == 0:
        return Par2Result(
            False,
            STATE_FAILED,
            "набор создан, но ни один файл не удалось переименовать — "
            "временный набор оставлен на диске",
        )

    return Par2Result(True, STATE_OK, created.log, recorded_size=size_after)
