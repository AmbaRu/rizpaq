























from __future__ import annotations

import re
import time

_PCT_RE = re.compile(r"Processing:\s*([\d]+(?:[.,]\d+)?)\s*%", re.I)
_COUNT_RE = re.compile(
    r"^(Block size|Source file count|Source block count|"
    r"Recovery block count|Recovery file count):\s*(\d+)",
    re.I,
)
_COUNT_FIELDS = {
    "block size": "block_size",
    "source file count": "source_files",
    "source block count": "source_blocks",
    "recovery block count": "recovery_blocks",
    "recovery file count": "recovery_files",
}

_WROTE_RE = re.compile(r"Wrote\s+(\d+)\s+bytes", re.I)


def _fmt_duration(seconds) -> str:
    pass
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "—"
    if seconds < 0:
        return "—"
    if seconds < 60:
        return "%ds" % seconds
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return "%d:%02d" % (minutes, sec)
    hours, minutes = divmod(minutes, 60)
    return "%d:%02d:%02d" % (hours, minutes, sec)


class Par2Progress:
    pass

    def __init__(self, archive_size=0, redundancy=None, clock=None):
        self.archive_size = int(archive_size or 0)
        self.redundancy = redundancy
        self._clock = clock or time.monotonic

        self.percent = None
        self.phase = "starting"
        self.block_size = None
        self.source_files = None
        self.source_blocks = None
        self.recovery_blocks = None
        self.recovery_files = None
        self.written = 0
        self.done = False

        self._last_percent = None
        self._last_time = self._clock()
        self._speed = 0.0
        self._write_speed = 0.0
        self._last_written = 0
        self._last_written_time = self._clock()

                                                                          

    def feed(self, line) -> bool:
        pass
        text = str(line or "").strip()
        if not text:
            return False
        changed = False

        count = _COUNT_RE.match(text)
        if count:
            key = _COUNT_FIELDS.get(count.group(1).lower())
            value = int(count.group(2))
            if key and getattr(self, key, None) != value:
                setattr(self, key, value)
                changed = True

        if text.lower().startswith("opening:"):
            if self.phase != "reading":
                self.phase = "reading"
                changed = True

        pct = _PCT_RE.search(text)
        if pct:
            value = float(pct.group(1).replace(",", "."))
            value = max(0.0, min(100.0, value))
            now = self._clock()
                                                                         
            if (
                self._last_percent is not None
                and self.archive_size > 0
                and value > self._last_percent
                and now > self._last_time
            ):
                delta = (
                    self.archive_size
                    * (value - self._last_percent) / 100.0
                )
                instant = delta / (now - self._last_time)
                self._speed = (
                    instant if self._speed <= 0 else
                    self._speed * 0.6 + instant * 0.4
                )
            self._last_percent = value
            self._last_time = now
            self.percent = value
            if self.phase != "reading":
                self.phase = "reading"
            changed = True

        if text.lower().startswith("writing recovery packets"):
            self.phase = "writing"
            changed = True
        elif text.lower().startswith("writing verification packets"):
            self.phase = "verification"
            changed = True
        elif text.lower().startswith("done"):
            self.phase = "done"
            self.done = True
            if self.percent is None or self.percent < 100:
                self.percent = 100.0
            changed = True

        wrote = _WROTE_RE.search(text)
        if wrote:
            now = self._clock()
            value = int(wrote.group(1))
            self.written += value
            delta_time = now - self._last_written_time
            if delta_time > 0:
                instant = value / delta_time
                self._write_speed = (
                    instant if self._write_speed <= 0 else
                    self._write_speed * 0.6 + instant * 0.4
                )
            self._last_written = value
            self._last_written_time = now
            changed = True

        return changed

                                                                          

    def snapshot(self) -> dict:
        pass




        read_bytes = 0
        eta_s = None
        if self.archive_size > 0 and self.percent is not None:
            read_bytes = int(self.archive_size * self.percent / 100.0)
            if self.percent < 100 and self._speed > 0:
                eta_s = int(
                    self.archive_size * (100 - self.percent) / 100.0
                    / self._speed
                )

        return {
            "phase": self.phase,
            "percent": int(self.percent) if self.percent is not None else None,
            "size": self.archive_size or None,
            "read": read_bytes or None,
            "written": self.written or None,
            "speed": self._speed or None,
            "write_speed": self._write_speed or None,
            "eta": _fmt_duration(eta_s),
            "eta_s": eta_s,
            "blocks": self.source_blocks,
            "recovery_blocks": self.recovery_blocks,
            "recovery_files": self.recovery_files,
            "redundancy": self.redundancy,
            "done": self.done,
        }


def format_speed(bytes_per_second) -> str:
    pass
    try:
        value = float(bytes_per_second)
    except (TypeError, ValueError):
        return "—"
    if value <= 0:
        return "—"
    for unit, mult in (("GB/s", 1 << 30), ("MB/s", 1 << 20),
                       ("KB/s", 1 << 10)):
        if value >= mult:
            return "%.1f %s" % (value / mult, unit)
    return "%d B/s" % int(value)
