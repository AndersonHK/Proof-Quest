import json
from pathlib import Path
import pytest, jsonschema
from dataset import Dataset, DatasetError
from engine import generate, grade, History
from settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_schema_and_demo():
    dataset = Dataset(ROOT / "Examples" / "Demo" / "dataset.json")
    for name, value in [("dataset", dataset.manifest), ("questions", dataset.bank)]:
        jsonschema.validate(
            value, json.loads((ROOT / "Schemas" / f"{name}.schema.json").read_text())
        )
    assert len(dataset.chapters) == 2 and dataset.audio_path is None


def test_many_chapters_long_unicode_and_random_pools(make_dataset):
    dataset = Dataset(make_dataset(32, long=True))
    bank = dataset.bank
    variants = {q["id"]: set() for q in bank["questions"]}
    for seed in range(30):
        exam = generate(bank, 100, seed=seed)
        assert len(exam["questions"]) == 32
        assert len({q["chapter"] for q in exam["questions"]}) == 32
        for q in exam["questions"]:
            assert (
                len(q["options"]) == 5 and sum(o["correct"] for o in q["options"]) == 1
            )
            variants[q["id"]].add(next(o["text"] for o in q["options"] if o["correct"]))
    assert all(len(v) == 2 for v in variants.values())
    assert (
        generate(bank, 10, seed=4)["questions"]
        == generate(bank, 10, seed=4)["questions"]
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(schema_version=9),
        lambda m: m["chapters"].append(m["chapters"][0]),
        lambda m: m.update(question_bank="../outside.json"),
    ],
)
def test_bad_manifest_rejected(make_dataset, change):
    path = make_dataset()
    m = json.loads(path.read_text())
    change(m)
    path.write_text(json.dumps(m))
    with pytest.raises(DatasetError):
        Dataset(path)


@pytest.mark.parametrize(
    "change",
    [
        lambda q: q.update(chapter="missing"),
        lambda q: q.update(wrong=["one"]),
        lambda q: q["wrong"].__setitem__(0, q["correct"][0]),
    ],
)
def test_bad_questions_rejected(make_dataset, change):
    path = make_dataset()
    bankpath = path.parent / "questions.json"
    b = json.loads(bankpath.read_text())
    change(b["questions"][0])
    bankpath.write_text(json.dumps(b))
    with pytest.raises(DatasetError):
        Dataset(path)


def test_timing_schema_and_bounds(make_dataset):
    path = make_dataset(audio=True)
    d = Dataset(path)
    jsonschema.validate(
        d.timings, json.loads((ROOT / "Schemas" / "timings.schema.json").read_text())
    )
    data = d.timings
    data["words"][0]["end"] = 9999
    (path.parent / "timings.json").write_text(json.dumps(data))
    with pytest.raises(DatasetError):
        Dataset(path)


def test_history_grading_restart_and_isolation(make_dataset, tmp_path):
    d = Dataset(make_dataset(6))
    e = generate(d.bank, 6, seed=5)
    h = History(tmp_path / "one.sqlite3")
    h.begin(e)
    answers = {
        "0": next(j for j, o in enumerate(e["questions"][0]["options"]) if o["correct"])
    }
    h.save(e, answers, 4, ("answer", {"index": 0}))
    h.close()
    h = History(tmp_path / "one.sqlite3")
    assert h.pending() == (e, answers, 4)
    result = h.finish(e, answers, 5)
    assert result["correct"] == 1 and sum(r["unanswered"] for r in result["rows"]) == 5
    h.export(tmp_path / "export.jsonl")
    assert (
        json.loads((tmp_path / "export.jsonl").read_text(encoding="utf-8"))["exam"] == e
    )
    h.close()
    other = History(tmp_path / "two.sqlite3")
    assert other.runs() == []
    other.close()


def test_ini_relative_unicode_percent_and_settings(tmp_path, make_dataset):
    settings = Settings(tmp_path / "home")
    path = make_dataset()
    settings.select_dataset(path)
    for k, v in [
        ("volume", 42),
        ("playback_rate", 1.25),
        ("note", "50% 漢字 🌙"),
        ("chapters", ["a", "b"]),
    ]:
        settings.set(k, v)
    settings.save()
    again = Settings(settings.home)
    assert again.dataset_path() == path and again.get("note", "") == "50% 漢字 🌙"
    assert again.get("playback_rate", 1) == 1.25
    assert settings.path.parent == settings.home
