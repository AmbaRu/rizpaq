




from __future__ import annotations

from ui.i18n import tr


def format_size(size: int) -> str:
    pass


    if size < 1024:
        return f"{size} B"
    value = float(size)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024.0
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
    return f"{size} B"


def plural_ru(n: int, forms: tuple) -> str:
    pass


    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return forms[0]
    if 2 <= n10 <= 4 and not (12 <= n100 <= 14):
        return forms[1]
    return forms[2]


                                                                
                                                                   
                                                 
_WEEKDAY_ORDER = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
_WEEKDAY_KEYS = {
    "MON": "scheduler.mon",
    "TUE": "scheduler.tue",
    "WED": "scheduler.wed",
    "THU": "scheduler.thu",
    "FRI": "scheduler.fri",
    "SAT": "scheduler.sat",
    "SUN": "scheduler.sun",
}


def _weekday_labels(codes) -> list:
    pass






    present = {str(c).upper() for c in (codes or []) if c}
    return [tr(_WEEKDAY_KEYS[c]) for c in _WEEKDAY_ORDER if c in present]


def format_schedule(schedule) -> str:
    pass



























    if not schedule or not isinstance(schedule, dict):
        return tr("sched.fmt.none")
    if not schedule.get("enabled"):
        return tr("sched.fmt.none")

    frequency = str(schedule.get("frequency") or "").lower()
    time_str = str(schedule.get("time") or "").strip()

    try:
        interval = max(1, int(schedule.get("interval") or 1))
    except (TypeError, ValueError):
        interval = 1

    try:
        if frequency == "minute":
            if interval == 1:
                return tr("sched.fmt.minute_one")
            return tr("sched.fmt.minute_n", n=interval)

        if frequency == "hourly":
            if interval == 1:
                return tr("sched.fmt.hourly_one")
            return tr("sched.fmt.hourly_n", n=interval)

        if frequency == "daily":
            if interval == 1:
                return tr("sched.fmt.daily_one", time=time_str)
            return tr("sched.fmt.daily_n", n=interval, time=time_str)

        if frequency == "weekly":
            days = _weekday_labels(schedule.get("days"))
            days_str = ", ".join(days) if days else ""
            if interval == 1:
                return tr(
                    "sched.fmt.weekly_one", days=days_str, time=time_str
                ).strip()
            return tr(
                "sched.fmt.weekly_n",
                n=interval,
                days=days_str,
                time=time_str,
            ).strip()

        if frequency == "monthly":
            try:
                day = int(schedule.get("day_of_month") or 1)
            except (TypeError, ValueError):
                day = 1
            if interval == 1:
                return tr("sched.fmt.monthly_one", day=day, time=time_str)
            return tr(
                "sched.fmt.monthly_n", n=interval, day=day, time=time_str
            )
    except Exception:
        pass

    return tr("sched.fmt.none")
