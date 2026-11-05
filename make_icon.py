#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QBuffer, QIODevice, QRectF, qVersion
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QTransform,
)

OUT_DIR = Path(__file__).resolve().parent
ICO = OUT_DIR / "app.ico"
PREVIEW = OUT_DIR / "app_icon_preview.png"

SIZES = (16, 24, 32, 48, 64, 128, 256)


def render(size: int) -> QImage:
    s = float(size)
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)


    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0.0, QColor("#7ba0cb"))
    grad.setColorAt(1.0, QColor("#2f6db5"))
    m = s * 0.02
    tile = QRectF(0, 0, s, s).adjusted(m, m, -m, -m)
    r = s * 0.20
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(tile, r, r)


    bw = max(1.0, s * 0.04)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(31, 79, 146, 120), bw))
    p.drawRoundedRect(tile.adjusted(bw / 2, bw / 2, -bw / 2, -bw / 2), r, r)


    if size >= 24:
        p.setPen(Qt.NoPen)
        bar_h = s * 0.040
        gap = s * 0.045
        widths = (0.44, 0.50, 0.56)
        alphas = (70, 95, 120)
        total = 3 * bar_h + 2 * gap
        y = s - s * 0.08 - total
        for w_frac, alpha in zip(widths, alphas):
            w = s * w_frac
            x = (s - w) / 2.0
            p.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            p.drawRoundedRect(QRectF(x, y, w, bar_h), bar_h / 2, bar_h / 2)
            y += bar_h + gap


    font = QFont()
    font.setFamily("Arial Black")
    font.setBold(True)
    font.setPixelSize(max(8, int(s * 0.60)))

    path = QPainterPath()
    path.addText(0, 0, font, "R")
    br = path.boundingRect()

    target = s * (0.52 if size >= 24 else 0.56)
    scale = min(
        target / max(br.width(), 1e-6),
        target / max(br.height(), 1e-6),
    )
    path.translate(-br.center().x(), -br.center().y())
    tr = QTransform()
    tr.scale(scale, scale)
    path = tr.map(path)

    cx = s / 2.0
    cy = s * 0.44 if size >= 24 else s * 0.50
    path.translate(cx, cy)


    shadow = QPainterPath()
    shadow.addPath(path)
    shadow.translate(s * 0.015, s * 0.025)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(20, 50, 90, 110)))
    p.drawPath(shadow)

    p.setBrush(QBrush(QColor(255, 255, 255)))
    p.drawPath(path)

    p.end()
    return img


def _png_bytes(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    return bytes(buf.data())


def write_ico(path: Path, images: list) -> None:

    n = len(images)
    data = bytearray(struct.pack("<HHH", 0, 1, n))
    offset = 6 + 16 * n
    entries, blobs = [], []
    for img in images:
        blob = _png_bytes(img)
        w = img.width() % 256
        h = img.height() % 256
        entries.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(blob), offset))
        offset += len(blob)
        blobs.append(blob)
    for e in entries:
        data += e
    for b in blobs:
        data += b
    path.write_bytes(bytes(data))


def _report(path: Path, ok: bool) -> bool:
    exists = path.is_file()
    size = path.stat().st_size if exists else 0
    print(f"  {'OK  ' if (ok and exists) else 'FAIL'} {path}  ({size} bytes)")
    return ok and exists


def main() -> int:
    QGuiApplication(sys.argv)
    print(f"Qt {qVersion()}; папка вывода: {OUT_DIR}")

    ok_prev = _report(PREVIEW, render(256).save(str(PREVIEW)))

    ok_ico = False
    try:
        write_ico(ICO, [render(sz) for sz in SIZES])
        ok_ico = True
    except Exception:
        traceback.print_exc()
        ok_ico = render(256).save(str(ICO))
    ok_ico = _report(ICO, ok_ico)

    return 0 if (ok_prev and ok_ico) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        input("Нажми Enter для выхода...")
        sys.exit(1)
