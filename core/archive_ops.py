





from __future__ import annotations

from typing import Optional

from .models import ArchiveEntry


def slice_at_version(entries: list, n: int) -> list:
    pass










    best_file: dict = {}
    best_dir: dict = {}

    for e in entries:
        if e.version is None or e.version > n:
            continue
        bucket = best_dir if e.is_dir else best_file
        old = bucket.get(e.path)
        if old is None or (e.version, e.datetime) > (old.version, old.datetime):
            bucket[e.path] = e

    result = [e for e in best_file.values() if e.flag != "-"]
    result += [e for e in best_dir.values() if e.flag != "-"]
    return result


def version_numbers(entries: list) -> list:
    pass
    nums = sorted({e.version for e in entries if e.version is not None})
    return nums
