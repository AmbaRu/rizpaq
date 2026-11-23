
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core import retention
from core.zpaq_cli import run_zpaq


class RetentionWorker(QThread):
    pass

    done = Signal(dict)

    def __init__(self, zpaq: str, arc: str, policy: str,
                 password=None, apply: bool = False, parent=None):
        super().__init__(parent)
        self.zpaq = str(zpaq)
        self.arc = str(arc)
        self.policy = str(policy)
        self.password = password
        self.apply = bool(apply)

    def run(self):
        try:
            if self.apply:
                ok, text = retention.run_apply(
                    self.zpaq, self.arc, self.policy, self.password
                )
            else:
                if not retention.valid_policy(self.policy):
                    ok, text = False, "invalid retention policy"
                else:
                    rc, out = run_zpaq(retention.preview_cmd(
                        self.zpaq, self.arc, self.policy, self.password
                    ))
                    ok, text = rc == 0, out or ""
        except Exception as exc:
            ok, text = False, "%s: %s" % (type(exc).__name__, exc)
        self.done.emit({
            "ok": ok,
            "text": text,
            "apply": self.apply,
            "path": self.arc,
        })
