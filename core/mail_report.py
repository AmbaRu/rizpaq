



























from __future__ import annotations

import os
import re
import tempfile

TLS_STARTTLS = "starttls"
TLS_SSL = "ssl"
TLS_CHOICES = (TLS_STARTTLS, TLS_SSL)

                                                               
DEFAULT_PORTS = {TLS_STARTTLS: 587, TLS_SSL: 465}


class MailConfig:
    pass







    __slots__ = (
        "enabled", "server", "port", "tls", "user", "password",
        "from_addr", "to", "customer",
    )

    def __init__(self, enabled=False, server="", port=0, tls=TLS_STARTTLS,
                 user="", password="", from_addr="", to="", customer=""):
        self.enabled = bool(enabled)
        self.server = str(server or "").strip()
        self.port = _clean_port(port)
        self.tls = tls if tls in TLS_CHOICES else TLS_STARTTLS
        self.user = str(user or "").strip()
        self.password = str(password or "")
        self.from_addr = str(from_addr or "").strip()
        self.to = str(to or "").strip()
        self.customer = str(customer or "").strip()

    @property
    def port_value(self) -> int:
        pass
        return self.port or DEFAULT_PORTS.get(self.tls, 587)

    def ready(self) -> bool:
        pass
        return self.enabled and not self.missing()

    def missing(self) -> list:
        pass
        out = []
        if not self.server:
            out.append("server")
        if not self.from_addr:
            out.append("from")
        if not self.to:
            out.append("to")
        return out


def _clean_port(value) -> int:
    pass
    try:
        port = int(value)
    except (TypeError, ValueError):
        return 0
    if port < 0 or port > 65535:
        return 0
    return port


def from_settings(settings) -> MailConfig:
    pass





    def _get(name, default=""):
        try:
            return getattr(settings, name, default)
        except Exception:
            return default

    return MailConfig(
        enabled=_get("mail_report_enabled", False),
        server=_get("mail_smtp_server", ""),
        port=_get("mail_smtp_port", 0),
        tls=_get("mail_smtp_tls", TLS_STARTTLS),
        user=_get("mail_smtp_user", ""),
        password=_get("mail_smtp_password", ""),
        from_addr=_get("mail_from", ""),
        to=_get("mail_to", ""),
        customer=_get("mail_customer", ""),
    )


def smtp_args(mail: MailConfig) -> list:
    pass






    args = ["-mailserver", mail.server]
    if mail.port:
        args += ["-mailport", str(mail.port)]
    if mail.tls == TLS_SSL:
        args.append("-mailssl")
    if mail.user:
        args += ["-mailuser", mail.user]
        if mail.password:
            args += ["-mailpassword", mail.password]
    if mail.from_addr:
        args += ["-mailfrom", mail.from_addr]
    return args


def report_args(mail: MailConfig, customer: str = "") -> list:
    pass







    if not mail.ready():
        return []
    args = smtp_args(mail)
    args += ["-mailfull", mail.to]
    name = str(customer or mail.customer or "").strip()
    if name:
        args += ["-customer", name]
    return args


def test_email_cmd(zpaq_bin, mail: MailConfig, subject: str) -> list:
    pass




    cmd = [str(zpaq_bin), "work", "email"]
    cmd += smtp_args(mail)
    if mail.to:
        cmd += ["-mailto", mail.to]
    cmd += ["-mailsubject", str(subject or "Rizpaq")]
    return cmd


def log_email_cmd(zpaq_bin, mail: MailConfig, subject: str, body_file,
                  customer: str = "") -> list:
    pass








    cmd = [str(zpaq_bin), "work", "email"]
    cmd += smtp_args(mail)
    if mail.to:
        cmd += ["-mailto", mail.to]
    cmd += ["-mailsubject", str(subject or "Rizpaq")]
    name = str(customer or "").strip()
    if name:
        cmd += ["-customer", name]
    if body_file:
        cmd += ["-mailbodyfile", str(body_file)]
    return cmd


def report_state(ok: bool, warnings: bool = False) -> str:
    pass
    if not ok:
        return "ERROR"
    return "WARNING" if warnings else "OK"


def subject_for(customer, ok: bool, warnings: bool = False) -> str:
    pass



    state = report_state(ok, warnings)
    parts = [state]
    name = str(customer or "").strip()
    if name:
        parts.append(name)
    parts.append("FULL")
    return " ".join(parts)


def send_log_email(zpaq_bin, mail: MailConfig, subject: str, body: str,
                   customer: str = "") -> tuple:
    pass







    fd, path = tempfile.mkstemp(prefix="rizpaq_mail_", suffix=".log")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(body or ""))
        cmd = log_email_cmd(zpaq_bin, mail, subject, path, customer)
        try:
            from core.zpaq_cli import run_zpaq

            rc, output = run_zpaq(cmd)
            return int(rc), str(output or "")
        except Exception as exc:
            return 1, "ERROR: %s: %s" % (type(exc).__name__, exc)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def mail_not_sent(output) -> bool:
    pass






    low = str(output or "").lower()
    if not low:
        return False
    english = "not sent" in low and "mail" in low
    russian = "не отправлено" in low and (
        "почт" in low or "письм" in low
    )
    return english or russian


def effective_rc(rc: int, output, mail_enabled: bool) -> int:
    pass







    if not mail_enabled or rc != 1:
        return rc
    low = str(output or "").lower()
    if mail_not_sent(low) and "(all ok)" in low:
        return 0
    return rc


def safe_log_line(cmd: list, password: str = "") -> str:
    pass
    from core.zpaq_cli import safe_cmdline

    return safe_cmdline(cmd, password or "")


def send_test_email(zpaq_bin, mail: MailConfig, subject: str = "Rizpaq"):
    pass






    if not mail.server or not mail.to:
        return 1, "ERROR: SMTP server and recipient are required"
    cmd = test_email_cmd(zpaq_bin, mail, subject)
    try:
        from core.zpaq_cli import run_zpaq

        rc, output = run_zpaq(cmd)
        return int(rc), str(output or "")
    except Exception as exc:
        return 1, "ERROR: %s: %s" % (type(exc).__name__, exc)


_ADDRESS_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def looks_like_address(value) -> bool:
    pass
    return bool(_ADDRESS_RE.match(str(value or "").strip()))
