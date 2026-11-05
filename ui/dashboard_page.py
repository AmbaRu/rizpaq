from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.archive_index import load_entries
from core import dashboard_alerts
from core.par2_ops import par2_main_name
from core.run_history import RunEntry, load_history
from core.tasks import (
    _archive_size,
    container_path,
    iter_jobs,
    load_container,
)

from ui import skins
from ui.dashboard_charts import (
    Par2Gauge,
    RunTrend,
    StatusDonut,
    segment_color,
)
from ui.dashboard_feed import RunFeed
from ui.i18n import tr


_STATUS_COLOR_TOKEN = {
    "ok": "OK_GREEN",
    "error": "DIFF_REMOVED",
    "busy": "BUSY_STEEL",
    "never": "TEXT_MUTED",
}


_TILE_SPECS = (
    ("all", "ACCENT", "dashboard.tile.all"),
    ("ok", "OK_GREEN", "dashboard.tile.ok"),
    ("error", "DIFF_REMOVED", "dashboard.tile.error"),
    ("busy", "BUSY_STEEL", "dashboard.tile.busy"),
    ("never", "TEXT_MUTED", "dashboard.tile.never"),
    ("nopar2", "WARN_ORANGE", "dashboard.tile.nopar2"),
    ("issues", "WARN_ORANGE", "dashboard.tile.issues"),
)


_DONUT_FILTER = {"ok": "ok", "error": "error", "busy": "busy",
                 "never": "never"}


def _status_color(token: Optional[str]) -> QColor:

    name = _STATUS_COLOR_TOKEN.get(token or "never", "TEXT_MUTED")
    return QColor(skins.color(name))


def _reason_text(reason: Optional[str]) -> str:

    if not reason:
        return ""
    return tr(f"backup.reason.{reason}")


def _status_display(status: Optional[str], reason: Optional[str]) -> str:

    text = tr(f"dashboard.status.{status}" if status else "dashboard.status.never")
    if status == "error" and reason:
        text = f"{text} — {_reason_text(reason)}"
    return text


def _job_type_key(row: "_Row") -> str:
    if row.action == "par2" or (
            row.action == "test" and row.test_mode == "par2"):
        return "dashboard.type.par2"
    if row.action == "test":
        return "dashboard.type.test"
    return "dashboard.type.backup"


def _format_size(size: Optional[int]) -> str:
    if size is None:
        return "—"
    if size < 1024:
        return f"{size} Б"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} КБ"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} МБ"
    return f"{size / (1024 * 1024 * 1024):.1f} ГБ"


def _parse_par2_date(text: str) -> str:
    try:
        return datetime.strptime(
            str(text or "").strip(), "%Y-%m-%d %H:%M:%S"
        ).strftime("%d.%m.%Y")
    except ValueError:
        return ""


class _Row:


    __slots__ = (
        "work_id", "job_id", "work_title", "job_title", "action",
        "test_mode", "archive_path", "archive_size", "archive_files",
        "last_run", "last_status", "last_reason", "run_count",
        "par2_enabled", "has_set",

        "password", "par2_created", "par2_outdated",
        "logical_size", "versions",
    )

    def __init__(self):
        self.work_id = ""
        self.job_id = ""
        self.work_title = ""
        self.job_title = ""
        self.action = ""
        self.test_mode = ""
        self.archive_path = ""
        self.archive_size: Optional[int] = None
        self.archive_files: Optional[int] = None
        self.last_run = ""
        self.last_status: Optional[str] = None
        self.last_reason: Optional[str] = None
        self.run_count = 0
        self.par2_enabled = False
        self.has_set: Optional[bool] = None
        self.password = False
        self.par2_created = ""
        self.par2_outdated = False
        self.logical_size: Optional[int] = None
        self.versions: Optional[int] = None


