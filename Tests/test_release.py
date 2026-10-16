import configparser, hashlib, json, sqlite3, sys, zipfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from distribution import (
    DEMO_SETTINGS,
    create_archive,
    deploy,
    extract_archive,
    inspect_archive,
    migrate_state,
    write_demo_settings,
)


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "stage"
    root.mkdir()
    files = {
        "ProofQuest.exe": b"synthetic-executable",
        "_internal/python39.dll": b"synthetic-runtime",
        "_internal/Examples/Demo/dataset.json": b'{"id":"demo"}',
        "_internal/Examples/Demo/questions.json": b"{}",
        "_internal/Docs/User-Guide.md": b"# Synthetic help",
    }
    for name, data in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    write_demo_settings(root)
    manifest = {
        "version": "test",
        "files": sorted([*files, "proofquest.ini"]),
        "executable_sha256": hashlib.sha256(files["ProofQuest.exe"]).hexdigest(),
    }
    (root / "release-manifest.json").write_text(json.dumps(manifest))
    return root


def test_zip_is_complete_and_selects_demo(bundle, tmp_path):
    archive = create_archive(bundle, tmp_path / "release.zip")
    receipt = inspect_archive(archive)
    assert receipt["version"] == "test"
    extracted = extract_archive(archive, tmp_path / "unpacked")
    assert (extracted / "proofquest.ini").read_text() == DEMO_SETTINGS
    assert (extracted / "ProofQuest.exe").read_bytes() == b"synthetic-executable"
    assert (extracted / "_internal/Examples/Demo/dataset.json").exists()


def test_local_update_preserves_ini_and_history(bundle, tmp_path):
    destination = deploy(bundle, tmp_path / "Local" / "ProofQuest")
    (destination / "proofquest.ini").write_text("personal selection and settings")
    (destination / "Logs").mkdir()
    history = destination / "Logs" / "practice.sqlite3"
    history.write_bytes(b"history")
    old = destination / "_internal" / "obsolete.dll"
    old.write_bytes(b"old")
    receipt = json.loads((destination / "release-manifest.json").read_text())
    receipt["files"].append("_internal/obsolete.dll")
    (destination / "release-manifest.json").write_text(json.dumps(receipt))
    deploy(bundle, destination)
    assert (
        destination / "proofquest.ini"
    ).read_text() == "personal selection and settings"
    assert history.read_bytes() == b"history" and not old.exists()


@pytest.mark.parametrize(
    "entry",
    [
        "../escape.txt",
        "ProofQuest/../../escape.txt",
        "ProofQuest/Logs/history.sqlite3",
        "ProofQuest/Private/book.txt",
    ],
)
def test_zip_rejects_traversal_and_private_files(bundle, tmp_path, entry):
    archive = create_archive(bundle, tmp_path / "bad.zip")
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr(entry, "private")
    with pytest.raises(ValueError):
        extract_archive(archive, tmp_path / "extracted")
    assert not (tmp_path / "extracted").exists()


def test_zip_rejects_personal_ini(bundle, tmp_path):
    (bundle / "proofquest.ini").write_text(
        '[ProofQuest]\ndataset="../../Private/book.json"\n'
    )
    with pytest.raises(ValueError, match="public demo defaults"):
        create_archive(bundle, tmp_path / "bad.zip")


def test_verified_legacy_migration_rebases_path_and_retains_runs(tmp_path):
    old = tmp_path / "Dist" / "ProofQuest"
    new = tmp_path / "Local" / "ProofQuest"
    old.mkdir(parents=True)
    selected = tmp_path / "Private" / "课程.json"
    selected.parent.mkdir()
    selected.write_text("{}")
    (old / "proofquest.ini").write_text(
        '[ProofQuest]\ndataset="../../Private/课程.json"\nvolume=42\n', encoding="utf-8"
    )
    db = old / "Logs" / "course" / "practice.sqlite3"
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE runs(id TEXT,answer TEXT)")
    conn.execute("INSERT INTO runs VALUES(?,?)", ("saved", "🌙"))
    conn.commit()
    conn.close()
    migrate_state(old, new)
    config = configparser.ConfigParser(interpolation=None)
    config.read(new / "proofquest.ini", encoding="utf-8")
    assert (new / json.loads(config["ProofQuest"]["dataset"])).resolve() == selected
    assert config["ProofQuest"]["volume"] == "42"
    conn = sqlite3.connect(new / "Logs" / "course" / "practice.sqlite3")
    assert conn.execute("SELECT * FROM runs").fetchall() == [("saved", "🌙")]
    conn.close()
    assert (
        not (old / "Logs").exists()
        and (old / "proofquest.ini").read_text() == DEMO_SETTINGS
    )


def test_migration_refuses_existing_personal_state(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    write_demo_settings(old)
    (new / "proofquest.ini").write_text("personal")
    with pytest.raises(ValueError, match="already exist"):
        migrate_state(old, new)
    assert (new / "proofquest.ini").read_text() == "personal"
