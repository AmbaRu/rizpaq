from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


TEMP_PREFIXES: Tuple[str, ...] = (
    "rizpaq_open_",
    "rizpaq_test_",
    "rizpaq_transcode_",
    "rizpaq_drag_",
    "rizpaq_batch_",
    "rizpaq_link_",
    "rizpaq_task_test_",
    "zpaq_gui_ex_",
    "zpaq_gui_batch_",
)


DEFAULT_MAX_AGE = 3600


def is_stale(path: Path, max_age: float, now: Optional[float] = None) -> bool:

    try:
        ts = path.stat().st_mtime
    except OSError:
        return False

    if now is None:
        now = time.time()

    return (now - ts) > max_age


def _is_link_or_reparse(path: Path) -> bool:

    try:
        if path.is_symlink():
            return True
    except OSError:
        return True


    try:
        import stat as _stat

        return bool(path.stat(follow_symlinks=False).st_file_attributes
                    & _stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError, ValueError):

        return False


def _is_owned_temp_dir(path: Path, temp_root: Path, prefixes: Tuple[str, ...]) -> bool:

    if path.parent.resolve() != temp_root.resolve():
        return False

    return path.name.startswith(prefixes)


def cleanup_stale_temp(
    max_age: float = DEFAULT_MAX_AGE,
    prefixes: Iterable[str] = TEMP_PREFIXES,
    temp_root: Optional[str] = None,
    dry_run: bool = False,
) -> List[str]:
    removed: List[str] = []

    try:
        root = Path(temp_root) if temp_root else Path(tempfile.gettempdir())
        pref = tuple(prefixes)

        if not root.is_dir():
            return removed

        for entry in root.iterdir():
            try:
                if not entry.is_dir():
                    continue

                if not _is_owned_temp_dir(entry, root, pref):
                    continue

                if _is_link_or_reparse(entry):
                    continue

                if not is_stale(entry, max_age):
                    continue

                removed.append(str(entry))

                if not dry_run:
                    shutil.rmtree(entry, ignore_errors=True)
            except Exception:
                continue
    except Exception:
        return removed

    return removed


def remove_temp_dir(path, prefixes: Iterable[str] = TEMP_PREFIXES) -> bool:
    try:
        p = Path(path)
        root = Path(tempfile.gettempdir())

        if not _is_owned_temp_dir(p, root, tuple(prefixes)):
            return False

        if _is_link_or_reparse(p):
            return False

        shutil.rmtree(p, ignore_errors=True)
        return True
    except Exception:
        return False
