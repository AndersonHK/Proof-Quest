import pytest
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from dataset import Dataset
from player import Listening


def choose_rate(view, rate):
    view.rate.setCurrentIndex(view.rate.findData(rate))
    view.rate.activated.emit(view.rate.currentIndex())


@pytest.mark.parametrize("state", ["playing", "paused", "stopped"])
def test_rate_changes_preserve_transport_and_audio_settings(qt, make_dataset, state):
    view = Listening(Dataset(make_dataset(audio=True)))
    try:
        QTest.qWait(250)
        view.audio.setMuted(True)
        view.audio.setVolume(0.31)
        device = view.audio.device()
        view.seek(500)
        if state != "stopped":
            view.player.play()
            QTest.qWait(120)
            if state == "paused":
                view.player.pause()
                QTest.qWait(80)
        position = view.player.position()
        expected = view.player.playbackState()
        states = []
        view.player.playbackStateChanged.connect(states.append)
        choose_rate(view, 1.25)
        QTest.qWait(100)
        assert view.player.playbackRate() == pytest.approx(1.25)
        assert view.player.playbackState() == expected
        assert position - 100 <= view.player.position() < position + 500
        assert view.audio.isMuted()
        assert view.audio.volume() == pytest.approx(0.31)
        assert view.audio.device() == device
        if state == "playing":
            # A direct live rate change leaves WMF audio silent on some devices.
            assert states == [QMediaPlayer.PausedState, QMediaPlayer.PlayingState]
        else:
            assert not states
        states.clear()
        choose_rate(view, 1.25)
        assert not states
    finally:
        view.shutdown()
        view.close()


def test_rapid_speed_changes_do_not_override_a_user_pause(qt, make_dataset):
    view = Listening(Dataset(make_dataset(audio=True)))
    try:
        QTest.qWait(250)
        view.audio.setMuted(True)
        view.player.play()
        QTest.qWait(100)
        for rate in (2, 0.75, 1.5, 1.1, 1.75, 1):
            choose_rate(view, rate)
        view.toggle()
        QTest.qWait(250)
        assert view.player.playbackState() == QMediaPlayer.PausedState
        assert view.player.playbackRate() == 1
    finally:
        view.shutdown()
        view.close()
