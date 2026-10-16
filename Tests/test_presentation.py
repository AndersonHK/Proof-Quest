import json
from pathlib import Path
import pytest
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtMultimedia import QMediaDevices
from app import Trainer
from dataset import Dataset, DatasetError
from engine import generate
from presentation import Feedback, POSITIVE, NEGATIVE, display_answers
from settings import Settings
from widgets import JumpSlider
from player import Listening


@pytest.mark.parametrize(
    "answers,expected",
    [
        (["The value is 120.", "117", "0.0", "−4"], ["120", "117", "0", "-4"]),
        (
            ["The resulting set is {3, 1}.", "{8}", "∅", "{}"],
            ["{1, 3}", "{8}", "∅", "∅"],
        ),
        (
            ["In order: T, F, T.", "(F, T, F)", "T,F,F"],
            ["T, F, T", "F, T, F", "T, F, F"],
        ),
        (["The tight order is Θ(n²).", "Θ(n)"], ["Θ(n²)", "Θ(n)"]),
        (
            ["Exactly: symmetric, reflexive.", "antisymmetric only"],
            ["reflexive, symmetric", "antisymmetric"],
        ),
        (
            ["The value is important.", "Meaningful prose."],
            ["The value is important.", "Meaningful prose."],
        ),
    ],
)
def test_group_formatting_and_legacy_snapshots(answers, expected):
    original = list(answers)
    assert display_answers(answers) == expected
    assert answers == original


def test_feedback_shuffles_without_repetition_and_stays_stable():
    feedback = Feedback()
    for correct, pool in [(True, POSITIVE), (False, NEGATIVE)]:
        values = [feedback.phrase((correct, i), correct) for i in range(12)]
        assert len(set(values)) == 12 and set(values) == set(pool)
        assert feedback.phrase((correct, 0), correct) == values[0]
        assert feedback.phrase((correct, 12), correct) != values[-1]


def test_formatted_fixture_validation_and_exam_generation(make_dataset):
    path = make_dataset()
    bankpath = path.parent / "questions.json"
    bank = json.loads(bankpath.read_text())
    q = bank["questions"][0]
    q.update(
        answer_format="number", correct=["12", "12.0"], wrong=[str(i) for i in range(8)]
    )
    bankpath.write_text(json.dumps(bank))
    d = Dataset(path)
    for seed in range(10):
        e = generate(d.bank, 2, seed=seed)
        numeric = next(q for q in e["questions"] if q["id"] == "q0")
        assert all(o["text"].lstrip("-").isdigit() for o in numeric["options"])
    q["wrong"][0] = "12.00"
    bankpath.write_text(json.dumps(bank))
    with pytest.raises(DatasetError, match="collide"):
        Dataset(path)


def test_count_always_editable_and_presets_remain_presets(qt, make_dataset, tmp_path):
    w = Trainer(Dataset(make_dataset(100)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(50)
    assert w.count.isEnabled() and w.mode.itemText(3) == "Full bank · 100"
    w.count.setValue(17)
    assert w.mode.currentIndex() == 5
    w.mode.setCurrentIndex(3)
    assert w.count.value() == 100 and w.mode.currentIndex() == 3
    w.mode.setCurrentIndex(0)
    assert w.count.value() == 12 and w.mode.currentIndex() == 0
    w.count.stepDown()
    assert w.mode.currentIndex() == 5 and w.count.value() == 11
    w.close()


def test_failed_feedback_red_and_time_removed(qt, make_dataset, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)
    w = Trainer(Dataset(make_dataset()), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(50)
    for i, q in enumerate(w.exam["questions"]):
        w.show_question(i)
        w.select_answer(next(j for j, o in enumerate(q["options"]) if not o["correct"]))
    w.elapsed_base = 11862
    w.finish_exam()
    w.show_question(0)
    assert "#49301e" in w.explanation.styleSheet() and "197:42" not in w.banner.text()
    assert not w.explanation.text().startswith("Not this time.")
    first = w.explanation.text()
    w.show_question(1)
    w.show_question(0)
    assert w.explanation.text() == first
    w.close()


def test_window_fits_tall_screen_and_stays_inside_short_screen(
    qt, make_dataset, tmp_path
):
    w = Trainer(Dataset(make_dataset()), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(100)
    w.prompt.setText(
        "A multi-line question that should retain all its information. " * 4
    )
    for radio in w.options:
        radio.setText(
            "A complete answer with enough text to wrap onto multiple lines. " * 3
        )
    w.explanation.setText("A review explanation with useful details. " * 5)
    w.explanation.show()
    w.result = {"test": True}
    w.resize(1240, 720)
    QTest.qWait(50)
    w.fit_question_height(QRect(0, 0, 1800, 1800))
    QTest.qWait(100)
    assert w.height() > 720 and w.question_scroll.verticalScrollBar().maximum() == 0
    w.fit_question_height(QRect(0, 0, 1800, 740))
    QTest.qWait(50)
    assert (
        w.frameGeometry().height() <= 740
        and w.question_scroll.verticalScrollBar().maximum() > 0
    )
    w.result = None
    w.close()


def test_sliders_jump_drag_and_keep_keyboard_control(qt):
    slider = JumpSlider(Qt.Horizontal)
    slider.setRange(0, 100)
    slider.resize(400, 40)
    slider.show()
    QTest.qWait(40)
    releases = QSignalSpy(slider.sliderReleased)
    QTest.mouseClick(slider, Qt.LeftButton, pos=QPoint(300, 20))
    assert 73 <= slider.value() <= 78 and releases.count() == 1
    QTest.mousePress(slider, Qt.LeftButton, pos=QPoint(100, 20))
    QTest.mouseMove(slider, QPoint(200, 20))
    QTest.mouseRelease(slider, Qt.LeftButton, pos=QPoint(200, 20))
    assert 48 <= slider.value() <= 52 and releases.count() == 2
    before = slider.value()
    QTest.keyClick(slider, Qt.Key_Right)
    assert slider.value() == before + 1
    slider.close()


def test_player_routing_click_seek_and_volume(qt, make_dataset):
    p = Listening(Dataset(make_dataset(audio=True)))
    p.show()
    QTest.qWait(150)
    p.restore_output("unavailable-device")
    assert p.preferred_output == "system"
    p.audio.setMuted(True)
    p.volume.setValue(35)
    assert not p.audio.isMuted() and p.audio.volume() == pytest.approx(0.35)
    QTest.mouseClick(
        p.volume,
        Qt.LeftButton,
        pos=QPoint(int(p.volume.width() * 0.8), p.volume.height() // 2),
    )
    assert 0.7 < p.audio.volume() < 0.9, (
        p.size(),
        p.volume.geometry(),
        p.volume.value(),
        type(p.volume),
    )
    QTest.mouseClick(
        p.slider,
        Qt.LeftButton,
        pos=QPoint(p.slider.width() // 2, p.slider.height() // 2),
    )
    assert 1100 <= p.player.position() <= 1400
    assert p.audio.device() == QMediaDevices.defaultAudioOutput()
    p.shutdown()
    p.close()
