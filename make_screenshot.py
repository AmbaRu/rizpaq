#!/usr/bin/env python3


import os
import sys
import ctypes

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    def do_grab():
        windows = app.topLevelWidgets()
        best = None
        best_area = 0
        for w in windows:
            if not w.isVisible():
                continue
            r = w.geometry()
            area = r.width() * r.height()
            if area > best_area:
                best_area = area
                best = w
        if best is None:
            print("Нет видимых окон")
            os._exit(1)
        pixmap = best.grab()
        out = os.path.join(ROOT, "doc", "сайт", "screenshot.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        ok = pixmap.save(out, "PNG")
        print(f"Скриншот: {out} {pixmap.width()}x{pixmap.height()} ok={ok}")
        os._exit(0 if ok else 1)

    window = MainWindow()
    window.show()

    QTimer.singleShot(2000, do_grab)
    app.exec()


if __name__ == "__main__":
    main()
