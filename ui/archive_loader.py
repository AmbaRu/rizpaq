from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QInputDialog, QMessageBox

from core import archive_index
from core.parser import parse_info
from core.zpaq_cli import looks_like_password_error
from ui.i18n import tr
from ui.presentation import format_size
from ui.qt_compat import (
    PASSWORD_ECHO,
    YES_BUTTON,
    YES_NO_BUTTONS,
    multipart_pattern,
)
from workers import StreamingListWorker, ZpaqWorker


_MIN_ZPAQ_SIZE = 13


class ArchiveLoaderMixin:


    def _cache(self, path: str) -> dict:
        key = multipart_pattern(path)
        return self._arc_cache.setdefault(
            key,
            {
                "entries": [],
                "versions": [],
                "summary": None,
                "password": None,
                "loaded": False,
                "info_loaded": False,
            },
        )

    def _activate_archive(self, path: str) -> None:
        self.archive_path = path
        c = self._cache(path)
        self.entries = c["entries"]
        self.versions = c["versions"]
        self.summary = c["summary"]
        self.password = c.get("password")
        self.version_slice = None
        self._rebuild_versions_menu()


        switcher = getattr(self, "_switch_main_page", None)
        if callable(switcher):
            try:
                switcher("archive")
            except Exception:
                pass


    def _check_zpaq_file_sane(self, path: str) -> bool:
        if "?" in str(path):

            return True

        try:
            size = os.path.getsize(path)
        except OSError:
            return True

        if size >= _MIN_ZPAQ_SIZE:
            return True


        name = Path(path).name
        if size == 0:
            msg = tr("archive.error.empty_file", name=name)
        else:
            msg = tr("archive.error.truncated_file", name=name, size=size)

        ans = QMessageBox.question(
            self,
            tr("archive.error.open_title"),
            msg + "\n\n" + tr("archive.error.delete_offer"),
            YES_NO_BUTTONS,
        )
        if ans == YES_BUTTON:
            try:
                os.remove(path)
                self.statusBar().showMessage(tr("archive.error.deleted", name=name))
                try:
                    self._on_refresh()
                except Exception:
                    pass
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    tr("archive.error.open_title"),
                    tr("delete.failed", name=name) + f"\n{exc}",
                )
        return False


    @staticmethod
    def _file_stamp(path) -> tuple | None:
        try:
            st = os.stat(str(path))
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return None

    def _try_index_load(self, path: str, make_active: bool, inner: str) -> bool:
        stamp = self._file_stamp(path)
        if stamp is None:

            try:
                archive_index.forget(str(path))
            except Exception:
                pass
            return False

        mtime_ns, size = stamp

        try:
            if not archive_index.is_fresh(str(path), mtime_ns, size):
                return False
            entries = archive_index.load_entries(str(path))
        except Exception:

            return False

        if entries is None:


            return False

        ctx = {"path": path, "make_active": make_active, "inner": inner}
        self._apply_list_entries(ctx, entries, report=None)
        return True

    def _index_store_if_unchanged(self, ctx: dict, entries: list) -> None:
        path = ctx.get("path")
        if not path:
            return
        if "?" in str(path):
            return
        stamp = ctx.get("file_stamp")
        if not stamp:
            return

        current = self._file_stamp(path)
        if current != stamp:
            return

        try:
            archive_index.store_entries(
                str(path), current[0], current[1], entries
            )
        except Exception:

            pass


    def _load_archive_list(self, path: str, make_active: bool, inner: str):

        if str(path).lower().endswith((".zip", ".7z", ".rar")):
            self._load_universal_archive_list(path, make_active, inner)
            return


        if not self._check_zpaq_file_sane(path):
            if make_active:
                self.navigate_fs(Path(path).parent)
            return


        if self._try_index_load(path, make_active, inner):
            return


        ctx = {
            "path": path,
            "make_active": make_active,
            "inner": inner,
            "file_stamp": self._file_stamp(path),
        }
        pw = self._cache(path).get("password")
        cmd = [
            self.zpaq_bin, "l", path,
            "-all", "-terse", "-csv", "\t", "-csvhf", "#", "-utf", "-noeta",
        ]
        if pw:
            cmd += ["-key", pw]

        self.log_command(cmd)
        reading_text = tr("status.reading_archive", name=Path(path).name)
        if make_active:
            self._start_busy(reading_text)
        else:
            self.statusBar().showMessage(reading_text)

        worker = StreamingListWorker(cmd, context=ctx)
        worker.result.connect(self._on_streaming_list_result)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()

    def _load_universal_archive_list(self, path: str, make_active: bool, inner: str):

        self._load_req = {"path": path, "make_active": make_active, "inner": inner, "is_universal": True}
        pw = self._cache(path).get("password")

        from workers.universal_worker import UniversalListWorker

        worker = UniversalListWorker(self.seven_zip_bin, path, pw)
        worker.listed.connect(
            lambda entries, log: self._on_universal_list_result(
                entries, log, path, make_active, inner
            )
        )


        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)

        reading_text = tr("status.reading_archive", name=Path(path).name)
        if make_active:
            self._start_busy(reading_text)
        else:
            self.statusBar().showMessage(reading_text)
        worker.start()

    def _load_info(self, path: str, quiet: bool = False):
        pw = self._cache(path).get("password")
        cmd = [self.zpaq_bin, "i", path, "-comment"]
        if pw:
            cmd += ["-key", pw]

        self.log_command(cmd)
        info_text = tr("status.archive_info_requested")

        if quiet:

            try:
                self.statusBar().showMessage(info_text)
            except Exception:
                pass
        else:
            try:


                self._start_busy(info_text)
            except Exception:
                pass

        worker = ZpaqWorker("info", cmd, {"path": path})
        worker.result.connect(self._on_worker_result)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.start()


    def _on_worker_result(self, result):
        kind = result.get("kind")
        if kind != "info":
            return

        rc = result.get("rc", 1)
        output = result.get("output", "")
        ctx = result.get("context", {}) or {}

        self.log_output(output)

        path = ctx.get("path")
        self._handle_info_result(path, rc, output)


        self._stop_busy()
        self._open_pending_dialogs(path)

    def _on_streaming_list_result(self, result: dict):
        try:
            rc = int(result.get("rc", 1))
            cancelled = bool(result.get("cancelled"))
            entries = result.get("entries") or []
            report = result.get("report")
            tail = str(result.get("tail") or "")

            path = result.get("path")
            if not path:
                self._refresh_status_for_current_mode()
                return

            make_active = bool(result.get("make_active"))
            inner = result.get("inner", "")


            if rc != 0 or cancelled:
                if tail:
                    self.log_output(tail)

            if cancelled:
                self.statusBar().showMessage(tr("status.cancel_requested"))
                return

            if rc != 0:
                if looks_like_password_error(tail):
                    pw, ok = QInputDialog.getText(
                        self,
                        tr("dialog.password.required_title"),
                        tr("dialog.password.required_text", name=Path(path).name),
                        PASSWORD_ECHO,
                    )
                    if ok and pw:
                        self._cache(path)["password"] = pw
                        if make_active and path == self.archive_path:
                            self.password = pw
                        self._load_archive_list(path, make_active, inner)
                    return

                if make_active and path == self.archive_path:
                    self.navigate_fs(Path(path).parent)
                self._refresh_status_for_current_mode()
                QMessageBox.critical(
                    self, tr("archive.error.open_title"), tail or ""
                )
                return

            if not entries:


                if report is not None and not report.ok:
                    self._report_list_loss(report)
                if make_active and path == self.archive_path:
                    self.navigate_fs(Path(path).parent)
                self._refresh_status_for_current_mode()
                QMessageBox.warning(
                    self,
                    tr("archive.error.no_data_title"),
                    tr("archive.error.no_data_text"),
                )
                return


            self._index_store_if_unchanged(result, entries)

            self._apply_list_entries(result, entries, report)
        finally:
            self._stop_busy()

    def _on_universal_list_result(self, entries, log, path, make_active, inner):

        self._stop_busy()
        self.log_output(log)

        if not entries:
            if make_active and path == self.archive_path:
                self.navigate_fs(Path(path).parent)
            self._refresh_status_for_current_mode()
            QMessageBox.warning(
                self,
                tr("archive.error.no_data_title"),
                tr("archive.error.no_data_text"),
            )
            return

        c = self._cache(path)
        c["entries"] = entries
        c["loaded"] = True
        c["versions"] = []
        c["summary"] = None
        c["info_loaded"] = True

        try:
            self.tree.build_archive_subtree(path, entries)
        except Exception:
            pass

        if make_active:
            self._activate_archive(path)
            try:
                self._nav_key = None
            except Exception:
                pass

            self.mode = "universal"
            self.archive_inner = inner
            self._populate_right_archive()
            self._update_chrome()
            self._rebuild_versions_menu()

            label = inner or "/"
            self.statusBar().showMessage(
                f"{Path(path).name} :: {label}"
            )
        else:
            self._refresh_status_for_current_mode()

    def _apply_list_entries(self, ctx: dict, entries: list, report) -> None:
        path = ctx.get("path")
        if not path:
            return
        make_active = bool(ctx.get("make_active"))
        inner = ctx.get("inner", "")

        c = self._cache(path)
        c["entries"] = entries
        c["loaded"] = True

        try:
            self.tree.build_archive_subtree(path, entries)
        except Exception:
            pass

        if make_active:
            self._activate_archive(path)
            try:
                self._nav_key = None
            except Exception:
                pass
            self.navigate_archive(inner, from_tree=False)
            if not c["info_loaded"]:
                self._load_info(path)
        else:
            self._refresh_status_for_current_mode()

        if report is not None and not report.ok:
            self._report_list_loss(report)

    def _report_list_loss(self, report) -> None:
        if report is None or report.ok:
            return
        try:
            self.log_output(report.log_text())
        except Exception:
            pass
        try:
            self.statusBar().showMessage(
                tr("status.list_partially_parsed", count=report.dropped)
            )
        except Exception:
            pass

    def _handle_info_result(self, path, rc: int, output: str):
        if not path:
            return

        if rc != 0 and not (output or "").strip():
            self._refresh_status_for_current_mode()
            return

        summary, versions = parse_info(output)
        if summary is None and not versions:
            self._refresh_status_for_current_mode()
            return

        c = self._cache(path)
        if versions:
            c["versions"] = versions
        if summary is not None:
            c["summary"] = summary
        c["info_loaded"] = True

        if path == self.archive_path:
            if versions:
                self.versions = versions
            if summary is not None:
                self.summary = summary
            self._rebuild_versions_menu()
            if summary:
                self.statusBar().showMessage(
                    tr(
                        "status.archive_summary",
                        versions=summary.versions,
                        files=summary.files,
                        size=format_size(summary.size),
                    )
                )
            else:
                self._refresh_status_for_current_mode()
        else:
            self._refresh_status_for_current_mode()

    def _open_pending_dialogs(self, path: str) -> None:
        if not path:
            return

        key = multipart_pattern(path)

        pending_info = getattr(self, "_pending_info_path", None)
        if pending_info and multipart_pattern(pending_info) == key:
            self._pending_info_path = None
            opener = getattr(self, "_open_info_dialog", None)
            if callable(opener):
                try:
                    opener(path)
                except Exception:
                    pass

        pending_rep = getattr(self, "_pending_create_report", None)
        if pending_rep:
            dest = pending_rep.get("dest") or ""
            if multipart_pattern(dest) == key:
                self._pending_create_report = None

                self._create_report = pending_rep
                shower = getattr(self, "_show_create_report", None)
                if callable(shower):
                    try:
                        shower()
                    except Exception:
                        pass
