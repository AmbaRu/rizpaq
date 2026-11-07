


































from __future__ import annotations

import time

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core import archive_index
from core import config as config_mod
from ui.i18n import tr
from ui.presentation import format_size
from ui.qt_compat import HEADER_STRETCH, USER_ROLE
from workers.catalog_worker import CatalogWorker

                                                                        
COL_PATH = 0
COL_SIZE = 1
COL_DATE = 2
COL_ENTRIES = 3
COL_INDEXED = 4
COL_MISSING = 5
COLUMN_COUNT = 6


def _format_time(timestamp: int) -> str:
    if not timestamp:
        return ""
    try:
        return time.strftime("%d.%m.%Y %H:%M", time.localtime(int(timestamp)))
    except (OverflowError, OSError, ValueError):
        return ""


class ArchiveCatalogDialog(QDialog):
    pass

    def __init__(self, roots=None, index_on_scan: bool = True,
                 zpaq_bin: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("catalog.title"))
        self.resize(820, 520)

        self._zpaq_bin = str(zpaq_bin or "")
        self._worker = None
        self._chosen = ""
        self._roots = self._dedup_roots(roots or [])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

                                                                         
        roots_header = QHBoxLayout()
        roots_header.addWidget(QLabel(tr("catalog.roots")))
        roots_header.addStretch(1)

        self.add_roots_btn = QPushButton(tr("catalog.add_roots"))
        self.add_roots_btn.clicked.connect(self._on_add_roots)
        roots_header.addWidget(self.add_roots_btn)

        self.remove_roots_btn = QPushButton(tr("catalog.remove_roots"))
        self.remove_roots_btn.clicked.connect(self._on_remove_roots)
        roots_header.addWidget(self.remove_roots_btn)

        layout.addLayout(roots_header)

        self.roots_list = QListWidget()
        self.roots_list.setSelectionMode(
            QAbstractItemView.ExtendedSelection)
        self.roots_list.setMaximumHeight(90)
        layout.addWidget(self.roots_list)
        self._fill_roots()

                                                                         
        self.index_check = QCheckBox(tr("catalog.index_on_scan"))
        self.index_check.setChecked(bool(index_on_scan))
        self.index_check.setToolTip(tr("catalog.index_on_scan.tip"))
        self.index_check.toggled.connect(self._on_index_toggled)
        layout.addWidget(self.index_check)

                                                                          
        self.table = QTableWidget()
        self.table.setColumnCount(COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels([
            tr("catalog.col.path"),
            tr("catalog.col.size"),
            tr("catalog.col.date"),
            tr("catalog.col.entries"),
            tr("catalog.col.indexed"),
            tr("catalog.col.missing"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(
            COL_PATH, HEADER_STRETCH)
        self.table.itemDoubleClicked.connect(self._on_double_clicked)
        layout.addWidget(self.table, 1)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

                                                                          
        buttons = QHBoxLayout()

        self.scan_btn = QPushButton(tr("catalog.scan"))
        self.scan_btn.clicked.connect(self._on_scan)
        buttons.addWidget(self.scan_btn)

        self.stop_btn = QPushButton(tr("catalog.stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        buttons.addWidget(self.stop_btn)

        buttons.addStretch(1)

        self.open_btn = QPushButton(tr("catalog.open"))
        self.open_btn.clicked.connect(self._on_open)
        buttons.addWidget(self.open_btn)

        self.forget_btn = QPushButton(tr("catalog.forget"))
        self.forget_btn.clicked.connect(self._on_forget)
        buttons.addWidget(self.forget_btn)

        self.close_btn = QPushButton(tr("catalog.close"))
        self.close_btn.clicked.connect(self.reject)
        buttons.addWidget(self.close_btn)

        layout.addLayout(buttons)

        self._reload()

                                                                            

    def chosen_path(self) -> str:
        pass
        return self._chosen

    def roots(self) -> list:
        return list(self._roots)

    def index_on_scan(self) -> bool:
        return self.index_check.isChecked()

                                                                             

    @staticmethod
    def _dedup_roots(roots) -> list:
        out = []
        seen = set()
        for root in roots:
            path = str(root or "").strip()
            if not path:
                continue
            key = path.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(path)
        return out

    def _fill_roots(self) -> None:
        from PySide6.QtWidgets import QListWidgetItem

        self.roots_list.clear()
        for root in self._roots:
            row = QListWidgetItem(root)
            row.setData(USER_ROLE, root)
            self.roots_list.addItem(row)

    def _on_add_roots(self) -> None:
        from ui.source_select_window import SourceSelectWindow

        dlg = SourceSelectWindow(self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._roots = self._dedup_roots(
            list(self._roots) + list(dlg.selected_paths()))
        self._fill_roots()
        self._persist()

    def _on_remove_roots(self) -> None:
        selected_rows = {
            self.roots_list.row(item)
            for item in self.roots_list.selectedItems()
        }
        if not selected_rows:
            return
        self._roots = [
            root for index, root in enumerate(self._roots)
            if index not in selected_rows
        ]
        self._fill_roots()
        self._persist()

    def _on_index_toggled(self, _checked: bool) -> None:
        pass
        self._persist()

    def _persist(self) -> None:
        try:
            config_mod.update(
                catalog_roots=list(self._roots),
                catalog_index_on_scan=self.index_check.isChecked(),
            )
        except Exception:
            pass

                                                                            

    def _reload(self) -> None:
        try:
            rows = archive_index.catalog_list()
        except Exception:
            rows = []
        self._fill_table(rows)

    def _fill_table(self, rows: list) -> None:
        self.table.setRowCount(len(rows))
        for row, rec in enumerate(rows):
            path = str(rec.get("path") or "")
            item_path = QTableWidgetItem(path)
            item_path.setData(USER_ROLE, path)
            self.table.setItem(row, COL_PATH, item_path)

            self.table.setItem(
                row, COL_SIZE,
                QTableWidgetItem(format_size(int(rec.get("size") or 0))))
            self.table.setItem(
                row, COL_DATE,
                QTableWidgetItem(_format_time(int(rec.get("mtime_ns") or 0)
                                              // 1_000_000_000)))
            self.table.setItem(
                row, COL_ENTRIES,
                QTableWidgetItem(str(int(rec.get("entries_count") or 0))))
            self.table.setItem(
                row, COL_INDEXED,
                QTableWidgetItem(
                    tr("catalog.yes") if rec.get("indexed")
                    else tr("catalog.no")))
            self.table.setItem(
                row, COL_MISSING,
                QTableWidgetItem(
                    tr("catalog.missing") if rec.get("missing") else ""))

        if not rows:
            self.status_label.setText(tr("catalog.empty"))
        else:
            self.status_label.setText(
                tr("catalog.count", count=len(rows)))

                                                                             

    def _on_scan(self) -> None:
        if self._worker is not None:
            return
        if not self._roots:
            QMessageBox.information(
                self, tr("catalog.title"), tr("catalog.no_roots"))
            return

        self._persist()
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.open_btn.setEnabled(False)
        self.forget_btn.setEnabled(False)
        self.add_roots_btn.setEnabled(False)
        self.remove_roots_btn.setEnabled(False)
        self.index_check.setEnabled(False)
        self.status_label.setText(tr("catalog.scanning"))

        worker = CatalogWorker(
            self._roots,
            self._zpaq_bin,
            index_on_scan=self.index_check.isChecked(),
            parent=self,
        )
        worker.progress.connect(self._on_progress)
        worker.found.connect(self._on_found)
        worker.done.connect(self._on_done)
        self._worker = worker
        worker.start()

    def _on_stop(self) -> None:
        worker = self._worker
        if worker is None:
            return
        worker.cancel_request()
        self.stop_btn.setEnabled(False)
        self.status_label.setText(tr("catalog.stopping"))

    def _on_progress(self, info: dict) -> None:
        phase = str(info.get("phase") or "")
        if phase == "scan":
            self.status_label.setText(tr(
                "catalog.progress_scan",
                directories=int(info.get("directories") or 0),
                found=int(info.get("found") or 0),
            ))
        elif phase == "index":
            current = str(info.get("current") or "")
            text = tr(
                "catalog.progress_index",
                indexed=int(info.get("indexed") or 0),
                total=int(info.get("total") or 0),
            )
            if current:
                text = f"{text}  {current}"
            self.status_label.setText(text)

    def _on_found(self, _found: list) -> None:
                                                                       
                                                               
        self._reload()

    def _on_done(self, result: dict) -> None:
        worker = self._worker
        try:
            self._apply_done(result)
        finally:
                                                                     
                                                                     
                                                                     
                                          
            if worker is not None:
                try:
                    worker.wait(3000)
                except Exception:
                    pass
            self._worker = None

    def _apply_done(self, result: dict) -> None:
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.open_btn.setEnabled(True)
        self.forget_btn.setEnabled(True)
        self.add_roots_btn.setEnabled(True)
        self.remove_roots_btn.setEnabled(True)
        self.index_check.setEnabled(True)

        self._reload()

        if not result.get("ok"):
            if result.get("error"):
                QMessageBox.warning(
                    self, tr("catalog.error_title"),
                    tr("catalog.error_text", error=result.get("error")))
            elif result.get("cancelled"):
                self.status_label.setText(tr("catalog.cancelled"))
            else:
                self.status_label.setText(tr("catalog.done_empty"))
            return

        if result.get("cancelled"):
            self.status_label.setText(tr("catalog.cancelled"))
            return

        self.status_label.setText(tr(
            "catalog.done",
            found=len(result.get("found") or []),
            indexed=int(result.get("indexed") or 0),
            errors=int(result.get("error_count") or 0),
        ))

    def _on_double_clicked(self, _row: int, _col: int) -> None:
        self._on_open()

    def _selected_rows(self) -> list:
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        return rows

    def _on_open(self) -> None:
        rows = self._selected_rows()
        if not rows:
            return
        item = self.table.item(rows[0], COL_PATH)
        if item is None:
            return
        path = str(item.data(USER_ROLE) or item.text())
        if not path:
            return
        missing = self.table.item(rows[0], COL_MISSING)
        if missing is not None and missing.text():
            QMessageBox.warning(
                self, tr("catalog.title"),
                tr("catalog.file_missing", path=path))
            return
        self._chosen = path
        self.accept()

    def _on_forget(self) -> None:
        rows = self._selected_rows()
        if not rows:
            return
        paths = []
        for row in rows:
            item = self.table.item(row, COL_PATH)
            if item is not None:
                paths.append(str(item.data(USER_ROLE)
                                 or item.text()))
        for path in paths:
            if path:
                archive_index.catalog_forget(path)
        self._reload()

                                                                             

    def closeEvent(self, event) -> None:
        worker = self._worker
        if worker is not None:
            worker.cancel_request()
                                                                   
                                                                 
            try:
                worker.wait(5000)
            except Exception:
                pass
            self._worker = None
        super().closeEvent(event)
