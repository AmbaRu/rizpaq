from __future__ import annotations

import os
import time
from pathlib import Path


PLAIN_ARCHIVE_MAGIC = b"7kSt"

_INCOMPLETE_MARKERS = (
    "incomplete transaction",
    "incomplete trans",
    "detected a 'gap'",
    "almost certainly incomplete",
    "skipping block",
    "missing end of segment",
)


def incomplete_archive_action(dest: str, existed_before: bool) -> dict:
    p = Path(dest)
    if not p.exists():
        return {"action": "none", "reason": "файла нет"}
    if not p.is_file():
        return {"action": "keep",
                "reason": "это не файл, а каталог — удалять нельзя"}
    if existed_before:
        return {"action": "keep",
                "reason": "файл существовал до попытки: это готовый архив "
                          "с незавершённой транзакцией"}
    return {"action": "delete",
            "reason": "файл создан этой неудачной попыткой"}


def archive_encryption(path) -> str:
    try:
        with open(path, "rb") as f:
            head = f.read(len(PLAIN_ARCHIVE_MAGIC))
    except OSError:
        return "unknown"
    if head == PLAIN_ARCHIVE_MAGIC:
        return "plain"
    if len(head) < len(PLAIN_ARCHIVE_MAGIC):
        return "unknown"
    return "encrypted"


def repair_temp_path(dest: str) -> str:
    p = Path(dest)
    suffix = p.suffix or ".zpaq"
    token = f"{os.getpid()}-{time.time_ns()}"
    return str(p.with_name(f"{p.stem}.repair-{token}{suffix}"))


def incomplete_repair_plan(dest: str, password=None) -> dict:
    p = Path(dest)
    temp = repair_temp_path(dest)
    if "?" in str(p):
        return {"action": "none", "temp": temp, "reason": "многотомный архив"}
    if not p.is_file():
        return {"action": "none", "temp": temp, "reason": "это не файл"}

    kind = archive_encryption(str(p))
    if kind == "plain":
        return {
            "action": "trim",
            "temp": temp,
            "password": None,
            "reason": "обычный архив: trim в копию",
        }
    if kind == "encrypted":
        pw = str(password or "")
        if not pw:
            return {
                "action": "none",
                "temp": temp,
                "password": None,
                "needs_password": True,
                "reason": "архив зашифрован, пароль неизвестен",
            }
        return {
            "action": "crop",
            "temp": temp,
            "password": pw,
            "reason": "шифрованный архив: crop с ключом в копию",
        }
    return {"action": "none", "temp": temp, "reason": "формат не распознан"}


def incomplete_repair_command(zpaq: str, dest: str, plan: dict) -> list:
    action = plan.get("action")
    temp = plan.get("temp", "")
    if action == "trim":
        return [zpaq, "trim", dest, "-to", temp]
    if action == "crop":
        return [zpaq, "crop", dest, "-kill", "-to", temp,
                "-key", plan.get("password") or ""]
    raise ValueError(f"unknown repair action: {action!r}")


def incomplete_repair_check_command(zpaq: str, temp: str, plan: dict) -> list:
    cmd = [zpaq, "i", temp]
    if plan.get("action") == "crop" and plan.get("password"):
        cmd += ["-key", plan["password"]]
    return cmd


def incomplete_repair_verified(text: str, rc: int) -> bool:
    if rc != 0:
        return False
    low = (text or "").lower()
    return not any(marker in low for marker in _INCOMPLETE_MARKERS)
