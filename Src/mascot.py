"""Fable's restrained, pose-based idle animation, rendered at 30 fps."""

import math
import time
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class Fable(QWidget):
    def __init__(self, assets, size=84):
        super().__init__()
        self.frames = {
            name: QPixmap(str(assets / (name + ".png")))
            for name in ("neutral", "half", "blink", "peek")
        }
        if any(frame.isNull() for frame in self.frames.values()):
            raise RuntimeError("Fable artwork is missing from the application bundle.")
        self.setFixedSize(size, size)
        self.setAccessibleName("Fable, your fox study companion")
        self.setToolTip("Fable is judging. Affectionately. Click for a check-in.")
        self.setCursor(Qt.PointingHandCursor)
        self.started = time.monotonic()
        self.reaction = None
        self.preview_time = None
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    @staticmethod
    def pose_at(elapsed, reaction=None):
        if reaction is not None and 0 <= reaction < 1.6:
            if reaction < 0.10:
                return "neutral"
            if reaction < 0.20:
                return "half"
            if reaction < 1.20:
                return "peek"
            if reaction < 1.30:
                return "half"
            return "neutral"
        cycle = elapsed % 7.4
        if 6.0 <= cycle < 6.067 or 6.167 <= cycle < 6.234:
            return "half"
        if 6.067 <= cycle < 6.167:
            return "blink"
        return "neutral"

    def check_in(self):
        self.reaction = time.monotonic()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.check_in()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        elapsed = (
            self.preview_time
            if self.preview_time is not None
            else time.monotonic() - self.started
        )
        reaction = None if self.reaction is None else time.monotonic() - self.reaction
        pose = self.pose_at(elapsed, reaction)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # Native rendering transforms leave the image-generated PNG artwork untouched.
        scale = 1 + 0.006 * math.sin(elapsed * math.tau / 4.5)
        width = self.width()
        height = self.height()
        painter.translate(width / 2, height * 0.94)
        painter.scale(1, scale)
        painter.translate(-width / 2, -height * 0.94)
        target_width = height * 1000 / 1100
        painter.drawPixmap(
            QRectF((width - target_width) / 2, 0, target_width, height),
            self.frames[pose],
            QRectF(150, 100, 1000, 1100),
        )

    def showEvent(self, event):
        self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def shutdown(self):
        self.timer.stop()
