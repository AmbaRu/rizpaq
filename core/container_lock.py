from __future__ import annotations

import os
import threading
import time
from pathlib import Path


DEFAULT_TIMEOUT_S = 2.0


POLL_INTERVAL_S = 0.05


LOCK_SUFFIX = ".lock"


class ContainerLockBusy(Exception):
        pass


def lock_path_for(container_path) -> Path:
    return Path(str(container_path) + LOCK_SUFFIX)


_locks: dict = {}
_os_owner: dict = {}
_locks_guard = threading.Lock()


def _reentrant_key(path: Path) -> str:

    try:
        return os.path.normcase(os.path.abspath(str(path)))
    except Exception:
        return str(path)


def _get_lock(key: str) -> threading.RLock:

    with _locks_guard:
        lk = _locks.get(key)
        if lk is None:
            lk = threading.RLock()
            _locks[key] = lk
        return lk


def _get_os_owner(key: str):

    with _locks_guard:
        return _os_owner.get(key)


def _set_os_owner(key: str, ident) -> None:

    with _locks_guard:
        if ident is None:
            _os_owner.pop(key, None)
        else:
            _os_owner[key] = ident


_k32 = None
_k32_guard = threading.Lock()


def _get_kernel32():

    global _k32
    if _k32 is not None:
        return _k32
    with _k32_guard:
        if _k32 is not None:
            return _k32
        import ctypes
        from ctypes import wintypes

        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateFileW.restype = wintypes.HANDLE
        k.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        _k32 = k
        return k


def _open_exclusive_windows(path: Path):
    import ctypes

    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_ALWAYS = 4
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    k = _get_kernel32()
    handle = k.CreateFileW(
        str(path),
        GENERIC_READ | GENERIC_WRITE,
        0,
        None,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )


    if not handle or handle == INVALID_HANDLE_VALUE:


        err = ctypes.get_last_error()
        if err in (32, 33):
            return None
        raise OSError(err, f"CreateFileW failed for {path}")
    return handle


def _close_windows(handle) -> None:

    try:
        k = _get_kernel32()
        k.CloseHandle(handle)
    except Exception:
        pass


def _acquire_posix(path: Path):
    import fcntl

    f = open(path, "a+b")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        f.close()
        return None


class container_lock:

    def __init__(self, container_path, timeout_s: float = DEFAULT_TIMEOUT_S):
        self._path = lock_path_for(container_path)
        self._timeout_s = timeout_s
        self._key = _reentrant_key(self._path)
        self._handle = None
        self._posix_file = None
        self._rlock = None
        self._reentrant = False

    def __enter__(self) -> "container_lock":


        rlock = _get_lock(self._key)
        if not rlock.acquire(timeout=self._timeout_s):
            raise ContainerLockBusy(
                f"container {self._path} is busy (held by another thread)"
            )
        self._rlock = rlock


        if _get_os_owner(self._key) == threading.get_ident():
            self._reentrant = True
            return self


        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            rlock.release()
            self._rlock = None
            raise

        deadline = time.monotonic() + self._timeout_s
        last_err = None
        while True:
            try:
                if os.name == "nt":
                    h = _open_exclusive_windows(self._path)
                    if h is not None:
                        self._handle = h
                        _set_os_owner(self._key, threading.get_ident())
                        return self
                else:
                    f = _acquire_posix(self._path)
                    if f is not None:
                        self._posix_file = f
                        _set_os_owner(self._key, threading.get_ident())
                        return self
            except OSError as exc:


                last_err = exc
                break

            if time.monotonic() >= deadline:
                break
            time.sleep(POLL_INTERVAL_S)


        rlock.release()
        self._rlock = None
        if last_err is not None:
            raise ContainerLockBusy(
                f"cannot lock container {self._path}: {last_err}"
            ) from last_err
        raise ContainerLockBusy(
            f"container {self._path} is busy (locked by another process)"
        )

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._reentrant:


                return False


            if self._handle is not None:
                _close_windows(self._handle)
                self._handle = None
            if self._posix_file is not None:
                try:
                    self._posix_file.close()
                except Exception:
                    pass
                self._posix_file = None
            _set_os_owner(self._key, None)
            return False
        finally:
            if self._rlock is not None:
                try:
                    self._rlock.release()
                except Exception:
                    pass
                self._rlock = None


def container_is_locked(container_path) -> bool:
    p = lock_path_for(container_path)
    if not p.parent.is_dir():
        return False

    key = _reentrant_key(p)


    if _get_os_owner(key) is not None:
        return True

    try:
        if os.name == "nt":
            h = _open_exclusive_windows(p)
            if h is None:
                return True
            _close_windows(h)
            return False
        else:
            f = _acquire_posix(p)
            if f is None:
                return True
            f.close()
            return False
    except OSError:


        return True
