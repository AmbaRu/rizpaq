from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.i18n import tr


class Par2OptionsWidget(QWidget):

    masterToggled = Signal(bool)

    def __init__(self, parent=None, show_master: bool = True):
        super().__init__(parent)
        self._show_master = bool(show_master)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)


        self.intro = QLabel(tr("par2.intro"))
        self.intro.setWordWrap(True)

        self.intro.setProperty("hint", True)
        outer.addWidget(self.intro)


        if self._show_master:
            self.master = QCheckBox(tr("par2.enable"))
            self.master.toggled.connect(self._on_master)
            outer.addWidget(self.master)
        else:
            self.master = None


        self.box = QGroupBox(tr("par2.settings_group"))
        gl = QVBoxLayout(self.box)
        gl.setSpacing(8)


        form = QFormLayout()
        form.setSpacing(8)
        self.redundancy = QSpinBox()
        self.redundancy.setRange(1, 100)
        self.redundancy.setSuffix(" %")
        form.addRow(tr("par2.redundancy"), self.redundancy)
        gl.addLayout(form)

        self.redundancy_hint = QLabel(tr("par2.redundancy_hint"))
        self.redundancy_hint.setWordWrap(True)
        self.redundancy_hint.setProperty("hint", True)
        gl.addWidget(self.redundancy_hint)


        self.auto_blocks = QRadioButton(tr("par2.block_auto"))
        self.manual_blocks = QRadioButton(tr("par2.block_manual"))
        gl.addWidget(self.auto_blocks)
        gl.addWidget(self.manual_blocks)

        manual = QFormLayout()
        manual.setSpacing(8)
        self.block_size = QSpinBox()
        self.block_size.setRange(1, 1024 * 1024 * 1024)
        self.block_size.setSingleStep(4096)
        self.block_size.setSuffix(tr("par2.bytes_suffix"))
        manual.addRow(tr("par2.block_size"), self.block_size)

        self.block_count = QSpinBox()
        self.block_count.setRange(100, 100000)
        manual.addRow(tr("par2.block_count"), self.block_count)
        gl.addLayout(manual)

        self.auto_hint = QLabel(tr("par2.block_auto_hint"))
        self.auto_hint.setWordWrap(True)
        self.auto_hint.setProperty("hint", True)
        gl.addWidget(self.auto_hint)

        self.block_warning = QLabel(tr("par2.block_manual_warning"))
        self.block_warning.setWordWrap(True)
        self.block_warning.setProperty("warning", True)
        gl.addWidget(self.block_warning)

        self.auto_blocks.toggled.connect(self._on_blocks)
        self.manual_blocks.toggled.connect(self._on_blocks)


        other = QFormLayout()
        other.setSpacing(8)
        self.memory = QSpinBox()
        self.memory.setRange(0, 1024 * 64)
        self.memory.setSuffix(tr("par2.mb_suffix"))


        self.memory.setSpecialValueText(tr("par2.automatic"))
        other.addRow(tr("par2.memory"), self.memory)

        self.threads = QSpinBox()
        self.threads.setRange(0, 1024)
        self.threads.setSpecialValueText(tr("par2.automatic"))
        other.addRow(tr("par2.threads"), self.threads)

        self.recursion = QCheckBox(tr("par2.recursion"))
        other.addRow(self.recursion)

        self.uniform = QCheckBox(tr("par2.uniform"))
        other.addRow(self.uniform)
        gl.addLayout(other)


        self.limits = QLabel(tr("par2.limits_note"))
        self.limits.setWordWrap(True)
        self.limits.setProperty("hint", True)
        gl.addWidget(self.limits)

        outer.addWidget(self.box)


        self.redundancy.setValue(5)
        self.auto_blocks.setChecked(True)
        self.manual_blocks.setChecked(False)
        self.block_size.setValue(65536)
        self.block_count.setValue(2000)
        self._on_blocks()

        if self.master is not None:
            self._on_master(self.master.isChecked())


    def _on_master(self, checked: bool):

        self.box.setEnabled(bool(checked))
        self.masterToggled.emit(bool(checked))

    def _on_blocks(self, _checked=None):
        manual = self.manual_blocks.isChecked()
        self.block_size.setEnabled(manual)
        self.block_count.setEnabled(manual)
        self.block_warning.setVisible(manual)
        self.auto_hint.setVisible(not manual)

    def set_master(self, checked: bool):

        if self.master is None:
            return
        blocked = self.master.blockSignals(True)
        self.master.setChecked(bool(checked))
        self.master.blockSignals(blocked)
        self._on_master(self.master.isChecked())


    def collect(self) -> dict:
        out = {"redundancy": self.redundancy.value()}

        if self.manual_blocks.isChecked():
            out["block_size"] = self.block_size.value()
        else:
            out["block_size"] = None
            out["block_count"] = None

        memory = self.memory.value()
        if memory > 0:
            out["memory_mb"] = memory

        threads = self.threads.value()
        if threads > 0:
            out["threads"] = threads

        out["recursion"] = bool(self.recursion.isChecked())
        out["uniform"] = bool(self.uniform.isChecked())
        return out

    def apply(self, options: dict):
        opts = dict(options or {})

        self.redundancy.setValue(int(opts.get("redundancy") or 5))

        saved_manual = bool(opts.get("block_size") or opts.get("block_count"))


        for btn in (self.auto_blocks, self.manual_blocks):
            btn.blockSignals(True)
        self.manual_blocks.setChecked(saved_manual)
        self.auto_blocks.setChecked(not saved_manual)
        for btn in (self.auto_blocks, self.manual_blocks):
            btn.blockSignals(False)

        self.block_size.setValue(int(opts.get("block_size") or 65536))
        self.block_count.setValue(int(opts.get("block_count") or 2000))

        self.memory.setValue(int(opts.get("memory_mb") or 0))
        self.threads.setValue(int(opts.get("threads") or 0))
        self.recursion.setChecked(bool(opts.get("recursion")))
        self.uniform.setChecked(bool(opts.get("uniform")))
        self._on_blocks()
