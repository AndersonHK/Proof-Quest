import json
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from app import Trainer
from dataset import Dataset
from engine import History
from settings import Settings


def window(qt, make_dataset, tmp_path):
    w = Trainer(Dataset(make_dataset(4)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(40)
    clock = [100.0]
    w.journey.now = lambda: clock[0]
    w.journey.since = clock[0]
    return w, clock


def test_answer_wink_and_complete_round_trip(qt, make_dataset, tmp_path):
    w, clock = window(qt, make_dataset, tmp_path)
    for i, q in enumerate(w.exam["questions"]):
        w.show_question(i)
        w.options[next(j for j, o in enumerate(q["options"]) if o["correct"])].click()
        assert w.mascot.reaction is not None
        assert w.journey.state == "home"
    w.finish_exam()
    assert w.journey.state == "celebrate" and w.mascot.pose_override == "ready"
    clock[0] += 0.7
    w.journey.tick()
    assert w.mascot.pose_override == "hooray" and w.journey.effects.isVisible()
    assert w.journey.effects.testAttribute(Qt.WA_TransparentForMouseEvents)
    clock[0] += 1.2
    w.journey.tick()
    assert w.journey.state == "exit_left"
    clock[0] += 0.7
    w.journey.tick()
    assert w.journey.state == "enter_review"
    clock[0] += 0.8
    w.journey.tick()
    assert w.journey.state == "review" and w.mascot.pose_override == "mug"
    w.show_question(0)
    clock[0] += 0.4
    w.journey.tick()
    assert w.mascot.pose_override == "sip"
    sip_since = w.journey.sip_since
    w.show_question(0)
    assert (
        w.journey.sip_since == sip_since
    )  # Reselecting the same question does not restart.
    w.tabs.setCurrentIndex(1)
    w.journey.tick()
    assert not w.mascot.isVisible()
    w.tabs.setCurrentIndex(0)
    w.new_exam()
    assert w.journey.state == "exit_right" and w.mascot.flip
    clock[0] += 0.9
    w.journey.tick()
    assert w.journey.state == "enter_home"
    assert w.mascot.pose_override.startswith("walk")
    clock[0] += 0.7
    w.journey.tick()
    assert w.journey.state == "home" and w.mascot.pose_override is None
    assert not w.mascot_review.isVisible()
    w.close()
    assert not w.journey.timer.isActive()


def test_nonrecord_skips_confetti_and_rapid_regeneration_recovers(
    qt, make_dataset, tmp_path
):
    w, clock = window(qt, make_dataset, tmp_path)
    w.journey.finished(False)
    assert w.journey.state == "exit_left"
    assert not w.journey.effects.isVisible()
    w.journey.regenerated()
    w.journey.regenerated()
    clock[0] += 2
    w.journey.tick()
    assert w.journey.state == "home"
    w.journey.finished(True)
    w.journey.regenerated()
    clock[0] += 2
    w.journey.tick()
    assert w.journey.state == "home" and not w.journey.effects.isVisible()
    w.close()


def test_personal_best_uses_percentage_and_persistent_book_history(tmp_path):
    path = tmp_path / "book1.sqlite3"
    history = History(path)
    assert not history.is_personal_best({"correct": 0, "total": 10})
    assert history.is_personal_best({"correct": 6, "total": 10})
    for identity, status, right, total in [
        ("a", "completed", 6, 10),
        ("b", "abandoned", 10, 10),
    ]:
        history.db.execute(
            "INSERT INTO runs VALUES(?, '', '', ?, '{}', '{}', 0, ?)",
            (identity, status, json.dumps({"correct": right, "total": total})),
        )
    history.db.commit()
    history.close()

    history = History(path)
    assert not history.is_personal_best({"correct": 12, "total": 20})
    assert not history.is_personal_best({"correct": 5, "total": 10})
    assert history.is_personal_best({"correct": 7, "total": 10})
    other = History(tmp_path / "book2.sqlite3")
    assert other.is_personal_best({"correct": 1, "total": 10})
    other.close()
    history.close()


def test_sip_survives_question_changes_and_click_blinks_with_mug(
    qt, make_dataset, tmp_path
):
    w, clock = window(qt, make_dataset, tmp_path)
    w.journey.finished(False)
    clock[0] += 2
    w.journey.tick()
    w.journey.question_changed()
    started = w.journey.sip_since
    clock[0] += 0.4
    w.journey.question_changed()
    QTest.mouseClick(w.mascot, Qt.LeftButton)
    assert w.journey.sip_since == started
    assert w.mascot.pose_override == "sip"
    clock[0] = started + 1.55
    w.journey.tick()
    assert w.mascot.pose_override == "content"
    clock[0] += 0.4
    w.journey.tick()
    assert w.mascot.pose_override == "mug"
    w.close()
