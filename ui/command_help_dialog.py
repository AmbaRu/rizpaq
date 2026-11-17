










from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from core import zpaq_help
from ui.i18n import tr


class CommandHelpDialog(QDialog):
    pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("help.cmd.title"))
        self.resize(900, 620)

        self._items = []
        self._root = zpaq_help.find_reference_root()

        top = QHBoxLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText(tr("help.cmd.search"))
        self.search.textChanged.connect(self._rebuild)
        top.addWidget(self.search)

        body = QHBoxLayout()
        self.list = QListWidget(self)
        self.list.currentRowChanged.connect(self._show_current)
        self.text = QTextBrowser(self)
        self.text.setReadOnly(True)
        mono = QFont("Consolas", 9)
        mono.setStyleHint(QFont.Monospace)
        self.text.setFont(mono)
        body.addWidget(self.list, 2)
        body.addWidget(self.text, 3)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)

        self.copy_button = QPushButton(tr("help.cmd.copy"), self)
        self.copy_button.clicked.connect(self._copy)
        buttons.addButton(self.copy_button, QDialogButtonBox.ActionRole)

        self.full_button = QPushButton(tr("help.cmd.open_full"), self)
        self.full_button.clicked.connect(self._open_full)
        buttons.addButton(self.full_button, QDialogButtonBox.ActionRole)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(QLabel(tr("help.cmd.empty"), self))
        layout.addLayout(body)
        layout.addWidget(buttons)

        self._rebuild()

                                                                                
    def _rebuild(self):
        query = self.search.text() if hasattr(self, "search") else ""
        self._items = zpaq_help.search(query, self._root)
        self.list.clear()
        for item in self._items:
            title = item.get("title") or ""
            self.list.addItem(
                f"{item['name']} — {title}" if title else item["name"]
            )
        if self._items:
            self.list.setCurrentRow(0)
        else:
            self.text.setPlainText(tr("help.cmd.not_found"))

    def _show_current(self, row: int):
        if row < 0 or row >= len(self._items):
            self.text.setPlainText(tr("help.cmd.empty"))
            return
        name = self._items[row]["name"]
        found = zpaq_help.lookup(name, self._root)
        if found is None:
            self.text.setPlainText(tr("help.cmd.not_found"))
            return
        header = f"# {found['name']} — {found['title']}\n"
        header += f"[{found['source']}]\n\n"
        self.text.setPlainText(header + found["text"])

    def _copy(self):
        text = self.text.toPlainText()
        if not text:
            return
        clipboard = _clipboard()
        if clipboard is not None:
            clipboard.setText(text)
            QMessageBox.information(self, tr("help.cmd.title"), tr("help.cmd.copied"))

    def _open_full(self):
        path = zpaq_help.reference_path(self._root)
        if path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            return
                                                                    
        if QMessageBox.question(
            self,
            tr("help.cmd.no_file_title"),
            tr("help.cmd.no_file_text"),
        ) == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(zpaq_help.WIKI_URL))


def _clipboard():
    pass
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    return app.clipboard() if app is not None else None
