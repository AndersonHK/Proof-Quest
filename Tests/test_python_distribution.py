import json
import sys
import zipfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from build_python import build_python, inspect_python_archive, source_payload

ROOT = Path(__file__).resolve().parents[1]


def test_python_zip_is_reproducible_and_has_only_public_sources(tmp_path):
    a = build_python(ROOT, tmp_path / "a.zip")
    b = build_python(ROOT, tmp_path / "b.zip")
    assert a.read_bytes() == b.read_bytes()
    receipt = inspect_python_archive(a, ROOT)
    assert receipt["version"] == (ROOT / "VERSION").read_text().strip()
    assert "Src/player.py" in receipt["files"]
    assert not any(
        n.endswith((".exe", ".dll", ".mp3", ".sqlite3")) for n in receipt["files"]
    )


@pytest.mark.parametrize(
    "name",
    ["ProofQuest/Private/book.txt", "../escape.py", "ProofQuest/Src/session.mp3"],
)
def test_python_zip_rejects_unapproved_content(tmp_path, name):
    archive = build_python(ROOT, tmp_path / "bad.zip")
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr(name, "do not ship")
    with pytest.raises(ValueError):
        inspect_python_archive(archive)
