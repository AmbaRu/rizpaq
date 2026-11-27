











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
