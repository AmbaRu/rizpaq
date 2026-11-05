from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from core.run_history import RunEntry, load_history


DEFAULT_SINCE_DAYS = 7


@dataclass
class Digest:


    since_dt: Optional[datetime] = None
    entries: list = field(default_factory=list)
    backups_ok: int = 0
    backups_err: int = 0
    backups_busy: int = 0
    tests_ok: int = 0
    tests_err: int = 0
    tests_busy: int = 0

    last_error: Optional[RunEntry] = None

    @property
    def is_empty(self) -> bool:

        return not self.entries

    @property
    def has_problem(self) -> bool:

        return bool(self.backups_err + self.tests_err
                    + self.backups_busy + self.tests_busy)


def _bucket(entry: RunEntry) -> tuple[str, str]:

    group = "tests" if entry.action == "test" else "backups"
    return group, entry.status if entry.status in ("ok", "error", "busy") \
        else "error"


def collect_digest(tasks_dir, since: Optional[int] = None,
                   now: Optional[datetime] = None) -> Optional[Digest]:
    if not tasks_dir:
        return None
    try:
        history = load_history(tasks_dir)
    except Exception:
        return None
    if not history:
        return None

    now_dt = now or datetime.now()
    since_dt: Optional[datetime] = None
    if isinstance(since, int) and not isinstance(since, bool) and since > 0:
        try:
            since_dt = datetime.fromtimestamp(since)
        except (OSError, OverflowError, ValueError):
            since_dt = None
    if since_dt is None:
        since_dt = now_dt - timedelta(days=DEFAULT_SINCE_DAYS)

    digest = Digest(since_dt=since_dt)
    for entry in history:
        dt = entry.ts_dt
        if dt is None or dt <= since_dt:
            continue
        digest.entries.append(entry)
        group, state = _bucket(entry)
        if state == "ok":
            setattr(digest, f"{group}_ok",
                    getattr(digest, f"{group}_ok") + 1)
        elif state == "busy":
            setattr(digest, f"{group}_busy",
                    getattr(digest, f"{group}_busy") + 1)
        else:
            setattr(digest, f"{group}_err",
                    getattr(digest, f"{group}_err") + 1)
        if entry.status == "error" and digest.last_error is None:
            digest.last_error = entry

    if digest.is_empty:
        return None
    return digest
