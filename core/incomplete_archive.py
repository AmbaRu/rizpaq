from __future__ import annotations

from pathlib import Path


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
