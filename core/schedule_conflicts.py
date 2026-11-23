












from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

HORIZON_DAYS = 8
TOLERANCE_MINUTES = 10


def _minute(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _start_minute(schedule: dict) -> int:
    pass
    text = str(schedule.get("time") or "00:00")
    parts = text.split(":")
    hour = _minute(parts[0]) if parts else 0
    minute = _minute(parts[1]) if len(parts) > 1 else 0
    return (max(0, min(23, hour)) * 60) + max(0, min(59, minute))


def _interval(schedule: dict, default: int = 1) -> int:
    try:
        return max(1, int(schedule.get("interval", default) or default))
    except (TypeError, ValueError):
        return default


def occurrence_minutes(
    schedule: dict,
    now: Optional[datetime] = None,
    days: int = HORIZON_DAYS,
) -> set[int]:
    pass





    if not schedule or not schedule.get("enabled"):
        return set()

    base = (now or datetime.now()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    freq = str(schedule.get("frequency") or "daily").lower()
    interval = _interval(schedule)
    start = _start_minute(schedule)
    result: set[int] = set()

    for day in range(days):
        date = base + timedelta(days=day)
        for minute_of_day in range(24 * 60):
            absolute = day * 1440 + minute_of_day
            hit = False
            if freq in ("minute", "continuous"):
                hit = absolute % interval == 0
            elif freq == "hourly":
                hour = minute_of_day // 60
                hit = (minute_of_day % 60 == start % 60) and (hour % interval == 0)
            elif freq == "daily":
                hit = (
                    minute_of_day == start
                    and day % interval == 0
                )
            elif freq == "weekly":
                names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
                code = names[date.weekday()]
                hit = (
                    minute_of_day == start
                    and code in (schedule.get("days") or [])
                    and (day // 7) % interval == 0
                )
            elif freq == "monthly":
                dom = _minute(schedule.get("day_of_month"), 1)
                hit = (
                    minute_of_day == start
                    and date.day == dom
                    and (date.month - 1) % interval == 0
                )
            if hit:
                result.add(absolute)
    return result


def schedules_overlap(a: dict, b: dict, now: Optional[datetime] = None) -> bool:
    pass
    left = occurrence_minutes(a, now)
    right = occurrence_minutes(b, now)
    if not left or not right:
        return False
                                                               
    for minute in left:
        for delta in range(-TOLERANCE_MINUTES, TOLERANCE_MINUTES + 1):
            if minute + delta in right:
                return True
    return False


def _same_dest(a, b) -> bool:
    da = str(a.get("dest") or "").strip()
    db = str(b.get("dest") or "").strip()
    if not da or not db:
        return False
    try:
        return os.path.normcase(os.path.normpath(da)) == os.path.normcase(
            os.path.normpath(db)
        )
    except Exception:
        return da.lower() == db.lower()


def find_conflicts(
    container: dict,
    work: dict,
    job: dict,
    schedule: dict,
    now: Optional[datetime] = None,
) -> list[dict]:
    pass






    from core.tasks import iter_jobs

    conflicts = []
    if not schedule or not schedule.get("enabled"):
        return conflicts

    self_id = str(job.get("id") or "")
    for other_work, other_job in iter_jobs(container or {}):
        if str(other_job.get("id") or "") == self_id:
            continue
        if str(other_job.get("action") or "backup").lower() != "backup":
            continue
        if not _same_dest(work, other_work):
            continue
        if schedules_overlap(schedule, other_job.get("schedule") or {}, now):
            conflicts.append({
                "work": str(other_work.get("title") or ""),
                "job": str(other_job.get("title") or ""),
                "job_id": str(other_job.get("id") or ""),
            })
    return conflicts
