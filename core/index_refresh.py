from __future__ import annotations

import os
from pathlib import Path

from core.archive_index import store_entries
from core.parser import ParseReport, parse_csv_line_reported
from core.zpaq_cli import run_zpaq


_LIST_FLAGS = ("-all", "-terse", "-csv", "\t", "-csvhf", "#",
               "-utf", "-noeta")


def build_list_cmd(zpaq_bin: str, path: str, password: str = None) -> list:
    cmd = [zpaq_bin, "l", str(path), *(_LIST_FLAGS)]
    if password:
        cmd += ["-key", password]
    return cmd


def file_stamp(path: str):

    try:
        st = os.stat(str(path))
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def store_fresh_listing(path: str, entries: list) -> int:
    stamp = file_stamp(path)
    if stamp is None or "?" in str(path):
        return 0
    try:
        store_entries(str(path), stamp[0], stamp[1], entries)
    except Exception:
        return 0
    return len(entries)


def refresh_index_sync(zpaq_bin: str, path: str,
                       password: str = None,
                       is_cancelled=None) -> int:
    if not path or "?" in str(path):
        return 0
    if not Path(path).is_file():
        return 0

    if is_cancelled is not None:
        try:
            if is_cancelled():
                return 0
        except Exception:
            pass

    stamp = file_stamp(path)
    if stamp is None:
        return 0

    try:
        rc, output = run_zpaq(
            build_list_cmd(zpaq_bin, path, password),
            is_cancelled=is_cancelled,
        )
    except Exception:
        return 0
    if rc != 0 or not output:
        return 0


    if file_stamp(path) != stamp:
        return 0

    report = ParseReport()
    entries: list = []
    try:
        for raw in output.splitlines():
            line = raw.strip()
            if not line:
                continue
            entry = parse_csv_line_reported(line, report)
            if entry is not None:
                entries.append(entry)
    except Exception:
        return 0

    if not entries:
        return 0
    return store_fresh_listing(path, entries)
