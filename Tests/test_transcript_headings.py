import json
import re
from copy import deepcopy
import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel
from dataset import Dataset, DatasetError, validate_timings
from player import Listening
from transcript_layout import build_transcript


def structured_timing():
    text = "Chapter One. Tiny 🦊 Topic.\n\nFirst sentence. Second sentence."
    matches = list(re.finditer(r"\S.*?(?:[.!?](?=\s|$)|$)", text, re.S))
    words = []
    sentences = []
    for si, sentence in enumerate(matches):
        first = len(words)
        for word in re.finditer(r"\w+|🦊", sentence.group()):
            time = 100 + len(words) * 150
            words.append(
                {
                    "start": sentence.start() + word.start(),
                    "end": sentence.start() + word.end(),
                    "start_ms": time,
                    "end_ms": time + 100,
                    "sentence": si,
                }
            )
        sentences.append(
            {
                "start": sentence.start(),
                "end": sentence.end(),
                "start_ms": words[first]["start_ms"],
                "first_word": first,
            }
        )
    return {
        "text": text,
        "words": words,
        "sentences": sentences,
        "duration_ms": 2500,
        "voice": "SyntheticVoice",
        "sections": [],
        "headings": [
            {"start": 0, "end": sentences[1]["end"], "level": 1},
            {"start": sentences[2]["start"], "title": "Working notes 🧠", "level": 2},
            {"start": sentences[3]["start"], "end": sentences[3]["end"], "level": 3},
        ],
    }


def test_headings_keep_word_mapping_search_and_seek(qt, make_dataset):
    path = make_dataset(audio=True)
    data = structured_timing()
    (path.parent / "timings.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    p = Listening(Dataset(path))
    p.show()
    QTest.qWait(150)
    assert p.display.startswith("Chapter One. Tiny 🦊 Topic.\nWorking notes 🧠\n")
    assert "SyntheticVoice" not in p.note.text() and "at 1×" not in p.note.text()
    assert any(
        label.text().endswith(" · Listening Guide") for label in p.findChildren(QLabel)
    )
    for word, (start, end) in zip(data["words"], p.word_ranges):
        cursor = QTextCursor(p.text.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        assert cursor.selectedText() == data["text"][word["start"] : word["end"]]
    for block in p.display_blocks:
        cursor = QTextCursor(p.text.document())
        cursor.setPosition(block["start"] + 1)
        assert (
            cursor.charFormat().fontPointSize()
            == {0: 14, 1: 24, 2: 19, 3: 16}[block["level"]]
        )
        assert cursor.blockFormat().headingLevel() == block["level"]
    p.search.setText("Working notes")
    p.find_match(1)
    assert p.player.position() == data["sentences"][2]["start_ms"]
    fox_index = next(
        i
        for i, w in enumerate(data["words"])
        if data["text"][w["start"] : w["end"]] == "🦊"
    )
    p.tick(data["words"][fox_index]["start_ms"] + 10)
    assert p.text.extraSelections()[1].cursor.selectedText() == "🦊"
    p.jump_to_char(p.word_ranges[-1][0])
    assert p.player.position() == data["sentences"][-1]["start_ms"]
    p.shutdown()
    p.close()


def test_unstructured_transcripts_keep_existing_display():
    data = structured_timing()
    data.pop("headings")
    display = build_transcript(data)
    assert display["display"] == "\n".join(
        data["text"][s["start"] : s["end"]] for s in data["sentences"]
    )
    assert all(b["level"] == 0 for b in display["blocks"])


@pytest.mark.parametrize(
    "change",
    [
        lambda h: h[0].update(start=1),
        lambda h: h[0].update(end=5),
        lambda h: h[1].update(level=4),
        lambda h: h[1].update(title="Two\nparagraphs"),
        lambda h: h[0].update(title="Duplicate replacement"),
        lambda h: h[1].update(start=0),
    ],
)
def test_invalid_heading_metadata_is_rejected(change):
    data = structured_timing()
    change(data["headings"])
    with pytest.raises(DatasetError):
        validate_timings(data)
