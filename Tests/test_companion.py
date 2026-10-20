from collections import deque
import json
import random
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from app import Trainer
from companion import Dialogue, QUIPS, question_hint
from dataset import Dataset
from engine import History, generate
from settings import Settings


def test_original_quips_and_review_messages_do_not_repeat_last_three():
    assert len(set(QUIPS)) >= 12
    d = Dialogue(random.Random(18))
    seen = deque(maxlen=3)
    for _ in range(50):
        text = d.quip()
        assert text not in seen
        seen.append(text)
    stats = {
        "current_correct": True,
        "first_correct": False,
        "streak": 4,
        "streak_hinted": 0,
        "current_hinted": False,
        "attempts": 8,
        "right": 6,
    }
    for _ in range(30):
        text = d.review(stats)
        assert text not in seen
        seen.append(text)
    stats.update(current_correct=None)
    assert "Not attempted" in Dialogue(random.Random(2)).review(stats)


def test_click_offer_then_hint_logs_usage_and_question_change_resets(
    qt, make_dataset, tmp_path
):
    d = Dataset(make_dataset(3))
    d.bank["questions"][0][
        "hint"
    ] = "Compare the roles of the assumptions before calculating."
    w = Trainer(d, Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(60)
    q = w.exam["questions"][w.current]
    QTest.mouseClick(w.mascot, Qt.LeftButton)
    assert "again for a hint" in w.speech_home.text
    assert not w.history.db.execute("SELECT 1 FROM events WHERE kind='hint'").fetchone()
    QTest.mouseClick(w.mascot, Qt.LeftButton)
    assert w.speech_home.text == "Hint · " + question_hint(q, w.bank)
    data = json.loads(
        w.history.db.execute("SELECT payload FROM events WHERE kind='hint'").fetchone()[
            0
        ]
    )
    assert data["question_id"] == q["id"]
    w.show_question(1)
    assert w.speech.armed is None and not w.speech_home.text
    QTest.mouseClick(w.mascot, Qt.LeftButton)
    assert "again for a hint" in w.speech_home.text
    w.close()
    assert not w.speech.timer.isActive()


def test_review_waits_for_sip_and_talks_without_interrupting(
    qt, make_dataset, tmp_path
):
    w = Trainer(Dataset(make_dataset(3)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(60)
    clock = [100.0]
    w.journey.now = lambda: clock[0]
    w.speech.now = lambda: clock[0]
    w.journey.since = 100.0
    for i, q in enumerate(w.exam["questions"]):
        w.answers[str(i)] = next(j for j, o in enumerate(q["options"]) if o["correct"])
    w.finish_exam()
    clock[0] += 4
    w.journey.tick()
    w.speech.tick()
    assert w.speech_review.text and w.journey.talk_since is not None
    w.show_question(1)
    started = w.journey.sip_since
    clock[0] += 0.4
    w.show_question(2)
    w.speech.tick()
    w.journey.tick()
    assert w.journey.sip_since == started and w.mascot.pose_override == "sip"
    assert not w.speech_review.text
    clock[0] += 1.2
    w.journey.tick()
    w.speech.tick()
    w.journey.tick()
    assert w.speech_review.text and w.mascot.pose_override.startswith("mugtalk")
    assert w.speech.key() == (w.exam["id"], 2)
    w.new_exam()
    assert not w.speech_review.isVisible() and not w.speech.pending_review
    w.close()


def test_question_statistics_ignore_blanks_abandonments_and_future_runs(
    make_dataset, tmp_path
):
    bank = Dataset(make_dataset(1)).bank
    h = History(tmp_path / "h.sqlite3")
    ids = []
    for n, (correct, status, hinted) in enumerate(
        [
            (False, "completed", False),
            (None, "completed", False),
            (True, "abandoned", False),
            (True, "completed", True),
            (True, "completed", False),
            (True, "completed", False),
        ]
    ):
        exam = generate(bank, seed=n)
        h.begin(exam)
        ids.append(exam["id"])
        q = exam["questions"][0]
        answers = (
            {}
            if correct is None
            else {
                "0": next(
                    i for i, o in enumerate(q["options"]) if o["correct"] == correct
                )
            }
        )
        if hinted:
            h.save(exam, answers, 1, ("hint", {"question_id": q["id"], "index": 0}))
        h.finish(exam, answers, 1, status)
    first = h.question_performance(q["id"], ids[3])
    assert first["first_correct"] and first["current_hinted"]
    assert first["attempts"] == 2 and first["streak"] == 1
    final = h.question_performance(q["id"], ids[-1])
    assert final["attempts"] == 4 and final["right"] == 3
    assert (
        final["streak"] == 3
        and final["streak_hinted"] == 1
        and not final["first_correct"]
    )
    skipped = h.question_performance(q["id"], ids[1])
    assert skipped["current_correct"] is None and skipped["attempts"] == 1
    h.close()


def test_hint_fallback_never_uses_correct_answer_or_explanation():
    q = {
        "topic": "An unfamiliar course",
        "correct": ["SECRET"],
        "explanation": "SECRET explained",
    }
    assert "SECRET" not in question_hint(q, {})
    assert (
        question_hint(q, {"topic_hints": {q["topic"]: "Check the units."}})
        == "Check the units."
    )
    q["hint"] = "Check the assumptions."
    assert (
        question_hint(q, {"topic_hints": {q["topic"]: "Check the units."}})
        == "Check the assumptions."
    )


def test_speech_is_floating_mouth_anchored_and_does_not_shift_controls(
    qt, make_dataset, tmp_path
):
    w = Trainer(Dataset(make_dataset(3)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(120)
    before = (w.prompt.geometry(), w.regenerate.geometry(), w.size())
    QTest.mouseClick(w.mascot, Qt.LeftButton)
    QTest.qWait(80)
    bubble = w.speech_home
    assert bubble.parentWidget() is w.centralWidget()
    assert bubble.testAttribute(Qt.WA_TransparentForMouseEvents)
    assert (w.prompt.geometry(), w.regenerate.geometry(), w.size()) == before
    assert abs(bubble.x() - (w.mascot.x() + w.mascot.width() - 8)) <= 1
    from PySide6.QtCore import QPoint

    title_bottom = w.brand_label.mapTo(
        w.centralWidget(), QPoint(0, w.brand_label.height())
    ).y()
    assert bubble.y() + bubble.body_top >= title_bottom - 1 and bubble.width() == 560
    assert (
        abs(bubble.y() + bubble.tail_y - (w.mascot.y() + w.mascot.height() * 0.52)) <= 1
    )
    w.resize(w.width() + 100, w.height())
    w.speech.tick()
    assert bubble.geometry().right() < w.centralWidget().width()
    w.close()


def test_quips_fit_one_line_and_invitation_is_separate(qt, make_dataset, tmp_path):
    from PySide6.QtGui import QFont, QFontMetrics

    metrics = QFontMetrics(QFont("Segoe UI", 11))
    assert all(metrics.horizontalAdvance(quip) <= 560 - 46 for quip in QUIPS)
    w = Trainer(Dataset(make_dataset(1)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(50)
    QTest.mouseClick(w.mascot, Qt.LeftButton)
    lines = w.speech_home.text.splitlines()
    assert len(lines) == 2 and lines[0] in QUIPS
    assert lines[1] == "Click Fable again for a hint."
    w.close()


def test_long_hints_get_slower_reveal_and_reading_time_after_reveal(
    qt, make_dataset, tmp_path
):
    from speech import speech_timing

    short = "Check the assumption."
    long = " ".join(["Consider the assumptions and test one concrete example."] * 8)
    short_times = speech_timing(short)
    reveal, reading, fade = speech_timing(long)
    assert (
        reveal > short_times[0] and reading > short_times[1] and fade > short_times[2]
    )
    assert reading >= len(long.split()) / 3
    w = Trainer(Dataset(make_dataset(1)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(50)
    clock = [100.0]
    w.speech.now = lambda: clock[0]
    w.speech.post(long)
    assert w.journey.talk_duration >= reveal
    clock[0] += reveal + reading - 0.1
    w.speech.tick()
    assert w.speech_home.opacity == 1 and w.speech_home.isVisible()
    clock[0] += fade + 0.2
    w.speech.tick()
    assert not w.speech_home.isVisible()
    assert speech_timing("漢字" * 100)[1] > short_times[1]
    w.close()


def test_review_bubble_and_pointer_move_together_below_timer(
    qt, make_dataset, tmp_path
):
    from PySide6.QtCore import QPoint

    w = Trainer(Dataset(make_dataset(2)), Settings(tmp_path / "home"))
    try:
        w.show()
        QTest.qWait(100)
        w.journey.finished(False)
        w.journey.since -= 2
        w.journey.tick()
        qt.processEvents()
        w.speech.post(
            "Not attempted. This question was excluded from scoring.", review=True
        )
        bubble = w.speech_review
        bottom = max(
            c.mapTo(w.centralWidget(), QPoint(0, c.height())).y()
            for c in (w.exam_time, w.timer_button)
        )
        assert bubble.body_top >= 16
        assert bubble.y() + bubble.body_top >= bottom + 3
        assert abs(bubble.tail_y - bubble.body_top - 3) <= 1
    finally:
        w.close()
