from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.par2_ops import par2_main_name


_DISK_LOW_BYTES = 10 * 1024 ** 3


_PAR2_CHECK_DAYS = 30


_SILENT_FACTOR = 3
_SILENT_MIN_SECONDS = 24 * 3600


_INTERVAL_SECONDS = {
    "minute": 60,
    "hourly": 3600,
    "daily": 24 * 3600,
    "weekly": 7 * 24 * 3600,
    "monthly": 30 * 24 * 3600,
}


_LAST_RUN_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")


@dataclass
class Alert:


    kind: str
    work_id: str = ""
    job_id: str = ""
    text_key: str = ""
    params: dict = field(default_factory=dict)


def _format_size(size: Optional[int]) -> str:

    if size is None:
        return "—"
    if size < 1024:
        return f"{size} Б"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} КБ"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} МБ"
    return f"{size / (1024 * 1024 * 1024):.1f} ГБ"


def _parse_dt(value) -> Optional[datetime]:

    text = str(value or "").strip()
    if not text:
        return None
    for fmt in _LAST_RUN_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def free_bytes(path: str) -> Optional[int]:

    try:
        return shutil.disk_usage(os.path.dirname(str(path)) or ".").free
    except Exception:
        return None


def is_set_outdated(par2_size, current_size) -> bool:

    try:
        return bool(par2_size) and bool(current_size) \
            and int(current_size) > int(par2_size)
    except Exception:
        return False


def collect_alerts(container: dict, history: list) -> list:
    try:
        works = container.get("works") or []
    except Exception:
        works = []
    now = datetime.now()
    alerts: list = []


    last_by_job: dict = {}
    for entry in history or []:
        dt = getattr(entry, "ts_dt", None)
        jid = str(getattr(entry, "job_id", "") or "")
        if dt is None or not jid:
            continue
        prev = last_by_job.get(jid)
        if prev is None or dt > prev:
            last_by_job[jid] = dt


    by_dest: dict = {}
    for work in works:
        dest = str(work.get("dest") or "")
        if dest:
            key = os.path.normcase(os.path.normpath(dest))
            by_dest.setdefault(key, []).append(work)

        wid = str(work.get("id") or "")
        jobs = work.get("jobs") or []


        for src in (work.get("sources") or []):
            text = str(src or "")
            if not text:
                continue
            try:
                missing = not Path(text).exists()
            except Exception:
                missing = False
            if missing:
                alerts.append(Alert(
                    "source_missing", wid,
                    text_key="dashboard.alerts.source_missing",
                    params={"path": text},
                ))


        if dest:
            dest_path = Path(dest)
            ran = any(
                (job.get("run_count") or 0) > 0 or job.get("last_run")
                for job in jobs
            )


            if ran and not dest_path.is_file():
                alerts.append(Alert(
                    "archive_missing", wid,
                    text_key="dashboard.alerts.archive_missing",
                    params={"path": dest},
                ))

                current_size = None
                set_exists = False
            else:
                current_size = None
                if dest_path.is_file():
                    try:
                        current_size = dest_path.stat().st_size
                    except OSError:
                        current_size = None


                par2_size = work.get("par2_size")
                set_exists = Path(par2_main_name(dest)).is_file()
                if set_exists and is_set_outdated(par2_size, current_size):
                    alerts.append(Alert(
                        "par2_outdated", wid,
                        text_key="dashboard.alerts.par2_outdated",
                        params={
                            "old": _format_size(int(par2_size)),
                            "new": _format_size(current_size),
                        },
                    ))


                if current_size is not None:
                    free = free_bytes(dest)
                    if free is not None and free < _DISK_LOW_BYTES:
                        alerts.append(Alert(
                            "disk_low", wid,
                            text_key="dashboard.alerts.disk_low",
                            params={"free": _format_size(free)},
                        ))


            if set_exists:
                check_last = None
                has_check_job = False
                for job in jobs:
                    mode = str(job.get("test_mode") or "")
                    action = str(job.get("action") or "")
                    if "par2" not in (mode, action):
                        continue
                    has_check_job = True
                    jid = str(job.get("id") or "")
                    dt = last_by_job.get(jid) \
                        or _parse_dt(job.get("last_run"))
                    if dt is not None and (
                            check_last is None or dt > check_last):
                        check_last = dt
                if not has_check_job or check_last is None:
                    alerts.append(Alert(
                        "par2_check_old", wid,
                        text_key="dashboard.alerts.par2_check_never",
                    ))
                elif (now - check_last).days > _PAR2_CHECK_DAYS:
                    alerts.append(Alert(
                        "par2_check_old", wid,
                        text_key="dashboard.alerts.par2_check_old",
                        params={"days": (now - check_last).days},
                    ))


        for job in jobs:
            schedule = job.get("schedule")
            if not isinstance(schedule, dict) or not schedule.get("enabled"):
                continue
            freq = str(schedule.get("frequency") or "daily")
            try:
                interval = max(1, int(schedule.get("interval", 1) or 1))
            except Exception:
                interval = 1
            step = _INTERVAL_SECONDS.get(freq, _INTERVAL_SECONDS["daily"]) \
                * interval
            jid = str(job.get("id") or "")
            last = last_by_job.get(jid) or _parse_dt(job.get("last_run"))
            if last is None:
                continue
            overdue = (now - last).total_seconds()
            if overdue > step * _SILENT_FACTOR \
                    and overdue > _SILENT_MIN_SECONDS:
                alerts.append(Alert(
                    "job_silent", wid, jid,
                    text_key="dashboard.alerts.job_silent",
                    params={
                        "job": str(job.get("title") or ""),
                        "days": max(1, int(overdue // (24 * 3600))),
                    },
                ))


    for group in by_dest.values():
        if len(group) > 1:
            for work in group:
                alerts.append(Alert(
                    "shared_dest", str(work.get("id") or ""),
                    text_key="dashboard.alerts.shared_dest",
                    params={"path": str(work.get("dest") or "")},
                ))

    return alerts


def job_streaks(history: list) -> dict:
    runs: dict = {}
    for entry in history or []:
        status = getattr(entry, "status", "")
        jid = str(getattr(entry, "job_id", "") or "")
        if status not in ("ok", "error") or not jid:
            continue
        dt = getattr(entry, "ts_dt", None)
        runs.setdefault(jid, []).append((dt or datetime.min, status))

    out: dict = {}
    for jid, items in runs.items():
        items.sort(key=lambda pair: pair[0])
        status = items[-1][1]
        count = 0
        for _, st in reversed(items):
            if st == status:
                count += 1
            else:
                break
        out[jid] = (status, count)
    return out
