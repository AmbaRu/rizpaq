from __future__ import annotations

import fnmatch


def match_query(query: str, path: str) -> bool:
    q = (query or "").strip()
    if not q:
        return True
    if "*" in q or "?" in q:
        low_q = q.lower()
        low_path = path.lower()

        name = low_path.rsplit("/", 1)[-1]

        return fnmatch.fnmatch(name, low_q) or fnmatch.fnmatch(low_path, low_q)
    return q.lower() in path.lower()


def search_all(query: str, archives) -> list:
    q = (query or "").strip()
    results: list = []
    if not q:
        return results

    for archive_path, entries in archives or []:
        if not entries:
            continue
        for e in entries:
            path = getattr(e, "path", "") or ""
            if not path or not match_query(q, path):
                continue
            results.append({
                "archive": archive_path,
                "path": path,
                "size": int(getattr(e, "size", 0) or 0),
                "version": getattr(e, "version", None),
                "is_dir": bool(getattr(e, "is_dir", False)),
                "date": getattr(e, "datetime", "") or "",
            })
    return results
