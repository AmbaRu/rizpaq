

















from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui import skins
from ui.i18n import tr

                                                                
                                                                 
                                                                     
SEGMENT_ORDER = ("ok", "error", "busy", "never")
SEGMENT_COLOR = {
    "ok": "OK_GREEN",
    "error": "DIFF_REMOVED",
    "busy": "BUSY_STEEL",
    "never": "TEXT_MUTED",
}


def segment_color(token_key: str) -> QColor:
    pass
    return QColor(skins.color(SEGMENT_COLOR.get(token_key, "TEXT_MUTED")))


def _angle_span(count: int, total: int) -> int:
    pass
    if total <= 0 or count <= 0:
        return 0
    return max(1, int(360 * 16 * count / total))


def _donut_geometry(w: int, h: int) -> tuple:
    pass
    side = min(w, h)
    margin = 14
    rect = QRectF(
        (w - side) / 2 + margin,
        (h - side) / 2 + margin,
        side - 2 * margin,
        side - 2 * margin,
    )
    return rect, max(10.0, side * 0.11)


class StatusDonut(QWidget):
    pass







    segmentClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._counts = {"ok": 0, "error": 0, "busy": 0, "never": 0}
        self.setMinimumSize(150, 150)
                                                                   
        self.setMouseTracking(True)

    def set_counts(self, counts: dict) -> None:
        for key in self._counts:
            try:
                self._counts[key] = int(counts.get(key, 0) or 0)
            except (TypeError, ValueError):
                self._counts[key] = 0
        self.update()

    def total(self) -> int:
        return sum(self._counts.values())

                                                                                  

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        total = self.total()

        rect, pen_w = _donut_geometry(self.width(), self.height())

        if total <= 0:
                                                                      
                                                                  
            pen = QPen(QColor(skins.color("BORDER")), int(pen_w))
            pen.setCapStyle(Qt.RoundCap)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
        else:
            start = 90 * 16                                            
            for key in SEGMENT_ORDER:
                span = _angle_span(self._counts[key], total)
                if not span:
                    continue
                pen = QPen(segment_color(key), int(pen_w))
                pen.setCapStyle(Qt.FlatCap)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawArc(rect, start, -span)
                start -= span

                                                                        
                                                                 
        f = self.font()
        f.setPointSize(max(f.pointSize(), 9) + 7)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(skins.color("TEXT_MAIN")))
        text = f"{total:,}".replace(",", " ")
        painter.drawText(rect, Qt.AlignCenter, text)

                                                                             

    def _segment_at(self, pos) -> Optional[str]:
        pass
        total = self.total()
        if total <= 0:
            return None
        rect, pen_w = _donut_geometry(self.width(), self.height())
        center = rect.center()
        dx, dy = pos.x() - center.x(), pos.y() - center.y()
        dist = (dx * dx + dy * dy) ** 0.5
        ring = rect.width() / 2
        if not (ring - pen_w / 2 <= dist <= ring + pen_w / 2):
            return None
                                                                   
                                                                   
        ang = math.degrees(math.atan2(-dy, dx))
        if ang > 90:
            ang -= 360
        clockwise = (90 - ang) % 360                                   
        acc = 0.0
        for key in SEGMENT_ORDER:
            acc += 360.0 * self._counts[key] / total
            if clockwise <= acc:
                return key
        return SEGMENT_ORDER[-1]

    def mousePressEvent(self, event) -> None:
        key = self._segment_at(event.position())
        if key is not None:
            self.segmentClicked.emit(key)

    def mouseMoveEvent(self, event) -> None:
        key = self._segment_at(event.position())
        if key is None:
            self.setToolTip("")
            return
        caption = tr(f"dashboard.status.{key}")
        self.setToolTip(f"{caption}: {self._counts[key]}")


class Par2Gauge(QWidget):
    pass










    def __init__(self, parent=None):
        super().__init__(parent)
        self._covered = 0
        self._total = 0
        self.setMinimumSize(150, 120)

    def set_value(self, covered: int, total: int) -> None:
        self._covered = max(0, int(covered or 0))
        self._total = max(0, int(total or 0))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        size = min(w - 20, h - 20)
        rect = QRectF((w - size) / 2, (h - size) / 2, size, size)
                                                                       
                                                                    
        span_total = 270 * 16
        pen_w = max(9, int(size * 0.09))

        track = QPen(QColor(skins.color("BORDER")), pen_w)
        track.setCapStyle(Qt.RoundCap)
        painter.setPen(track)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(rect, 135 * 16, -span_total)

        if self._total > 0:
            frac = min(1.0, self._covered / self._total)
            token = "OK_GREEN" if frac >= 0.999 else "WARN_ORANGE"
            val = QPen(QColor(skins.color(token)), pen_w)
            val.setCapStyle(Qt.RoundCap)
            painter.setPen(val)
            painter.drawArc(rect, 135 * 16, -int(span_total * frac))

                                                               
                                                             
        f = self.font()
        f.setPointSize(max(f.pointSize(), 9) + 6)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(skins.color("TEXT_MAIN")))
        if self._total > 0:
            text = f"{round(100 * self._covered / self._total)}%"
        else:
            text = "—"
        painter.drawText(rect.adjusted(0, size * 0.12, 0, size * 0.12),
                         Qt.AlignCenter, text)


class RunTrend(QWidget):
    pass







    def __init__(self, parent=None):
        super().__init__(parent)
        self._series: list = []                      
        self.setMinimumHeight(120)

    def set_series(self, series: list) -> None:
        self._series = list(series)[-30:]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        area = self.rect().adjusted(6, 10, -6, -22)
        f = self.font()
        painter.setFont(f)
        fm = QFontMetrics(f)

        if not self._series or all(o + e == 0 for _, o, e in self._series):
            painter.setPen(QColor(skins.color("TEXT_MUTED")))
            painter.drawText(self.rect(), Qt.AlignCenter, tr(
                "dashboard.trend.empty"))
            return

        peak = max(max(o + e for _, o, e in self._series), 1)
        n = len(self._series)
        slot = area.width() / n
        bar_w = max(3.0, slot * 0.62)

                                                                       
                                                               
        grid = QPen(QColor(skins.color("PROGRESS_TRACK")), 1)
        painter.setPen(grid)
        for frac in (0.25, 0.5, 0.75):
            y = area.top() + area.height() * frac
            painter.drawLine(QPointF(area.left(), y),
                             QPointF(area.right(), y))

        ok_c = QColor(skins.color("OK_GREEN"))
        err_c = QColor(skins.color("DIFF_REMOVED"))
        label_pen = QColor(skins.color("TEXT_MUTED"))
        label_step = max(1, n // 6)

        x = area.left()
        for i, (label, ok_n, err_n) in enumerate(self._series):
            height = area.height() * (ok_n + err_n) / peak
            if height > 0:
                                                                       
                                                                       
                                                                       
                                                      
                err_h = area.height() * err_n / peak
                ok_h = height - err_h
                if err_h > 0:
                    painter.fillRect(
                        QRectF(x + (slot - bar_w) / 2, area.bottom() - height,
                               bar_w, err_h), err_c)
                if ok_h > 0:
                    painter.fillRect(
                        QRectF(x + (slot - bar_w) / 2, area.bottom() - ok_h,
                               bar_w, ok_h), ok_c)
            if i % label_step == 0 or i == n - 1:
                painter.setPen(label_pen)
                tw = fm.horizontalAdvance(label)
                painter.drawText(
                    QPointF(x + (slot - tw) / 2, area.bottom() + 16), label)
            x += slot
