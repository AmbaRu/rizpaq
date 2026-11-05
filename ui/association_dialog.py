from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)
from ui.i18n import tr


class AssociationDialog(QDialog):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("association.title"))
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)


        native_group = QGroupBox(tr("association.native_group"))
        native_layout = QVBoxLayout()

        from core.file_association import is_registered, is_rzp_registered

        self._cb_zpaq = QCheckBox(tr("association.zpaq"))
        self._cb_zpaq.setChecked(is_registered())
        native_layout.addWidget(self._cb_zpaq)

        self._cb_rzp = QCheckBox(tr("association.rzp"))
        self._cb_rzp.setChecked(is_rzp_registered())
        native_layout.addWidget(self._cb_rzp)

        native_group.setLayout(native_layout)
        layout.addWidget(native_group)


        uni_group = QGroupBox(tr("association.universal_group"))
        uni_layout = QVBoxLayout()

        from core.file_association import is_universal_registered

        self._cb_zip = QCheckBox(tr("association.zip"))
        self._cb_zip.setChecked(is_universal_registered(".zip"))
        uni_layout.addWidget(self._cb_zip)

        self._cb_7z = QCheckBox(tr("association.7z"))
        self._cb_7z.setChecked(is_universal_registered(".7z"))
        uni_layout.addWidget(self._cb_7z)

        self._cb_rar = QCheckBox(tr("association.rar"))
        self._cb_rar.setChecked(is_universal_registered(".rar"))
        uni_layout.addWidget(self._cb_rar)

        uni_group.setLayout(uni_layout)
        layout.addWidget(uni_group)


        warn = QLabel(tr("association.warning"))
        warn.setWordWrap(True)

        warn.setObjectName("assocWarn")
        layout.addWidget(warn)

        layout.addStretch(1)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._apply_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_and_accept(self):
        from core.file_association import (
            is_registered,
            is_rzp_registered,
            is_universal_registered,
            register_rzp,
            register_universal,
            register_zpaq,
            unregister_rzp,
            unregister_universal,
            unregister_zpaq,
        )


        stuck: list = []


        want_zpaq = self._cb_zpaq.isChecked()
        if want_zpaq:
            if not is_registered():
                register_zpaq()
        else:
            if not unregister_zpaq():
                stuck.append(".zpaq")


        want_rzp = self._cb_rzp.isChecked()
        if want_rzp:
            if not is_rzp_registered():
                register_rzp()
        else:
            if not unregister_rzp():
                stuck.append(".rzp")


        for cb, ext in [
            (self._cb_zip, ".zip"),
            (self._cb_7z, ".7z"),
            (self._cb_rar, ".rar"),
        ]:
            want = cb.isChecked()
            if want:
                if not is_universal_registered(ext):
                    register_universal(ext)
            else:
                if not unregister_universal(ext):
                    stuck.append(ext)


        try:
            from core.config import update as _cfg_update
            _cfg_update(associations_asked=True)
        except Exception:
            pass


        if stuck:
            ext_list = ", ".join(stuck)
            try:
                QMessageBox.warning(
                    self,
                    tr("association.title"),
                    tr("association.user_choice_failed_text", ext=ext_list),
                )
            except Exception:
                pass

        self.accept()
