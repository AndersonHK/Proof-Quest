"""Audio playback uses the media clock and service word timestamps, never guessed WPM."""

import bisect, json, os, sys

# Qt 6.8's FFmpeg resampler rejects some Windows headset channel masks and can
# advance the clock while emitting silence. Native WMF playback avoids that path.
# This changes this process only and leaves an explicit developer override intact.
if sys.platform == "win32":
    os.environ.setdefault("QT_MEDIA_BACKEND", "windows")
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QShortcut,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QMediaDevices
from widgets import JumpSlider
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def clock(ms):
    s = max(0, int(ms) // 1000)
    return f"{s//60:02d}:{s%60:02d}"


class Transcript(QTextEdit):
    clicked = Signal(int)

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setObjectName("transcript")

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and not self.textCursor().hasSelection():
            self.clicked.emit(
                self.cursorForPosition(event.position().toPoint()).position()
            )


class Listening(QWidget):
    def __init__(self, dataset):
        super().__init__()
        self.dataset = dataset
        self.resume_position = 0
        self.last_index = None
        self.search_cursor = -1
        self.match = None
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.75)
        self.audio.setMuted(False)
        self.devices = QMediaDevices(self)
        self.preferred_output = "system"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        heading = QLabel(dataset.title + " · listening guide")
        heading.setObjectName("title")
        layout.addWidget(heading)
        self.note = QLabel(
            "One idea at a time. Click any word to replay its sentence. Ctrl+F finds and jumps."
        )
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        controls = QHBoxLayout()
        self.play = QPushButton("▶ Play")
        self.play.setObjectName("primary")
        self.play.clicked.connect(self.toggle)
        back = QPushButton("↶ 10 s")
        back.clicked.connect(lambda: self.seek(self.player.position() - 10000))
        forward = QPushButton("10 s ↷")
        forward.clicked.connect(lambda: self.seek(self.player.position() + 10000))
        self.chapter = QComboBox()
        self.chapter.setMinimumWidth(260)
        self.rate = QComboBox()
        for speed in [0.75, 1, 1.1, 1.25, 1.5, 1.75, 2]:
            self.rate.addItem(f"{speed:g}×", speed)
        self.rate.setCurrentIndex(1)
        self.rate.activated.connect(
            lambda: self.player.setPlaybackRate(self.rate.currentData())
        )
        self.volume = JumpSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(75)
        self.volume.setFixedWidth(110)
        self.volume.valueChanged.connect(self.set_volume)
        for w in [
            self.play,
            back,
            forward,
            self.chapter,
            self.rate,
            QLabel("Volume"),
            self.volume,
        ]:
            controls.addWidget(w)
        controls.addStretch()
        layout.addLayout(controls)
        routing = QHBoxLayout()
        routing.addWidget(QLabel("Audio output"))
        self.output = QComboBox()
        self.output.setMinimumWidth(300)
        self.output.activated.connect(self.choose_output)
        routing.addWidget(self.output, 1)
        self.output_status = QLabel("")
        routing.addWidget(self.output_status)
        layout.addLayout(routing)
        self.devices.audioOutputsChanged.connect(self.refresh_outputs)
        self.refresh_outputs()
        timeline = QHBoxLayout()
        self.time = QLabel("00:00 / 00:00")
        self.time.setMinimumWidth(130)
        self.slider = JumpSlider(Qt.Horizontal)
        self.slider.valueCommitted.connect(self.seek)
        self.slider.setSingleStep(5000)
        self.slider.setPageStep(30000)
        timeline.addWidget(self.time)
        timeline.addWidget(self.slider)
        layout.addLayout(timeline)
        search = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find in transcript (Ctrl+F)")
        self.search.returnPressed.connect(lambda: self.find_match(1))
        self.search.textEdited.connect(self.reset_search)
        prev = QPushButton("Previous match")
        prev.clicked.connect(lambda: self.find_match(-1))
        nxt = QPushButton("Next match")
        nxt.clicked.connect(lambda: self.find_match(1))
        self.match_label = QLabel("")
        self.follow = QCheckBox("Follow narration")
        self.follow.setChecked(True)
        for w in [self.search, prev, nxt, self.match_label, self.follow]:
            search.addWidget(w)
        layout.addLayout(search)
        self.text = Transcript()
        self.text.clicked.connect(self.jump_to_char)
        layout.addWidget(self.text, 1)
        self.shortcut = QShortcut(QKeySequence.Find, self)
        self.shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut.activated.connect(self.focus_find)
        self.space = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.space.activated.connect(self.toggle)
        self.data = None
        if dataset.timings is not None:
            self.data = dataset.timings
            self.prepare_transcript()
            self.player.setSource(QUrl.fromLocalFile(str(dataset.audio_path)))
            self.slider.setRange(0, self.data["duration_ms"])
            for s in self.data.get("sections", []):
                self.chapter.addItem(s["title"], s["start_ms"])
            self.chapter.setEnabled(self.chapter.count() > 0)
            self.chapter.activated.connect(
                lambda: self.seek(self.chapter.currentData())
            )
            self.note.setText(
                f"{self.data.get('voice','Audio')} · {clock(self.data['duration_ms'])} at 1× · Click a word to replay its sentence. Ctrl+F finds and jumps."
            )
        else:
            self.note.setText(
                "This dataset has no listening guide. Practice and progress are ready to use."
            )
            self.play.setEnabled(False)
            self.chapter.setEnabled(False)
        self.player.mediaStatusChanged.connect(self.media_ready)
        self.player.playbackStateChanged.connect(
            lambda: self.play.setText(
                "Ⅱ Pause" if self.player.isPlaying() else "▶ Play"
            )
        )
        self.player.errorOccurred.connect(
            lambda *args: self.note.setText(
                "Playback error: " + self.player.errorString()
            )
        )
        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def prepare_transcript(self):
        self.word_ranges = []
        pieces = []
        offset = 0
        self.sentence_offsets = []
        for s in self.data["sentences"]:
            segment = self.data["text"][s["start"] : s["end"]]
            self.sentence_offsets.append(offset)
            pieces.append(segment)
            offset += len(segment) + 1
        self.display = "\n".join(pieces)
        self.text.setPlainText(self.display)
        cursor = QTextCursor(self.text.document())
        cursor.select(QTextCursor.Document)
        block = QTextBlockFormat()
        block.setLineHeight(130, QTextBlockFormat.ProportionalHeight.value)
        block.setBottomMargin(4)
        cursor.mergeBlockFormat(block)
        for w in self.data["words"]:
            s = self.data["sentences"][w["sentence"]]
            base = self.sentence_offsets[w["sentence"]]
            self.word_ranges.append(
                (base + w["start"] - s["start"], base + w["end"] - s["start"])
            )
        # Qt cursor positions count UTF-16 units; dataset offsets count Unicode code points.
        self.to_qt = [0]
        for char in self.display:
            self.to_qt.append(self.to_qt[-1] + (2 if ord(char) > 0xFFFF else 1))
        self.word_ranges = [(self.to_qt[a], self.to_qt[b]) for a, b in self.word_ranges]
        self.sentence_offsets = [self.to_qt[p] for p in self.sentence_offsets]
        self.word_chars = [x[0] for x in self.word_ranges]
        self.word_times = [w["start_ms"] for w in self.data["words"]]

    def media_ready(self, status):
        if (
            status in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia)
            and self.resume_position
        ):
            position = self.resume_position
            self.resume_position = 0
            self.seek(position)

    def toggle(self):
        if not self.data:
            return
        if self.player.isPlaying():
            self.player.pause()
        else:
            self.refresh_outputs()
            if self.audio.device().isNull():
                self.output_status.setText(
                    "No output device available. Connect speakers or headphones."
                )
                return
            self.audio.setMuted(False)
            self.audio.setVolume(self.volume.value() / 100)
            self.player.play()

    def set_volume(self, value):
        self.audio.setMuted(False)
        self.audio.setVolume(value / 100)
        if hasattr(self, "output_status"):
            self.output_status.setText("Volume is zero" if value == 0 else "")

    def choose_output(self, index):
        self.preferred_output = self.output.itemData(index) or "system"
        self.apply_output()

    def restore_output(self, identifier):
        self.preferred_output = identifier
        self.refresh_outputs()

    def refresh_outputs(self):
        available = QMediaDevices.audioOutputs()
        default = QMediaDevices.defaultAudioOutput()
        self.output.blockSignals(True)
        self.output.clear()
        self.output.addItem(
            "System default — " + (default.description() or "unavailable"), "system"
        )
        for device in available:
            self.output.addItem(device.description(), bytes(device.id()).hex())
        selected = self.output.findData(self.preferred_output)
        if selected < 0:
            self.preferred_output = "system"
            selected = 0
            self.output_status.setText(
                "Previous device unavailable; using system default."
            )
        self.output.setCurrentIndex(selected)
        self.output.blockSignals(False)
        self.apply_output()

    def apply_output(self):
        device = QMediaDevices.defaultAudioOutput()
        if self.preferred_output != "system":
            device = next(
                (
                    d
                    for d in QMediaDevices.audioOutputs()
                    if bytes(d.id()).hex() == self.preferred_output
                ),
                device,
            )
        if self.audio.device() != device:
            self.audio.setDevice(device)
        if device.isNull():
            self.output_status.setText("No output device available.")

    def seek(self, ms):
        if not self.data:
            return
        ms = max(0, min(int(ms), self.data["duration_ms"]))
        self.player.setPosition(ms)
        self.last_index = None
        self.tick(ms)

    def jump_to_char(self, pos):
        if not self.data:
            return
        i = max(0, bisect.bisect_right(self.word_chars, pos) - 1)
        sentence = self.data["sentences"][self.data["words"][i]["sentence"]]
        self.seek(sentence["start_ms"])
        # A click always reveals the chosen sentence, even when auto-follow is off.
        cursor = self.text.textCursor()
        cursor.setPosition(self.sentence_offsets[self.data["words"][i]["sentence"]])
        self.text.setTextCursor(cursor)
        self.text.ensureCursorVisible()

    def focus_find(self):
        self.search.setFocus()
        self.search.selectAll()

    def reset_search(self):
        self.search_cursor = -1
        self.match = None
        self.match_label.clear()
        self.last_index = None

    def find_match(self, direction):
        if not self.data:
            return
        needle = self.search.text().strip()
        if not needle:
            return
        import re

        matches = [
            m.start()
            for m in re.finditer(re.escape(needle), self.display, re.IGNORECASE)
        ]
        if not matches:
            self.match_label.setText("No matches")
            return
        if direction > 0:
            chosen = next((p for p in matches if p > self.search_cursor), matches[0])
        else:
            chosen = next(
                (p for p in reversed(matches) if p < self.search_cursor), matches[-1]
            )
        self.search_cursor = chosen
        self.match = (self.to_qt[chosen], self.to_qt[chosen + len(needle)])
        self.match_label.setText(f"{matches.index(chosen)+1} / {len(matches)}")
        self.jump_to_char(self.to_qt[chosen])

    def selection(self, start, end, background, foreground=None):
        sel = QTextEdit.ExtraSelection()
        sel.cursor = QTextCursor(self.text.document())
        sel.cursor.setPosition(start)
        sel.cursor.setPosition(end, QTextCursor.KeepAnchor)
        sel.format.setBackground(QColor(background))
        if foreground:
            sel.format.setForeground(QColor(foreground))
        return sel

    def tick(self, position=None):
        if not self.data:
            return
        ms = self.player.position() if position is None else position
        if not self.slider.isSliderDown():
            self.slider.setValue(ms)
        self.time.setText(f'{clock(ms)} / {clock(self.data["duration_ms"])}')
        ch = max(
            0,
            bisect.bisect_right(
                [s["start_ms"] for s in self.data.get("sections", [])], ms
            )
            - 1,
        )
        self.chapter.setCurrentIndex(ch)
        i = bisect.bisect_right(self.word_times, ms) - 1
        active = i >= 0 and ms < self.data["words"][i]["end_ms"]
        key = (i, active, self.match)
        if key == self.last_index:
            return
        self.last_index = key
        selections = []
        if i >= 0:
            start, end = self.word_ranges[i]
            selections.append(
                self.selection(0, start if active else end, "#3b2856", "#eddefa")
            )
            if active:
                selections.append(self.selection(start, end, "#f3ce8c", "#241733"))
            if self.follow.isChecked() and not self.search.hasFocus():
                c = self.text.textCursor()
                c.setPosition(start)
                self.text.setTextCursor(c)
                self.text.ensureCursorVisible()
                y = self.text.cursorRect().top()
                h = self.text.viewport().height()
                if y > h * 0.65 or y < h * 0.15:
                    bar = self.text.verticalScrollBar()
                    bar.setValue(bar.value() + int(y - h * 0.4))
        if self.match:
            selections.append(self.selection(*self.match, "#684589", "#fff5e5"))
        self.text.setExtraSelections(selections)

    def shutdown(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.timer.stop()
