from collections import Counter
from copy import deepcopy
import itertools
import random
import sys
from pathlib import Path
import pytest
from dataset import Dataset, DatasetError, validate_bank
from engine import generate, sample_choices
from theme import EXPLANATIONS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from audit_choices import inspect_choices


def test_curated_sampling_preserves_balanced_verdicts(make_dataset):
    bank = Dataset(make_dataset(1)).bank
    q = bank["questions"][0]
    q["correct"] = [
        "Valid: the implication applies.",
        "Valid: the premises force this conclusion.",
    ]
    q["wrong"] = [
        f'{"Valid" if i < 4 else "Invalid"}: mistaken reason {i}.' for i in range(8)
    ]
    small = [
        list(a + b)
        for a in itertools.combinations(range(4), 1)
        for b in itertools.combinations(range(4, 8), 3)
    ]
    large = [
        list(a + b)
        for a in itertools.combinations(range(4), 2)
        for b in itertools.combinations(range(4, 8), 2)
    ]
    q["distractor_sets"] = small * 9 + large * 4
    validate_bank(bank)
    observed = Counter()
    for seed in range(300):
        exam = generate(bank, seed=seed)
        question = exam["questions"][0]
        assert "distractor_sets" not in question
        options = question["options"]
        assert sum(o["correct"] for o in options) == 1
        counts = Counter(o["text"].split(":")[0] for o in options)
        assert sorted(counts.values()) == [2, 3]
        observed[counts["Valid"]] += 1
        assert not inspect_choices(options)
    assert observed[2] > 100 and observed[3] > 100


@pytest.mark.parametrize(
    "groups", [[], [[0, 1, 2]], [[0, 1, 2, 2]], [[0, 1, 2, 999]], [[False, 1, 2, 3]]]
)
def test_invalid_curated_sets_are_rejected(make_dataset, groups):
    bank = Dataset(make_dataset(1)).bank
    bank["questions"][0]["distractor_sets"] = groups
    with pytest.raises(DatasetError, match="distractor"):
        validate_bank(bank)


def test_audit_detects_verdict_and_format_clues():
    options = [{"text": "Invalid: the conclusion can fail.", "correct": True}] + [
        {"text": f"Valid: reason {i}.", "correct": False} for i in range(4)
    ]
    assert "AP02-singleton-verdict" in inspect_choices(options)
    options = [{"text": "The calculated amount equals seven.", "correct": True}] + [
        {"text": str(i), "correct": False} for i in range(4)
    ]
    assert "AP01-format-outlier" in inspect_choices(options)


def test_explanation_contrast_and_noncolor_labels():
    def luminance(hexcolor):
        rgb = [int(hexcolor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [
            x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb
        ]
        return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))

    for text, background, border, label in EXPLANATIONS.values():
        hi, lo = sorted((luminance(text), luminance(background)), reverse=True)
        assert (hi + 0.05) / (
            lo + 0.05
        ) >= 7  # Stronger than the 4.5:1 minimum for these panels.
        assert label


def test_complexity_alternative_has_no_unique_constant_cue():
    from presentation import display_answers

    assert display_answers(["Θ(2 × n²)", "Θ(n)", "Θ(log n)"], "complexity") == [
        "Θ(n²)",
        "Θ(n)",
        "Θ(log n)",
    ]
