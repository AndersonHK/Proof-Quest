import json
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox, QApplication, QDialog
from app import Trainer
from dataset import Dataset
from settings import Settings
from player import Listening

ROOT = Path(__file__).resolve().parents[1]


def test_switch_preserves_pending_and_preferences(
    qt, make_dataset, tmp_path, monkeypatch
):
    one = make_dataset(7)
    two = make_dataset(32)
    settings = Settings(tmp_path / "home")
    settings.select_dataset(one)
    w = Trainer(Dataset(one), settings)
    w.show()
    QTest.qWait(100)
    w.options[2].click()
    old = w.exam["id"]
    w.listen.volume.setValue(42)
    assert w.switch_dataset(two)
    assert len(w.chapter_checks) == 32 and w.answers == {}
    assert w.settings.dataset_path() == two and w.listen.volume.value() == 42
    assert w.switch_dataset(one)
    assert w.exam["id"] == old and w.answers == {"0": 2}
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    assert not w.switch_dataset(tmp_path / "missing.json")
    assert w.exam["id"] == old and warnings
    w.close()
    assert Settings(settings.home).get("volume", 75) == 42


def test_grading_long_text_help_and_layout(qt, make_dataset, tmp_path, monkeypatch):
    w = Trainer(Dataset(make_dataset(6, long=True)), Settings(tmp_path / "home"))
    w.show()
    QTest.qWait(150)
    assert "<literal>" in w.prompt.text() and len(w.prompt.text()) > 5000
    for i, q in enumerate(w.exam["questions"]):
        w.show_question(i)
        right = next(j for j, o in enumerate(q["options"]) if o["correct"])
        w.options[right].click()
    w.finish_exam()
    assert w.result["correct"] == 6 and w.stack.currentIndex() == 1
    out = ROOT / "Out" / "Ui"
    out.mkdir(parents=True, exist_ok=True)
    w.grab().save(str(out / "graded.png"))
    QTimer.singleShot(150, lambda: QApplication.activeModalWidget().accept())
    w.show_help()
    w.close()


def test_unicode_word_highlighting_search_and_seek(qt, make_dataset):
    d = Dataset(make_dataset(audio=True))
    p = Listening(d)
    p.resize(1000, 700)
    p.show()
    p.audio.setMuted(True)
    QTest.qWait(150)
    p.tick(400)
    selection = p.text.extraSelections()
    assert selection[1].cursor.selectedText() == "🌙"
    p.tick(700)
    selection = p.text.extraSelections()
    assert selection[1].cursor.selectedText() == "world"
    p.search.setText("你好")
    p.find_match(1)
    assert p.player.position() == 1000
    p.jump_to_char(p.word_ranges[1][0])
    assert p.player.position() == 100
    p.tick(1300)
    selection = p.text.extraSelections()
    end = selection[0].cursor.selectionEnd()
    p.tick(100)
    selection = p.text.extraSelections()
    assert selection[0].cursor.selectionEnd() < end
    p.player.play()
    before = p.player.position()
    QTest.qWait(350)
    assert p.player.position() > before
    p.shutdown()
    p.close()
