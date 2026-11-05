from __future__ import annotations

from ui.extract_progress_dialog import ExtractProgressDialog


class ProgressBridgeMixin:


    def _ensure_extract_dialog(self) -> ExtractProgressDialog:
        dlg = getattr(self, "_extract_progress_dialog", None)

        if dlg is None:
            dlg = ExtractProgressDialog(parent=None)

            try:
                dlg.cancelRequested.connect(self._cancel_long_operations)
            except Exception:
                pass

            self._extract_progress_dialog = dlg

        return dlg


    def _ui_file_started(self, name: str = "") -> None:
        try:
            self._ensure_extract_dialog().begin_file(name)
        except Exception:
            pass

    def _ui_folder_started(self, total: int) -> None:
        try:
            self._ensure_extract_dialog().begin_folder(total)
        except Exception:
            pass

    def _ui_folder_batch_started(self) -> None:
        try:
            self._ensure_extract_dialog().begin_batch()
        except Exception:
            pass


    def _ui_folder_tick(self, i: int, total: int, path: str) -> None:
        try:
            dlg = getattr(self, "_extract_progress_dialog", None)
            if dlg is not None:
                dlg.tick(i, total, path)
        except Exception:
            pass

    def _ui_folder_percent(self, pct: int) -> None:
        try:
            dlg = getattr(self, "_extract_progress_dialog", None)
            if dlg is not None:
                dlg.set_percent(pct)
        except Exception:
            pass

    def _ui_extract_info(self, info: dict) -> None:
        try:
            dlg = getattr(self, "_extract_progress_dialog", None)
            if dlg is not None:
                dlg.update_info(info)
        except Exception:
            pass

    def _ui_extract_output(self, text: str) -> None:
        try:
            dlg = getattr(self, "_extract_progress_dialog", None)
            if dlg is not None:
                dlg.append_output(text)
        except Exception:
            pass


    def _ui_extract_finished(self, ok: bool, total: int, msg: str) -> None:
        try:
            dlg = getattr(self, "_extract_progress_dialog", None)
            if dlg is not None:
                dlg.finish(bool(ok), msg or "")
        except Exception:
            pass
