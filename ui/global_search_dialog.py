




















from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.archive_index import list_archives, load_entries
from core.search import search_all
from ui.i18n import tr
from ui.presentation import format_size

                                                                       
                                                                      
                                                                   
                                                                  
                                              
_MAX_RESULT_ROWS = 2000


class GlobalSearchDialog(QDialog):
    pass








    archive_requested = Signal(str)
                                                                    
                                                                        
                                                                        
                                          
    catalog_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("global_search.title"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("search.placeholder"))
        self.search_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_edit)

        self.results = QTableWidget()
        self.results.setColumnCount(5)
        self.results.setHorizontalHeaderLabels([
            tr("global_search.archive"),
            tr("table.header.path"),
            tr("table.header.size"),
            tr("table.header.version"),
            tr("table.header.date"),
        ])
        self.results.setSelectionBehavior(QTableWidget.SelectRows)
        self.results.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.verticalHeader().setVisible(False)
        self.results.setSortingEnabled(False)
        self.results.itemDoubleClicked.connect(self._on_result_double_clicked)
        layout.addWidget(self.results, 1)

        self.count_label = QLabel("")
        bottom = QHBoxLayout()
        bottom.addWidget(self.count_label, 1)

        self.all_archives_btn = QPushButton(tr("global_search.all_archives"))
        self.all_archives_btn.setToolTip(
            tr("global_search.all_archives.tip"))
        self.all_archives_btn.clicked.connect(self.catalog_requested.emit)
        bottom.addWidget(self.all_archives_btn)

        layout.addLayout(bottom)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(180)
        self._timer.timeout.connect(self._apply_search)

                                                                     
                                                                     
                                                                    
                                                                    
                                       
        self._archives = None

                                                                          

    def reset_search(self) -> None:
        pass







        self._archives = None
        self.results.clearContents()
        self.results.setRowCount(0)
        self.count_label.setText("")
        self.search_edit.clear()
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def open(self) -> None:
        pass
        self.reset_search()
        super().open()

                                                                            

    def _on_text_changed(self, _text: str) -> None:
        self._timer.start()

    def _apply_search(self) -> None:
        query = self.search_edit.text()
        if not (query or "").strip():
            self.results.clearContents()
            self.results.setRowCount(0)
            self.count_label.setText("")
            return

        if self._archives is None:
            self._archives = self._collect_archives()
        matches = search_all(query, self._archives)
        total = len(matches)
        shown = matches[:_MAX_RESULT_ROWS]

        self.results.setRowCount(len(shown))
        for row, m in enumerate(shown):
            self.results.setItem(row, 0, QTableWidgetItem(m["archive"]))
            self.results.setItem(row, 1, QTableWidgetItem(m["path"]))
            self.results.setItem(
                row, 2, QTableWidgetItem(format_size(m["size"]))
            )
            version = m["version"]
            self.results.setItem(
                row, 3, QTableWidgetItem(
                    str(version) if version is not None else tr("table.version")
                )
            )
            self.results.setItem(row, 4, QTableWidgetItem(m["date"] or ""))

        if not total:
            self.count_label.setText(tr("table.not_found", query=query))
        elif total > _MAX_RESULT_ROWS:
            self.count_label.setText(
                tr("search.count_shown_of",
                   found=total, shown=_MAX_RESULT_ROWS)
            )
        else:
            self.count_label.setText(
                tr("search.count_found_of", found=total, total=total)
            )

    def _collect_archives(self) -> list:
        pass





        out: list = []
        for arc in list_archives():
            path = str(arc.get("path") or "")
            entries = load_entries(path)
            if not entries:
                continue
            out.append((path, entries))
        return out

    def _on_result_double_clicked(self, _row: int, _col: int) -> None:
        row = self.results.currentRow()
        if row < 0:
            return
        archive = self.results.item(row, 0)
        if archive is None:
            return
        self.archive_requested.emit(str(archive.text()))
