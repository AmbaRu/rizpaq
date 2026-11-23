






from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


def build_series(samples, days: int = 30, now: Optional[datetime] = None):
    pass





    points = []
    for item in samples or []:
        try:
            ts = int(item[0])
            size = int(item[1])
        except (TypeError, ValueError, IndexError):
            continue
        points.append((ts, size))
    if not points:
        return []
    points.sort()

    end = (now or datetime.now()).date()
    start = end - timedelta(days=max(1, int(days)) - 1)
    by_day = {}
    for ts, size in points:
        day = datetime.fromtimestamp(ts).date()
        if start <= day <= end:
            by_day[day] = size

                                                                       
    before = [s for ts, s in points if datetime.fromtimestamp(ts).date() < start]
    current = before[-1] if before else 0

    series = []
    day = start
    while day <= end:
        if day in by_day:
            current = by_day[day]
        series.append((day.strftime("%d.%m"), current))
        day += timedelta(days=1)
    return series


def saving_text(logical: int, actual: int) -> Optional[float]:
    pass
    if not actual or actual <= 0 or not logical or logical <= 0:
        return None
    return float(logical) / float(actual)
