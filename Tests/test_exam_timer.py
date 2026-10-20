import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox
from app import Trainer
from dataset import Dataset
from settings import Settings
from exam_timer import ExamTimer, duration_text


def test_active_time_excludes_waiting_pauses_and_unfocused_intervals():
    now = [0.0]
    t = ExamTimer(lambda: now[0])
    t.transition(focused=True)
    now[0] = 100
    assert t.elapsed() == 0
    t.activity()
    now[0] += 12.5
    t.transition(focused=False)
    now[0] += 1000
    assert t.elapsed() == 12.5
    t.transition(focused=True)
    now[0] += 7.5
    t.toggle()
    now[0] += 100
    t.activity()
    assert t.elapsed() == 20 and t.state == "paused"
    t.transition(focused=False)
    t.transition(focused=True)
    assert t.state == "paused"
    t.toggle()
    now[0] += 10
    t.finish()
    now[0] += 500
    t.activity()
    t.toggle()
    assert t.elapsed() == 30 and t.state == "finished"
    assert duration_text(3661) == "01:01:01"


def test_activity_tabs_focus_manual_pause_and_fixed_timer_layout(
    qt, make_dataset, tmp_path, monkeypatch
):
    w = Trainer(Dataset(make_dataset(4)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(100)
    now = [100.0]
    w.exam_timer.now = lambda: now[0]
    w.exam_timer.reset()
    QApplication.sendEvent(w, QEvent(QEvent.WindowActivate))
    now[0] += 20
    w.show_question(0)  # Rendering a saved question is not user activity.
    w.autosave()
    assert w.elapsed() == 0
    w.sidebar.itemClicked.emit(w.sidebar.item(0))
    now[0] += 10
    w.tabs.setCurrentIndex(1)
    now[0] += 5
    assert w.elapsed() == 15
    w.tabs.setCurrentIndex(0)
    w.update_exam_clock()
    qt.processEvents()
    before = (w.exam_time.geometry(), w.timer_button.geometry(), w.banner.geometry())
    w.timer_button.click()
    qt.processEvents()
    assert before == (
        w.exam_time.geometry(),
        w.timer_button.geometry(),
        w.banner.geometry(),
    )
    w.tabs.setCurrentIndex(1)
    now[0] += 100
    w.tabs.setCurrentIndex(0)
    w.options[0].click()
    w.next_question()
    assert w.elapsed() == 15 and w.exam_timer.state == "paused"
    w.timer_button.click()
    now[0] += 5
    QApplication.sendEvent(w, QEvent(QEvent.WindowDeactivate))
    now[0] += 100
    assert w.elapsed() == 20 and w.timer_button.text() == "▶ Resume"
    QApplication.sendEvent(w, QEvent(QEvent.WindowActivate))
    now[0] += 5
    assert w.elapsed() == 25
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    w.finish_exam()
    now[0] += 100
    assert w.elapsed() == 25 and not w.timer_button.isEnabled()
    assert w.history.runs()[0]["seconds"] == 25
    w.new_exam()
    assert w.exam_timer.state == "running" and w.elapsed() == 0
    w.close()


def test_restored_runs_wait_for_activity_and_keep_explicit_pause(
    qt, make_dataset, tmp_path
):
    path = make_dataset(3)
    settings = Settings(tmp_path / "home")
    w = Trainer(Dataset(path), settings)
    w.exam_timer.total = 37
    w.close()
    w = Trainer(Dataset(path), Settings(settings.home))
    assert w.elapsed() == 37 and w.exam_timer.state == "waiting"
    w.select_answer(1)
    assert w.exam_timer.state == "running"
    w.exam_timer.transition(focused=True)
    w.toggle_exam_timer()
    w.close()
    w = Trainer(Dataset(path), Settings(settings.home))
    assert w.exam_timer.state == "paused"
    w.select_answer(2)
    w.tabs.setCurrentIndex(1)
    assert w.exam_timer.state == "paused"
    w.close()
