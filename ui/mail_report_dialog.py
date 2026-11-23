











from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from core import config as config_mod
from core import mail_report, scheduler
from ui.i18n import tr
from ui.qt_compat import PASSWORD_ECHO


class _TestMailWorker(QThread):
    pass

    done = Signal(int, str)

    def __init__(self, zpaq_bin: str, mail: mail_report.MailConfig,
                 subject: str, parent=None):
        super().__init__(parent)
        self._zpaq_bin = zpaq_bin
        self._mail = mail
        self._subject = subject

    def run(self):
        rc, output = mail_report.send_test_email(
            self._zpaq_bin, self._mail, self._subject
        )
        self.done.emit(rc, output)


class MailReportDialog(QDialog):
    pass

    def __init__(self, settings=None, zpaq_bin: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("mail.title"))
        self.setToolTip(tr("tip.mail_report"))
        self.resize(620, 480)
        self._saved = None
        self._worker = None
        self._zpaq_bin = str(zpaq_bin or getattr(parent, "zpaq_bin", "") or "")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        self._enabled = QCheckBox(tr("mail.enabled"))
        lay.addWidget(self._enabled)

        self._heartbeat = QCheckBox(tr("mail.heartbeat"))
        lay.addWidget(self._heartbeat)

        watch_row = QHBoxLayout()
        self._hb_task_btn = QPushButton()
        self._hb_task_btn.clicked.connect(self._on_heartbeat_task)
        watch_row.addWidget(self._hb_task_btn)
        watch_row.addWidget(QLabel(tr("mail.heartbeat_hour")))
        self._hb_hour = QSpinBox()
        self._hb_hour.setRange(0, 23)
        self._hb_hour.setValue(9)
        watch_row.addWidget(self._hb_hour)
        self._hb_task_status = QLabel("")
        watch_row.addWidget(self._hb_task_status, 1)
        lay.addLayout(watch_row)
        self._refresh_heartbeat_task()

        form = QFormLayout()

        self._server = QLineEdit()
        self._server.setPlaceholderText("smtp.example.com")
        form.addRow(tr("mail.server.label"), self._server)

        self._port = QSpinBox()
        self._port.setRange(0, 65535)
        self._port.setSpecialValueText(tr("mail.port.auto"))
        form.addRow(tr("mail.port.label"), self._port)

        self._tls = QComboBox()
        self._tls.addItem(tr("mail.tls.starttls"), mail_report.TLS_STARTTLS)
        self._tls.addItem(tr("mail.tls.ssl"), mail_report.TLS_SSL)
        self._tls.currentIndexChanged.connect(self._update_port_hint)
        form.addRow(tr("mail.tls.label"), self._tls)

        self._user = QLineEdit()
        self._user.setPlaceholderText("user@example.com")
        form.addRow(tr("mail.user.label"), self._user)

        self._password = QLineEdit()
        self._password.setEchoMode(PASSWORD_ECHO)
        form.addRow(tr("mail.password.label"), self._password)

        self._from = QLineEdit()
        self._from.setPlaceholderText("user@example.com")
        form.addRow(tr("mail.from.label"), self._from)

        self._to = QLineEdit()
        self._to.setPlaceholderText("me@example.com")
        form.addRow(tr("mail.to.label"), self._to)

        self._customer = QLineEdit()
        form.addRow(tr("mail.customer.label"), self._customer)

        lay.addLayout(form)

        hint = QLabel(tr("mail.hint"))
        hint.setWordWrap(True)
        lay.addWidget(hint)

        test_row = QHBoxLayout()
        self._test_btn = QPushButton(tr("mail.test"))
        self._test_btn.clicked.connect(self._on_test)
        test_row.addWidget(self._test_btn)
        self._test_status = QLabel("")
        self._test_status.setWordWrap(True)
        test_row.addWidget(self._test_status, 1)
        lay.addLayout(test_row)

        lay.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

        self._enabled.toggled.connect(self._set_enabled_state)
        self._load(settings if settings is not None else config_mod.load())

                                                                         

    def _collect(self) -> mail_report.MailConfig:
        pass
        return mail_report.MailConfig(
            enabled=self._enabled.isChecked(),
            server=self._server.text(),
            port=self._port.value(),
            tls=str(self._tls.currentData() or mail_report.TLS_STARTTLS),
            user=self._user.text(),
            password=self._password.text(),
            from_addr=self._from.text(),
            to=self._to.text(),
            customer=self._customer.text(),
        )

    def _load(self, settings) -> None:
        mail = mail_report.from_settings(settings)
        self._enabled.setChecked(mail.enabled)
        self._heartbeat.setChecked(
            bool(getattr(settings, "mail_heartbeat_enabled", False))
        )
        self._server.setText(mail.server)
        self._port.setValue(mail.port)
        index = self._tls.findData(mail.tls)
        self._tls.setCurrentIndex(index if index >= 0 else 0)
        self._update_port_hint()
        self._user.setText(mail.user)
        self._password.setText(mail.password)
        self._from.setText(mail.from_addr)
        self._to.setText(mail.to)
        self._customer.setText(mail.customer)
        self._set_enabled_state(mail.enabled)

    def _set_enabled_state(self, enabled: bool) -> None:
        for widget in (
            self._server, self._port, self._tls, self._user,
            self._password, self._from, self._to, self._customer,
        ):
            widget.setEnabled(bool(enabled))
        self._test_btn.setEnabled(bool(enabled))

    def _update_port_hint(self, _index=None) -> None:
        pass





        tls = str(self._tls.currentData() or mail_report.TLS_STARTTLS)
        port = mail_report.DEFAULT_PORTS.get(tls, 587)
        self._port.setSpecialValueText(tr("mail.port.auto", port=port))

                                                                             

    def _save(self) -> None:
        mail = self._collect()
        if mail.enabled:
            problem = self._validation_error(mail)
            if problem:
                QMessageBox.warning(self, tr("mail.error.title"), problem)
                return
        self._saved = config_mod.update(
            mail_report_enabled=mail.enabled,
            mail_smtp_server=mail.server,
            mail_smtp_port=mail.port,
            mail_smtp_tls=mail.tls,
            mail_smtp_user=mail.user,
            mail_smtp_password=mail.password,
            mail_from=mail.from_addr,
            mail_to=mail.to,
            mail_customer=mail.customer,
            mail_heartbeat_enabled=self._heartbeat.isChecked(),
        )
        self.accept()

    def _validation_error(self, mail: mail_report.MailConfig) -> str:
        pass
        labels = {
            "server": tr("mail.field.server"),
            "from": tr("mail.field.from"),
            "to": tr("mail.field.to"),
        }
        missing = [labels[key] for key in mail.missing()]
        if missing:
            return tr("mail.error.missing", fields=", ".join(missing))
        if not mail_report.looks_like_address(mail.from_addr):
            return tr("mail.error.address", field=labels["from"])
        if not mail_report.looks_like_address(mail.to):
            return tr("mail.error.address", field=labels["to"])
        return ""

                                                                           

    def _refresh_heartbeat_task(self) -> None:
        pass
        registered = False
        try:
            registered = scheduler.is_heartbeat_task_scheduled()
        except Exception:
            pass
        self._hb_task_btn.setText(
            tr("mail.heartbeat_task_remove" if registered
               else "mail.heartbeat_task_create")
        )
        self._hb_task_status.setText(tr(
            "mail.heartbeat_task_status",
            state=tr("mail.heartbeat_task_on" if registered
                     else "mail.heartbeat_task_off"),
        ))

    def _on_heartbeat_task(self) -> None:
        pass
        try:
            registered = scheduler.is_heartbeat_task_scheduled()
            if registered:
                ok = scheduler.remove_heartbeat_task()
            else:
                ok = scheduler.create_heartbeat_task(self._hb_hour.value())
            if not ok:
                QMessageBox.warning(
                    self, tr("mail.heartbeat"),
                    tr("mail.heartbeat_task_failed"),
                )
        except Exception as exc:
            QMessageBox.warning(self, tr("mail.heartbeat"), str(exc))
        self._refresh_heartbeat_task()

    def _on_test(self) -> None:
        if self._worker is not None:
            return
        mail = self._collect()
                                                                  
                                             
        mail.enabled = True
        problem = self._validation_error(mail)
        if problem:
            QMessageBox.warning(self, tr("mail.error.title"), problem)
            return
        if not self._zpaq_bin:
            QMessageBox.warning(
                self, tr("mail.error.title"), tr("mail.error.no_engine")
            )
            return

        self._test_btn.setEnabled(False)
        self._test_status.setText(tr("mail.test.sending"))
        worker = _TestMailWorker(
            self._zpaq_bin, mail, tr("mail.test_subject"), self
        )
        worker.done.connect(self._on_test_done)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        worker.start()

    def _on_test_done(self, rc: int, output: str) -> None:
        if rc == 0:
            self._test_status.setText(tr("mail.test.ok"))
            return
        tail = (output or "").strip()
        if len(tail) > 400:
            tail = "…" + tail[-400:]
        self._test_status.setText(
            tr("mail.test.fail", rc=rc) + ("\n" + tail if tail else "")
        )

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._test_btn.setEnabled(self._enabled.isChecked())

                                                                            

    def saved_settings(self):
        pass
        return self._saved
