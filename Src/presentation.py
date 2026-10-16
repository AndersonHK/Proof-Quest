"""Consistent answer notation and non-repeating review feedback."""

import random
import re
from decimal import Decimal, InvalidOperation

POSITIVE = (
    "Nicely done.",
    "That checks out.",
    "Right on target.",
    "You have this one.",
    "A clean solution.",
    "Good call.",
    "Well spotted.",
    "Exactly right.",
    "One more concept secured.",
    "The evidence agrees.",
    "A solid answer.",
    "Point earned.",
)
NEGATIVE = (
    "A useful mistake to catch.",
    "One to revisit.",
    "Here is the missing piece.",
    "A small course correction.",
    "This one needs another look.",
    "Let us untangle this.",
    "A detour, not a dead end.",
    "Here is what makes the answer work.",
    "Another clue for next time.",
    "Close the gap with this idea.",
    "A good spot to sharpen your recall.",
    "Here is the key distinction.",
)


class Feedback:
    def __init__(self):
        self.decks = {True: [], False: []}
        self.previous = {True: None, False: None}
        self.cache = {}

    def phrase(self, key, correct):
        if key not in self.cache:
            deck = self.decks[correct]
            if not deck:
                deck.extend(POSITIVE if correct else NEGATIVE)
                random.shuffle(deck)
                if deck[-1] == self.previous[correct]:
                    deck[0], deck[-1] = deck[-1], deck[0]
            value = deck.pop()
            self.previous[correct] = value
            self.cache[key] = value
        return self.cache[key]


def parse_answer(text, kind):
    """Return one canonical notation, or None if this isn't the declared shape."""
    value = text.strip()
    if kind == "number":
        value = re.sub(r"^The value (?:is|of)\s+", "", value, flags=re.I)
        value = value.rstrip(".")
        if not re.fullmatch(r"[+−-]?\d+(?:\.\d+)?", value):
            return None
        try:
            result = Decimal(value.replace("−", "-"))
            if result == 0:
                return "0"
            return (
                format(result, "f").rstrip("0").rstrip(".")
                if "." in value
                else str(int(result))
            )
        except InvalidOperation:
            return None
    if kind == "set":
        value = re.sub(r"^The resulting set is\s+", "", value, flags=re.I).rstrip(".")
        if value in ("∅", "{}", "{ }"):
            return "∅"
        if not re.fullmatch(r"\{\s*[+−-]?\d+(?:\s*,\s*[+−-]?\d+)*\s*\}", value):
            return None
        members = sorted(
            set(int(x.strip().replace("−", "-")) for x in value[1:-1].split(","))
        )
        return "{" + ", ".join(map(str, members)) + "}"
    if kind == "truth_column":
        value = re.sub(r"^In order:\s*", "", value, flags=re.I).rstrip(".")
        if value.startswith("(") and value.endswith(")"):
            value = value[1:-1].strip()
        if not re.fullmatch(r"[TF](?:\s*,\s*[TF])+", value):
            return None
        return ", ".join(v.strip() for v in value.split(","))
    if kind == "complexity":
        value = re.sub(r"^The tight order is\s+", "", value, flags=re.I).rstrip(".")
        return value if re.fullmatch(r"Θ\(.+\)", value) else None
    if kind == "property_list":
        value = re.sub(r"^Exactly:\s*", "", value, flags=re.I).rstrip(".").lower()
        value = value.removesuffix(" only")
        parts = [p.strip() for p in value.split(",")]
        allowed = ("reflexive", "symmetric", "antisymmetric", "transitive")
        if value == "none of the four":
            return "None of the four"
        if not parts or any(p not in allowed for p in parts):
            return None
        return ", ".join(p for p in allowed if p in parts)
    return None


FORMATS = ("number", "set", "truth_column", "complexity", "property_list")


def display_answers(texts, kind=None):
    """Normalize the entire choice group, never just the right answer.

    Older saved snapshots have no format metadata. Infer only when every choice
    matches the same narrowly recognized notation. Their stored text stays intact.
    """
    for candidate in [kind] if kind else FORMATS:
        values = [parse_answer(text, candidate) for text in texts]
        if all(v is not None for v in values):
            return values
    return list(texts)
