import json, os, re, sys, wave
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Src"))
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qt():
    from app import STYLE, configure_fonts

    app = QApplication.instance() or QApplication([])
    configure_fonts(app)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    return app


@pytest.fixture
def make_dataset(tmp_path):
    counter = [0]

    def make(chapters=2, audio=False, long=False):
        counter[0] += 1
        root = tmp_path / f"data-{counter[0]}"
        root.mkdir()
        template = json.loads(
            (ROOT / "Examples" / "Demo" / "questions.json").read_text(encoding="utf-8")
        )["questions"][0]
        qs = []
        for i in range(chapters):
            q = {
                **template,
                "id": f"q{i}",
                "chapter": f"c{i}",
                "family": f"f{i}",
                "topic": f"topic{i}",
            }
            if long:
                q["prompt"] = "🌙 漢字 <literal> " + "Long question text. " * 300
                q["correct"] = [
                    "答え 🌙 " + "valid text " * 250,
                    "Another valid answer.",
                ]
            qs.append(q)
        manifest = {
            "schema_version": 1,
            "id": f"synthetic-{counter[0]}",
            "title": "Synthetic 🌙 dataset",
            "chapters": [
                {"id": f"c{i}", "title": f"Unit {i}"} for i in range(chapters)
            ],
            "question_bank": "questions.json",
        }
        (root / "questions.json").write_text(
            json.dumps({"version": "1", "questions": qs}, ensure_ascii=False),
            encoding="utf-8",
        )
        if audio:
            text = "Hello 🌙 world.\n你好 world."
            words = []
            for i, m in enumerate(re.finditer(r"\w+|🌙", text)):
                words.append(
                    {
                        "start": m.start(),
                        "end": m.end(),
                        "start_ms": 100 + i * 300,
                        "end_ms": 300 + i * 300,
                        "sentence": 0 if i < 3 else 1,
                    }
                )
            sentences = [
                {"start": 0, "end": 14, "first_word": 0, "start_ms": 100},
                {"start": 15, "end": len(text), "first_word": 3, "start_ms": 1000},
            ]
            timings = {
                "text": text,
                "duration_ms": 2500,
                "words": words,
                "sentences": sentences,
                "sections": [{"title": "Demo guide", "start_ms": 0}],
            }
            (root / "timings.json").write_text(
                json.dumps(timings, ensure_ascii=False), encoding="utf-8"
            )
            with wave.open(str(root / "guide.wav"), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(24000)
                f.writeframes(b"\0\0" * 60000)
            manifest["audio"] = {"file": "guide.wav", "timings": "timings.json"}
        path = root / "dataset.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return path

    return make
