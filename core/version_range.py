











from __future__ import annotations

import re

MAX_LEN = 32
_ALLOWED = re.compile(r"^[0-9:]+$")


def normalize_range(text) -> str | None:
    pass
    value = str(text or "").strip()
    if not value:
        return None
    if len(value) > MAX_LEN or value.count(":") > 2:
        return None
    if not _ALLOWED.fullmatch(value) or not any(c.isdigit() for c in value):
        return None
    return value


def is_valid_range(text) -> bool:
    pass
    return normalize_range(text) is not None


def expand_range(spec: str, versions) -> list:
    pass







    value = normalize_range(spec)
    if not value:
        return []
    nums = sorted(
        int(v) for v in versions
        if str(v).strip().isdigit() and int(v) > 0
    )
    if not nums:
        return []

    parts = value.split(":")
    if len(parts) == 1:
        wanted = {int(parts[0])}
    elif len(parts) == 2:
        start = int(parts[0]) if parts[0] else nums[0]
        end = int(parts[1]) if parts[1] else nums[-1]
        wanted = set(range(start, end + 1))
    elif len(parts) == 3 and parts[0] == "" and parts[1] == "":
        count = int(parts[2])
        wanted = set(nums[-count:]) if count > 0 else set()
    else:
        return []

    return [n for n in nums if n in wanted]
