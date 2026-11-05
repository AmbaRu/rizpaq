from __future__ import annotations

import os
import re
import subprocess
import time
from typing import Callable, Optional


from core.engine_path import (
    EnginePathError,
    drop_substitutes,
    rewrite_cmd,
)
from core.proc_health import (
    Liveness,
    make_cpu_reader,
)

CANCELLED_TEXT = "Operation cancelled by user"


def decode_bytes(data: bytes) -> str:

    if not data:
        return ""

    for enc in ("utf-8", "cp1251", "cp866", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass

    return data.decode("utf-8", errors="replace")


_PASSWORD_VALUE_FLAGS = ("-key",)

_PASSWORD_INLINE_PREFIX = "-p"
_MASK = "***"


def mask_secrets(cmd: list, password: Optional[str] = None) -> list:
    args = list(cmd or [])
    if not password:
        return args

    masked: list = []
    expect_value = False

    for arg in args:
        if expect_value:
            masked.append(_MASK)
            expect_value = False
            continue

        if arg in _PASSWORD_VALUE_FLAGS:
            masked.append(arg)
            expect_value = True
            continue


        if (
            isinstance(arg, str)
            and arg.startswith(_PASSWORD_INLINE_PREFIX)
            and arg[len(_PASSWORD_INLINE_PREFIX):] == password
        ):
            masked.append(_PASSWORD_INLINE_PREFIX + _MASK)
            continue

        masked.append(_MASK if arg == password else arg)

    return masked


def safe_cmdline(cmd: list, password: Optional[str] = None) -> str:

    masked = mask_secrets(cmd, password)

    try:
        return subprocess.list2cmdline(masked)
    except Exception:
        return " ".join(masked)


def looks_like_password_error(text: str) -> bool:
    low = (text or "").lower()
    return (
        "password" in low
        or "wrong password" in low
        or "crypt" in low
        or "key" in low
    )


_BUSY_MARKER = "another zpaqfranz is running"


def looks_like_busy_error(text: str) -> bool:
    return _BUSY_MARKER in (text or "").lower()


def _is_cancelled(is_cancelled: Optional[Callable[[], bool]]) -> bool:
    if is_cancelled is None:
        return False

    try:
        return bool(is_cancelled())
    except Exception:
        return False


def _kill_proc(proc, timeout: float = 5.0) -> None:
    if proc is None:
        return

    try:
        proc.kill()
    except Exception:
        pass

    try:
        proc.wait(timeout=timeout)
    except Exception:
        pass


def _close_pipe(proc) -> None:
    if proc is None:
        return

    try:
        if proc.stdout is not None:
            proc.stdout.close()
    except Exception:
        pass


def _popen_kwargs() -> dict:
    kwargs: dict = {}

    if os.name == "nt":

        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    return kwargs


DEFAULT_STALL_TIMEOUT = 90
STALL_TIMEOUT = DEFAULT_STALL_TIMEOUT


BUSY_STALL_MULTIPLIER = 30


def _stall_timeout() -> float:

    from core.proc_health import effective_stall_timeout
    return effective_stall_timeout(DEFAULT_STALL_TIMEOUT, STALL_TIMEOUT)


_PASSWORD_PROMPT = re.compile(rb"Enter AES password", re.IGNORECASE)


POLL_INTERVAL = 0.05


def run_zpaq(
    cmd: list,
    is_cancelled: Optional[Callable[[], bool]] = None,
    set_proc: Optional[Callable] = None,
) -> tuple:


    try:
        cmd, cwd, subs = rewrite_cmd(cmd)
    except EnginePathError as exc:


        return 1, f"ERROR: {exc}\n"
    except Exception:


        cmd, cwd, subs = list(cmd), None, []


    try:
        return _run_prepared(cmd, cwd, is_cancelled, set_proc)
    finally:
        drop_substitutes(subs)


def _run_prepared(
    cmd: list,
    cwd: Optional[str],
    is_cancelled: Optional[Callable[[], bool]],
    set_proc: Optional[Callable],
) -> tuple:


    try:
        popen_kwargs = _popen_kwargs()
        if cwd:
            popen_kwargs["cwd"] = cwd
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **popen_kwargs,
        )
    except FileNotFoundError:
        return 127, f"zpaqfranz not found: {cmd[0]}\n"
    except Exception as exc:
        return 1, f"ERROR: {exc}\n"

    if set_proc is not None:
        try:
            set_proc(proc)
        except Exception:
            pass

    chunks: list = []
    last_data = time.monotonic()


    stall_used = _stall_timeout()
    liv = Liveness(make_cpu_reader(proc), stall_timeout=stall_used,
                   busy_timeout=stall_used * BUSY_STALL_MULTIPLIER)


    try:
        os.set_blocking(proc.stdout.fileno(), False)
    except Exception:
        pass

    while True:
        if _is_cancelled(is_cancelled):
            _kill_proc(proc)
            try:
                proc.wait()
            except Exception:
                pass
            _close_pipe(proc)
            return -1, CANCELLED_TEXT + "\n"


        if proc.poll() is None:
            liv.verdict()
            if liv.stalled:
                tail = b"".join(chunks[-6:])
                output = decode_bytes(b"".join(chunks))
                if _PASSWORD_PROMPT.search(tail):
                    _kill_proc(proc)
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        pass
                    _close_pipe(proc)
                    return 1, output + (
                        "\nERROR: zpaqfranz запросил пароль и ждёт ввода. "
                        "Обычно это значит, что движок не смог открыть файл: "
                        "путь содержит нелатинские символы, а на этом томе "
                        "недоступны короткие имена 8.3. Переименуйте архив "
                        "или перенесите его в папку с латинским именем.\n"
                    )
                _kill_proc(proc)
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                if liv.busy:
                    reason = (
                        f"движок молчал {int(liv.last_silent)} с и всё это "
                        f"время продолжал работать — это превысило даже "
                        f"{int(stall_used * BUSY_STALL_MULTIPLIER)} с. "
                        f"Возможно, он зациклился.")
                else:
                    reason = (
                        f"движок не вывел ничего {int(stall_used)} с "
                        f"при живом процессе, который при этом простаивал "
                        f"— работа прервана.")
                _close_pipe(proc)
                return 1, output + (f"\nERROR: {reason}\n")

        try:
            chunk = proc.stdout.read(4096)
        except Exception:


            break

        if chunk:
            chunks.append(chunk)
            last_data = time.monotonic()
            liv.note_data()
            continue


        if proc.poll() is not None:

            try:
                tail = proc.stdout.read()
                if tail:
                    chunks.append(tail)
            except Exception:
                pass
            break

        time.sleep(POLL_INTERVAL)

    rc = proc.wait()
    output = decode_bytes(b"".join(chunks))
    _close_pipe(proc)

    if _is_cancelled(is_cancelled):
        return -1, output + "\n" + CANCELLED_TEXT + "\n"

    return rc, output


def check_zpaq(bin_path: str) -> bool:

    try:
        subprocess.run(
            [bin_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=4,
            **_popen_kwargs(),
        )
        return True
    except Exception:
        return False
