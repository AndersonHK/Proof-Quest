"""Monotonic active time, independent of the selected tab and wall-clock dates."""

import time


class ExamTimer:
    def __init__(self, now=time.monotonic):
        self.now = now
        self.focused = False
        self.reset()

    def reset(self, seconds=0, paused=False):
        self.total = float(seconds)
        self.state = "paused" if paused else "waiting"
        self.since = None

    @property
    def running(self):
        return self.state == "running" and self.focused

    def elapsed(self):
        return self.total + (self.now() - self.since if self.since is not None else 0)

    def transition(self, state=None, focused=None):
        self.total = self.elapsed()
        if state is not None:
            self.state = state
        if focused is not None:
            self.focused = focused
        self.since = self.now() if self.running else None

    def activity(self):
        if self.state == "waiting":
            self.transition("running")

    def toggle(self):
        if self.state != "finished":
            self.transition("paused" if self.running else "running")

    def finish(self):
        self.transition("finished")


def duration_text(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"
