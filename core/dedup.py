






















from __future__ import annotations

from pathlib import Path
from typing import Optional


def dedup_stats(versions, size_on_disk: Optional[int]) -> dict:
    pass






    logical = 0
    for version in versions or []:
        if isinstance(version, dict):
            value = version.get("bytes_added")
        else:
            value = getattr(version, "bytes_added", 0)
        try:
            logical += max(0, int(value or 0))
        except (TypeError, ValueError):
            continue

    actual = None
    if isinstance(size_on_disk, int) and not isinstance(size_on_disk, bool):
        actual = max(0, size_on_disk)

    saved = None
    ratio = None
    if actual is not None and actual > 0:
        saved = logical - actual
        ratio = logical / actual

    return {
        "logical": logical,
        "actual": actual,
        "saved": saved,
        "ratio": ratio,
    }


def archive_size_on_disk(path) -> Optional[int]:
    pass






    if not path:
        return None
    p = Path(str(path))
    try:
        if p.is_file():
            return p.stat().st_size
    except OSError:
        return None

    name = p.name
    if "?" not in name and "*" not in name:
        return None
    try:
        total = 0
        found = False
        for part in p.parent.glob(name):
            try:
                if part.is_file():
                    total += part.stat().st_size
                    found = True
            except OSError:
                continue
        return total if found else None
    except (OSError, ValueError):
        return None
