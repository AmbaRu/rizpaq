from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
    QRadioButton, QScrollArea, QSpinBox, QTabWidget, QVBoxLayout,
    QWidget,
)

from ui.i18n import tr
from ui.par2_options import Par2OptionsWidget
from ui.qt_compat import PASSWORD_ECHO

LEVEL_ARGS = {"m0": ["-m0"], "m1": ["-m1"], "m2": ["-m2"], "m3": ["-m3"], "m4": ["-m4"], "m5": ["-m5"]}
HASH_ARGS = {
    "crc32": "-crc32", "xxhash": "-xxhash", "sha1": "-sha1", "sha256": "-sha256",
    "xxh3": "-xxh3", "blake3": "-blake3", "sha3": "-sha3", "md5": "-md5",
    "windate": "-windate", "whirlpool": "-whirlpool", "xxhashb": "-xxhashb",
    "xxh3b": "-xxh3b", "sha1b": "-sha1b", "sha256b": "-sha256b", "sha3b": "-sha3b",
    "blake3b": "-blake3b", "md5b": "-md5b", "highway64": "-highway64",
    "highway128": "-highway128", "highway256": "-highway256",
}
_LIVE_WORKERS: set = set()
DATE_TEMPLATE = "%year-%month-%day"
_BLOCK_SIZES = [(0,"1 МиБ"),(1,"2 МиБ"),(2,"4 МиБ"),(3,"8 МиБ"),(4,"16 МиБ"),(5,"32 МиБ"),(6,"64 МиБ"),(7,"128 МиБ"),(8,"256 МиБ"),(9,"512 МиБ"),(10,"1024 МиБ"),(11,"2048 МиБ")]
_PREPROCESS = [(0,"Нет"),(1,"Packed LZ77"),(2,"Byte LZ77"),(3,"BWT"),(4,"Нет + E8E9"),(5,"Packed + E8E9"),(6,"Byte LZ77 + E8E9"),(7,"BWT + E8E9")]
_SEARCH_DEPTHS = [(16,"64K (быстро)"),(18,"256K"),(20,"1M (стандарт)"),(22,"4M"),(24,"16M (максимум)")]


def build_method_string(mode, block_b, preprocess_n2, search_depth_n5,
                        use_c, use_i, use_a, use_w, use_m, use_s, use_t):
    parts = [f"{mode}{block_b}"]
    n6 = block_b + 21
    parts.append(f"{preprocess_n2},6,0,{search_depth_n5},{n6},0")
    if use_c: parts.append("c0,0,0")
    if use_i: parts.append("i1,2,0,0")
    if use_a: parts.append("a24,0,0")
    if use_w: parts.append("w1,65,26,223,20,0")
    if use_m: parts.append("m8,24")
    if use_s: parts.append("s8,32,255")
    if use_t: parts.append("t8,24")
    return ",".join(parts)


def _split_masks(text: str) -> list:
    if not text:
        return []
    return [p.strip() for p in text.replace(",", ";").split(";") if p.strip()]


def _source_size(path: str) -> int:
    p = Path(path)
    try:
        if p.is_file():
            return p.stat().st_size
    except OSError:
        return 0
    total = 0
    stack = [p]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_dir():
                            stack.append(Path(e.path))
                        elif e.is_file():
                            total += e.stat().st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return total


