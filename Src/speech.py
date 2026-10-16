"""Warm yellow, click-through speech with smooth opacity and readable hold time."""

import time
import re
from PySide6.QtCore import QObject, QTimer, QRectF, QRect, Qt, QPointF, QPoint
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QFont,
    QFontMetrics,
    QTextLayout,
    QTextOption,
    QTextCharFormat,
)
from PySide6.QtWidgets import QWidget, QSizePolicy
from companion import Dialogue, question_hint


def speech_timing(text):
    # Account for unspaced scripts too; reading time starts after the reveal.
    units = max(len(text.split()), len(re.sub(r"\s", "", text)) / 6)
    return 0.6 + 0.07 * units, 3.0 + 0.4 * units, 0.5 + 0.012 * units


class SpeechBubble(QWidget):
    BACKGROUND, INK, BORDER = "#f5d98f", "#372717", "#bd984b"

    def __init__(self, parent=None, tail="left"):
        super().__init__(parent)
        self.tail = tail
        self.text = ""
        self.opacity = 0.0
        self.elapsed = 0.0
        self.tail_y = 16.0
        self.body_top = 1.0
        self.reveal_seconds = 2.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setStyleSheet("background:transparent;")
        self.setAccessibleName("Fable says")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(180)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        metrics = QFontMetrics(QFont("Segoe UI", 11))
        return max(
            64,
            metrics.boundingRect(
                QRect(0, 0, max(100, width - 46), 1000000), Qt.TextWordWrap, self.text
            ).height()
            + 24,
        )

    def paintEvent(self, event):
        if not self.text or self.opacity <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self.opacity)
        body = QRectF(
            10, self.body_top, self.width() - 20, self.height() - self.body_top - 1
        )
        path = QPainterPath()
        path.addRoundedRect(body, 12, 12)
        attachment_y = max(self.body_top + 16, self.tail_y)
        if self.tail == "left":
            path.moveTo(11, attachment_y - 6)
            path.lineTo(1, self.tail_y)
            path.lineTo(11, attachment_y + 9)
        else:
            x = self.width() - 11
            path.moveTo(x, attachment_y - 6)
            path.lineTo(self.width() - 1, self.tail_y)
            path.lineTo(x, attachment_y + 9)
        path.closeSubpath()
        painter.setPen(QColor(self.BORDER))
        painter.setBrush(QColor(self.BACKGROUND))
        painter.drawPath(path)
        painter.setPen(QColor(self.INK))
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        # U+2028 makes the quip/CTA paragraph break explicit to QTextLayout.
        layout = QTextLayout(self.text.replace("\n", "\u2028"), font)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        words = list(re.finditer(r"\S+", self.text))
        offsets = [0]
        for char in self.text:
            offsets.append(offsets[-1] + (2 if ord(char) > 0xFFFF else 1))
        formats = []
        for i, word in enumerate(words):
            alpha = max(
                0.0,
                min(
                    1.0,
                    (
                        self.elapsed
                        - (self.reveal_seconds - 0.3) * i / max(1, len(words) - 1)
                    )
                    / 0.3,
                ),
            )
            color = QColor(self.INK)
            color.setAlphaF(alpha * alpha * (3 - 2 * alpha))
            style = QTextCharFormat()
            style.setForeground(color)
            span = QTextLayout.FormatRange()
            span.start = offsets[word.start()]
            span.length = offsets[word.end()] - span.start
            span.format = style
            formats.append(span)
        layout.setFormats(formats)
        layout.beginLayout()
        height = 0.0
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(max(100, body.width() - 26))
            line.setPosition(QPointF(0, height))
            height += line.height()
        layout.endLayout()
        layout.draw(
            painter,
            QPointF(body.x() + 13, body.y() + max(9, (body.height() - height) / 2)),
        )


