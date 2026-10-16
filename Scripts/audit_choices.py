"""Heuristic curation warnings, not an academic-correctness certificate."""

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Src"))
from dataset import Dataset
from engine import sample_choices
from presentation import FORMATS, parse_answer


def inspect_choices(options):
    flags = set()
    texts = [o["text"].strip() for o in options]
    correct = next(i for i, o in enumerate(options) if o["correct"])
    if len({t.casefold() for t in texts}) < 5:
        flags.add("AP03-duplicate-display")
    verdicts = [
        re.match(r"^(valid|invalid|true|false|yes|no)\b", t, re.I) for t in texts
    ]
    values = [m[1].lower() if m else None for m in verdicts]
    if values[correct] and values.count(values[correct]) == 1 and all(values):
        flags.add("AP02-singleton-verdict")
    for kind in FORMATS:
        matches = [parse_answer(t, kind) is not None for t in texts]
        if sum(matches) == 4 and not matches[correct]:
            flags.add("AP01-format-outlier")
    lengths = [len(t.split()) for t in texts]
    others = [n for i, n in enumerate(lengths) if i != correct]
    if lengths[correct] > 2.5 * max(others) and lengths[correct] >= 12:
        flags.add("AP07-length-outlier")
    return flags


def audit(bank, samples=200):
    findings = []
    for q in bank["questions"]:
        counts = Counter()
        for seed in range(samples):
            counts.update(inspect_choices(sample_choices(q, random.Random(seed))))
        if counts:
            findings.append({"id": q["id"], "flags": dict(counts)})
    return {
        "questions": len(bank["questions"]),
        "samples_per_question": samples,
        "warning_questions": len(findings),
        "findings": findings,
        "limits": "Heuristics do not detect semantic duplicates, factual errors, or unrelated-topic filler. Apply Docs/Question-Curation.md manually.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(Dataset(args.manifest).bank)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f'{report["questions"]} questions sampled; {report["warning_questions"]} questions need heuristic review. Report: {args.out}'
    )


if __name__ == "__main__":
    main()
