import json
from PySide6.QtWidgets import QMessageBox
from app import Trainer
from dataset import Dataset
from engine import History, generate, grade
from settings import Settings


def test_blanks_do_not_enter_accuracy_or_exports(make_dataset, tmp_path):
    from analyze import analyze

    bank = Dataset(make_dataset(4)).bank
    exam = generate(bank, seed=18)
    good = next(
        i for i, o in enumerate(exam["questions"][0]["options"]) if o["correct"]
    )
    answers = {"0": good}
    result = grade(exam, answers)
    assert (result["correct"], result["total"], result["unanswered"]) == (1, 1, 3)
    h = History(tmp_path / "history.sqlite3")
    h.begin(exam)
    h.finish(exam, answers, 1)
    stats, _ = h.stats()
    assert sum(v["total"] for v in stats.values()) == 1
    # Legacy stored totals are reinterpreted in memory, without rewriting bytes.
    legacy = {**result, "total": 4}
    raw = json.dumps(legacy)
    h.db.execute("UPDATE runs SET result=?", (raw,))
    h.db.commit()
    assert h.runs()[0]["result"]["total"] == 1
    assert not h.is_personal_best({"correct": 1, "total": 2})
    assert h.db.execute("SELECT result FROM runs").fetchone()[0] == raw
    assert analyze(h.path, tmp_path / "csv") == 1
    h.close()


def test_all_blank_run_has_no_score_no_bonus_and_no_wrong_feedback(
    qt, make_dataset, tmp_path, monkeypatch
):
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.Yes)
    w = Trainer(Dataset(make_dataset(3)), Settings(tmp_path / "home"))
    w.finish_exam()
    w.show_question(0)
    assert w.result["total"] == 0 and w.result["unanswered"] == 3
    assert "No scored answers" in w.banner.text()
    assert "0 XP" in w.xp.text()
    assert "Not attempted" in w.explanation.text()
    assert w.sidebar.item(0).text().startswith("—")
    assert not w.history.stats()[0]
    w.close()
