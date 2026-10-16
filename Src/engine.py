"""Pure exam generation, grading, and durable SQLite history (no GUI dependencies)."""

from __future__ import annotations
import hashlib
import json
import random
import sqlite3
import uuid
from presentation import display_answers
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def load_bank(path):
    from dataset import read_json, validate_bank

    return validate_bank(read_json(path))


def sample_choices(question, rng):
    """Sample one correct formulation and four distractors, then shuffle uniformly."""
    wrong = (
        [question["wrong"][i] for i in rng.choice(question["distractor_sets"])]
        if question.get("distractor_sets")
        else rng.sample(question["wrong"], 4)
    )
    options = [{"text": rng.choice(question["correct"]), "correct": True}]
    options += [{"text": text, "correct": False} for text in wrong]
    rng.shuffle(options)
    formatted = display_answers(
        [o["text"] for o in options], question.get("answer_format")
    )
    for option, text in zip(options, formatted):
        option["text"] = text
    return options


def generate(bank, count=40, chapters=None, seed=None, weaknesses=None):
    chapters = (
        list(dict.fromkeys(q["chapter"] for q in bank["questions"]))
        if chapters is None
        else list(chapters)
    )
    seed = random.SystemRandom().randrange(2**63) if seed is None else seed
    rng = random.Random(seed)
    candidates = [q for q in bank["questions"] if q["chapter"] in chapters]
    if not candidates:
        raise ValueError("Choose at least one chapter.")
    count = min(max(1, count), len(candidates))
    # Stratify by topic, round-robin chapters; avoid repeated template families until needed.
    buckets = defaultdict(list)
    for q in candidates:
        buckets[(q["chapter"], q["topic"])].append(q)
    for values in buckets.values():
        rng.shuffle(values)
    selected, families = [], set()
    topics = list(buckets)
    if weaknesses:
        # Weighted order without replacement: recently weak topics tend to appear sooner.
        topics.sort(
            key=lambda k: rng.random() ** (1 / max(0.2, weaknesses.get(k[1], 1))),
            reverse=True,
        )
    else:
        by_chapter = defaultdict(list)
        for k in topics:
            by_chapter[k[0]].append(k)
        for keys in by_chapter.values():
            rng.shuffle(keys)
        topics = []
        while any(by_chapter.values()):
            order = list(by_chapter)
            rng.shuffle(order)
            for ch in order:
                if by_chapter[ch]:
                    topics.append(by_chapter[ch].pop())
    while len(selected) < count:
        progress = False
        for key in topics:
            values = buckets[key]
            fresh = next((q for q in values if q["family"] not in families), None)
            if fresh is not None:
                selected.append(fresh)
                families.add(fresh["family"])
                values.remove(fresh)
                progress = True
                if len(selected) == count:
                    break
        if not progress:
            # All conceptual families represented; additional numeric variants are useful for full-bank runs.
            remainder = [q for values in buckets.values() for q in values]
            rng.shuffle(remainder)
            selected.extend(remainder[: count - len(selected)])
            break
    rng.shuffle(selected)
    questions = []
    for q in selected:
        options = sample_choices(q, rng)
        questions.append(
            {
                **{
                    k: v
                    for k, v in q.items()
                    if k not in ("correct", "wrong", "distractor_sets")
                },
                "options": options,
            }
        )
    digest = hashlib.sha256(json.dumps(bank, sort_keys=True).encode()).hexdigest()
    return {
        "id": str(uuid.uuid4()),
        "seed": seed,
        "created_at": now(),
        "bank_sha256": digest,
        "bank_version": bank["version"],
        "questions": questions,
        "chapters": list(chapters),
    }


def grade(exam, answers):
    rows = []
    for i, q in enumerate(exam["questions"]):
        pick = answers.get(str(i), answers.get(i))
        correct = next(j for j, opt in enumerate(q["options"]) if opt["correct"])
        rows.append(
            {
                "index": i,
                "question_id": q["id"],
                "topic": q["topic"],
                "selected": pick,
                "correct_index": correct,
                "correct": pick == correct,
                "unanswered": pick is None,
            }
        )
    return normalize_result(
        {
            "correct": sum(r["correct"] for r in rows),
            "total": len(rows),
            "rows": rows,
        }
    )


def normalize_result(result):
    """Apply current scoring to saved rows without rewriting historical snapshots."""
    if not result or "rows" not in result:
        return result
    rows = result["rows"]
    attempted = [r for r in rows if r["selected"] is not None]
    return {
        **result,
        "total": len(attempted),
        "question_count": len(rows),
        "unanswered": len(rows) - len(attempted),
        "correct": sum(bool(r["correct"]) for r in attempted),
    }


