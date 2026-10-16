"""Answer controls wrap arbitrary Unicode text without truncating fixture content."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSizePolicy,
    QSlider,
    QStyle,
    QStyleOptionSlider,
)


class JumpSlider(QSlider):
    """A track click sets the exact value; handle dragging and keys remain native."""

    valueCommitted = Signal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self._jump_drag = False

    def value_at(self, position):
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        handle = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
        )
        groove = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self
        )
        if self.orientation() == Qt.Horizontal:
            span = groove.width() - handle.width()
            pos = position.x() - handle.width() / 2 - groove.x()
        else:
            span = groove.height() - handle.height()
            pos = position.y() - handle.height() / 2 - groove.y()
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), round(pos), max(1, span), option.upsideDown
        )

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        handle = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
        )
        if handle.contains(event.position().toPoint()):
            return super().mousePressEvent(event)
        self._jump_drag = True
        self.setSliderDown(True)
        self.setValue(self.value_at(event.position()))
        event.accept()

    def mouseMoveEvent(self, event):
        if self._jump_drag:
            self.setValue(self.value_at(event.position()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_down = self.isSliderDown()
        if self._jump_drag and event.button() == Qt.LeftButton:
            self.setValue(self.value_at(event.position()))
            self._jump_drag = False
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
        if was_down:
            self.valueCommitted.emit(self.value())

    def keyPressEvent(self, event):
        before = self.value()
        super().keyPressEvent(event)
        if self.value() != before:
            self.valueCommitted.emit(self.value())


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
