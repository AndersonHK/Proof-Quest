"""Event-driven mascot choreography; decorative layers never consume exam input."""

import math
import random
import time
from PySide6.QtCore import QObject, QPoint, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class Confetti(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")
        rng = random.Random(824)
        # Small symmetric bursts, nominally 30 degrees above horizontal.
        self.particles = [
            (
                side,
                rng.uniform(23, 37),
                rng.uniform(240, 390),
                rng.uniform(0, 0.16),
                rng.randrange(4),
                rng.uniform(-200, 200),
            )
            for side in (-1, 1)
            for _ in range(18)
        ]
        self.elapsed = None
        self.hide()

    def paintEvent(self, event):
        if self.elapsed is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = ["#b79aff", "#fff0cf", "#f3b8d4", "#d5c4ff"]
        for side, angle, speed, delay, color, spin in self.particles:
            t = self.elapsed - delay
            if not 0 <= t <= 1.55:
                continue
            radians = math.radians(angle)
            x = speed * math.cos(radians) * t
            if side == 1:
                x = self.width() - x
            y = self.height() * 0.42 - speed * math.sin(radians) * t + 120 * t * t
            painter.save()
            painter.setOpacity(min(1, max(0, (1.55 - t) / 0.45)))
            painter.translate(x, y)
            painter.rotate(spin * t)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(palette[color]))
            painter.drawRoundedRect(-3, -2, 6, 4, 1, 1)
            painter.restore()


class FableJourney(QObject):
    DURATIONS = {
        "celebrate": 1.8,
        "exit_left": 0.65,
        "enter_review": 0.85,
        "exit_right": 0.85,
        "enter_home": 0.65,
    }

    def __init__(self, shell, mascot, home, review, practice, now=time.monotonic):
        super().__init__(shell)
        self.shell, self.mascot = shell, mascot
        self.home, self.review, self.practice = home, review, practice
        self.now = now
        self.state = "home"
        self.since = now()
        self.sip_since = None
        self.blink_since = None
        self.return_start = None
        self.return_mug = True
        self.effects = Confetti(shell)
        mascot.setParent(shell)
        mascot.clicked.connect(self.clicked)
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.tick()

    def point(self, anchor):
        return QPointF(anchor.mapTo(self.shell, QPoint(0, 0)))

    def begin(self, state, at=None):
        self.state = state
        self.since = self.now() if at is None else at

    def answer_selected(self):
        # Deliberately independent of correctness; no hints before grading.
        if self.state == "home":
            self.mascot.check_in()

    def finished(self, personal_best):
        if self.state != "home":
            return
        self.review.show()
        self.sip_since = None
        self.mascot.reaction = None
        self.begin("celebrate" if personal_best else "exit_left")
        self.tick()

    def question_changed(self):
        if self.state == "review":
            if self.sip_since is None or self.now() - self.sip_since >= 1.5:
                self.sip_since = self.now()
            self.tick()

    def clicked(self):
        if self.state == "home":
            self.mascot.check_in()
        elif self.state == "review":
            # Finish an active sip before blinking; keep the mug in both poses.
            self.blink_since = max(self.now(), (self.sip_since or 0) + 1.5)
            self.tick()

    def regenerated(self):
        if self.state == "home":
            self.mascot.reaction = None
            return
        self.return_start = QPointF(self.mascot.pos())
        self.return_mug = self.state in ("enter_review", "review", "exit_right")
        self.effects.hide()
        self.sip_since = None
        self.blink_since = None
        self.begin("exit_right")
        self.tick()

    @staticmethod
    def interpolate(a, b, t):
        t = max(0, min(1, t))
        return a + (b - a) * t

    def tick(self):
        now = self.now()
        while (
            self.state in self.DURATIONS
            and now - self.since >= self.DURATIONS[self.state]
        ):
            at = self.since + self.DURATIONS[self.state]
            next_state = {
                "celebrate": "exit_left",
                "exit_left": "enter_review",
                "enter_review": "review",
                "exit_right": "enter_home",
                "enter_home": "home",
            }[self.state]
            self.begin(next_state, at)
            if next_state == "home":
                self.review.hide()
        t = now - self.since
        fox = self.mascot
        fox.pose_override, fox.flip, fox.lift, fox.squash = None, False, 0, 1
        home, review = self.point(self.home), self.point(self.review)
        position = home
        walk = int(t * 12) % 4
        right = QPointF(self.shell.width() + 4, review.y())
        left = QPointF(-fox.width() - 4, home.y())
        if self.state == "celebrate":
            # Anticipation, two happy hops, then settle before leaving.
            fox.pose_override = (
                "ready"
                if t < 0.2
                else (
                    "cheer"
                    if t < 0.4
                    else "hooray" if t < 1.3 else "cheer" if t < 1.5 else "ready"
                )
            )
            fox.lift = (
                7 * abs(math.sin(max(0, min(1, (t - 0.2) / 1.1)) * math.tau))
                if t < 1.3
                else 0
            )
            fox.squash = 0.96 if t < 0.2 else 1.0
        elif self.state == "exit_left":
            position = self.interpolate(home, left, t / 0.65)
            fox.pose_override = f"walk{walk}"
        elif self.state == "enter_review":
            position = self.interpolate(right, review, t / 0.85)
            fox.pose_override = f"carry{walk}"
        elif self.state == "review":
            position = review
            sip = None if self.sip_since is None else now - self.sip_since
            fox.pose_override = "mug"
            if sip is not None and 0 <= sip < 1.5:
                fox.pose_override = (
                    "lift"
                    if sip < 0.2
                    else "sip" if sip < 0.85 else "lift" if sip < 1.05 else "content"
                )
                fox.lift = 0.8 * math.sin(sip * math.pi / 1.5)
            elif self.blink_since is not None and 0 <= now - self.blink_since < 0.3:
                fox.pose_override = "content"
            elif int(t * 10) % 68 == 0:
                fox.pose_override = "content"
        elif self.state == "exit_right":
            origin = self.return_start if self.return_start is not None else review
            position = self.interpolate(
                origin, QPointF(self.shell.width() + 4, origin.y()), t / 0.85
            )
            fox.pose_override = f"{'carry' if self.return_mug else 'walk'}{walk}"
            fox.flip = True
        elif self.state == "enter_home":
            position = self.interpolate(left, home, t / 0.65)
            fox.pose_override = f"walk{walk}"
            fox.flip = True
        if self.state in ("exit_left", "enter_review", "exit_right", "enter_home"):
            fox.lift = 1.3 * abs(math.sin(t * math.tau * 6))
        # Review poses belong to Practice; never float over the transcript.
        visible = self.shell.isVisible() and (
            self.state == "home" or self.practice.isVisible()
        )
        fox.setVisible(visible)
        fox.move(position.toPoint())
        fox.raise_()
        fox.update()
        self.effects.setGeometry(self.shell.rect())
        self.effects.elapsed = t if self.state == "celebrate" else None
        self.effects.setVisible(visible and self.state == "celebrate")
        if self.state == "celebrate":
            self.effects.raise_()
            self.effects.update()

    def shutdown(self):
        self.timer.stop()
        self.effects.hide()
        self.mascot.shutdown()
