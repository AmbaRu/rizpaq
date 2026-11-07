














from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core import updater


class UpdateCheckWorker(QThread):
    pass

    done = Signal(dict)

    def __init__(self, url: str = "", current_version: str = "",
                 parent=None):
        super().__init__(parent)
        self._url = str(url or "")
        self._current = str(current_version or "")

    def run(self):
        result = {
            "ok": False,
            "info": None,
            "newer": False,
            "error": "",
            "current": self._current,
        }
        try:
            info = updater.fetch_manifest(
                self._url or None, timeout=updater.CHECK_TIMEOUT)
            result["info"] = info
            try:
                result["newer"] = updater.is_newer(
                    info["version"], self._current)
            except updater.UpdateError as exc:
                result["error"] = str(exc)
            result["ok"] = not result["error"]
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        self.done.emit(result)


class UpdateDownloadWorker(QThread):
    pass

    progress = Signal(dict)
    done = Signal(dict)

    def __init__(self, info: dict, dest_dir, parent=None):
        super().__init__(parent)
        self._info = dict(info or {})
        self._dest_dir = dest_dir
        self._cancel = False

    def cancel_request(self):
        pass
        self._cancel = True

    def _cancelled(self) -> bool:
        return bool(self._cancel)

    def run(self):
        result = {
            "ok": False,
            "path": "",
            "error": "",
            "cancelled": False,
        }
        try:
            def on_progress(read: int, total: int) -> None:
                percent = int(read * 100 / total) if total else 0
                self.progress.emit({
                    "read": int(read),
                    "total": int(total),
                    "percent": max(0, min(100, percent)),
                })

            path = updater.download_update(
                self._info,
                self._dest_dir,
                progress=on_progress,
                is_cancelled=self._cancelled,
            )
            updater.inspect_update_zip(path)
            result["path"] = str(path)
            result["ok"] = True
        except updater.UpdateCancelled:
            result["cancelled"] = True
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"

        if self._cancelled():
            result["cancelled"] = True
            result["ok"] = False
        self.done.emit(result)
