"""Fable's restrained, pose-based idle animation, rendered at 30 fps."""

import math
import time
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class Fable(QWidget):
    def __init__(self, assets, size=84):
        super().__init__()
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")
        self.frames = {
            name: QPixmap(str(assets / (name + ".png")))
            for name in ("neutral", "half", "blink", "peek")
        }
        self.sources = {name: QRectF(150, 100, 1000, 1100) for name in self.frames}
        for atlas_name, names in [
            (
                "routine",
                ["mug", "lift", "sip", "content", "walk0", "walk1", "walk2", "walk3"],
            ),
            (
                "celebration",
                [
                    "ready",
                    "cheer",
                    "hooray",
                    "unused",
                    "carry0",
                    "carry1",
                    "carry2",
                    "carry3",
                ],
            ),
        ]:
            atlas = QPixmap(str(assets / (atlas_name + ".png")))
            for i, name in enumerate(names):
                self.frames[name] = atlas
                self.sources[name] = QRectF(
                    (i % 4) * atlas.width() / 4,
                    (i // 4) * atlas.height() / 2,
                    atlas.width() / 4,
                    atlas.height() / 2,
                )
        if any(frame.isNull() for frame in self.frames.values()):
            raise RuntimeError("Fable artwork is missing from the application bundle.")
        self.setFixedSize(size, size)
        self.setAccessibleName("Fable, your fox study companion")
        self.setToolTip("Fable is judging. Affectionately. Click for a check-in.")
        self.setCursor(Qt.PointingHandCursor)
        self.started = time.monotonic()
        self.reaction = None
        self.preview_time = None
        self.pose_override = None
        self.flip = False
        self.lift = 0.0
        self.squash = 1.0
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
        pose = self.pose_override or self.pose_at(elapsed, reaction)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # Native rendering transforms leave the image-generated PNG artwork untouched.
        scale = 1 + 0.006 * math.sin(elapsed * math.tau / 4.5)
        width = self.width()
        height = self.height()
        painter.translate(width / 2, height * 0.94)
        painter.scale(1, scale * self.squash)
        painter.translate(-width / 2, -height * 0.94)
        painter.translate(0, -self.lift)
        if self.flip:
            painter.translate(width, 0)
            painter.scale(-1, 1)
        source = self.sources[pose]
        target_width = height * source.width() / source.height()
        painter.drawPixmap(
            QRectF((width - target_width) / 2, 0, target_width, height),
            self.frames[pose],
            source,
        )

    def showEvent(self, event):
        self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def shutdown(self):
        self.timer.stop()
