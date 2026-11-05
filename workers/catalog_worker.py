from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.archive_catalog import scan_roots
from core.archive_index import (
    catalog_mark_scanned,
    catalog_upsert,
    is_fresh,
)
from core.index_refresh import refresh_index_sync
from core.password_store import get_password


class CatalogWorker(QThread):


    progress = Signal(dict)
    found = Signal(list)
    done = Signal(dict)


    MAX_ERRORS = 20

    def __init__(self, roots, zpaq_bin: str, index_on_scan: bool = True,
                 parent=None):
        super().__init__(parent)
        self._roots = [str(r) for r in (roots or []) if str(r or "").strip()]
        self._zpaq_bin = str(zpaq_bin or "")
        self._index_on_scan = bool(index_on_scan)
        self._cancel = False


    def cancel_request(self):
        self._cancel = True

    def _cancelled(self) -> bool:
        return bool(self._cancel)


    def run(self):
        result = {
            "ok": False,
            "cancelled": False,
            "roots": list(self._roots),
            "found": [],
            "indexed": 0,
            "skipped_fresh": 0,
            "total": 0,
            "missing": 0,
            "error_count": 0,
            "errors": [],
            "error": "",
        }


        try:
            found = self._scan(result)
            result["found"] = list(found)

            if self._cancelled():
                result["cancelled"] = True
                self.done.emit(result)
                return

            self.found.emit(list(found))
            self._index(found, result)

            result["ok"] = not self._cancelled()
            result["cancelled"] = self._cancelled()
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            result["ok"] = False
            result["cancelled"] = self._cancelled()

        self.done.emit(result)


    def _scan(self, result: dict) -> list:
        errors = result["errors"]

        def on_error(path: str, exc: Exception) -> None:
            result["error_count"] += 1
            if len(errors) < self.MAX_ERRORS:
                errors.append(f"{path}: {type(exc).__name__}: {exc}")

        def on_progress(info: dict) -> None:
            self.progress.emit({
                "phase": "scan",
                "directories": int(info.get("directories") or 0),
                "found": int(info.get("found") or 0),
                "current": str(info.get("current") or ""),
            })

        found = scan_roots(
            self._roots,
            should_stop=self._cancelled,
            on_progress=on_progress,
            on_error=on_error,
        )


        paths = []
        for record in found:
            path = str(record.get("path") or "")
            if not path:
                continue
            catalog_upsert(path, record.get("size") or 0,
                           record.get("mtime_ns") or 0)
            paths.append(path)


        if not self._cancelled():
            result["missing"] = catalog_mark_scanned(self._roots, paths)

        return found


    def _index(self, found: list, result: dict) -> None:
        if not self._index_on_scan or not self._zpaq_bin:
            return


        candidates = [
            r for r in found
            if r.get("path") and "?" not in str(r["path"])
        ]
        result["total"] = len(candidates)
        if not candidates:
            return

        for record in candidates:
            if self._cancelled():
                return

            path = str(record["path"])
            size = int(record.get("size") or 0)
            mtime_ns = int(record.get("mtime_ns") or 0)

            self.progress.emit({
                "phase": "index",
                "indexed": result["indexed"],
                "total": len(candidates),
                "current": path,
            })


            if is_fresh(path, mtime_ns, size):
                result["skipped_fresh"] += 1
                continue

            password = None
            try:
                password = get_password(path)
            except Exception:
                password = None

            try:
                written = refresh_index_sync(
                    self._zpaq_bin, path, password,
                    is_cancelled=self._cancelled,
                )
            except Exception:
                written = 0

            if written:
                result["indexed"] += 1

        self.progress.emit({
            "phase": "index",
            "indexed": result["indexed"],
            "total": len(candidates),
            "current": "",
        })
