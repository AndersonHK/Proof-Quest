import json
from fractions import Fraction
import pytest
from dataset import Dataset, DatasetError
from engine import generate
from presentation import parse_answer, display_answers


def test_fraction_choices_share_canonical_notation():
    assert display_answers(["2/4", "3 / 9", "-2/-6", "0/7", "7/7"], "fraction") == [
        "1/2",
        "1/3",
        "1/3",
        "0",
        "1",
    ]
    assert parse_answer("1/0", "fraction") is None
    assert parse_answer("one half", "fraction") is None


def test_fraction_pool_rejects_equivalent_distractors(make_dataset):
    path = make_dataset(1)
    p = path.parent / "questions.json"
    b = json.loads(p.read_text())
    q = b["questions"][0]
    q.update(
        answer_format="fraction",
        correct=["1/2", "2/4"],
        wrong=["0", "1", "1/3", "2/3", "1/4", "3/4", "1/5", "4/5"],
    )
    p.write_text(json.dumps(b))
    d = Dataset(path)
    for seed in range(20):
        options = generate(d.bank, seed=seed)["questions"][0]["options"]
        assert len({Fraction(o["text"]) for o in options}) == 5
        assert next(o["text"] for o in options if o["correct"]) == "1/2"
    q["wrong"][-1] = "2/6"
    p.write_text(json.dumps(b))
    with pytest.raises(DatasetError, match="collide"):
        Dataset(path)