class DashboardPage(QWidget):

    def __init__(self, host=None, parent=None):
        super().__init__(parent)


        self._host = host
        self._rows: list[_Row] = []
        self._history: list[RunEntry] = []
        self._tiles: dict = {}
        self._tile_values: dict = {}


        self._alerts: list = []
        self._alert_works: set = set()
        self._streaks: dict = {}


        self._title_lbl: Optional[QLabel] = None
        self._tile_captions: dict = {}
        self._card_caps: dict = {}
        self._donut_legend: list = []
        self._trend_legend: list = []
        self._build_ui()


    def refresh(self):

        self._load_data()

    def retranslate(self):
        if self._title_lbl is not None:
            self._title_lbl.setText(tr("dashboard.title"))
        self._btn_refresh.setText(tr("dashboard.btn.refresh"))

        for kind, _color, caption_key in _TILE_SPECS:
            lbl = self._tile_captions.get(kind)
            if lbl is not None:
                lbl.setText(tr(caption_key))

        for key, lbl in self._card_caps.items():
            lbl.setText(tr(key))

        for lbl, key in self._donut_legend + self._trend_legend:
            lbl.setText(tr(key))

        self._table.setHorizontalHeaderLabels([
            tr("dashboard.col.job"),
            tr("dashboard.col.last_run"),
            tr("dashboard.col.status"),
        ])
        self._btn_open.setText(tr("dashboard.btn.open_archive"))
        self._btn_check_all.setText(tr("dashboard.btn.check_all"))


        try:
            self._update_stats()
            self._update_alerts()
            self._update_feed()
        except Exception:
            pass

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)


        head = QHBoxLayout()
        title = QLabel(tr("dashboard.title"))
        self._title_lbl = title
        tf = title.font()
        tf.setPointSize(max(tf.pointSize(), 9) + 6)
        tf.setBold(True)
        title.setFont(tf)
        head.addWidget(title)
        head.addStretch()

        self._btn_refresh = QPushButton(tr("dashboard.btn.refresh"))
        self._btn_refresh.clicked.connect(self._load_data)
        head.addWidget(self._btn_refresh)
        root.addLayout(head)


        root.addLayout(self._build_tiles_row())


        charts = QHBoxLayout()
        charts.setSpacing(8)
        charts.addWidget(self._make_card(
            tr("dashboard.card.status"), self._build_donut_card(), 3,
            cap_key="dashboard.card.status"))
        charts.addWidget(self._make_card(
            tr("dashboard.card.par2"), self._build_gauge_card(), 2,
            cap_key="dashboard.card.par2"))
        charts.addWidget(self._make_card(
            tr("dashboard.card.trend"), self._build_trend_card(), 4,
            cap_key="dashboard.card.trend"))
        root.addLayout(charts)


        root.addWidget(self._build_alerts_card())


        body = QHBoxLayout()
        body.setSpacing(8)
        body.addWidget(self._build_table(), stretch=3)

        feed_card = self._make_card(tr("dashboard.feed.title"),
                                    self._build_feed(), 0)
        feed_card.setMinimumWidth(300)
        feed_card.setMaximumWidth(360)
        body.addWidget(feed_card)
        root.addLayout(body, stretch=1)


        root.addLayout(self._build_footer())


    def _build_tiles_row(self) -> QHBoxLayout:

        row = QHBoxLayout()
        row.setSpacing(8)
        self._tile_group = QButtonGroup(self)
        self._tile_group.setExclusive(True)
        for kind, color_token, caption_key in _TILE_SPECS:
            tile = self._make_tile(kind, color_token, tr(caption_key))
            self._tile_group.addButton(tile)
            row.addWidget(tile, stretch=1)
        self._tiles["all"].setChecked(True)
        return row

    def _make_tile(self, kind: str, color_token: str, caption: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("dashTile")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(56)

        lay = QVBoxLayout(btn)
        lay.setContentsMargins(12, 4, 12, 4)
        lay.setSpacing(0)

        value = QLabel("0")
        value.setObjectName("dashTileValue")
        value.setAlignment(Qt.AlignCenter)
        caption_lbl = QLabel(caption)
        caption_lbl.setObjectName("dashTileCaption")
        caption_lbl.setAlignment(Qt.AlignCenter)
        caption_lbl.setWordWrap(True)
        lay.addWidget(value)
        lay.addWidget(caption_lbl)
        self._tile_captions[kind] = caption_lbl

        btn.clicked.connect(lambda _checked=False, k=kind: self._set_filter(k))
        self._tiles[kind] = btn
        self._tile_values[kind] = value
        self._style_tile(btn, color_token)
        return btn

    def _style_tile(self, btn: QPushButton, color_token: str):
        accent_line = skins.color(color_token)
        qss = f"""
        QPushButton#dashTile {{
            background: {skins.color('BASE_BG')};
            border: 1px solid {skins.color('BORDER_SOFT')};
            border-left: 4px solid {accent_line};
            border-radius: 8px;
        }}
        QPushButton#dashTile:hover {{
            background: {skins.color('ROW_HOVER')};
            border: 1px solid {skins.color('BORDER')};
            border-left: 4px solid {accent_line};
        }}
        QPushButton#dashTile:checked {{
            background: {skins.color('ROW_HOVER')};
            border: 2px solid {skins.color('ACCENT')};
            border-left: 4px solid {accent_line};
        }}
        QLabel#dashTileValue {{
            color: {accent_line};
            font-size: 18px;
            font-weight: bold;
        }}
        QLabel#dashTileCaption {{
            color: {skins.color('TEXT_MUTED')};
        }}
        """
        btn.setStyleSheet(qss)


    def _make_card(self, title: str, inner: QWidget, stretch: int = 0,
                   cap_key: str = None) -> QFrame:
        card = QFrame()
        card.setObjectName("dashCard")
        card.setStyleSheet(f"""
            QFrame#dashCard {{
                background: {skins.color('BASE_BG')};
                border: 1px solid {skins.color('BORDER_SOFT')};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(6)

        cap = QLabel(title)
        if cap_key:
            self._card_caps[cap_key] = cap
        f = cap.font()
        f.setBold(True)
        cap.setFont(f)
        cap.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
        lay.addWidget(cap)
        lay.addWidget(inner, stretch=stretch or 1)
        return card

    def _build_donut_card(self) -> QWidget:

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._donut = StatusDonut()
        self._donut.segmentClicked.connect(self._on_donut_segment)
        lay.addWidget(self._donut, stretch=1)

        legend = QHBoxLayout()
        legend.setSpacing(10)
        for key in ("ok", "error", "busy", "never"):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {segment_color(key).name()};")
            lbl = QLabel(tr(f"dashboard.status.{key}"))
            lbl.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
            legend.addWidget(dot)
            legend.addWidget(lbl)
            legend.addStretch()
            self._donut_legend.append((lbl, f"dashboard.status.{key}"))
        lay.addLayout(legend)
        return page

    def _build_gauge_card(self) -> QWidget:

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._gauge = Par2Gauge()
        lay.addWidget(self._gauge, stretch=1)

        self._lbl_gauge = QLabel()
        self._lbl_gauge.setAlignment(Qt.AlignCenter)
        self._lbl_gauge.setStyleSheet(
            f"color: {skins.color('TEXT_MUTED')};")
        lay.addWidget(self._lbl_gauge)

        self._lbl_par2 = QLabel()
        self._lbl_files = QLabel()
        self._lbl_volume = QLabel()


        self._lbl_free = QLabel()
        for lbl in (self._lbl_par2, self._lbl_files, self._lbl_volume,
                    self._lbl_free):
            lbl.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
            lay.addWidget(lbl)
        return page

    def _build_trend_card(self) -> QWidget:

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._trend = RunTrend()
        lay.addWidget(self._trend, stretch=1)

        legend = QHBoxLayout()
        legend.setSpacing(6)
        for key, key_caption in (
            ("ok", "dashboard.legend.ok"),
            ("error", "dashboard.legend.error"),
        ):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {segment_color(key).name()};")
            lbl = QLabel(tr(key_caption))
            lbl.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
            legend.addWidget(dot)
            legend.addWidget(lbl)
            self._trend_legend.append((lbl, key_caption))
        legend.addStretch()
        lay.addLayout(legend)
        return page


    def _build_alerts_card(self) -> QFrame:
        card_inner = QWidget()
        card = self._make_card(tr("dashboard.card.alerts"), card_inner,
                               cap_key="dashboard.card.alerts")
        self._alerts_lay = QVBoxLayout(card_inner)
        self._alerts_lay.setContentsMargins(0, 0, 0, 0)
        self._alerts_lay.setSpacing(2)
        return card

    def _update_alerts(self):

        while self._alerts_lay.count():
            item = self._alerts_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not self._alerts:
            ok = QLabel("●  " + tr("dashboard.alerts.all_ok"))
            ok.setStyleSheet(f"color: {skins.color('OK_GREEN')};")
            self._alerts_lay.addWidget(ok)
            return

        shown = self._alerts[:6]
        for alert in shown:
            btn = QPushButton(tr(alert.text_key, **alert.params))
            btn.setObjectName("dashAlert")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton#dashAlert {{
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding: 1px 4px;
                    color: {skins.color('TEXT_MAIN')};
                }}
                QPushButton#dashAlert:hover {{
                    color: {skins.color('ACCENT')};
                }}
            """)
            btn.clicked.connect(
                lambda _checked=False, a=alert: self._goto_alert(a))
            self._alerts_lay.addWidget(btn)

        extra = len(self._alerts) - len(shown)
        if extra > 0:
            more = QLabel(tr("dashboard.alerts.more", n=extra))
            more.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
            self._alerts_lay.addWidget(more)

    def _goto_alert(self, alert):

        work_id = alert.work_id
        job_id = alert.job_id
        if not job_id:


            for row in self._rows:
                if row.work_id == work_id:
                    job_id = row.job_id
                    break
        if work_id:
            self._navigate_row(work_id, job_id)

    def _build_feed(self) -> QWidget:

        self._feed = RunFeed()
        self._feed.jobActivated.connect(self._navigate_row)
        return self._feed


    def _build_table(self) -> QTableWidget:


        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels([
            tr("dashboard.col.job"),
            tr("dashboard.col.last_run"),
            tr("dashboard.col.status"),
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().hide()


        self._table.setSortingEnabled(False)
        self._table.doubleClicked.connect(self._on_row_double_clicked)

        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        return self._table

    def _build_footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        self._btn_open = QPushButton(tr("dashboard.btn.open_archive"))
        self._btn_open.clicked.connect(self._on_open_archive)
        self._btn_check_all = QPushButton(tr("dashboard.btn.check_all"))
        self._btn_check_all.clicked.connect(self._on_check_all)
        footer.addWidget(self._btn_open)
        footer.addStretch()
        footer.addWidget(self._btn_check_all)
        return footer


    def _load_data(self):

        self._rows = []
        self._alerts = []
        self._alert_works = set()
        self._streaks = {}

        host = self._host
        tasks_dir = None
        if host is not None:
            getter = getattr(host, "_tasks_dir", None)
            if callable(getter):
                try:
                    tasks_dir = getter()
                except Exception:
                    tasks_dir = None

        container = None
        if tasks_dir:
            container = load_container(container_path(tasks_dir))


            try:
                self._history = load_history(tasks_dir)
            except Exception:
                self._history = []


        index_cache: dict = {}
        if container is not None:
            seen_dests = set()
            for work, _job in iter_jobs(container):
                dest = str(work.get("dest") or "")
                if not dest or dest in seen_dests:
                    continue
                seen_dests.add(dest)
                summary = {"files": None, "logical": None,
                           "versions": None}
                try:
                    entries = load_entries(dest)
                except Exception:
                    entries = None
                if entries:
                    latest = max(
                        (e.version for e in entries
                         if getattr(e, "version", None) is not None),
                        default=None,
                    )
                    if latest is not None:


                        rows = [e for e in entries if e.version == latest]
                        files = [e for e in rows if not e.is_dir]
                        summary["files"] = len(files)
                        summary["logical"] = sum(e.size for e in files)
                        summary["versions"] = len({
                            e.version for e in entries
                            if e.version is not None})
                    else:

                        files = [e for e in entries if not e.is_dir]
                        summary["files"] = len(files)
                        summary["logical"] = sum(e.size for e in files)
                index_cache[dest] = summary

            for work, job in iter_jobs(container):
                dest = str(work.get("dest") or "")
                self._rows.append(self._build_row(
                    work, job, index_cache.get(dest) or {}))


            try:
                self._alerts = dashboard_alerts.collect_alerts(
                    container, self._history)
            except Exception:
                self._alerts = []
            self._alert_works = {a.work_id for a in self._alerts}
            try:
                self._streaks = dashboard_alerts.job_streaks(self._history)
            except Exception:
                self._streaks = {}

        self._refresh_table()
        self._update_stats()
        self._update_button_states()
        self._update_feed()
        self._update_alerts()

    def _build_row(self, work: dict, job: dict, idx: dict = None) -> _Row:
        idx = idx or {}
        row = _Row()
        row.work_id = str(work.get("id", ""))
        row.job_id = str(job.get("id", ""))
        row.work_title = str(work.get("title") or "")
        row.job_title = str(job.get("title") or "")
        row.action = str(job.get("action") or "backup")
        row.test_mode = str(job.get("test_mode") or "")
        row.archive_path = str(work.get("dest") or "")
        row.archive_size = _archive_size(row.archive_path)


        row.archive_files = idx.get("files")
        row.logical_size = idx.get("logical")
        row.versions = idx.get("versions")

        if row.archive_path:
            row.has_set = Path(par2_main_name(row.archive_path)).is_file()


        row.password = bool(work.get("password_b64"))
        row.par2_created = str(work.get("par2_created") or "")
        row.par2_outdated = row.has_set and dashboard_alerts.is_set_outdated(
            work.get("par2_size"), row.archive_size)

        row.last_run = str(job.get("last_run") or "")
        row.last_status = job.get("last_status")
        row.last_reason = job.get("last_reason")
        row.run_count = int(job.get("run_count") or 0)
        row.par2_enabled = bool(job.get("par2_enabled"))
        return row

    def _refresh_table(self):
        self._table.setRowCount(0)

        for work_id, rows, par2_on, par2_ok in self._grouped_visible_rows():
            first = rows[0]
            r = self._table.rowCount()
            self._table.insertRow(r)


            header_item = self._item(
                self._work_header_text(first, par2_on, par2_ok))
            header_bg = QColor(skins.color("ROW_HOVER"))
            header_fg = QColor(skins.color("TEXT_MAIN"))


            hfont = header_item.font()
            hfont.setBold(True)
            header_item.setFont(hfont)
            header_item.setBackground(header_bg)
            header_item.setForeground(header_fg)
            header_payload = {
                "work_id": work_id,
                "archive_path": first.archive_path,
            }
            header_item.setData(Qt.UserRole + 100, header_payload)
            self._table.setItem(r, 0, header_item)
            for col in (1, 2):
                filler = self._item("")
                filler.setBackground(header_bg)
                self._table.setItem(r, col, filler)

            self._table.setSpan(r, 0, 1, self._table.columnCount())


            for row in rows:
                r = self._table.rowCount()
                self._table.insertRow(r)


                self._table.setItem(
                    r, 0,
                    self._item(
                        f"{tr(_job_type_key(row))} · {row.job_title}")
                )
                self._table.setItem(
                    r, 1, self._item(row.last_run or tr("dashboard.never"))
                )
                status_text = _status_display(row.last_status, row.last_reason)
                streak = self._streaks.get(row.job_id)
                if streak and streak[1] >= 2:
                    status_text += " · " + tr(
                        "dashboard.streak.runs", n=streak[1])
                status_item = self._item(status_text)
                status_item.setForeground(_status_color(row.last_status))


                bold = status_item.font()
                bold.setBold(True)
                status_item.setFont(bold)
                self._table.setItem(r, 2, status_item)


                payload = {
                    "work_id": row.work_id,
                    "job_id": row.job_id,
                    "archive_path": row.archive_path,
                }
                for col in range(self._table.columnCount()):
                    item = self._table.item(r, col)
                    if item is not None:
                        item.setData(Qt.UserRole + 100, payload)

    def _grouped_visible_rows(self):
        all_by_work: dict = {}
        all_order: list = []
        for row in self._rows:
            if row.work_id not in all_by_work:
                all_by_work[row.work_id] = []
                all_order.append(row.work_id)
            all_by_work[row.work_id].append(row)

        visible_order: list = []
        visible_by_work: dict = {}
        for row in self._filtered_rows():
            if row.work_id not in visible_by_work:
                visible_by_work[row.work_id] = []
                visible_order.append(row.work_id)
            visible_by_work[row.work_id].append(row)

        groups = []
        for wid in visible_order:
            rows = visible_by_work[wid]
            all_rows = all_by_work.get(wid) or rows
            par2_on = any(r.par2_enabled for r in all_rows)
            par2_ok = par2_on and any(
                r.par2_enabled and r.has_set for r in all_rows)
            groups.append((wid, rows, par2_on, par2_ok))
        return groups

    def _work_header_text(self, row: _Row, par2_on: bool,
                          par2_ok: bool) -> str:
        parts = [row.work_title]
        if row.archive_path:
            parts.append(row.archive_path)
        size = _format_size(row.archive_size)
        if size != "—":
            parts.append(size)
        if row.archive_files is not None:
            parts.append(
                f"{tr('dashboard.stats.files')}: "
                f"{row.archive_files:,}".replace(",", " ")
            )
        if row.versions and row.versions > 1:
            parts.append(tr("dashboard.header.versions", n=row.versions))
        if row.logical_size and row.archive_size:
            ratio = row.logical_size / row.archive_size
            if ratio >= 1.05:
                parts.append(tr(
                    "dashboard.header.ratio", ratio=f"{ratio:.1f}"))
        if par2_on:
            if not par2_ok:
                parts.append(tr("dashboard.group.par2_missing"))
            else:
                label = tr("dashboard.group.par2_set")
                set_date = _parse_par2_date(row.par2_created)
                if set_date:
                    label += " " + tr(
                        "dashboard.header.set_from", date=set_date)
                if row.par2_outdated:
                    label += " ⚠ " + tr("dashboard.header.set_outdated")
                parts.append(label)
        else:


            parts.append(tr("dashboard.group.par2_off"))
        if row.password:
            parts.append("🔒")
        return "  ·  ".join(p for p in parts if p)


    def _filtered_rows(self):

        active = self._active_filter()
        if active == "ok":
            return [r for r in self._rows if r.last_status == "ok"]
        if active == "error":
            return [r for r in self._rows if r.last_status == "error"]
        if active == "busy":
            return [r for r in self._rows if r.last_status == "busy"]
        if active == "never":
            return [r for r in self._rows
                    if r.last_status not in ("ok", "error", "busy")]
        if active == "nopar2":
            return [r for r in self._rows if r.par2_enabled and not r.has_set]
        if active == "issues":

            return [r for r in self._rows
                    if r.work_id in self._alert_works]
        return list(self._rows)

    def _active_filter(self) -> str:
        btn = self._tile_group.checkedButton()
        for kind, tile in self._tiles.items():
            if tile is btn:
                return kind
        return "all"

    def _set_filter(self, name: str):

        tile = self._tiles.get(name)
        if tile is not None:
            tile.setChecked(True)
        self._refresh_table()

    def _on_donut_segment(self, key: str):

        self._set_filter(_DONUT_FILTER.get(key, "all"))


    def _update_stats(self):

        counts = {
            "all": len(self._rows),
            "ok": 0, "error": 0, "busy": 0, "never": 0, "nopar2": 0,
            "issues": 0,
        }
        par2_total = 0
        par2_covered = 0


        backup_total = 0
        backup_covered = 0
        files_total = 0
        volume = 0
        seen_works = set()

        for r in self._rows:
            status = r.last_status if r.last_status in (
                "ok", "error", "busy") else "never"
            counts[status] += 1
            if r.par2_enabled:
                par2_total += 1
                if r.has_set:
                    par2_covered += 1
                else:
                    counts["nopar2"] += 1


            if r.action == "backup":
                backup_total += 1
                if r.has_set:
                    backup_covered += 1
            if r.archive_files:
                files_total += r.archive_files
            if r.work_id not in seen_works:
                seen_works.add(r.work_id)
                if r.archive_size:
                    volume += r.archive_size

        for kind, value_lbl in self._tile_values.items():
            if kind == "issues":


                value_lbl.setText(f"{len(self._alert_works):,}".replace(",", " "))
                continue
            value_lbl.setText(f"{counts[kind]:,}".replace(",", " "))


        self._donut.set_counts({
            "ok": counts["ok"],
            "error": counts["error"],
            "busy": counts["busy"],
            "never": counts["never"],
        })


        self._gauge.set_value(backup_covered, backup_total)
        if backup_total:
            self._lbl_gauge.setText(tr(
                "dashboard.gauge.covered",
                covered=backup_covered, total=backup_total))
        else:
            self._lbl_gauge.setText(tr("dashboard.gauge.empty"))


        self._lbl_par2.setText(f"{tr('dashboard.stats.par2')}: {par2_total}")
        self._lbl_files.setText(
            f"{tr('dashboard.stats.files')}: {files_total:,}".replace(",", " ")
        )
        self._lbl_volume.setText(
            f"{tr('dashboard.stats.volume')}: {_format_size(volume)}"
        )


        dests = sorted({r.archive_path for r in self._rows if r.archive_path})
        frees = []
        for dest in dests:
            free = dashboard_alerts.free_bytes(dest)
            if free is not None:
                frees.append(free)
        if frees:
            self._lbl_free.setText(tr(
                "dashboard.gauge.free", free=_format_size(min(frees))))
        else:
            self._lbl_free.setText("")


        self._trend.set_series(self._trend_series())

    def _trend_series(self) -> list:
        today = datetime.now().date()
        buckets: dict = {}
        for e in self._history:
            if e.ts_dt is None:
                continue
            day = e.ts_dt.date()
            if (today - day).days > 29 or (today - day).days < 0:
                continue
            ok_n, err_n = buckets.get(day, (0, 0))
            if e.status == "error":
                err_n += 1
            else:


                if e.status == "ok":
                    ok_n += 1
            buckets[day] = (ok_n, err_n)

        series = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            ok_n, err_n = buckets.get(day, (0, 0))
            series.append((day.strftime("%d.%m"), ok_n, err_n))
        return series

    def _update_feed(self):


        self._feed.set_entries(self._history)

    def _update_button_states(self):

        has_rows = len(self._rows) > 0
        self._btn_open.setEnabled(has_rows)
        self._btn_check_all.setEnabled(has_rows)


    def _selected_row(self) -> Optional[_Row]:
        sel = self._table.selectionModel().selectedRows()
        if not sel:
            return None
        payload = sel[0].data(Qt.UserRole + 100)
        if not isinstance(payload, dict):
            return None
        for row in self._rows:
            if (row.work_id == payload.get("work_id")
                    and row.job_id == payload.get("job_id")):
                return row
        return None

    def _navigate_row(self, work_id: str, job_id: str):

        row = next(
            (r for r in self._rows
             if r.work_id == work_id and r.job_id == job_id),
            None,
        )
        if row is None:
            return
        host = self._host
        if host is None:
            return
        page = getattr(host, "backup_page", None)
        if page is not None:
            reveal = getattr(page, "reveal_job", None)
            if callable(reveal):
                try:
                    reveal(row.work_id, row.job_id)
                    return
                except Exception:
                    pass
        enter = getattr(host, "_enter_archive", None)
        if callable(enter) and row.archive_path:
            try:
                enter(row.archive_path)
            except Exception:
                pass

    def _on_row_double_clicked(self, index):
        payload = index.data(Qt.UserRole + 100)
        if isinstance(payload, dict):
            if payload.get("job_id"):
                self._navigate_row(
                    payload.get("work_id") or "",
                    payload.get("job_id") or "")
                return
            archive_path = payload.get("archive_path")
            if archive_path:
                self._enter_archive(archive_path)
            return

        row = self._selected_row()
        if row is None:
            return
        self._navigate_row(row.work_id, row.job_id)

    def _enter_archive(self, path: str):

        host = self._host
        if host is None or not path:
            return
        enter = getattr(host, "_enter_archive", None)
        if callable(enter):
            try:
                enter(path)
            except Exception as exc:
                QMessageBox.warning(
                    self, tr("dashboard.error_title"),
                    tr("dashboard.error_open", error=str(exc)),
                )

    def _on_open_archive(self):

        row = self._selected_row()
        if row is None or not row.archive_path:
            return
        self._enter_archive(row.archive_path)

    def _on_check_all(self):

        rows = self._rows if not self._table.selectionModel().selectedRows() \
            else [r for r in self._rows if r in self._selected_rows()]


        host = self._host
        if host is None:
            return
        par2_jobs = [r for r in rows if r.par2_enabled and r.archive_path]
        if not par2_jobs:
            QMessageBox.information(
                self, tr("dashboard.check_title"),
                tr("dashboard.check_no_par2"),
            )
            return
        confirm = QMessageBox.question(
            self, tr("dashboard.check_title"),
            tr("dashboard.check_confirm", count=len(par2_jobs)),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return


        started = 0
        for row in par2_jobs:
            try:
                ok = host._start_par2_verify(row.archive_path)
                if ok:
                    started += 1
            except Exception:
                continue
        if started:
            try:
                host.statusBar().showMessage(
                    tr("dashboard.check_started", count=started), 5000
                )
            except Exception:
                pass
        self._load_data()

    def _selected_rows(self):

        sel = self._table.selectionModel().selectedRows()
        out = []
        for index in sel:
            payload = index.data(Qt.UserRole + 100)
            if isinstance(payload, dict):
                for row in self._rows:
                    if (row.work_id == payload.get("work_id")
                            and row.job_id == payload.get("job_id")):
                        out.append(row)
                        break
        return out


    @staticmethod
    def _item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
