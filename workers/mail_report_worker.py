






from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core import mail_report


class MailReportWorker(QThread):
    pass

    done = Signal(int, str)

    def __init__(self, zpaq_bin: str, mail: mail_report.MailConfig,
                 subject: str, body: str, customer: str = "", parent=None):
        super().__init__(parent)
        self._zpaq_bin = zpaq_bin
        self._mail = mail
        self._subject = subject
        self._body = body
        self._customer = customer

    def run(self):
        rc, output = mail_report.send_log_email(
            self._zpaq_bin, self._mail, self._subject, self._body,
            self._customer,
        )
        self.done.emit(int(rc), str(output or ""))
