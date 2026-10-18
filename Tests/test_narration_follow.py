import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QAbstractSlider
from dataset import Dataset
from player import Listening


@pytest.mark.parametrize("gesture", ["wheel", "keyboard", "scrollbar", "drag"])
def test_manual_browsing_pauses_follow_until_sync(qt, make_dataset, gesture):
    view = Listening(Dataset(make_dataset(audio=True)))
    try:
        view.resize(1200, 650)
        view.show()
        # Extra display lines make the viewport scrollable without real audio.
        view.text.setPlainText(view.display + "\n" + "Browsing line.\n" * 100)
        QTest.qWait(50)
        assert view.follow.isChecked() and view.sync.isHidden()
        bar = view.text.verticalScrollBar()
        bar.setValue(100)
        assert view.follow.isChecked()  # Programmatic scrolling must not detach.
        if gesture == "wheel":
            pos = QPointF(40, 40)
            event = QWheelEvent(
                pos,
                pos,
                QPoint(),
                QPoint(0, -120),
                Qt.NoButton,
                Qt.NoModifier,
                Qt.NoScrollPhase,
                False,
            )
            QApplication.sendEvent(view.text.viewport(), event)
        elif gesture == "keyboard":
            QTest.keyClick(view.text, Qt.Key_PageDown)
        elif gesture == "scrollbar":
            bar.triggerAction(QAbstractSlider.SliderPageStepAdd)
        else:
            bar.setSliderDown(True)
            bar.setSliderPosition(400)
            bar.setSliderDown(False)
        assert not view.follow.isChecked()
        assert view.follow.isHidden() and view.sync.isVisible()
        before = bar.value()
        view.tick(1100)
        assert bar.value() == before
        position = view.player.position()
        view.sync.click()
        assert view.follow.isChecked() and view.sync.isHidden()
        assert view.player.position() == position  # Sync scrolls; it does not seek.
        assert bar.value() < before
        assert view.sync.font().bold()
        assert view.sync.font().pointSizeF() > view.follow.font().pointSizeF()
    finally:
        view.shutdown()
        view.close()
