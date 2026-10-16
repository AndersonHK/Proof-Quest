"""Original Fable dialogue and conservative, evidence-based review comments."""

from collections import deque
import random

QUIPS = (
    "Need a break? I can supervise the daydreaming.",
    "Bored already? My snack lecture hasn't even started.",
    "You rang? My office hours are suspiciously generous.",
    "Decorative ears. Fully functional judgment.",
    "That tickles my professional credibility.",
    "I was calculating how long until tea.",
    "Clicking the fox doesn't count as revision.",
    "Excellent click. Now show me the reasoning.",
    "Study break, or am I the study material?",
    "Less critical poking. More critical thinking.",
    "A hint? Finally, something in my job description.",
    "Your cursor has impeccable taste in foxes.",
    "The answer isn't behind my tail. I checked.",
    "Please form an orderly queue of one question.",
    "Do I look like a shortcut? Fine. A small one.",
    "Take a breath. The theorem can wait.",
)

ENCOURAGE = {
    True: (
        "Good reasoning deserves a victory sip.",
        "Try explaining the method without looking.",
        "Nicely handled. Explain the key step to yourself before moving on.",
        "A little more confidence, earned one question at a time.",
        "That worked. Give the reasoning a moment to settle.",
        "One sound argument. One quietly impressed fox.",
    ),
    False: (
        "Find the first step where the reasoning went wrong.",
        "Check the assumption behind your choice.",
        "Read the explanation, then try saying the rule without looking.",
        "This one goes in the retry pile.",
        "Try the rule on a smaller example.",
        "A sip, a breath, and one more look at the assumption.",
    ),
}


class Dialogue:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.recent = deque(maxlen=3)

    def choose(self, groups):
        for group in groups:
            available = [(key, text) for key, text in group if key not in self.recent]
            if available:
                key, text = self.rng.choice(available)
                self.recent.append(key)
                return text
        return None

    def quip(self):
        return self.choose([[(f"quip-{i}", text) for i, text in enumerate(QUIPS)]])

    def review(self, stats):
        current = stats["current_correct"]
        if current is None:
            return self.choose(
                [
                    [
                        (
                            "skip-0",
                            "Not attempted. This question was excluded from scoring.",
                        ),
                        (
                            "skip-1",
                            "No score attached to this one. Read it at your own pace.",
                        ),
                        (
                            "skip-2",
                            "Left blank. Revisit this question in a later run.",
                        ),
                        (
                            "skip-3",
                            "This question sat out the score. Its explanation is still here.",
                        ),
                    ]
                ]
            )
        priority = []
        hint_note = " With a hint this time." if stats["current_hinted"] else ""
        if current and stats["first_correct"]:
            priority.append(
                [
                    (f"first-{i}", text + hint_note)
                    for i, text in enumerate(
                        (
                            "First recorded correct answer on this question. A small milestone!",
                            "You got this question right for the first time. Progress worth noticing.",
                            "A first correct attempt on this one. I'll raise my mug to that.",
                            "Your first correct answer to this question.",
                        )
                    )
                ]
            )
        if current and stats["streak"] >= 2:
            n = stats["streak"]
            note = " Hinted attempts included." if stats["streak_hinted"] else ""
            priority.append(
                [
                    (f"streak-{i}", text + note)
                    for i, text in enumerate(
                        (
                            f"That's {n} correct attempted answers in a row on this question.",
                            f"This question's streak is now {n}. Quietly impressive.",
                            f"{n} consecutive attempted answers correct here. Keep the reasoning fresh.",
                            f"You have answered this question correctly {n} times in a row.",
                        )
                    )
                ]
            )
        if stats["attempts"] >= 5:
            n, r = stats["attempts"], stats["right"]
            priority.append(
                [
                    (f"stats-{i}", text)
                    for i, text in enumerate(
                        (
                            f"On this question: {r} correct out of {n} attempted answers. Blanks don't enter that count.",
                            f"Your recorded accuracy here is {r}/{n} attempted answers.",
                            f"You've attempted this question {n} times and answered it correctly {r} times.",
                            f"The notebook says {r} of {n} attempts correct here. Let's keep building on it.",
                        )
                    )
                ]
            )
        priority.append(
            [
                (f"encourage-{current}-{i}", text)
                for i, text in enumerate(ENCOURAGE[current])
            ]
        )
        return self.choose(priority)


def question_hint(question, bank):
    return (
        question.get("hint")
        or bank.get("topic_hints", {}).get(question["topic"])
        or (
            "No topic note is supplied for this dataset yet. Name the relevant definition, check the assumptions, and try a small example before choosing."
        )
    )
