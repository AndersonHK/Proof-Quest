from pathlib import Path
from PySide6.QtTest import QTest
from mascot import Fable
from theme import STYLE

ROOT = Path(__file__).resolve().parents[1]


def test_fable_artwork_and_blink_inbetweens(qt):
    widget = Fable(ROOT / "Assets" / "Fable", 160)
    widget.show()
    assert all(not p.isNull() for p in widget.frames.values())
    assert Fable.pose_at(1) == "neutral"
    assert Fable.pose_at(6.03) == "half"
    assert Fable.pose_at(6.10) == "blink"
    assert Fable.pose_at(6.2) == "half"
    assert Fable.pose_at(6.4) == "neutral"
    assert widget.timer.interval() <= 66
    widget.check_in()
    QTest.qWait(250)
    assert Fable.pose_at(1, 0.6) == "peek"
    assert Fable.pose_at(1, 1.25) == "half"
    assert Fable.pose_at(1, 1.55) == "neutral"
    widget.hide()
    assert not widget.timer.isActive()
    widget.close()


def test_theme_keeps_cream_and_violet_identity():
    assert "#fff0cf" in STYLE and "#b79aff" in STYLE
    assert "#8ce0c7" not in STYLE