class SpeechDirector(QObject):
    def __init__(self, window, home, review, now=time.monotonic):
        super().__init__(window.centralWidget())
        self.window, self.home, self.review = window, home, review
        for bubble in (home, review):
            bubble.setParent(window.centralWidget())
            bubble.hide()
        self.now = now
        self.dialogue = Dialogue()
        self.armed = None
        self.pending_review = False
        self.cache = {}
        self.active = None
        self.since = 0.0
        self.hold = 8.0
        self.fade_seconds = 0.5
        self.window.journey.arrived_review.connect(self.request_review)
        self.window.mascot.clicked.connect(self.clicked)
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.review.hide()

    def key(self):
        w = self.window
        return (w.exam["id"], w.current) if w.exam else None

    def hide_message(self):
        if self.active:
            self.active.text = ""
            self.active.opacity = 0
            self.active.update()
            self.active.hide()
        self.active = None
        self.review.hide()

    def post(self, text, review=False):
        if not text:
            return
        self.hide_message()
        self.active = self.review if review else self.home
        self.active.text = text
        self.active.setAccessibleDescription(text)
        self.active.updateGeometry()
        self.position()
        self.active.show()
        self.since = self.now()
        reveal, reading, self.fade_seconds = speech_timing(text)
        self.active.reveal_seconds = reveal
        self.hold = reveal + reading
        self.window.journey.talk(reveal + 0.3)
        self.tick()

    def position(self):
        if not self.active:
            return
        fox = self.window.mascot
        parent = self.window.centralWidget()
        width = min(560 if self.active is self.home else 420, parent.width() - 16)
        height = self.active.heightForWidth(width)
        mouth_y = fox.y() + fox.height() * 0.52
        x = (
            fox.x() + fox.width() - 8
            if self.active is self.home
            else fox.x() - width + 8
        )
        y = max(4, min(mouth_y - 4, parent.height() - height - 4))
        self.active.body_top = 1.0
        if self.active is self.home:
            title = self.window.brand_label
            title_bottom = title.mapTo(parent, QPoint(0, title.height())).y()
            # The pointer stays at the mouth while the balloon body clears the title.
            self.active.body_top = max(1.0, title_bottom - 1 - y)
            height += round(self.active.body_top - 1)
        x = max(4, min(x, parent.width() - width - 4))
        self.active.setGeometry(round(x), round(y), width, height)
        self.active.tail_y = max(4, min(height - 12, mouth_y - y))
        self.active.raise_()

    def clicked(self):
        w = self.window
        if w.journey.state != "home" or w.result or not w.exam:
            return
        if w.tabs.currentWidget() != w.practice:
            self.post(self.dialogue.quip() + "\nReturn to Practice for a hint.")
            return
        if self.armed == self.key():
            self.armed = None
            q = w.exam["questions"][w.current]
            self.post("Hint · " + question_hint(q, w.bank))
            w.history.save(
                w.exam,
                w.answers,
                w.elapsed(),
                ("hint", {"question_id": q["id"], "index": w.current}),
            )
        else:
            self.armed = self.key()
            self.post(self.dialogue.quip() + "\nClick Fable again for a hint.")

    def request_review(self):
        self.pending_review = True

    def question_changed(self):
        self.armed = None
        self.window.journey.talk_since = None
        self.hide_message()
        self.pending_review = bool(self.window.result)

    def reset(self):
        self.armed = None
        self.pending_review = False
        self.cache.clear()
        self.hide_message()
        self.window.journey.talk_since = None

    def tick(self):
        w = self.window
        if (
            self.pending_review
            and w.result
            and w.journey.state == "review"
            and not w.journey.sipping()
            and w.practice.isVisible()
        ):
            q = w.exam["questions"][w.current]
            key = self.key()
            if key not in self.cache:
                self.cache[key] = w.history.question_performance(q["id"], w.exam["id"])
            self.pending_review = False
            self.post(self.dialogue.review(self.cache[key]), review=True)
            return
        if not self.active:
            return
        self.position()
        # Floating overlays must not follow the user onto another tab.
        if self.active is self.review:
            self.active.setVisible(w.practice.isVisible())
        elapsed = self.now() - self.since
        if elapsed >= self.hold + self.fade_seconds:
            self.armed = None
            self.hide_message()
            return
        alpha = min(
            1.0,
            elapsed / 0.45,
            max(0.0, (self.hold + self.fade_seconds - elapsed) / self.fade_seconds),
        )
        self.active.opacity = alpha * alpha * (3 - 2 * alpha)
        self.active.elapsed = elapsed
        self.active.update()

    def shutdown(self):
        self.timer.stop()
        self.hide_message()
