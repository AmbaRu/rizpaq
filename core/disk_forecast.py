









from __future__ import annotations

from typing import Optional

                                                
MIN_SPAN_SECONDS = 24 * 3600


def daily_growth(samples, now: Optional[float] = None) -> Optional[float]:
    pass






    points = []
    for item in samples or []:
        try:
            ts = int(item[0])
            size = int(item[1])
        except (TypeError, ValueError, IndexError):
            continue
        points.append((ts, size))
    if len(points) < 2:
        return None
    points.sort()
    span = points[-1][0] - points[0][0]
    if span < MIN_SPAN_SECONDS:
        return None
    delta = points[-1][1] - points[0][1]
    if delta <= 0:
        return 0.0
    return float(delta) / (span / float(24 * 3600))


def days_to_full(free_bytes: Optional[int], growth: Optional[float]) -> Optional[int]:
    pass
    if not free_bytes or free_bytes <= 0:
        return None
    if not growth or growth <= 0:
        return None
    return int(float(free_bytes) / float(growth))


def forecast_size(size: int, growth: Optional[float], days: int) -> Optional[int]:
    pass
    if not growth or growth <= 0:
        return None
    return int(int(size or 0) + float(growth) * int(days))
