"""Answer controls wrap arbitrary Unicode text without truncating fixture content."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QRadioButton, QSizePolicy


class AnswerChoice(QRadioButton):
    def __init__(self):
        super().__init__()
        self.caption = QLabel()
        self.caption.setWordWrap(True)
        self.caption.setTextFormat(Qt.PlainText)
        self.caption.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.caption.setStyleSheet("background:transparent;border:0;padding:0;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(38, 8, 15, 8)
        layout.addWidget(self.caption)
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def setText(self, text):
        self.caption.setText(text)
        self.setAccessibleName(text)
        self.updateGeometry()

    def text(self):
        return self.caption.text()

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return max(44, self.layout().totalHeightForWidth(width))

    def sizeHint(self):
        return QSize(350, self.heightForWidth(600))

    def minimumSizeHint(self):
        return QSize(100, 44)