def _auto_checksize(total: int) -> str:
    total = int(total)
    return _fmt_checksize(total + max(total // 20, 1 << 20))


def _fmt_checksize(n: int) -> str:
    for suf, mult in (("T", 1 << 40), ("G", 1 << 30), ("M", 1 << 20), ("K", 1 << 10)):
        v = (n + mult - 1) // mult
        if v >= 1 and v * mult <= n + n // 4:
            return f"{v}{suf}"
    return str(max(int(n), 1))


class _SizeWorker(QThread):
    size_ready = Signal(object)

    def __init__(self, sources):
        super().__init__(None)
        self._sources = list(sources)

    def run(self):
        self.size_ready.emit(sum(_source_size(s) for s in self._sources))


class ArchiveCreateDialog(QDialog):
    def __init__(
        self,
        sources,
        default_dest: str,
        parent=None,
        initial_settings=None,
        edit_work_id=None,
        edit_job_id=None,
        add_to_work_id=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("create.dialog_title"))
        self.setMinimumSize(560, 480)
        self.resize(620, 560)

        self._sources = [str(s) for s in sources]
        self._result = None
        self._source_total = 0
        self._auto_checkspace = ""
        self._user_cleared = False
        self._size_worker = None
        self._schedule = None


        self._already_saved = False


        self._edit_work_id = edit_work_id
        self._edit_job_id = edit_job_id


        self._add_to_work_id = add_to_work_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._tabs = QTabWidget()


        page_general = QWidget()
        cl = QVBoxLayout(page_general)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(8)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)


        self._work_title_edit = QLineEdit()
        self._work_title_edit.setPlaceholderText(tr("create.work_title_placeholder"))
        form.addRow(tr("create.work_title"), self._work_title_edit)

        self._job_title_edit = QLineEdit()
        self._job_title_edit.setPlaceholderText(tr("create.job_title_placeholder"))
        form.addRow(tr("create.job_title"), self._job_title_edit)


        self._source_list = QListWidget()
        self._source_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._source_list.setMinimumHeight(72)
        self._source_list.setMaximumHeight(140)
        for s in self._sources:
            self._source_list.addItem(s)
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
        self._dest_edit = QLineEdit(default_dest)
        br_btn = QPushButton("…")
        br_btn.setFixedWidth(32)
        br_btn.clicked.connect(self._browse_dest)
        dt_btn = QPushButton(tr("create.btn_insert_date"))
        dt_btn.clicked.connect(self._insert_date_template)
        dest_row.addWidget(self._dest_edit, 1)
        dest_row.addWidget(dt_btn)
        dest_row.addWidget(br_btn)
        form.addRow(tr("create.destination"), dest_row)

        self._note_label = QLabel("")
        self._note_label.setWordWrap(True)
        form.addRow("", self._note_label)
        date_hint = QLabel(tr("create.date_hint"))
        date_hint.setWordWrap(True)
        form.addRow("", date_hint)
        self._comment_edit = QLineEdit()
        form.addRow(tr("create.comment"), self._comment_edit)

        pwd_row = QHBoxLayout()
        self._pwd_edit = QLineEdit()
        self._pwd_edit.setEchoMode(PASSWORD_ECHO)
        self._pwd_edit.setPlaceholderText(tr("create.password"))
        self._pwd2_edit = QLineEdit()
        self._pwd2_edit.setEchoMode(PASSWORD_ECHO)
        self._pwd2_edit.setPlaceholderText(tr("create.password_confirm"))
        pwd_row.addWidget(self._pwd_edit, 1)
        pwd_row.addWidget(self._pwd2_edit, 1)
        form.addRow(tr("create.password"), pwd_row)
        cl.addLayout(form)
        cl.addStretch(1)


        page_comp = QWidget()
        gl = QFormLayout(page_comp)
        gl.setContentsMargins(12, 12, 12, 12)
        gl.setSpacing(8)

        self._level_combo = QComboBox()
        for k, t in [("m0", "create.level_m0"), ("m1", "create.level_m1"),
                     ("m2", "create.level_m2"), ("m3", "create.level_m3"),
                     ("m4", "create.level_m4"), ("m5", "create.level_m5"),
                     ("method", "create.level_method")]:
            self._level_combo.addItem(tr(t), k)
        self._level_combo.setCurrentIndex(2)
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        gl.addRow(tr("create.level"), self._level_combo)

        self._hash_combo = QComboBox()
        self._hash_combo.addItem(tr("create.hash_default"), "")
        for key in ("xxhash", "xxh3", "sha256", "sha3", "blake3", "sha1",
                    "crc32", "md5", "windate", "whirlpool", "xxhashb",
                    "xxh3b", "sha1b", "sha256b", "sha3b", "blake3b", "md5b",
                    "highway64", "highway128", "highway256"):
            self._hash_combo.addItem(key, key)
        gl.addRow(tr("create.hash"), self._hash_combo)

        self._method_group = QGroupBox(tr("create.method_group"))
        ml = QFormLayout()
        ml.setContentsMargins(10, 10, 10, 10)
        ml.setSpacing(6)
        self._method_mode_combo = QComboBox()
        self._method_mode_combo.addItem(tr("create.method_mode_journal"), "x")
        self._method_mode_combo.addItem(tr("create.method_mode_stream"), "s")
        self._method_mode_combo.currentIndexChanged.connect(self._on_method_changed)
        ml.addRow(tr("create.method_mode"), self._method_mode_combo)
        self._method_block_combo = QComboBox()
        for v, l in _BLOCK_SIZES:
            self._method_block_combo.addItem(l, v)
        self._method_block_combo.setCurrentIndex(6)
        self._method_block_combo.currentIndexChanged.connect(self._on_method_changed)
        ml.addRow(tr("create.method_block"), self._method_block_combo)
        self._method_preproc_combo = QComboBox()
        for v, l in _PREPROCESS:
            self._method_preproc_combo.addItem(l, v)
        self._method_preproc_combo.setCurrentIndex(6)
        self._method_preproc_combo.currentIndexChanged.connect(self._on_method_changed)
        ml.addRow(tr("create.method_preproc"), self._method_preproc_combo)
        self._method_depth_combo = QComboBox()
        for v, l in _SEARCH_DEPTHS:
            self._method_depth_combo.addItem(l, v)
        self._method_depth_combo.setCurrentIndex(2)
        self._method_depth_combo.currentIndexChanged.connect(self._on_method_changed)
        ml.addRow(tr("create.method_depth"), self._method_depth_combo)

        mg = QGridLayout()
        mg.setContentsMargins(0, 4, 0, 4)
        mg.setHorizontalSpacing(12)
        mg.setVerticalSpacing(4)
        self._method_c_cb = QCheckBox(tr("create.method_model_c"))
        self._method_c_cb.setChecked(True)
        self._method_c_cb.toggled.connect(lambda _: self._on_method_changed())
        self._method_i_cb = QCheckBox(tr("create.method_model_i"))
        self._method_i_cb.setChecked(True)
        self._method_i_cb.toggled.connect(lambda _: self._on_method_changed())
        self._method_a_cb = QCheckBox(tr("create.method_model_a"))
        self._method_a_cb.setChecked(True)
        self._method_a_cb.toggled.connect(lambda _: self._on_method_changed())
        self._method_w_cb = QCheckBox(tr("create.method_model_w"))
        self._method_w_cb.setChecked(True)
        self._method_w_cb.toggled.connect(lambda _: self._on_method_changed())
        self._method_m_cb = QCheckBox(tr("create.method_model_m"))
        self._method_m_cb.setChecked(True)
        self._method_m_cb.toggled.connect(lambda _: self._on_method_changed())
        self._method_s_cb = QCheckBox(tr("create.method_model_s"))
        self._method_s_cb.setChecked(True)
        self._method_s_cb.toggled.connect(lambda _: self._on_method_changed())
        self._method_t_cb = QCheckBox(tr("create.method_model_t"))
        self._method_t_cb.setChecked(True)
        self._method_t_cb.toggled.connect(lambda _: self._on_method_changed())
        mg.addWidget(self._method_c_cb, 0, 0)
        mg.addWidget(self._method_i_cb, 0, 1)
        mg.addWidget(self._method_a_cb, 1, 0)
        mg.addWidget(self._method_w_cb, 1, 1)
        mg.addWidget(self._method_m_cb, 2, 0)
        mg.addWidget(self._method_s_cb, 2, 1)
        mg.addWidget(self._method_t_cb, 3, 0)
        ml.addRow(tr("create.method_models"), mg)
        self._method_preview = QLabel("")
        self._method_preview.setWordWrap(True)
        self._method_preview.setObjectName("methodPreview")
        ml.addRow(tr("create.method_preview"), self._method_preview)
        self._method_group.setLayout(ml)
        self._method_group.setVisible(False)
        gl.addRow(self._method_group)

        self._only_edit = QLineEdit()
        self._only_edit.setPlaceholderText("*.txt; *.doc")
        gl.addRow(tr("create.only"), self._only_edit)
        self._not_edit = QLineEdit()
        self._not_edit.setPlaceholderText("*.tmp; *.bak; Thumbs.db")
        gl.addRow(tr("create.not"), self._not_edit)
        vr = QHBoxLayout()
        vr.addWidget(QLabel(tr("create.verify_mode")))
        self._verify_combo = QComboBox()
        self._verify_combo.addItem(tr("create.verify_none"), "")
        self._verify_combo.addItem(tr("create.verify_test"), "full")
        self._verify_combo.addItem(tr("create.verify_verify"), "verify")
        self._verify_combo.addItem(tr("create.verify_paranoid"), "paranoid")
        vr.addWidget(self._verify_combo, 1)
        gl.addRow(vr)


        page_adv = QWidget()
        av = QVBoxLayout(page_adv)
        av.setContentsMargins(12, 12, 12, 12)
        av.setSpacing(8)
        self._opt_longpath = QCheckBox(tr("create.opt_longpath"))
        self._opt_longpath.setChecked(True)
        self._opt_date = QCheckBox(tr("create.opt_date"))
        self._opt_norecurse = QCheckBox(tr("create.opt_norecurse"))
        self._opt_forcewindows = QCheckBox(tr("create.opt_forcewindows"))
        self._opt_force_xls = QCheckBox(tr("create.opt_force_xls"))
        self._opt_nochecksum = QCheckBox(tr("create.opt_nochecksum"))
        self._opt_nodedup = QCheckBox(tr("create.opt_nodedup"))
        self._opt_vss = QCheckBox(tr("create.opt_vss"))
        self._opt_noonedrive = QCheckBox(tr("create.opt_noonedrive"))
        self._opt_ignore = QCheckBox(tr("create.opt_ignore"))
        self._opt_shutdown = QCheckBox(tr("create.opt_shutdown"))
        fg = QGridLayout()
        fg.setContentsMargins(0, 0, 0, 0)
        fg.setHorizontalSpacing(18)
        fg.setVerticalSpacing(6)
        for col, column in enumerate((
            (self._opt_longpath, self._opt_date, self._opt_norecurse,
             self._opt_forcewindows, self._opt_force_xls, self._opt_nochecksum),
            (self._opt_nodedup, self._opt_vss, self._opt_noonedrive,
             self._opt_ignore, self._opt_shutdown),
        )):
            for row, cb in enumerate(column):
                fg.addWidget(cb, row, col)
        av.addLayout(fg)

        al = QFormLayout()
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(8)
        cr = QHBoxLayout()
        self._opt_copy = QCheckBox(tr("create.opt_copy"))
        self._copy_edit = QLineEdit()
        self._copy_edit.textChanged.connect(self._on_copy_text_changed)
        cb_btn = QPushButton("…")
        cb_btn.setFixedWidth(32)
        cb_btn.clicked.connect(self._browse_copy)
        cr.addWidget(self._opt_copy)
        cr.addWidget(self._copy_edit, 1)
        cr.addWidget(cb_btn)
        al.addRow(cr)

        csr = QHBoxLayout()
        self._opt_checkspace = QCheckBox(tr("create.opt_checkspace"))
        self._checkspace_edit = QLineEdit()
        self._checkspace_edit.setPlaceholderText("10G")
        self._checkspace_edit.textChanged.connect(self._on_checkspace_text_changed)
        csr.addWidget(self._opt_checkspace)
        csr.addWidget(self._checkspace_edit, 1)
        al.addRow(csr)

        er = QHBoxLayout()
        er.addWidget(QLabel(tr("create.errorlog")))
        self._errorlog_edit = QLineEdit()
        eb = QPushButton("…")
        eb.setFixedWidth(32)
        eb.clicked.connect(self._browse_errorlog)
        er.addWidget(self._errorlog_edit, 1)
        er.addWidget(eb)
        al.addRow(er)

        sr = QHBoxLayout()
        self._opt_sfx = QCheckBox(tr("create.opt_sfx"))
        self._sfx_edit = QLineEdit()
        self._sfx_edit.textChanged.connect(self._on_sfx_text_changed)
        sb = QPushButton("…")
        sb.setFixedWidth(32)
        sb.clicked.connect(self._browse_sfx)
        sr.addWidget(self._opt_sfx)
        sr.addWidget(self._sfx_edit, 1)
        sr.addWidget(sb)
        al.addRow(sr)

        chr_ = QHBoxLayout()
        self._opt_chunk = QCheckBox(tr("create.opt_chunk"))
        self._chunk_combo = QComboBox()
        self._chunk_combo.addItem("—", "")
        for sz in ("100MB", "500MB", "700MB", "1GB", "2GB", "4GB", "8GB",
                   "16GB", "25GB", "50GB"):
            self._chunk_combo.addItem(sz, sz)
        self._chunk_combo.addItem("…", "__custom__")
        self._chunk_combo.setMinimumWidth(140)
        self._chunk_last_index = 0
        self._chunk_custom = ""
        self._chunk_combo.currentIndexChanged.connect(self._on_chunk_index_changed)
        chr_.addWidget(self._opt_chunk)
        chr_.addWidget(self._chunk_combo, 1)
        al.addRow(chr_)

        av.addLayout(al)
        av.addStretch(1)

        self._tabs.addTab(page_general, tr("create.tab_general"))
        self._tabs.addTab(page_comp, tr("create.tab_compression"))


        self._tabs.addTab(self._build_par2_page(),
                           tr("create.tab_protection"))
        self._tabs.addTab(page_adv, tr("create.tab_advanced"))
        layout.addWidget(self._tabs, 1)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        for std in (QDialogButtonBox.Ok, QDialogButtonBox.Cancel):
            b = buttons.button(std)
            if b:
                b.setAutoDefault(False)
                b.setDefault(False)


        btn_save = QPushButton()
        btn_save.setAutoDefault(False)
        if self._edit_work_id or self._add_to_work_id:
            btn_save.setText("💾 " + tr("task.save_edit"))
            btn_save.clicked.connect(self._on_save_only)
        else:
            btn_save.setText("💾 " + tr("task.save_button"))
            btn_save.clicked.connect(self._on_save_task)
        buttons.addButton(btn_save, QDialogButtonBox.ActionRole)

        btn_sched = QPushButton("📅 " + tr("scheduler.schedule_button"))
        btn_sched.setAutoDefault(False)
        btn_sched.clicked.connect(self._on_schedule_task)
        buttons.addButton(btn_sched, QDialogButtonBox.ActionRole)

        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._dest_edit.textChanged.connect(self._update_note)
        self._update_note()
        self._start_size_worker()
        self._update_longpath_state()
        self._update_method_preview()
        if initial_settings:
            self._apply_settings(initial_settings)


    def _on_level_changed(self, _i):
        self._method_group.setVisible(self._level_combo.currentData() == "method")

    def _on_method_changed(self, *_a):
        self._update_method_preview()

    def _get_method_params(self):
        return {
            "mode": self._method_mode_combo.currentData() or "x",
            "block_b": self._method_block_combo.currentData() or 6,
            "preprocess_n2": self._method_preproc_combo.currentData() or 6,
            "search_depth_n5": self._method_depth_combo.currentData() or 20,
            "use_c": self._method_c_cb.isChecked(),
            "use_i": self._method_i_cb.isChecked(),
            "use_a": self._method_a_cb.isChecked(),
            "use_w": self._method_w_cb.isChecked(),
            "use_m": self._method_m_cb.isChecked(),
            "use_s": self._method_s_cb.isChecked(),
            "use_t": self._method_t_cb.isChecked(),
        }

    def _build_current_method_string(self):
        return build_method_string(**self._get_method_params())

    def _update_method_preview(self):
        self._method_preview.setText(f"-method {self._build_current_method_string()}")

    def _set_method_params(self, p):
        for combo, key, d in [
            (self._method_mode_combo, "mode", "x"),
            (self._method_block_combo, "block_b", 6),
            (self._method_preproc_combo, "preprocess_n2", 6),
            (self._method_depth_combo, "search_depth_n5", 20),
        ]:
            for i in range(combo.count()):
                if combo.itemData(i) == p.get(key, d):
                    combo.setCurrentIndex(i)
                    break
        for cb, k in [
            (self._method_c_cb, "use_c"), (self._method_i_cb, "use_i"),
            (self._method_a_cb, "use_a"), (self._method_w_cb, "use_w"),
            (self._method_m_cb, "use_m"), (self._method_s_cb, "use_s"),
            (self._method_t_cb, "use_t"),
        ]:
            cb.setChecked(p.get(k, True))
        self._update_method_preview()


    def _get_sources(self):
        return [self._source_list.item(i).text() for i in range(self._source_list.count())]

    def _add_source(self, path):
        for i in range(self._source_list.count()):
            if self._source_list.item(i).text() == path:
                return
        self._source_list.addItem(path)
        self._start_size_worker()
        self._update_longpath_state()

    def _on_select_sources(self):
        from ui.source_select_window import SourceSelectWindow
        d = SourceSelectWindow(self)
        if d.exec() == QDialog.Accepted:
            for p in d.selected_paths():
                self._add_source(p)

    def _on_remove_source(self):
        for it in self._source_list.selectedItems():
            self._source_list.takeItem(self._source_list.row(it))
        self._start_size_worker()
        self._update_longpath_state()


    def _start_size_worker(self):
        if self._size_worker:
            try:
                self._size_worker.size_ready.disconnect(self._on_size_ready)
            except Exception:
                pass
        w = _SizeWorker(self._get_sources())
        w.size_ready.connect(self._on_size_ready)
        w.finished.connect(lambda wr=w: _LIVE_WORKERS.discard(wr))
        _LIVE_WORKERS.add(w)
        self._size_worker = w
        w.start()


    def _update_longpath_state(self):
        hd = any(Path(str(s)).is_dir() for s in self._get_sources() if s)
        if hd:
            if not self._opt_longpath.isEnabled():
                self._opt_longpath.setChecked(True)
            self._opt_longpath.setEnabled(True)
        else:
            self._opt_longpath.setChecked(False)
            self._opt_longpath.setEnabled(False)

    def _insert_date_template(self):
        t = self._dest_edit.text()
        if DATE_TEMPLATE in t:
            return
        idx = t.lower().rfind(".zpaq")
        self._dest_edit.setText(
            t[:idx] + "_" + DATE_TEMPLATE + t[idx:] if idx > 0
            else t + "_" + DATE_TEMPLATE
        )

    def _dest_exists(self):
        d = self._dest_edit.text().strip()
        if not d or "?" in d:
            return False
        try:
            return Path(d).is_file()
        except Exception:
            return False

    def _set_checkspace(self, v):
        self._checkspace_edit.blockSignals(True)
        self._checkspace_edit.setText(v)
        self._checkspace_edit.blockSignals(False)
        self._opt_checkspace.setChecked(bool(v.strip()))

    def _on_size_ready(self, total):
        total = int(total)
        self._source_total = total
        if total <= 0 or self._user_cleared:
            return
        c = self._checkspace_edit.text().strip()
        if c and c != self._auto_checkspace:
            return
        self._auto_checkspace = _auto_checksize(total)
        self._set_checkspace(self._auto_checkspace)


    def _build_par2_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(10)


        self._par2_widget = Par2OptionsWidget(show_master=True)
        self._opt_par2 = self._par2_widget.master
        self._par2_box = self._par2_widget.box
        self._par2_redundancy = self._par2_widget.redundancy
        self._par2_auto_blocks = self._par2_widget.auto_blocks
        self._par2_manual_blocks = self._par2_widget.manual_blocks
        self._par2_block_size = self._par2_widget.block_size
        self._par2_block_count = self._par2_widget.block_count
        self._par2_auto_hint = self._par2_widget.auto_hint
        self._par2_block_warning = self._par2_widget.block_warning
        self._par2_memory = self._par2_widget.memory
        self._par2_threads = self._par2_widget.threads
        self._par2_recursion = self._par2_widget.recursion
        self._par2_uniform = self._par2_widget.uniform

        outer.addWidget(self._par2_widget)

        outer.addStretch(1)


        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        host = QWidget()
        host_lay = QVBoxLayout(host)
        host_lay.setContentsMargins(0, 0, 0, 0)
        host_lay.addWidget(scroll)
        return host

    def _on_par2_master(self, checked: bool):

        self._par2_widget._on_master(checked)

    def _on_par2_blocks(self, _checked=None):

        self._par2_widget._on_blocks()

    def _par2_collect(self) -> dict:
        return self._par2_widget.collect()

    def _par2_apply(self, options: dict):

        self._par2_widget.apply(options)

    def _on_chunk_index_changed(self, idx):
        data = self._chunk_combo.itemData(idx) or ""
        if data == "__custom__":
            self._chunk_combo.blockSignals(True)
            t, ok = QInputDialog.getText(
                self, tr("create.opt_chunk"), tr("create.chunk_required"),
                QLineEdit.Normal, self._chunk_custom,
            )
            if ok and t.strip():
                v = t.strip()
                self._chunk_custom = v
                tgt = next(
                    (i for i in range(self._chunk_combo.count())
                     if self._chunk_combo.itemData(i) == v),
                    self._chunk_combo.count() - 1,
                )
                if tgt == self._chunk_combo.count() - 1:
                    self._chunk_combo.insertItem(tgt, v, v)
                self._chunk_combo.setCurrentIndex(tgt)
                self._chunk_last_index = tgt
                data = v
            else:
                self._chunk_combo.setCurrentIndex(self._chunk_last_index)
                data = self._chunk_combo.itemData(self._chunk_last_index) or ""
            self._chunk_combo.blockSignals(False)
        elif data:
            self._chunk_last_index = idx
        self._opt_chunk.setChecked(bool(data))

    def _on_checkspace_text_changed(self, t):
        self._opt_checkspace.setChecked(bool(t.strip()))
        self._user_cleared = not t.strip()

    def _on_copy_text_changed(self, t):
        self._opt_copy.setChecked(bool(t.strip()))

    def _on_sfx_text_changed(self, t):
        self._opt_sfx.setChecked(bool(t.strip()))

    def _update_note(self):
        self._note_label.setText(
            tr("create.will_append") if self._dest_exists() else tr("create.will_create")
        )
        c = self._checkspace_edit.text().strip()
        if not c and not self._user_cleared and self._source_total > 0:
            self._auto_checkspace = _auto_checksize(self._source_total)
            self._set_checkspace(self._auto_checkspace)

    def _browse_dest(self):
        p, _ = QFileDialog.getSaveFileName(
            self, tr("create.dialog_title"),
            self._dest_edit.text().strip() or str(Path.home()),
            tr("create.filter"),
            options=QFileDialog.DontConfirmOverwrite,
        )
        if p:
            if not p.lower().endswith(".zpaq"):
                p += ".zpaq"
            self._dest_edit.setText(p)

    def _browse_copy(self):
        d = QFileDialog.getExistingDirectory(self, tr("create.opt_copy"))
        if d:
            self._copy_edit.setText(d)

    def _browse_errorlog(self):
        p, _ = QFileDialog.getSaveFileName(
            self, tr("create.errorlog"), options=QFileDialog.DontConfirmOverwrite
        )
        if p:
            self._errorlog_edit.setText(p)

    def _browse_sfx(self):
        p, _ = QFileDialog.getSaveFileName(
            self, tr("create.opt_sfx"), "",
            "EXE (*.exe);;All files (*.*)",
            options=QFileDialog.DontConfirmOverwrite,
        )
        if p:
            if not p.lower().endswith(".exe"):
                p += ".exe"
            self._sfx_edit.setText(p)


    def _build_params_rows(self, s):
        rows = []
        lk = s.get("level_key", "")
        if lk == "method":
            mp = s.get("method_params", {})
            ll = f"-method {build_method_string(**mp)}" if mp else "-method"
        else:
            ll = {
                "m0": tr("create.level_m0"), "m1": tr("create.level_m1"),
                "m2": tr("create.level_m2"), "m3": tr("create.level_m3"),
                "m4": tr("create.level_m4"), "m5": tr("create.level_m5"),
            }.get(lk, tr("create.level_m2"))
        rows.append((tr("create.level"), ll))
        rows.append((tr("create.hash"), s.get("hash_key") or tr("create.hash_default")))
        if s.get("comment"):
            rows.append((tr("create.comment"), s["comment"]))
        rows.append((
            tr("create.password"),
            tr("create.done.set") if s.get("password") else tr("create.done.notset"),
        ))
        vl = {
            "": tr("create.verify_none"), "full": tr("create.verify_test"),
            "verify": tr("create.verify_verify"),
            "paranoid": tr("create.verify_paranoid"),
        }.get(s.get("verify", ""), tr("create.verify_none"))
        rows.append((tr("create.verify_mode"), vl))
        if s.get("only_masks"):
            rows.append((tr("create.done.include"), "; ".join(s["only_masks"])))
        if s.get("not_masks"):
            rows.append((tr("create.done.exclude"), "; ".join(s["not_masks"])))
        opts = [
            tr(lk) for k, lk in (
                ("longpath", "create.opt_longpath"), ("date", "create.opt_date"),
                ("norecursion", "create.opt_norecurse"),
                ("forcewindows", "create.opt_forcewindows"),
                ("force_xls", "create.opt_force_xls"),
                ("nochecksum", "create.opt_nochecksum"),
                ("nodedup", "create.opt_nodedup"),
                ("vss", "create.opt_vss"),
                ("noonedrive", "create.opt_noonedrive"),
                ("ignore", "create.opt_ignore"), ("shutdown", "create.opt_shutdown"),
            ) if s.get(k)
        ]
        if opts:
            rows.append((tr("create.done.options"), "; ".join(opts)))
        if s.get("copy"):
            rows.append((tr("create.opt_copy"), s["copy"]))
        if s.get("checkspace"):
            rows.append((tr("create.opt_checkspace"), s["checkspace"]))
        if s.get("errorlog"):
            rows.append((tr("create.errorlog"), s["errorlog"]))
        if s.get("sfx"):
            rows.append((tr("create.opt_sfx"), s["sfx"]))
        if s.get("chunk"):
            rows.append((tr("create.opt_chunk"), s["chunk"]))
        return rows

    def _collect_settings(self):
        sources = self._get_sources()
        dest = self._dest_edit.text().strip()
        p1 = self._pwd_edit.text()
        lk = self._level_combo.currentData() or "m2"
        hk = self._hash_combo.currentData() or ""
        comment = self._comment_edit.text().strip()
        only = _split_masks(self._only_edit.text())
        not_ = _split_masks(self._not_edit.text())
        verify = self._verify_combo.currentData() or ""
        copy = self._copy_edit.text().strip() if self._opt_copy.isChecked() else ""


        par2_enabled = self._opt_par2.isChecked()
        cs = self._checkspace_edit.text().strip() if self._opt_checkspace.isChecked() else ""
        chunk = ""
        if self._opt_chunk.isChecked():
            chunk = self._chunk_combo.currentData() or ""
            if chunk == "__custom__":
                chunk = self._chunk_custom or ""
        sfx = self._sfx_edit.text().strip() if self._opt_sfx.isChecked() else ""
        mp = None
        if lk == "method":
            mp = self._get_method_params()
            la = ["-method", build_method_string(**mp)]
        else:
            la = LEVEL_ARGS.get(lk, ["-m2"])


        work_title = self._work_title_edit.text().strip()
        job_title = self._job_title_edit.text().strip()

        s = {
            "sources": sources, "dest": dest, "password": p1 or None,


            "work_title": work_title,
            "title": job_title,
            "level": la, "level_key": lk, "hash": HASH_ARGS.get(hk, ""),
            "hash_key": hk, "comment": comment, "only_masks": only,
            "not_masks": not_, "longpath": bool(self._opt_longpath.isChecked()),
            "date": bool(self._opt_date.isChecked()),
            "norecursion": bool(self._opt_norecurse.isChecked()),
            "forcewindows": bool(self._opt_forcewindows.isChecked()),
            "force_xls": bool(self._opt_force_xls.isChecked()),
            "nochecksum": bool(self._opt_nochecksum.isChecked()),
            "nodedup": bool(self._opt_nodedup.isChecked()),
            "verify": verify, "vss": bool(self._opt_vss.isChecked()),
            "copy": copy, "checkspace": cs,
            "noonedrive": bool(self._opt_noonedrive.isChecked()),
            "ignore": bool(self._opt_ignore.isChecked()),
            "errorlog": self._errorlog_edit.text().strip(),
            "shutdown": bool(self._opt_shutdown.isChecked()),
            "sfx": sfx, "chunk": chunk,
            "par2_enabled": par2_enabled,
        }
        if par2_enabled:


            s["par2_options"] = self._par2_collect()
        if mp:
            s["method_params"] = mp
        if self._schedule:
            s["schedule"] = self._schedule
        return s

    def _apply_settings(self, s):


        self._work_title_edit.setText(str(s.get("work_title") or ""))
        self._job_title_edit.setText(str(s.get("title") or ""))

        self._source_list.clear()
        for src in s.get("sources", []):
            self._source_list.addItem(str(src))
        self._sources = [str(x) for x in s.get("sources", [])]
        if s.get("dest"):
            self._dest_edit.setText(s["dest"])
        pw = s.get("password") or ""
        self._pwd_edit.setText(pw)
        self._pwd2_edit.setText(pw)
        lk = s.get("level_key", "m2")
        for i in range(self._level_combo.count()):
            if self._level_combo.itemData(i) == lk:
                self._level_combo.setCurrentIndex(i)
                break
        self._on_level_changed(self._level_combo.currentIndex())
        hk = s.get("hash_key", "")
        for i in range(self._hash_combo.count()):
            if self._hash_combo.itemData(i) == hk:
                self._hash_combo.setCurrentIndex(i)
                break
        self._comment_edit.setText(s.get("comment", ""))
        self._only_edit.setText("; ".join(s.get("only_masks", [])))
        self._not_edit.setText("; ".join(s.get("not_masks", [])))
        v = s.get("verify", "")
        for i in range(self._verify_combo.count()):
            if self._verify_combo.itemData(i) == v:
                self._verify_combo.setCurrentIndex(i)
                break
        for cb, k in [
            (self._opt_longpath, "longpath"), (self._opt_date, "date"),
            (self._opt_norecurse, "norecursion"),
            (self._opt_forcewindows, "forcewindows"),
            (self._opt_force_xls, "force_xls"),
            (self._opt_nochecksum, "nochecksum"),
            (self._opt_nodedup, "nodedup"), (self._opt_vss, "vss"),
            (self._opt_noonedrive, "noonedrive"), (self._opt_ignore, "ignore"),
            (self._opt_shutdown, "shutdown"),
        ]:
            cb.setChecked(bool(s.get(k, False)))
        cp = s.get("copy", "")
        self._copy_edit.setText(cp)
        self._opt_copy.setChecked(bool(cp))
        csp = s.get("checkspace", "")
        self._checkspace_edit.setText(csp)
        self._opt_checkspace.setChecked(bool(csp))
        if csp:
            self._auto_checkspace = csp
        self._errorlog_edit.setText(s.get("errorlog", ""))
        sfx = s.get("sfx", "")
        self._sfx_edit.setText(sfx)
        self._opt_sfx.setChecked(bool(sfx))
        chunk = s.get("chunk", "")
        if chunk:
            found = False
            for i in range(self._chunk_combo.count()):
                if self._chunk_combo.itemData(i) == chunk:
                    self._chunk_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                self._chunk_custom = chunk
                idx = self._chunk_combo.count() - 1
                self._chunk_combo.insertItem(idx, chunk, chunk)
                self._chunk_combo.setCurrentIndex(idx)
            self._opt_chunk.setChecked(True)
        else:
            self._opt_chunk.setChecked(False)


        raw_par2 = s.get("par2_options")


        self._par2_options = dict(raw_par2) if isinstance(raw_par2, dict) else {}
        self._par2_apply(self._par2_options)
        self._opt_par2.setChecked(bool(s.get("par2_enabled", False)))
        if s.get("method_params"):
            self._set_method_params(s["method_params"])
        self._schedule = s.get("schedule")
        self._update_note()
        self._start_size_worker()
        self._update_longpath_state()
        self._update_method_preview()


    def _validate_settings(self, settings: dict) -> bool:

        if not settings.get("sources"):
            QMessageBox.warning(self, tr("create.dialog_title"), tr("create.no_source"))
            return False
        if not settings.get("dest"):
            QMessageBox.warning(self, tr("create.dialog_title"), tr("create.dest_required"))
            return False
        return True

    def _on_save_only(self):
        settings = self._collect_settings()
        if not self._validate_settings(settings):
            return

        host = self.parent()
        try:
            if self._edit_work_id and self._edit_job_id:
                handler = getattr(host, "_save_edited_job", None)
                if not callable(handler):
                    QMessageBox.warning(
                        self, tr("task.save_title"),
                        tr("task.save_error", error="host method not found"),
                    )
                    return
                ok = handler(settings, self._edit_work_id, self._edit_job_id)
                if ok:
                    self.reject()
                return

            if self._add_to_work_id:
                handler = getattr(host, "_save_new_job", None)
                if not callable(handler):
                    QMessageBox.warning(
                        self, tr("task.save_title"),
                        tr("task.save_error", error="host method not found"),
                    )
                    return
                handler(settings, work_id=self._add_to_work_id)
                self.reject()
                return

            QMessageBox.warning(
                self, tr("task.save_title"),
                tr("task.save_error", error="no save context"),
            )
        except Exception as exc:
            QMessageBox.warning(
                self, tr("task.save_title"), tr("task.save_error", error=str(exc))
            )

    def _on_save_task(self):
        settings = self._collect_settings()
        if not self._validate_settings(settings):
            return
        handler = getattr(self.parent(), "_save_new_job", None)
        if not callable(handler):
            QMessageBox.warning(
                self, tr("task.save_title"), tr("task.save_error", error="host method not found")
            )
            return
        try:
            handler(settings)
        except Exception as exc:
            QMessageBox.warning(
                self, tr("task.save_title"), tr("task.save_error", error=str(exc))
            )

    def _on_schedule_task(self):
        settings = self._collect_settings()
        if not self._validate_settings(settings):
            return

        from ui.scheduler_dialog import ScheduleDialog

        dlg = ScheduleDialog(self, initial_schedule=self._schedule)
        if dlg.exec() != QDialog.Accepted:
            return
        schedule = dlg.result_schedule()
        if not schedule:
            return


        settings["schedule"] = schedule
        self._schedule = schedule

        host = self.parent()
        ok = False
        try:
            if self._edit_work_id and self._edit_job_id:
                handler = getattr(host, "_save_edited_job", None)
                if callable(handler):
                    ok = bool(handler(
                        settings, self._edit_work_id, self._edit_job_id
                    ))
            else:
                handler = getattr(host, "_save_new_job", None)
                if not callable(handler):
                    QMessageBox.warning(
                        self, tr("scheduler.title"),
                        tr("task.save_error", error="host method not found"),
                    )
                    return

                if self._add_to_work_id:
                    ok = bool(handler(
                        settings,
                        work_id=self._add_to_work_id,
                    ))
                else:
                    ok = bool(handler(settings))
        except Exception as exc:
            QMessageBox.warning(
                self, tr("scheduler.title"), tr("task.save_error", error=str(exc))
            )
            return

        if ok:


            self._already_saved = True


    def _validate_and_accept(self):


        if self._already_saved:
            self.reject()
            return

        settings = self._collect_settings()
        if not self._validate_settings(settings):
            return

        if self._pwd_edit.text() != self._pwd2_edit.text():
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.password_mismatch")
            )
            return
        dest = settings["dest"]
        if not dest.lower().endswith(".zpaq") and "?" not in dest:
            dest += ".zpaq"
            self._dest_edit.setText(dest)
            settings["dest"] = dest

        if self._opt_copy.isChecked() and not self._copy_edit.text().strip():
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.copy_required")
            )
            return
        if self._opt_checkspace.isChecked() and not self._checkspace_edit.text().strip():
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.checkspace_required")
            )
            return
        chunk = ""
        if self._opt_chunk.isChecked():
            chunk = self._chunk_combo.currentData() or ""
            if chunk == "__custom__":
                chunk = ""
        if self._opt_chunk.isChecked() and not chunk:
            QMessageBox.warning(
                self, tr("create.dialog_title"), tr("create.chunk_required")
            )
            return
        sfx = self._sfx_edit.text().strip() if self._opt_sfx.isChecked() else ""
        if self._opt_sfx.isChecked() and not sfx:
            sfx = str(Path(dest).with_suffix(".exe"))

        settings["params_rows"] = self._build_params_rows(settings)

        self._result = settings
        self.accept()

    def result_settings(self):
        return self._result
