from __future__ import annotations

import os
import time
from typing import Callable, Optional

from core.paths import multipart_pattern


ARCHIVE_EXTS = (".zpaq",)


SKIP_DIR_NAMES = {
    "$recycle.bin",
    "system volume information",
}


PROGRESS_EVERY_DIRS = 25
PROGRESS_EVERY_SECONDS = 0.2


def _should_stop(should_stop: Optional[Callable[[], bool]]) -> bool:
    if should_stop is None:
        return False
    try:
        return bool(should_stop())
    except Exception:
        return False


def _call(callback, *args) -> None:

    if callback is None:
        return
    try:
        callback(*args)
    except Exception:
        pass


def _is_archive_name(name: str) -> bool:
    low = name.lower()
    return any(low.endswith(ext) for ext in ARCHIVE_EXTS)


def scan_roots(
    roots,
    on_found: Optional[Callable[[dict], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
    on_progress: Optional[Callable[[dict], None]] = None,
    on_error: Optional[Callable[[str, Exception], None]] = None,
) -> list:
    roots = [str(r) for r in (roots or []) if str(r or "").strip()]


    raw: dict = {}

    directories = 0
    last_report = time.monotonic()

    def report(current: str = "", force: bool = False) -> None:
        nonlocal last_report
        now = time.monotonic()
        if not force and now - last_report < PROGRESS_EVERY_SECONDS:
            return
        last_report = now
        _call(on_progress, {
            "directories": directories,
            "found": len(raw),
            "current": current,
        })

    def remember(path: str) -> None:
        try:
            st = os.stat(path)
        except OSError as exc:
            _call(on_error, path, exc)
            return
        absolute = os.path.abspath(path)
        key = os.path.normcase(absolute)
        prev = raw.get(key)
        if prev is not None:
            _orig, size, mtime_ns, parts = prev
            raw[key] = (
                _orig,
                size + int(st.st_size),
                max(mtime_ns, int(st.st_mtime_ns)),
                parts + 1,
            )
            return
        raw[key] = (absolute, int(st.st_size), int(st.st_mtime_ns), 1)

    for root in roots:
        if _should_stop(should_stop):
            break

        root_abs = os.path.abspath(root)
        if os.path.isfile(root_abs):

            if _is_archive_name(os.path.basename(root_abs)):
                remember(root_abs)
            continue

        if not os.path.isdir(root_abs):
            _call(on_error, root_abs, FileNotFoundError(root_abs))
            continue

        stack = [root_abs]
        while stack:
            if _should_stop(should_stop):
                break

            current = stack.pop()
            directories += 1
            report(current)

            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if _should_stop(should_stop):
                            break
                        try:


                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                if entry.name.lower() in SKIP_DIR_NAMES:
                                    continue
                                stack.append(entry.path)
                            elif entry.is_file(follow_symlinks=False):
                                if _is_archive_name(entry.name):
                                    remember(entry.path)
                        except OSError as exc:
                            _call(on_error, entry.path, exc)
            except OSError as exc:
                _call(on_error, current, exc)

    report(force=True)


    grouped: dict = {}
    for key, (original, size, mtime_ns, parts) in raw.items():
        mask = multipart_pattern(original)
        mask_key = os.path.normcase(os.path.abspath(mask))
        prev = grouped.get(mask_key)
        if prev is None:
            grouped[mask_key] = [mask, size, mtime_ns, parts]
        else:
            prev[1] += size
            prev[2] = max(prev[2], mtime_ns)
            prev[3] += parts

    out: list = []
    for key in sorted(grouped):
        path, size, mtime_ns, parts = grouped[key]
        record = {
            "path": path,
            "size": int(size),
            "mtime_ns": int(mtime_ns),
            "parts": int(parts),
            "missing": False,
        }
        out.append(record)
        _call(on_found, record)

    return out
