












from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from core import config as config_mod
from core import dashboard_alerts, mail_report, notify, run_history, tasks


def state_path() -> Path:
    pass
    try:
        return config_mod.default_path().parent / "mail_heartbeat.json"
    except Exception:
        return Path.home() / "mail_heartbeat.json"


def should_send(force: bool = False) -> bool:
    pass
    if force:
        return True
    try:
        data = json.loads(state_path().read_text(encoding="utf-8"))
        return str(data.get("last_date") or "") != str(date.today())
    except Exception:
        return True


def mark_sent() -> None:
    pass
    try:
        path = state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"last_date": str(date.today())}, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def build_report(tasks_dir: Optional[str] = None) -> list:
    pass






    cfg = config_mod.load()
    folder = tasks_dir or cfg.tasks_dir
    if not folder:
        return []
    try:
        container = tasks.load_container(tasks.container_path(folder))
        history = run_history.load_history(folder)
        alerts = dashboard_alerts.collect_alerts(container, history)
    except Exception:
        return []

    titles = {}
    for work in container.get("works") or []:
        wid = str(work.get("id") or "")
        titles[wid] = str(work.get("title") or "")
        for job in work.get("jobs") or []:
            titles[str(job.get("id") or "")] = str(job.get("title") or "")

    lines = []
    for alert in alerts or []:
        try:
            text = notify.tr(alert.text_key, **(alert.params or {}))
        except Exception:
            text = alert.text_key
        name = titles.get(str(alert.work_id or ""), "")
        job = titles.get(str(alert.job_id or ""), "")
        prefix = " / ".join(x for x in (name, job) if x)
        lines.append("- %s: %s" % (prefix, text) if prefix else "- %s" % text)
    return lines


def send_if_needed(zpaq_bin: str, cfg=None, tasks_dir: Optional[str] = None,
                   force: bool = False) -> tuple:
    pass





    try:
        cfg = cfg or config_mod.load()
        if not getattr(cfg, "mail_heartbeat_enabled", False):
            return 0, ""
        mail = mail_report.from_settings(cfg)
        if not mail.ready():
            return 0, ""
        if not should_send(force):
            return 0, ""
        lines = build_report(tasks_dir or cfg.tasks_dir)
        if not lines and not force:
            return 0, ""
        if not lines:
            lines = ["- %s" % notify.tr("mail.heartbeat_none")]

        subject = notify.tr(
            "mail.heartbeat_subject", count=len(lines)
        )
        header = [
            notify.tr("mail.heartbeat_header",
                      now=datetime.now().strftime("%d.%m.%Y %H:%M")),
            "",
        ]
        rc, out = mail_report.send_log_email(
            zpaq_bin, mail, subject, "\n".join(header + lines),
            getattr(cfg, "mail_customer", ""),
        )
        if rc == 0 and not mail_report.mail_not_sent(out):
            mark_sent()
        return int(rc), str(out or "")
    except Exception as exc:
        return 1, "%s: %s" % (type(exc).__name__, exc)
