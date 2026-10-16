"""Versioned, non-executable UTF-8 dataset loader with no chapter/text caps."""

import hashlib
import json
import math
from pathlib import Path


class DatasetError(ValueError):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise DatasetError(f"{Path(path).name}: {error}") from error


def require(condition, message):
    if not condition:
        raise DatasetError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def member_path(root, value):
    require(nonempty(value), "File references must be nonempty relative paths.")
    path = (root / value).resolve()
    require(
        not Path(value).is_absolute() and path.is_relative_to(root),
        "Dataset file references must stay inside the dataset folder.",
    )
    require(path.is_file(), f"Missing dataset file: {value}")
    return path


def validate_bank(bank, chapter_ids=None):
    require(isinstance(bank, dict), "Question bank must be an object.")
    require(nonempty(bank.get("version")), "Question bank needs a version string.")
    questions = bank.get("questions")
    require(
        isinstance(questions, list) and bool(questions),
        "The question bank must contain questions.",
    )
    ids = set()
    for index, q in enumerate(questions):
        require(isinstance(q, dict), f"Question {index+1} must be an object.")
        for key in [
            "id",
            "chapter",
            "topic",
            "family",
            "prompt",
            "explanation",
            "source",
        ]:
            require(
                nonempty(q.get(key)),
                f"Question {index+1}: {key} must be a nonempty string.",
            )
        require(q["id"] not in ids, f'Duplicate question ID: {q["id"]}')
        ids.add(q["id"])
        if chapter_ids is not None:
            require(
                q["chapter"] in chapter_ids,
                f'Question {q["id"]} references unknown chapter {q["chapter"]}.',
            )
        for key, minimum in [("correct", 2), ("wrong", 8)]:
            require(
                isinstance(q.get(key), list) and len(q[key]) >= minimum,
                f'{q["id"]}: at least {minimum} {key} alternatives required.',
            )
            require(
                all(nonempty(a) for a in q[key]),
                f'{q["id"]}: answers must be nonempty text.',
            )
        answers = q["correct"] + q["wrong"]
        require(
            len({a.strip().casefold() for a in answers}) == len(answers),
            f'{q["id"]}: duplicate/overlapping answer text.',
        )
    return bank


def validate_timings(data):
    require(
        isinstance(data, dict) and isinstance(data.get("text"), str),
        "Timings must include transcript text.",
    )
    text = data["text"]
    duration = data.get("duration_ms")
    require(
        isinstance(duration, (int, float)) and math.isfinite(duration) and duration > 0,
        "Audio duration must be positive and finite.",
    )
    words = data.get("words")
    sentences = data.get("sentences")
    sections = data.get("sections", [])
    require(isinstance(words, list) and bool(words), "Word timings are required.")
    require(
        isinstance(sentences, list) and bool(sentences),
        "Sentence offsets are required.",
    )
    previous_end = 0
    previous_time = -1
    for s in sentences:
        require(
            isinstance(s, dict)
            and all(
                type(s.get(k)) is int
                for k in ["start", "end", "start_ms", "first_word"]
            ),
            "Sentence offsets must be integers.",
        )
        require(
            previous_end <= s["start"] < s["end"] <= len(text),
            "Invalid or overlapping sentence character offsets.",
        )
        require(
            previous_time <= s["start_ms"] <= duration
            and 0 <= s["first_word"] < len(words),
            "Invalid sentence timing or word reference.",
        )
        previous_end = s["end"]
        previous_time = s["start_ms"]
    previous_end = 0
    previous_time = -1
    for w in words:
        require(
            isinstance(w, dict)
            and all(
                type(w.get(k)) is int
                for k in ["start", "end", "start_ms", "end_ms", "sentence"]
            ),
            "Word offsets must be integers.",
        )
        require(
            previous_end <= w["start"] < w["end"] <= len(text),
            "Invalid or overlapping word character offsets.",
        )
        require(
            previous_time <= w["start_ms"] <= w["end_ms"] <= duration,
            "Invalid word timing.",
        )
        require(0 <= w["sentence"] < len(sentences), "Unknown sentence reference.")
        s = sentences[w["sentence"]]
        require(
            s["start"] <= w["start"] < w["end"] <= s["end"],
            "Word lies outside its sentence.",
        )
        previous_end = w["end"]
        previous_time = w["start_ms"]
    for s in sentences:
        w = words[s["first_word"]]
        require(
            s["start"] <= w["start"] < s["end"] and s["start_ms"] == w["start_ms"],
            "Sentence start must match its first word.",
        )
    require(isinstance(sections, list), "Sections must be an array.")
    previous_time = -1
    for section in sections:
        require(
            isinstance(section, dict) and nonempty(section.get("title")),
            "Audio section needs a title.",
        )
        require(
            type(section.get("start_ms")) is int
            and previous_time <= section["start_ms"] <= duration,
            "Invalid audio section start.",
        )
        previous_time = section["start_ms"]
    return data


class Dataset:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.root = self.path.parent
        self.manifest = read_json(self.path)
        m = self.manifest
        require(
            isinstance(m, dict) and m.get("schema_version") == 1,
            "Unsupported dataset schema; expected schema_version 1.",
        )
        for key in ["id", "title", "question_bank"]:
            require(nonempty(m.get(key)), f"Dataset needs a nonempty {key}.")
        chapters = m.get("chapters")
        require(
            isinstance(chapters, list) and bool(chapters),
            "Dataset must define at least one chapter.",
        )
        require(
            all(
                isinstance(c, dict)
                and nonempty(c.get("id"))
                and nonempty(c.get("title"))
                for c in chapters
            ),
            "Chapters need string id and title fields.",
        )
        self.chapter_titles = {c["id"]: c["title"] for c in chapters}
        require(
            len(self.chapter_titles) == len(chapters), "Chapter IDs must be unique."
        )
        self.bank = validate_bank(
            read_json(member_path(self.root, m["question_bank"])), self.chapter_titles
        )
        used = {q["chapter"] for q in self.bank["questions"]}
        require(
            used == set(self.chapter_titles),
            "Each declared chapter must have at least one question.",
        )
        self.id = m["id"]
        self.title = m["title"]
        self.chapters = chapters
        self.history_key = hashlib.sha256(self.id.encode("utf-8")).hexdigest()[:24]
        self.audio_path = None
        self.timings = None
        audio = m.get("audio")
        if audio is not None:
            require(isinstance(audio, dict), "audio must be an object or null.")
            self.audio_path = member_path(self.root, audio.get("file"))
            self.timings = validate_timings(
                read_json(member_path(self.root, audio.get("timings")))
            )
