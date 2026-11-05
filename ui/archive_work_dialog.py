from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.qt_compat import PASSWORD_ECHO


class ArchiveWorkDialog(QDialog):


    def __init__(self, work: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("work.dialog_title"))
        self.setMinimumWidth(560)

        self._work = dict(work or {})
        self._result = None


        self._password_action = "keep"
        self._password_value = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)


        self._title_edit = QLineEdit(str(self._work.get("title") or ""))
        self._title_edit.setPlaceholderText(tr("create.work_title_placeholder"))
        form.addRow(tr("create.work_title"), self._title_edit)


        self._source_list = QListWidget()
        self._source_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._source_list.setMinimumHeight(80)
        self._source_list.setMaximumHeight(160)
        for s in self._work.get("sources") or []:
            self._source_list.addItem(str(s))
        form.addRow(tr("create.source"), self._source_list)

        src_btn_row = QHBoxLayout()
        btn_sel = QPushButton(tr("create.select_sources"))
        btn_sel.clicked.connect(self._on_select_sources)
        btn_rem = QPushButton(tr("create.remove_source"))
        btn_rem.clicked.connect(self._on_remove_source)
        src_btn_row.addWidget(btn_sel)
        src_btn_row.addWidget(btn_rem)
        src_btn_row.addStretch(1)
        form.addRow("", src_btn_row)


        dest_row = QHBoxLayout()
        self._dest_edit = QLineEdit(str(self._work.get("dest") or ""))
        br_btn = QPushButton("…")
        br_btn.setFixedWidth(32)
        br_btn.clicked.connect(self._browse_dest)
        dest_row.addWidget(self._dest_edit, 1)
        dest_row.addWidget(br_btn)
        form.addRow(tr("create.destination"), dest_row)


        self._comment_edit = QLineEdit(str(self._work.get("comment") or ""))
        form.addRow(tr("create.comment"), self._comment_edit)


        self._only_edit = QLineEdit(
            "; ".join(self._work.get("only_masks") or [])
        )
        self._only_edit.setPlaceholderText("*.txt; *.doc")
        form.addRow(tr("create.only"), self._only_edit)

        self._not_edit = QLineEdit(
            "; ".join(self._work.get("not_masks") or [])
        )
        self._not_edit.setPlaceholderText("*.tmp; *.bak; Thumbs.db")
        form.addRow(tr("create.not"), self._not_edit)


        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)

        self._pwd_status = QLabel(self._password_status_text())
        pw_row.addWidget(self._pwd_status)
        pw_row.addStretch(1)

        self._pwd_set_btn = QPushButton(tr("work.password_set"))
        self._pwd_set_btn.setAutoDefault(False)
        self._pwd_set_btn.clicked.connect(self._on_set_password)
        pw_row.addWidget(self._pwd_set_btn)

        self._pwd_clear_btn = QPushButton(tr("work.password_clear"))
        self._pwd_clear_btn.setAutoDefault(False)
        self._pwd_clear_btn.clicked.connect(self._on_clear_password)
        pw_row.addWidget(self._pwd_clear_btn)

        form.addRow(tr("check.password"), pw_row)

        layout.addLayout(form)
        layout.addStretch(1)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        for std in (QDialogButtonBox.Ok, QDialogButtonBox.Cancel):
            b = buttons.button(std)
            if b:
                b.setAutoDefault(False)
                b.setDefault(False)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._sync_password_widgets()


    def _password_is_set(self) -> bool:
        if self._password_action == "clear":
            return False
        if self._password_action == "set":
            return bool(self._password_value)
        return bool(self._work.get("password_b64"))

    def _password_status_text(self) -> str:
        return (
            tr("check.password_set")
            if self._password_is_set()
            else tr("check.password_not_set")
        )

    def _sync_password_widgets(self) -> None:

        self._pwd_status.setText(self._password_status_text())

        self._pwd_clear_btn.setEnabled(self._password_is_set())


        self._pwd_set_btn.setEnabled(True)


    def _on_select_sources(self):
        from ui.source_select_window import SourceSelectWindow

        d = SourceSelectWindow(self)
        if d.exec() != QDialog.Accepted:
            return
        existing = {
            self._source_list.item(i).text()
            for i in range(self._source_list.count())
        }
        for p in d.selected_paths():
            if p and p not in existing:
                self._source_list.addItem(str(p))
                existing.add(str(p))

    def _on_remove_source(self):
        for it in self._source_list.selectedItems():
            self._source_list.takeItem(self._source_list.row(it))

    def _browse_dest(self):
        p, _ = QFileDialog.getSaveFileName(
            self,
            tr("create.dialog_title"),
            self._dest_edit.text().strip() or str(Path.home()),
            tr("create.filter"),
            options=QFileDialog.DontConfirmOverwrite,
        )
        if p:
            if not p.lower().endswith(".zpaq"):
                p += ".zpaq"
            self._dest_edit.setText(p)


    def _on_set_password(self):
        text, ok = QInputDialog.getText(
            self,
            tr("dialog.password.set_title"),
            tr("work.password_enter"),
            PASSWORD_ECHO,
        )
        if not ok or not text:
            return
        text2, ok2 = QInputDialog.getText(
            self,
            tr("dialog.password.set_title"),
            tr("work.password_confirm"),
            PASSWORD_ECHO,
        )
        if not ok2:
            return
        if text != text2:
            QMessageBox.warning(
                self,
                tr("dialog.password.set_title"),
                tr("create.password_mismatch"),
            )
            return
        self._password_action = "set"
        self._password_value = text
        self._sync_password_widgets()

    def _on_clear_password(self):

        self._password_action = "clear"
        self._password_value = ""
        self._sync_password_widgets()


    def _validate(self) -> bool:
        if not self._collect_sources():
            QMessageBox.warning(
                self, tr("work.dialog_title"), tr("create.no_source")
            )
            return False
        if not self._dest_edit.text().strip():
            QMessageBox.warning(
                self, tr("work.dialog_title"), tr("create.dest_required")
            )
            return False
        return True

    def _collect_sources(self) -> list:
        return [
            self._source_list.item(i).text()
            for i in range(self._source_list.count())
        ]

    @staticmethod
    def _split_masks(text: str) -> list:
        if not text:
            return []
        return [
            p.strip()
            for p in text.replace(",", ";").split(";")
            if p.strip()
        ]

    def _collect_settings(self) -> dict:
        s = {
            "work_title": self._title_edit.text().strip(),
            "sources": self._collect_sources(),
            "dest": self._dest_edit.text().strip(),
            "comment": self._comment_edit.text().strip(),
            "only_masks": self._split_masks(self._only_edit.text()),
            "not_masks": self._split_masks(self._not_edit.text()),
            "password_action": self._password_action,
        }
        if self._password_action == "set":
            s["password"] = self._password_value
        return s

    def _on_accept(self):
        if not self._validate():
            return
        self._result = self._collect_settings()
        self.accept()

    def result_settings(self):

        return self._result
