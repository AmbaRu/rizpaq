



















from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core import par2_ops
from core.paths import (
    backup_binary_index_path,
    backup_index_path,
    backup_parts,
    is_backup_set,
)

ACTION_CREATE = "create"
ACTION_REFRESH = "refresh"
ACTION_SKIP = "skip"


def is_service_file(path: str) -> bool:
    pass
    name = Path(str(path)).name.lower()
    return name.endswith("_backup.txt") or name.endswith("_backup.index")


def archive_files(path: str) -> List[str]:
    pass






    p = str(path or "")
    if not p:
        return []
    if is_backup_set(p):
        out = [str(x) for x in backup_parts(p)]
        out.extend(
            x for x in (backup_index_path(p), backup_binary_index_path(p))
            if os.path.isfile(x)
        )
        return sorted(out)
    if "?" in p or "*" in p:
        try:
            q = Path(p)
            return sorted(str(x) for x in q.parent.glob(q.name) if x.is_file())
        except OSError:
            return []
    return [p] if os.path.isfile(p) else []


def set_is_ready(file: str) -> bool:
    pass
    main = par2_ops.par2_main_name(file)
    if not os.path.isfile(main):
        return False
    volumes = [p for p in par2_ops.par2_set_files(file)
               if p != main and os.path.isfile(p)]
    return bool(volumes)


def _set_stamp(file: str) -> Optional[float]:
    pass
    main = par2_ops.par2_main_name(file)
    try:
        return os.path.getmtime(main) if os.path.isfile(main) else None
    except OSError:
        return None


def plan(archive_path: str) -> List[Tuple[str, str, bool]]:
    pass





    out: List[Tuple[str, str, bool]] = []
    for file in archive_files(archive_path):
        try:
            src_mtime = os.path.getmtime(file)
        except OSError:
            continue
        set_mtime = _set_stamp(file)
        if not set_is_ready(file):
            action = ACTION_CREATE
        elif set_mtime is None or src_mtime > set_mtime + 0.001:
                                                                      
            action = ACTION_REFRESH
        else:
            action = ACTION_SKIP
        out.append((file, action, is_service_file(file)))
    return out


def _int_option(options: dict, key: str):
    raw = (options or {}).get(key)
    if raw in (None, "", False):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def protect(
    bin_path: str,
    archive_path: str,
    options: Optional[dict] = None,
    on_line=None,
    register=None,
) -> dict:
    pass






    opts = dict(options or {})
    redundancy = _int_option(opts, "redundancy")
    if redundancy is None:
        redundancy = 5
    summary = {
        "ok": True,
        "created": 0,
        "refreshed": 0,
        "skipped": 0,
        "failed": 0,
        "sets": [],
        "log": "",
    }
    lines: List[str] = []
    for file, action, service in plan(archive_path):
        label = Path(file).name
        if action == ACTION_SKIP:
            summary["skipped"] += 1
            summary["sets"].append({"file": file, "action": ACTION_SKIP})
            lines.append(f"[par2] {label}: набор актуален, пропущен")
            continue
        res = par2_ops.refresh_par2_set(
            bin_path,
            file,
            redundancy=max(1, redundancy),
            memory_mb=_int_option(opts, "memory_mb"),
            threads=_int_option(opts, "threads"),
            block_size=_int_option(opts, "block_size"),
            recursion=bool(opts.get("recursion")),
            skip_if_unchanged=False,
            on_line=on_line,
            register=register,
        )
        entry = {
            "file": file,
            "action": action,
            "service": service,
            "ok": res.ok,
            "state": res.state,
        }
        summary["sets"].append(entry)
        if res.ok:
            if action == ACTION_CREATE:
                summary["created"] += 1
            else:
                summary["refreshed"] += 1
            lines.append(
                f"[par2] {label}: {'создан' if action == ACTION_CREATE else 'обновлён'} "
                f"набор ({res.recorded_size} байт)"
            )
        else:
            summary["ok"] = False
            summary["failed"] += 1
            tail = (res.log or "").strip().splitlines()
            reason = tail[-1] if tail else res.state
            lines.append(f"[par2] {label}: ОШИБКА — {reason[:200]}")
    summary["log"] = "\n".join(lines) + ("\n" if lines else "")
    return summary


def verify(bin_path: str, archive_path: str) -> dict:
    pass






    out = {"ok": True, "state": par2_ops.STATE_OK, "checked": 0, "log": ""}
    lines: List[str] = []
    files = archive_files(archive_path)
    if not files:
        return {
            "ok": False,
            "state": par2_ops.STATE_MISSING,
            "checked": 0,
            "log": "[par2] файлы архива не найдены\n",
        }
    rank = {
        par2_ops.STATE_OK: 0,
        par2_ops.STATE_MISSING: 1,
        par2_ops.STATE_BROKEN: 2,
        par2_ops.STATE_DAMAGED: 3,
        par2_ops.STATE_UNREPAIRABLE: 4,
        par2_ops.STATE_FAILED: 5,
    }
    worst = 0
    for file in files:
        label = Path(file).name
        set_index = par2_ops.par2_main_name(file)
        if not os.path.isfile(set_index):
            state = par2_ops.STATE_MISSING
            detail = "набор не создан"
        else:
            res = par2_ops.verify_parset(bin_path, set_index)
            state = res.state
            detail = "\n".join(
                ln for ln in (res.log or "").splitlines() if ln.strip()
            )[-300:]
        worst = max(worst, rank.get(state, 5))
        out["checked"] += 1
        lines.append(f"[par2] {label}: {state} — {detail}")
    out["state"] = next(
        (k for k, v in rank.items() if v == worst), par2_ops.STATE_OK
    )
    out["ok"] = worst == 0
    out["log"] = "\n".join(lines) + "\n"
    return out
