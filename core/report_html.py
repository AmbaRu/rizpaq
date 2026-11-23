






from __future__ import annotations

import html
from typing import Optional

_DEFAULT_LABELS = {
    "alerts": "Needs attention",
    "archives": "Archives",
    "runs": "Recent runs",
    "trend": "Run trend (30 days)",
    "size": "Archive size (30 days)",
    "work": "Work",
    "job": "Job",
    "archive": "Archive",
    "size_col": "Size",
    "files": "Files",
    "versions": "Versions",
    "status": "Status",
    "date": "Date",
    "rc": "Code",
    "none": "No data",
}

_CSS = """
body{font-family:Segoe UI,Arial,sans-serif;margin:28px;color:#222}
h1{font-size:22px;margin:0 0 4px} h2{font-size:16px;margin:22px 0 8px}
.meta{color:#777;font-size:12px;margin-bottom:16px}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border:1px solid #ddd;padding:5px 7px;text-align:left}
th{background:#f3f5f7}
.ok{color:#1a7f37}.error{color:#c0392b}.busy{color:#a66}
.empty{color:#777;font-style:italic}
"""

                                                                            
_STATUS_CLASS = {"ok": "ok", "error": "error", "busy": "busy"}


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _human_size(value: Optional[int]) -> str:
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    for unit, mult in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if n >= mult:
            return "%.1f %s" % (n / mult, unit)
    return "%d B" % int(n)


def _table(headers, rows) -> str:
    if not rows:
        return '<p class="empty">%s</p>' % _esc("—")
    out = ["<table><thead><tr>"]
    out.extend("<th>%s</th>" % _esc(h) for h in headers)
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        for cell in row:
            if isinstance(cell, tuple):
                text, cls = cell
                out.append('<td class="%s">%s</td>' % (
                    _esc(cls), _esc(text)))
            else:
                out.append("<td>%s</td>" % _esc(cell))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def render_dashboard_html(payload: dict) -> str:
    pass
    payload = payload or {}
    labels = dict(_DEFAULT_LABELS)
    labels.update(payload.get("labels") or {})

    summary = payload.get("summary") or {}
    parts = [
        "<!DOCTYPE html>",
        '<html lang="%s"><head><meta charset="utf-8">' % (
            _esc(str(payload.get("lang") or "ru")[:20]),
        ),
        "<title>%s</title><style>%s</style></head><body>" % (
            _esc(payload.get("title") or "Rizpaq"), _CSS,
        ),
        "<h1>%s</h1>" % _esc(payload.get("title") or "Rizpaq"),
        '<div class="meta">%s</div>' % _esc(payload.get("generated") or ""),
    ]

    if summary:
        parts.append("<p>%s: %s · %s: %s · %s: %s · %s: %s</p>" % (
            _esc(labels.get("work", "Work")), _esc(summary.get("works", 0)),
            _esc(labels.get("job", "Job")), _esc(summary.get("jobs", 0)),
            _esc(labels.get("status", "Status")),
            "%s OK / %s ERROR" % (
                _esc(summary.get("ok", 0)), _esc(summary.get("error", 0))),
            _esc(labels.get("archive", "Archive")),
            _esc(summary.get("archives", 0)),
        ))

    parts.append("<h2>%s</h2>" % _esc(labels["alerts"]))
    alerts = payload.get("alerts") or []
    if alerts:
        parts.append("<ul>" + "".join("<li>%s</li>" % _esc(a) for a in alerts)
                     + "</ul>")
    else:
        parts.append('<p class="empty">%s</p>' % _esc(labels["none"]))

    archive_rows = []
    for item in payload.get("archives") or []:
        status = str(item.get("status") or "")
        archive_rows.append([
            item.get("work", ""), item.get("job", ""),
            item.get("archive", ""), _human_size(item.get("size")),
            item.get("files", ""), item.get("versions", ""),
            (status, _STATUS_CLASS.get(status, "")),
            item.get("reason", ""),
        ])
    parts.append("<h2>%s</h2>" % _esc(labels["archives"]))
    parts.append(_table([
        labels["work"], labels["job"], labels["archive"], labels["size_col"],
        labels["files"], labels["versions"], labels["status"], " ",
    ], archive_rows))

    run_rows = []
    for item in payload.get("runs") or []:
        status = str(item.get("status") or "")
        run_rows.append([
            item.get("date", ""), item.get("work", ""), item.get("job", ""),
            (status, _STATUS_CLASS.get(status, "")), item.get("rc", ""),
        ])
    parts.append("<h2>%s</h2>" % _esc(labels["runs"]))
    parts.append(_table([
        labels["date"], labels["work"], labels["job"],
        labels["status"], labels["rc"],
    ], run_rows))

    parts.append("<h2>%s</h2>" % _esc(labels["trend"]))
    parts.append(_table([
        labels["date"], "OK", "ERROR",
    ], [list(r) for r in (payload.get("trend") or [])]))

    parts.append("<h2>%s</h2>" % _esc(labels["size"]))
    parts.append(_table([
        labels["date"], labels["size_col"],
    ], [[label, _human_size(size)] for label, size in
        (payload.get("size") or [])]))

    parts.append("</body></html>")
    return "\n".join(parts)
