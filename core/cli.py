from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt


_OPTION_FLAGS = ("--create", "--test", "--extract", "--extract-here", "--task")


_VALUE_FLAGS = ("--dest",)


_ARCHIVE_EXTENSIONS = (".zpaq", ".zip", ".7z", ".rar")


def find_archive_arg(args: list):

    i = 0
    n = len(args)
    while i < n:
        a = args[i]
        if a in _VALUE_FLAGS:
            i += 2
            continue
        if a in _OPTION_FLAGS:
            i += 1
            continue
        return a
    return None


def get_flag_value(args: list, flag: str):

    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            return args[i + 1]
    return None


def _raise_window(window):

    try:
        window.setWindowState(window.windowState() & ~Qt.WindowMinimized)
        window.show()
        window.raise_()
        window.activateWindow()
    except Exception:
        pass


def _extract_direct(window, arc: str, dest: str) -> bool:
    try:
        from PySide6.QtWidgets import QMessageBox

        from workers import ExtractFolderBatchWorker

        zpaq_bin = getattr(window, "zpaq_bin", None)
        if not zpaq_bin:
            zpaq_bin = os.environ.get("ZPAQ_BIN", "zpaqfranz")

        password = None
        try:
            password = window._cache(arc).get("password")
        except Exception:
            password = None


        try:
            Path(dest).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass


        try:
            window.extract_bar.begin_file(Path(arc).name)
        except Exception:
            pass

        worker = ExtractFolderBatchWorker(zpaq_bin, arc, password, "", None, dest)

        def _on_percent(p):
            try:
                window.extract_bar.set_percent(p)
            except Exception:
                pass

        def _on_done(result):
            ok = bool(result.get("ok"))
            log = result.get("log", "") or ""
            try:
                window.extract_bar.finish(ok, 0, dest)
            except Exception:
                pass
            if log:
                try:
                    window.log_output(log)
                except Exception:
                    pass
            if ok:
                try:
                    window.statusBar().showMessage(f"Распаковано в {dest}")
                except Exception:
                    pass
            else:
                try:
                    window.statusBar().showMessage("Ошибка распаковки")
                except Exception:
                    pass
                try:
                    QMessageBox.warning(
                        window, "Rizpaq", (log or "Ошибка распаковки")[:3000]
                    )
                except Exception:
                    pass

        def _cleanup(_w=None):
            try:
                if worker in window._workers:
                    window._workers.remove(worker)
            except Exception:
                pass

        worker.percent.connect(_on_percent)
        worker.done.connect(_on_done)
        worker.finished.connect(_cleanup)
        try:
            window._workers.append(worker)
        except Exception:
            pass
        worker.start()
        return True
    except Exception:
        return False


def handle_cli_command(window, args: list):

    if not args:
        _raise_window(window)
        return

    first = str(args[0]).strip()

    if not first:
        _raise_window(window)
        return

    if first == "--create":
        _raise_window(window)
        sources = [str(a) for a in args[1:] if str(a).strip()]
        if sources:
            window._start_create_archive(sources)
        return

    if first == "--test":
        _raise_window(window)
        if len(args) >= 2:
            window._on_test_archive(path=str(args[1]), mode="full")
        return

    if first == "--extract-here":
        if len(args) >= 2:
            arc = window._offer_nonlatin_rename(str(args[1]))
            if not arc:
                return
            dest = os.path.dirname(arc) or "."
            _raise_window(window)
            if _extract_direct(window, arc, dest):
                return
            window._enter_archive(arc)
        return

    if first == "--extract":
        if len(args) >= 2:
            arc = window._offer_nonlatin_rename(str(args[1]))
            if not arc:
                return
            dest = get_flag_value(args, "--dest")
            _raise_window(window)
            if dest and _extract_direct(window, arc, str(dest)):
                return
            window._enter_archive(arc)
        return


    if first.lower().endswith(".rzp"):
        _raise_window(window)
        opener = getattr(window, "_open_rzp", None)
        if callable(opener):
            try:
                opener(first)
            except Exception:
                pass
        return


    if first.lower().endswith(_ARCHIVE_EXTENSIONS):
        _raise_window(window)
        window._enter_archive(first)
