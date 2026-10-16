import importlib.util, json
from pathlib import Path


def test_release_refresh_preserves_private_files(tmp_path):
    script = Path(__file__).resolve().parents[1] / "Scripts" / "build.py"
    spec = importlib.util.spec_from_file_location("build", script)
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    staging = tmp_path / "stage"
    destination = tmp_path / "release"
    staging.mkdir()
    destination.mkdir()
    (staging / "ProofQuest.exe").write_bytes(b"new executable")
    (destination / "proofquest.ini").write_text("personal settings")
    (destination / "Logs").mkdir()
    (destination / "Logs" / "history.sqlite3").write_bytes(b"personal history")
    (destination / "_internal").mkdir()
    (destination / "_internal" / "obsolete.dll").write_bytes(b"old")
    (destination / "release-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    "_internal/obsolete.dll",
                    "proofquest.ini",
                    "Logs/history.sqlite3",
                    "../outside",
                ]
            }
        )
    )
    build.publish(staging, destination)
    assert (destination / "ProofQuest.exe").read_bytes() == b"new executable"
    assert (destination / "proofquest.ini").read_text() == "personal settings"
    assert (
        destination / "Logs" / "history.sqlite3"
    ).read_bytes() == b"personal history"
    assert not (destination / "_internal" / "obsolete.dll").exists()