class History:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = Path(path)
        self.db = sqlite3.connect(str(path))
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
          CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created TEXT, ended TEXT,
            status TEXT, snapshot TEXT, answers TEXT, seconds REAL, result TEXT);
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, run_id TEXT,
            at TEXT, kind TEXT, payload TEXT);
        """
        )
        self.db.commit()

    def begin(self, exam):
        with self.db:
            self.db.execute(
                "INSERT INTO runs VALUES(?,?,NULL,?,?,?,0,NULL)",
                (exam["id"], exam["created_at"], "in_progress", json.dumps(exam), "{}"),
            )

    def save(self, exam, answers, seconds, event=None):
        with self.db:
            self.db.execute(
                "UPDATE runs SET answers=?,seconds=? WHERE id=? AND status=?",
                (json.dumps(answers), seconds, exam["id"], "in_progress"),
            )
            if event:
                self.db.execute(
                    "INSERT INTO events(run_id,at,kind,payload) VALUES(?,?,?,?)",
                    (exam["id"], now(), event[0], json.dumps(event[1])),
                )

    def finish(self, exam, answers, seconds, status="completed"):
        result = grade(exam, answers)
        with self.db:
            self.db.execute(
                "UPDATE runs SET ended=?,status=?,answers=?,seconds=?,result=? WHERE id=? AND status=?",
                (
                    now(),
                    status,
                    json.dumps(answers),
                    seconds,
                    json.dumps(result),
                    exam["id"],
                    "in_progress",
                ),
            )
        return result

    def pending(self):
        row = self.db.execute(
            "SELECT snapshot,answers,seconds FROM runs WHERE status='in_progress' ORDER BY created DESC LIMIT 1"
        ).fetchone()
        return (json.loads(row[0]), json.loads(row[1]), row[2]) if row else None

    def is_personal_best(self, result):
        """Strict percentage record in this dataset's history; ties do not celebrate."""
        right, total = result["correct"], result["total"]
        if total <= 0 or right <= 0:
            return False
        for (saved,) in self.db.execute(
            "SELECT result FROM runs WHERE status='completed'"
        ):
            previous = normalize_result(json.loads(saved))
            if (
                previous["total"] > 0
                and right * previous["total"] <= previous["correct"] * total
            ):
                return False
        return True

    def runs(self):
        rows = self.db.execute(
            "SELECT id,created,status,seconds,result FROM runs ORDER BY created DESC"
        ).fetchall()
        return [
            {
                "id": r[0],
                "created": r[1],
                "status": r[2],
                "seconds": r[3],
                "result": normalize_result(json.loads(r[4])) if r[4] else None,
            }
            for r in rows
        ]

    def review(self, run_id):
        row = self.db.execute(
            "SELECT snapshot,answers,seconds,result FROM runs WHERE id=?", (run_id,)
        ).fetchone()
        return (
            json.loads(row[0]),
            json.loads(row[1]),
            row[2],
            normalize_result(json.loads(row[3])) if row[3] else None,
        )

    def stats(self):
        topics = defaultdict(lambda: {"right": 0, "total": 0})
        completed = [r for r in self.runs() if r["status"] == "completed"]
        for r in completed:
            for item in r["result"]["rows"]:
                if item["selected"] is None:
                    continue
                t = topics[item["topic"]]
                t["total"] += 1
                t["right"] += int(item["correct"])
        return dict(topics), completed

    def question_performance(self, question_id, current_run):
        """Attempts through this completed run; blanks/abandonments never break a streak."""
        attempts = []
        current_correct = None
        current_hinted = False
        for run_id, raw in self.db.execute(
            "SELECT id,result FROM runs WHERE status='completed' ORDER BY created,id"
        ):
            result = normalize_result(json.loads(raw))
            row = next(
                (r for r in result["rows"] if r["question_id"] == question_id), None
            )
            if row is not None and row["selected"] is not None:
                hinted = any(
                    json.loads(payload).get("question_id") == question_id
                    for (payload,) in self.db.execute(
                        "SELECT payload FROM events WHERE run_id=? AND kind='hint'",
                        (run_id,),
                    )
                )
                attempts.append((bool(row["correct"]), hinted))
                if run_id == current_run:
                    current_correct = bool(row["correct"])
                    current_hinted = hinted
            if run_id == current_run:
                break
        streak = 0
        streak_hinted = 0
        for right, hinted in reversed(attempts):
            if not right:
                break
            streak += 1
            streak_hinted += int(hinted)
        total_right = sum(right for right, _ in attempts)
        return {
            "attempts": len(attempts),
            "right": total_right,
            "streak": streak,
            "streak_hinted": streak_hinted,
            "hinted_attempts": sum(h for _, h in attempts),
            "current_correct": current_correct,
            "current_hinted": current_hinted,
            "first_correct": current_correct is True and total_right == 1,
        }

    def export(self, path):
        out = []
        for r in self.runs():
            exam, answers, seconds, result = self.review(r["id"])
            events = [
                {"at": e[0], "kind": e[1], "payload": json.loads(e[2])}
                for e in self.db.execute(
                    "SELECT at,kind,payload FROM events WHERE run_id=? ORDER BY id",
                    (r["id"],),
                )
            ]
            out.append(
                {
                    **r,
                    "exam": exam,
                    "answers": answers,
                    "result": result,
                    "events": events,
                }
            )
        Path(path).write_text(
            "\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n",
            encoding="utf-8",
        )

    def close(self):
        self.db.close()
