















from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time

from PySide6.QtCore import QMimeData, Qt, QTimer, QUrl
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QTableWidget,
)

from core.paths import find_extracted_path
from ui.i18n import tr
from ui.qt_compat import K_ARC_DIR, K_ARC_FILE, KIND_ROLE, USER_ROLE

                                                                       
_DRAG_CLEANUP_MS = 3000

                                               
_DRAG_EXTRACT_TIMEOUT = 120

                                                                     
                                                                      
_CMDLINE_LIMIT = 24000


def _chunk_patterns(patterns: list) -> list:
    pass





    chunks: list = []
    current: list = []
    size = 0

    for pat in patterns:
                                   
        cost = len(pat) + 8
        if current and size + cost > _CMDLINE_LIMIT:
            chunks.append(current)
            current = []
            size = 0
        current.append(pat)
        size += cost

    if current:
        chunks.append(current)

    return chunks or [[]]


def _extract_for_drag(zpaq_bin, archive_path, password, targets,
                      timeout=None, pump=None):
    pass














                                                                            
                                                                          
                                                                         
                                                                      
                                                     
    notes = {"timed_out": False, "chunks": 0, "chunks_done": 0,
             "timeout": 0}

    if not zpaq_bin or not archive_path or not targets:
        return [], None, notes

    if timeout is None:
        timeout = _DRAG_EXTRACT_TIMEOUT

    notes["timeout"] = timeout

    try:
        temp_dir = tempfile.mkdtemp(prefix="rizpaq_drag_")
    except Exception:
        return [], None, notes

    patterns = [
        (inner.rstrip("/") + "/*" if is_dir else inner)
        for inner, is_dir in targets
    ]

    deadline = time.monotonic() + timeout

    chunks = _chunk_patterns(patterns)
    notes["chunks"] = len(chunks)

    for chunk in chunks:
        cmd = [zpaq_bin, "x", archive_path]

        if password:
            cmd += ["-key", password]

        for pat in chunk:
            cmd += ["-only", pat]

        cmd += ["-to", temp_dir, "-noeta", "-force"]

        left = deadline - time.monotonic()
        if left <= 0:
                                                                           
                                                                     
            notes["timed_out"] = True
            break

        try:
            subprocess.run(cmd, capture_output=True, timeout=max(1.0, left))
        except subprocess.TimeoutExpired:
                                                                             
                                                                      
                                                               
            notes["timed_out"] = True
            break
        except Exception:
            continue

        notes["chunks_done"] += 1

                                                                            
                                                                          
                                                
        if pump is not None:
            try:
                pump()
            except Exception:
                pass

    urls = []

    for inner, is_dir in targets:
        try:
            found = find_extracted_path(
                temp_dir,
                inner,
                want_dir=bool(is_dir),
            )
        except Exception:
            found = None

        if found:
            urls.append(str(found))

                                                                          
    if not urls:
        try:
            names = os.listdir(temp_dir)
        except Exception:
            names = []

        urls = [os.path.join(temp_dir, n) for n in names]

    return urls, temp_dir, notes


class ArchiveTable(QTableWidget):
    pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        mw = self.window()

        if mw is None or getattr(mw, "mode", "fs") != "archive":
            return

                                                                
        targets = []
        seen_rows = set()

        for idx in self.selectedIndexes():
            if idx.column() != 0:
                continue

            row = idx.row()
            if row in seen_rows:
                continue

            seen_rows.add(row)

            item = self.item(row, 0)
            if not item:
                continue

            kind = item.data(KIND_ROLE)
            payload = item.data(USER_ROLE)

            if payload is None:
                continue

            if kind == K_ARC_FILE:
                path = getattr(payload, "path", None)
                if path:
                    targets.append((str(path), False))
            elif kind == K_ARC_DIR:
                targets.append((str(payload), True))

        if not targets:
            return

                                                                      
         
                                                                          
                                                                            
                                                                     
                                                                    
                        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.statusBar().showMessage(tr("status.preparing_drag"))
        except Exception:
            pass

        def _pump():
            try:
                QApplication.processEvents()
            except Exception:
                pass

        try:
            urls, temp_dir, notes = _extract_for_drag(
                getattr(mw, "zpaq_bin", None),
                getattr(mw, "archive_path", None),
                getattr(mw, "password", None),
                targets,
                pump=_pump,
            )
        finally:
            QApplication.restoreOverrideCursor()
            try:
                self.statusBar().clearMessage()
            except Exception:
                pass

        if not urls:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass
            if notes.get("timed_out"):
                                                                       
                                                                          
                                                                     
                                                                         
                QMessageBox.warning(
                    self,
                    tr("drag.error_title"),
                    tr("drag.extract_timeout",
                       seconds=notes.get("timeout") or 0),
                )
            return

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(u) for u in urls])

        drag = QDrag(self)
        drag.setMimeData(mime)

        try:
            exec_fn = getattr(drag, "exec", None) or getattr(drag, "exec_", None)
            if exec_fn:
                exec_fn(Qt.CopyAction)
        finally:
            if temp_dir:
                try:
                    QTimer.singleShot(
                        _DRAG_CLEANUP_MS,
                        lambda d=temp_dir: shutil.rmtree(d, ignore_errors=True),
                    )
                except Exception:
                    pass
