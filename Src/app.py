from __future__ import annotations
import argparse, html, json, os, random, sys, time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, QRect
from PySide6.QtGui import (
    QDesktopServices,
    QIcon,
    QKeySequence,
    QShortcut,
    QFontDatabase,
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from engine import History, generate, grade
from dataset import Dataset, DatasetError
from settings import Settings, resources_directory
from widgets import AnswerChoice
from presentation import Feedback, display_answers
from player import Listening, clock

ROOT = resources_directory()


def configure_fonts(app):
    # Offscreen Qt on Windows cannot always enumerate installed fonts. Register the
    # installed family explicitly; these system font files are not redistributed.
    fontdir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ["segoeui.ttf", "segoeuib.ttf", "seguisym.ttf", "cambria.ttc"]:
        path = fontdir / name
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    app.setFont(QFont("Segoe UI", 11))


STYLE = """
QWidget {background:#111b29;color:#e2e9f3;font-family:"Segoe UI";font-size:11pt;}
QMainWindow {background:#0c1420;}
QLabel#title {font-size:23pt;font-weight:700;color:#f4f7fb;}
QLabel#brand {font-size:25pt;font-weight:750;color:#8ce0c7;}
QLabel#muted {color:#95a8bf;font-size:10pt;}
QLabel#prompt {font-size:16pt;font-weight:600;line-height:150%;}
QLabel#banner {padding:16px;background:#193a3b;border-radius:10px;color:#b6f1df;}
QFrame#card {background:#192638;border:1px solid #304258;border-radius:14px;}
QPushButton {background:#24364b;border:1px solid #3d536b;border-radius:7px;padding:9px 15px;font-weight:600;}
QPushButton:hover {background:#314b62;border-color:#8ce0c7;}
QPushButton:disabled {color:#718096;background:#1a2735;}
QPushButton#primary {background:#64c8ae;color:#102527;border-color:#64c8ae;}
QPushButton#primary:disabled {background:#243a3e;color:#71908c;border-color:#354c50;}
QPushButton#danger {color:#ffd3ab;border-color:#a26a44;}
QListWidget,QTextBrowser,QTextEdit,QTableWidget {background:#152131;border:1px solid #304258;border-radius:8px;padding:8px;}
QListWidget::item {padding:9px;border-radius:5px;}
QListWidget::item:selected {background:#2c4c59;color:#ffffff;}
QRadioButton {background:#203149;border:1px solid #3c506b;border-radius:8px;padding:13px;spacing:12px;}
QRadioButton:hover {border-color:#8ce0c7;}
QRadioButton:checked {background:#284c57;border:2px solid #8ce0c7;}
QRadioButton::indicator {width:17px;height:17px;}
QTabWidget::pane {border:0;}
QTabBar::tab {padding:13px 25px;background:#172536;color:#a7b9cc;}
QTabBar::tab:selected {background:#243c49;color:#a4f2d8;border-bottom:3px solid #8ce0c7;}
QComboBox,QSpinBox,QLineEdit {background:#213146;border:1px solid #3d526a;border-radius:6px;padding:7px;}
QComboBox QAbstractItemView {background:#213146;selection-background-color:#36605c;}
QProgressBar {background:#23354a;border:0;border-radius:5px;height:14px;text-align:center;}
QProgressBar::chunk {background:#64c8ae;border-radius:5px;}
QHeaderView::section {background:#24384e;color:#dbe8f5;padding:8px;border:0;}
QSlider::groove:horizontal {height:6px;background:#3a4a5c;}
QSlider::handle:horizontal {background:#8ce0c7;width:14px;margin:-5px 0;border-radius:6px;}
QTextEdit#transcript {font-size:14pt;padding:20px;selection-background-color:#4a3e70;}
QToolTip {background:#22394b;color:white;border:1px solid #8ce0c7;}
"""


def label(text, name=None):
    w = QLabel(text)
    w.setWordWrap(True)
    w.setTextFormat(Qt.PlainText)
    if name:
        w.setObjectName(name)
    return w


class Trainer(QMainWindow):
    def __init__(self, dataset, settings):
        super().__init__()
        self.settings = settings
        self.initialize_dataset(dataset)

    def initialize_dataset(self, dataset):
        self.dataset = dataset
        self.feedback = Feedback()
        self._fit_pending = False
        self.setWindowTitle("Proof Quest — " + dataset.title)
        self.resize(
            self.settings.get("window_width", 1240),
            self.settings.get("window_height", 860),
        )
        self.setMinimumSize(980, 700)
        self.setWindowIcon(QIcon(str(ROOT / "Assets" / "badge.svg")))
        self.bank = dataset.bank
        self.user_dir = self.settings.home / "Logs" / dataset.history_key
        self.history = History(self.user_dir / "practice.sqlite3")
        self.exam = None
        self.answers = {}
        self.result = None
        self.elapsed_base = 0
        self.started = 0
        self.read_only = False
        self.current = 0
        shell = QWidget()
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(20, 14, 20, 14)
        top = QHBoxLayout()
        mascot = QLabel()
        mascot.setPixmap(QIcon(str(ROOT / "Assets" / "badge.svg")).pixmap(60, 60))
        top.addWidget(mascot)
        brand = label("PROOF QUEST", "brand")
        top.addWidget(brand)
        top.addStretch()
        self.xp = label("A little logic. A lot less panic.", "muted")
        self.xp.setMinimumWidth(280)
        self.xp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self.xp)
        outer.addLayout(top)
        controls = QHBoxLayout()
        controls.addWidget(label(dataset.title, "muted"), 1)
        self.select_dataset_button = QPushButton("▣ Select new dataset")
        self.select_dataset_button.clicked.connect(self.select_dataset)
        self.help_button = QPushButton("? Help")
        self.help_button.clicked.connect(self.show_help)
        controls.addWidget(self.select_dataset_button)
        controls.addWidget(self.help_button)
        outer.addLayout(controls)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)
        self.setCentralWidget(shell)
        self.practice = QWidget()
        self.tabs.addTab(self.practice, "◈  Practice")
        self.build_practice()
        self.listen = Listening(dataset)
        self.tabs.addTab(self.listen, "♫  Listen + transcript")
        self.progress = QWidget()
        self.tabs.addTab(self.progress, "↗  Your progress")
        self.build_progress()
        self.tabs.currentChanged.connect(self.tab_changed)
        self.statusBar().showMessage(
            "Answers save automatically. Choose carefully; the owl is judging no one."
        )
        for i in range(5):
            shortcut = QShortcut(QKeySequence(str(i + 1)), self.practice)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda j=i: self.choose_key(j))
        self.next_shortcut = QShortcut(QKeySequence("Alt+Right"), self.practice)
        self.next_shortcut.activated.connect(self.next_question)
        self.save_timer = QTimer(self)
        self.save_timer.setInterval(3000)
        self.save_timer.timeout.connect(self.autosave)
        self.save_timer.start()
        self.restore_preferences()
        self.refresh_stats()
        pending = self.history.pending()
        if pending:
            self.exam, self.answers, self.elapsed_base = pending
            self.started = time.monotonic()
            self.read_only = False
            self.banner.setText(
                "Welcome back. Your unfinished run is exactly where you left it."
            )
            self.fill_sidebar()
            self.show_question(0)
        else:
            self.new_exam(initial=True)

    def build_practice(self):
        layout = QVBoxLayout(self.practice)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(14)
        config = QHBoxLayout()
        config.addWidget(label("Run"))
        self.mode = QComboBox()
        self.mode.addItems(
            [
                "Sprint · 12",
                "Balanced · 40",
                "Deep dive · 80",
                f'Full bank · {len(self.bank["questions"])}',
                "Weak-topic sprint · 20",
                "Custom",
            ]
        )
        self.mode.setCurrentIndex(1)
        config.addWidget(self.mode)
        self.count = QSpinBox()
        self.count.setRange(1, len(self.bank["questions"]))
        self.count.setValue(40)
        self.count.setKeyboardTracking(False)
        config.addWidget(self.count)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.count.valueChanged.connect(self.count_edited)
        config.addStretch()
        self.regenerate = QPushButton("↻ Regenerate test")
        self.regenerate.clicked.connect(self.new_exam)
        config.addWidget(self.regenerate)
        layout.addLayout(config)
        self.chapter_checks = []
        chapter_scroll = QScrollArea()
        chapter_scroll.setWidgetResizable(True)
        chapter_scroll.setMaximumHeight(
            min(100, 24 + 28 * ((len(self.dataset.chapters) + 3) // 4))
        )
        chapter_widget = QWidget()
        chapter_grid = QGridLayout(chapter_widget)
        for i, ch in enumerate(self.dataset.chapters):
            c = QCheckBox(ch["title"])
            c.setChecked(True)
            c.setProperty("chapter_id", ch["id"])
            c.setToolTip(ch["title"])
            self.chapter_checks.append(c)
            chapter_grid.addWidget(c, i // 4, i % 4)
        chapter_scroll.setWidget(chapter_widget)
        layout.addWidget(chapter_scroll)
        self.banner = label(
            "Pick a challenge. Every fresh run reshuffles the evidence.", "banner"
        )
        layout.addWidget(self.banner)
        split = QSplitter()
        layout.addWidget(split, 1)
        side = QWidget()
        side_l = QVBoxLayout(side)
        side_l.setContentsMargins(0, 0, 12, 0)
        self.completed = label("")
        side_l.addWidget(self.completed)
        self.bar = QProgressBar()
        side_l.addWidget(self.bar)
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(245)
        self.sidebar.setMaximumWidth(350)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.currentRowChanged.connect(self.show_question)
        side_l.addWidget(self.sidebar, 1)
        side_l.addWidget(
            label(
                "○ Not completed   ● Completed\nAfter grading: ✓ Correct   ✕ Missed",
                "muted",
            )
        )
        split.addWidget(side)
        self.stack = QStackedWidget()
        split.addWidget(self.stack)
        split.setStretchFactor(1, 1)
        scroll = QScrollArea()
        self.question_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        card = QWidget()
        self.question_card = card
        self.card_layout = QVBoxLayout(card)
        self.card_layout.setContentsMargins(18, 12, 18, 12)
        self.card_layout.setSpacing(9)
        self.meta = label("", "muted")
        self.card_layout.addWidget(self.meta)
        self.prompt = label("", "prompt")
        self.prompt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.card_layout.addWidget(self.prompt)
        self.card_layout.addSpacing(10)
        self.options = []
        self.group = QButtonGroup(self)
        for i in range(5):
            radio = AnswerChoice()
            radio.setMinimumHeight(44)
            self.options.append(radio)
            self.group.addButton(radio, i)
            self.card_layout.addWidget(radio)
        self.group.idClicked.connect(self.select_answer)
        self.explanation = label("", "banner")
        self.explanation.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.card_layout.addWidget(self.explanation)
        self.card_layout.addStretch()
        scroll.setWidget(card)
        self.stack.addWidget(scroll)
        self.report = QTextBrowser()
        self.report.setOpenExternalLinks(False)
        self.report.anchorClicked.connect(self.report_link)
        self.stack.addWidget(self.report)
        footer = QHBoxLayout()
        self.previous = QPushButton("← Previous")
        self.previous.clicked.connect(
            lambda: self.show_question(max(0, self.current - 1))
        )
        self.next = QPushButton("Next question →")
        self.next.clicked.connect(self.next_question)
        self.clear = QPushButton("Clear choice")
        self.clear.clicked.connect(self.clear_answer)
        self.all_results = QPushButton("View graded report")
        self.all_results.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.finish = QPushButton("⚑ Finish exam")
        self.finish.setObjectName("primary")
        self.finish.clicked.connect(self.finish_exam)
        for w in [self.previous, self.next, self.clear, self.all_results]:
            footer.addWidget(w)
        footer.addStretch()
        footer.addWidget(self.finish)
        layout.addLayout(footer)

    def mode_changed(self, index):
        values = [12, 40, 80, len(self.bank["questions"]), 20, self.count.value()]
        self.count.blockSignals(True)
        self.count.setValue(values[index])
        self.count.blockSignals(False)

    def count_edited(self, value):
        self.mode.blockSignals(True)
        self.mode.setCurrentIndex(5)
        self.mode.blockSignals(False)

    def elapsed(self):
        return self.elapsed_base + (
            time.monotonic() - self.started if self.started else 0
        )

    def autosave(self):
        if self.exam and not self.result and not self.read_only:
            self.history.save(self.exam, self.answers, self.elapsed())
        self.save_preferences()

    def new_exam(self, checked=False, initial=False):
        chapters = [
            c.property("chapter_id") for c in self.chapter_checks if c.isChecked()
        ]
        if not chapters:
            QMessageBox.information(
                self,
                "Choose a chapter",
                "Select at least one chapter for your next run.",
            )
            return
        if self.exam and not self.result and not initial:
            answer = QMessageBox.question(
                self,
                "Start a fresh run?",
                "Your current run will be saved as abandoned, including its questions and answers. Generate a new test?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
            self.history.finish(self.exam, self.answers, self.elapsed(), "abandoned")
        weaknesses = None
        if self.mode.currentIndex() == 4:
            stats, _ = self.history.stats()
            weaknesses = {
                k: 1 + 4 * (1 - v["right"] / v["total"]) for k, v in stats.items()
            }
        self.exam = generate(
            self.bank, self.count.value(), chapters, weaknesses=weaknesses
        )
        self.answers = {}
        self.result = None
        self.read_only = False
        self.elapsed_base = 0
        self.started = time.monotonic()
        self.exam["dataset_id"] = self.dataset.id
        self.exam["dataset_title"] = self.dataset.title
        self.history.begin(self.exam)
        self.fill_sidebar()
        self.show_question(0)
        self.banner.setText(
            f'{len(self.exam["questions"])} questions · One correct choice each · No hints until you finish. Small steps. Stronger recall.'
        )
        self.refresh_stats()

    def fill_sidebar(self):
        self.sidebar.blockSignals(True)
        self.sidebar.clear()
        for i, q in enumerate(self.exam["questions"]):
            status = "○"
            if self.result:
                status = "✓" if self.result["rows"][i]["correct"] else "✕"
            elif str(i) in self.answers:
                status = "●"
            item = QListWidgetItem(
                f'{status}  Question {i+1:02d} · {self.dataset.chapter_titles.get(q["chapter"],q["chapter"])}\n     {q["topic"]}'
            )
            item.setToolTip(q["prompt"])
            self.sidebar.addItem(item)
        self.sidebar.setCurrentRow(
            self.current if self.current < len(self.exam["questions"]) else 0
        )
        self.sidebar.blockSignals(False)
        self.completed.setText(
            f'{len(self.answers)} / {len(self.exam["questions"])} completed'
        )
        self.bar.setRange(0, len(self.exam["questions"]))
        self.bar.setValue(len(self.answers))

    def show_question(self, index):
        if not self.exam or not 0 <= index < len(self.exam["questions"]):
            return
        self.current = index
        q = self.exam["questions"][index]
        self.stack.setCurrentIndex(0)
        self.sidebar.blockSignals(True)
        self.sidebar.setCurrentRow(index)
        self.sidebar.blockSignals(False)
        self.meta.setText(
            f'QUESTION {index+1} OF {len(self.exam["questions"])}  ·  {self.dataset.chapter_titles.get(q["chapter"],q["chapter"])}  ·  § {q["source"]}'
        )
        self.prompt.setText(q["prompt"])
        self.group.setExclusive(False)
        pick = self.answers.get(str(index))
        answers = display_answers(
            [o["text"] for o in q["options"]], q.get("answer_format")
        )
        for j, (radio, opt) in enumerate(zip(self.options, q["options"])):
            radio.setText(f"{j+1}.  {answers[j]}")
            radio.setChecked(j == pick)
            radio.setEnabled(not self.result and not self.read_only)
            radio.setToolTip(answers[j])
            radio.setStyleSheet("")
            if self.result:
                if opt["correct"]:
                    radio.setStyleSheet(
                        "QRadioButton {background:#215044;color:#d5ffef;border:2px solid #80dfb5;} QRadioButton:disabled {color:#d5ffef;}"
                    )
                elif j == pick:
                    radio.setStyleSheet(
                        "QRadioButton {background:#542d3b;color:#ffd8df;border:2px solid #d97c91;} QRadioButton:disabled {color:#ffd8df;}"
                    )
        self.group.setExclusive(True)
        self.explanation.setVisible(bool(self.result))
        self.explanation.setStyleSheet("")
        if self.result:
            row = self.result["rows"][index]
            verdict = self.feedback.phrase((self.exam["id"], index), row["correct"])
            if row["unanswered"]:
                verdict = "Left unanswered. " + verdict
            self.explanation.setText(verdict + " " + q["explanation"])
            if not row["correct"]:
                self.explanation.setStyleSheet(
                    "QLabel {background:#542d3b;color:#ffd8df;border:1px solid #d97c91;border-radius:10px;padding:16px;}"
                )
        else:
            self.explanation.setText(q["explanation"])
        self.previous.setEnabled(index > 0)
        self.next.setEnabled(index < len(self.exam["questions"]) - 1)
        self.clear.setVisible(not self.result and not self.read_only)
        self.finish.setEnabled(not self.result and not self.read_only)
        self.all_results.setVisible(bool(self.result))
        if not self.result and not self.read_only:
            self.history.save(
                self.exam, self.answers, self.elapsed(), ("visit", {"index": index})
            )
        self.schedule_fit()

    def schedule_fit(self):
        if not self._fit_pending:
            self._fit_pending = True
            QTimer.singleShot(0, self.fit_question_height)

    def fit_question_height(self, available=None):
        self._fit_pending = False
        if (
            not self.isVisible()
            or self.isMaximized()
            or self.isFullScreen()
            or self.stack.currentIndex() != 0
            or self.tabs.currentWidget() != self.practice
        ):
            return
        screen = available or self.screen().availableGeometry()
        self.card_layout.invalidate()
        self.card_layout.activate()
        width = self.question_scroll.viewport().width()
        required = self.card_layout.totalHeightForWidth(width)
        if required < 0:
            required = self.card_layout.sizeHint().height()
        # Reserve room for the review notification even before the exam is graded.
        if not self.result:
            inner = max(100, width - 68)
            height = (
                self.explanation.fontMetrics()
                .boundingRect(
                    QRect(0, 0, inner, 100000),
                    Qt.TextWordWrap,
                    self.explanation.text() + " Here is the key distinction.",
                )
                .height()
            )
            required += height + 44
        needed = self.height() + max(
            0, required - self.question_scroll.viewport().height() + 4
        )
        frame_extra = max(0, self.frameGeometry().height() - self.height())
        limit = max(1, screen.height() - frame_extra)
        self.setMinimumHeight(min(700, limit))
        target = min(needed, limit)
        if target != self.height():
            self.resize(self.width(), target)
            top = max(
                screen.top(),
                min(
                    self.frameGeometry().top(),
                    screen.bottom() - self.frameGeometry().height() + 1,
                ),
            )
            self.move(self.x(), top)

    def showEvent(self, event):
        super().showEvent(event)
        self.schedule_fit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if (
            hasattr(self, "question_scroll")
            and event.size().width() != event.oldSize().width()
        ):
            self.schedule_fit()

    def select_answer(self, index):
        if self.result or self.read_only:
            return
        before = self.answers.get(str(self.current))
        self.answers[str(self.current)] = index
        self.history.save(
            self.exam,
            self.answers,
            self.elapsed(),
            ("answer", {"index": self.current, "previous": before, "selected": index}),
        )
        self.fill_sidebar()

    def choose_key(self, index):
        if (
            self.tabs.currentWidget() == self.practice
            and self.stack.currentIndex() == 0
            and not self.result
        ):
            self.options[index].click()

    def clear_answer(self):
        self.answers.pop(str(self.current), None)
        self.history.save(
            self.exam, self.answers, self.elapsed(), ("clear", {"index": self.current})
        )
        self.fill_sidebar()
        self.show_question(self.current)

    def next_question(self):
        self.show_question(min(len(self.exam["questions"]) - 1, self.current + 1))

    def finish_exam(self):
        missing = len(self.exam["questions"]) - len(self.answers)
        if (
            missing
            and QMessageBox.question(
                self,
                "Finish with unanswered questions?",
                f"{missing} questions are unanswered and will be marked incorrect. Finish now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        self.elapsed_base = self.elapsed()
        self.started = 0
        self.result = self.history.finish(self.exam, self.answers, self.elapsed_base)
        self.fill_sidebar()
        self.show_question(self.current)
        self.build_report()
        self.stack.setCurrentIndex(1)
        self.refresh_stats()
        n = self.result["total"]
        right = self.result["correct"]
        pct = round(100 * right / n)
        flavor = (
            "A proof well played."
            if pct >= 90
            else (
                "The induction is gaining momentum."
                if pct >= 65
                else "Counterexamples located. Now you know where to train."
            )
        )
        self.banner.setText(
            f"{right} correct · {n-right} to revisit · {pct}% · {flavor}"
        )

    def build_report(self):
        e = html.escape
        r = self.result
        parts = [
            f'<h1>{r["correct"]} / {r["total"]} correct</h1><p>Green is the correct answer. Select any question in the sidebar to inspect all five choices.</p>'
        ]
        for row, q in zip(r["rows"], self.exam["questions"]):
            answers = display_answers(
                [o["text"] for o in q["options"]], q.get("answer_format")
            )
            selected = (
                "Unanswered" if row["selected"] is None else answers[row["selected"]]
            )
            correct = answers[row["correct_index"]]
            parts.append(
                f'<h3><a style="color:#8ce0c7" href="q:{row["index"]}">{"✓" if row["correct"] else "✕"} {row["index"]+1}. {e(q["prompt"])}</a></h3>'
            )
            if not row["correct"]:
                parts.append(f'<p style="color:#ffb3c1">Your answer: {e(selected)}</p>')
            parts.append(
                f'<p style="background:#215044;color:#d5ffef;padding:8px">Correct: {e(correct)}</p>'
            )
            color = "#b6f1df" if row["correct"] else "#ffd8df"
            background = "#193a3b" if row["correct"] else "#542d3b"
            phrase = self.feedback.phrase(
                (self.exam["id"], row["index"]), row["correct"]
            )
            parts.append(
                f'<p style="color:{color};background:{background};padding:12px">{e(phrase)} {e(q["explanation"])}</p><p style="color:#8ca2bc">Source {e(q["source"])} · {e(q["topic"])}</p><hr>'
            )
        self.report.setHtml("".join(parts))

    def report_link(self, url):
        if url.scheme() == "q":
            self.show_question(int(url.path()))

    def build_progress(self):
        layout = QVBoxLayout(self.progress)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addWidget(label("Your evidence board", "title"))
        self.stats_label = label("")
        layout.addWidget(self.stats_label)
        layout.addWidget(
            label(
                "Topic accuracy · unanswered questions count as misses · completed runs only",
                "muted",
            )
        )
        self.topic_table = QTableWidget(0, 4)
        self.topic_table.setHorizontalHeaderLabels(
            ["Topic", "Correct / seen", "Accuracy", "Practice suggestion"]
        )
        self.topic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.topic_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.topic_table, 1)
        layout.addWidget(
            label(
                "Run history · double-click a row to review its exact questions and choices",
                "muted",
            )
        )
        self.run_table = QTableWidget(0, 4)
        self.run_table.setHorizontalHeaderLabels(
            ["Started (local time)", "Status", "Score", "Time"]
        )
        self.run_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.run_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.run_table.cellDoubleClicked.connect(self.open_history)
        layout.addWidget(self.run_table, 1)
        actions = QHBoxLayout()
        export = QPushButton("Export all runs as JSONL")
        export.clicked.connect(self.export)
        folder = QPushButton("Open log folder")
        folder.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self.user_dir.resolve()))
            )
        )
        actions.addWidget(export)
        actions.addWidget(folder)
        actions.addStretch()
        layout.addLayout(actions)

    def refresh_stats(self):
        from datetime import datetime

        stats, runs = self.history.stats()
        total = sum(r["result"]["total"] for r in runs)
        right = sum(r["result"]["correct"] for r in runs)
        xp = right * 10 + len(runs) * 20
        level = 1 + xp // 250
        self.xp.setText(f"Level {level} · {xp:,} XP · {len(runs)} finished runs")
        self.stats_label.setText(
            f"{len(runs)} completed runs · {right}/{total} correct · "
            + (
                f"{100*right/total:.0f}% overall"
                if total
                else "Your first run starts the story."
            )
        )
        all_topics = sorted(
            set(q["topic"] for q in self.bank["questions"]),
            key=lambda t: stats.get(t, {"right": 0, "total": 1})["right"]
            / max(1, stats.get(t, {"total": 0})["total"]),
        )
        self.topic_table.setRowCount(len(all_topics))
        for i, t in enumerate(all_topics):
            s = stats.get(t, {"right": 0, "total": 0})
            acc = s["right"] / s["total"] if s["total"] else None
            suggestion = (
                "Unexplored"
                if acc is None
                else (
                    "Small sample — keep exploring"
                    if s["total"] < 5
                    else "Revisit this topic" if acc < 0.75 else "Keep it warm"
                )
            )
            for j, v in enumerate(
                [
                    t,
                    f'{s["right"]} / {s["total"]}',
                    f"{acc:.0%}" if acc is not None else "—",
                    suggestion,
                ]
            ):
                self.topic_table.setItem(i, j, QTableWidgetItem(v))
        self.history_rows = self.history.runs()
        self.run_table.setRowCount(len(self.history_rows))
        for i, r in enumerate(self.history_rows):
            score = (
                f'{r["result"]["correct"]}/{r["result"]["total"]}'
                if r["result"]
                else "In progress"
            )
            values = [
                datetime.fromisoformat(r["created"])
                .astimezone()
                .strftime("%b %d  %H:%M"),
                r["status"].replace("_", " "),
                score,
                clock(r["seconds"] * 1000),
            ]
            for j, v in enumerate(values):
                self.run_table.setItem(i, j, QTableWidgetItem(v))

    def tab_changed(self, index):
        if index == 2:
            self.autosave()
            self.refresh_stats()
        if index != 1:
            self.listen.player.pause()

    def open_history(self, row, column):
        r = self.history_rows[row]
        if r["status"] == "in_progress":
            self.tabs.setCurrentIndex(0)
            return
        # Review in a separate read-only dialog: the active exam continues untouched.
        exam, answers, seconds, result = self.history.review(r["id"])
        result = result or grade(exam, answers)
        dialog = QDialog(self)
        dialog.setWindowTitle("Saved run · exact question set")
        dialog.resize(950, 720)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        layout.addWidget(browser)
        e = html.escape
        parts = [f'<h1>{result["correct"]}/{result["total"]} · {e(r["status"])}</h1>']
        for item, q in zip(result["rows"], exam["questions"]):
            answers = display_answers(
                [o["text"] for o in q["options"]], q.get("answer_format")
            )
            parts.append(f'<h3>{item["index"]+1}. {e(q["prompt"])}</h3>')
            for j, opt in enumerate(q["options"]):
                color = (
                    "#8ce0c7"
                    if opt["correct"]
                    else "#ffb3c1" if item["selected"] == j else "#bbc9dc"
                )
                parts.append(
                    f'<p style="color:{color}">{"✓ " if opt["correct"] else ""}{"[selected] " if item["selected"]==j else ""}{e(answers[j])}</p>'
                )
            color = "#b6f1df" if item["correct"] else "#ffd8df"
            parts.append(f'<p style="color:{color}">{e(q["explanation"])}</p><hr>')
        browser.setHtml("".join(parts))
        dialog.exec()

    def export(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export practice history",
            str(self.user_dir / "practice_export.jsonl"),
            "JSON Lines (*.jsonl)",
        )
        if path:
            self.autosave()
            self.history.export(path)
            self.statusBar().showMessage("History exported: " + path, 10000)

    def save_preferences(self):
        self.settings.set("window_width", self.width())
        self.settings.set("window_height", self.height())
        self.settings.set("mode", self.mode.currentIndex())
        self.settings.set("question_count", self.count.value())
        self.settings.set(
            "chapters_" + self.dataset.history_key,
            [c.property("chapter_id") for c in self.chapter_checks if c.isChecked()],
        )
        self.settings.set("volume", self.listen.volume.value())
        self.settings.set("audio_output", self.listen.preferred_output)
        self.settings.set("playback_rate", self.listen.rate.currentData())
        self.settings.set("follow_narration", self.listen.follow.isChecked())
        self.settings.set(
            "audio_position_" + self.dataset.history_key, self.listen.player.position()
        )
        self.settings.save()

    def restore_preferences(self):
        mode = self.settings.get("mode", 1)
        self.mode.setCurrentIndex(
            mode if isinstance(mode, int) and 0 <= mode < 6 else 1
        )
        if self.mode.currentIndex() == 5:
            self.count.setValue(self.settings.get("question_count", 40))
        selected = self.settings.get(
            "chapters_" + self.dataset.history_key, list(self.dataset.chapter_titles)
        )
        for c in self.chapter_checks:
            c.setChecked(c.property("chapter_id") in selected)
        if not any(c.isChecked() for c in self.chapter_checks):
            for c in self.chapter_checks:
                c.setChecked(True)
        self.listen.volume.setValue(self.settings.get("volume", 75))
        self.listen.restore_output(self.settings.get("audio_output", "system"))
        rate = self.listen.rate.findData(self.settings.get("playback_rate", 1))
        self.listen.rate.setCurrentIndex(max(0, rate))
        self.listen.player.setPlaybackRate(self.listen.rate.currentData())
        self.listen.follow.setChecked(self.settings.get("follow_narration", True))
        self.listen.resume_position = self.settings.get(
            "audio_position_" + self.dataset.history_key, 0
        )

    def select_dataset(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a dataset manifest",
            str(self.dataset.root),
            "Dataset manifest (*.json)",
        )
        if path:
            self.switch_dataset(path)

    def switch_dataset(self, path):
        try:
            replacement = Dataset(path)
            self.autosave()
            self.settings.select_dataset(replacement.path)
        except (DatasetError, OSError, ValueError) as error:
            QMessageBox.warning(self, "Dataset could not be opened", str(error))
            return False
        self.save_timer.stop()
        self.save_timer.deleteLater()
        self.listen.shutdown()
        self.history.close()
        previous = self.takeCentralWidget()
        previous.deleteLater()
        self.initialize_dataset(replacement)
        return True

    def show_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Proof Quest help")
        dialog.resize(850, 680)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setOpenExternalLinks(False)
        text.setMarkdown((ROOT / "Docs" / "User-Guide.md").read_text(encoding="utf-8"))
        layout.addWidget(text)
        close = QPushButton("Got it")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    def closeEvent(self, event):
        try:
            self.autosave()
        except OSError as error:
            QMessageBox.warning(self, "Settings could not be saved", str(error))
        self.save_timer.stop()
        self.listen.shutdown()
        self.history.close()
        event.accept()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path)
    parser.add_argument(
        "--home", type=Path, help="Override portable settings/log directory for testing"
    )
    parser.add_argument(
        "--smoke-test",
        type=Path,
        help="Write a scripted executable validation receipt and exit",
    )
    parser.add_argument(
        "--audible-audio",
        action="store_true",
        help="Play the audio segment aloud during an explicit smoke test",
    )
    args = parser.parse_args()
    app = QApplication(sys.argv)
    configure_fonts(app)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    try:
        settings = Settings(args.home)
        path = (
            args.dataset
            or settings.dataset_path()
            or ROOT / "Examples" / "Demo" / "dataset.json"
        )
        while True:
            try:
                dataset = Dataset(path)
                break
            except DatasetError as error:
                if args.smoke_test:
                    raise
                QMessageBox.warning(None, "Select a valid dataset", str(error))
                chosen, _ = QFileDialog.getOpenFileName(
                    None,
                    "Locate a dataset manifest",
                    str(settings.home),
                    "Dataset manifest (*.json)",
                )
                if not chosen:
                    return 1
                path = Path(chosen)
        settings.select_dataset(dataset.path)
        window = Trainer(dataset, settings)
    except (OSError, ValueError) as error:
        QMessageBox.critical(
            None,
            "Proof Quest could not start",
            str(error)
            + "\nSelect a valid dataset with --dataset or correct proofquest.ini.",
        )
        return 1
    window.show()
    if args.smoke_test:
        from smoke import run_smoke

        QTimer.singleShot(
            500,
            lambda: run_smoke(window, args.smoke_test, app, audible=args.audible_audio),
        )
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
