"""Public ZIP packaging and data-preserving local deployment (standard library only)."""

import configparser
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE_NAME = "ProofQuest-win-x64.zip"
DEMO_DATASET = "_internal/Examples/Demo/dataset.json"
DEMO_SETTINGS = (
    "[ProofQuest]\n"
    'dataset = "_internal/Examples/Demo/dataset.json"\n'
    "window_width = 1240\n"
    "window_height = 860\n"
    "mode = 1\n"
    "question_count = 40\n"
    "volume = 75\n"
    "playback_rate = 1\n"
    "follow_narration = true\n"
)


def write_demo_settings(folder):
    path = Path(folder) / "proofquest.ini"
    path.write_bytes(DEMO_SETTINGS.encode("utf-8"))


def safe_relative(name):
    path = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or path.is_absolute()
        or ".." in path.parts
        or ":" in name
    ):
        raise ValueError(f"Unsafe distribution path: {name}")
    return path


def inspect_archive(path):
    """Validate a complete public bundle without extracting any files."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member names.")
        for info in archive.infolist():
            relative = safe_relative(info.filename)
            if relative.parts[0] != "ProofQuest":
                raise ValueError(
                    "The ZIP must contain one ProofQuest top-level folder."
                )
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Symlinks are not permitted in the ZIP.")
            if any(
                p.lower()
                in {"datasets", "private", "logs", "out", ".venv", "__pycache__"}
                for p in relative.parts
            ):
                raise ValueError(f"Private/generated content in ZIP: {relative}")
            if relative.suffix.lower() in {
                ".sqlite3",
                ".log",
                ".mp3",
                ".wav",
                ".docx",
                ".pdf",
            }:
                raise ValueError(f"Unexpected private content in ZIP: {relative}")
            if (
                relative.name.lower() == "proofquest.ini"
                and str(relative) != "ProofQuest/proofquest.ini"
            ):
                raise ValueError("Unexpected settings file in the ZIP.")
        required = [
            "ProofQuest.exe",
            "proofquest.ini",
            "release-manifest.json",
            DEMO_DATASET,
            "_internal/Examples/Demo/questions.json",
            "_internal/Docs/User-Guide.md",
        ]
        for relative in required:
            if "ProofQuest/" + relative not in names:
                raise ValueError(f"Missing runtime resource: {relative}")
        if not any(
            re.fullmatch(r"ProofQuest/_internal/python3\d+\.dll", name)
            for name in names
        ):
            raise ValueError("Missing bundled Python runtime DLL.")
        if (
            archive.read("ProofQuest/proofquest.ini")
            .decode("utf-8")
            .replace("\r\n", "\n")
            != DEMO_SETTINGS
        ):
            raise ValueError(
                "Distribution INI must contain only the public demo defaults."
            )
        manifest = json.loads(archive.read("ProofQuest/release-manifest.json"))
        actual = {
            name.removeprefix("ProofQuest/") for name in names if not name.endswith("/")
        }
        if actual != set(manifest["files"]) | {"release-manifest.json"}:
            raise ValueError("ZIP contents differ from the release manifest inventory.")
        digest = hashlib.sha256(archive.read("ProofQuest/ProofQuest.exe")).hexdigest()
        if digest != manifest["executable_sha256"]:
            raise ValueError("Executable hash does not match the release manifest.")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed.")
        return manifest


def create_archive(staging, destination):
    staging, destination = Path(staging).resolve(), Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".zip.tmp")
    with zipfile.ZipFile(
        temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(
                    path, "ProofQuest/" + path.relative_to(staging).as_posix()
                )
    inspect_archive(temporary)
    os.replace(temporary, destination)
    return destination


def extract_archive(archive_path, staging_parent):
    inspect_archive(archive_path)
    staging_parent = Path(staging_parent).resolve()
    staging_parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            relative = safe_relative(info.filename)
            target = (staging_parent / Path(*relative.parts)).resolve()
            if not target.is_relative_to(staging_parent):
                raise ValueError("Extraction escaped staging directory.")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
    return staging_parent / "ProofQuest"


def require_closed(folder):
    """Windows locks a loaded EXE against writing. Do not terminate a user's run."""
    executable = Path(folder) / "ProofQuest.exe"
    if os.name == "nt" and executable.exists():
        try:
            with executable.open("r+b"):
                pass
        except PermissionError as error:
            raise RuntimeError(
                f"Close Proof Quest in {folder} before updating or migrating it."
            ) from error


def deploy(staging, destination):
    """Copy release-managed files only; preserve local settings and practice data."""
    staging, destination = Path(staging).resolve(), Path(destination).resolve()
    require_closed(destination)
    manifest = json.loads(
        (staging / "release-manifest.json").read_text(encoding="utf-8")
    )
    names = set(manifest["files"]) | {"release-manifest.json"}
    for name in names:
        safe_relative(name)
        source = (staging / name).resolve()
        target = (destination / name).resolve()
        if not source.is_relative_to(staging) or not target.is_relative_to(destination):
            raise ValueError("Release inventory escaped its folder.")
        if not source.is_file():
            raise ValueError(f"Missing managed file: {name}")
    destination.mkdir(parents=True, exist_ok=True)
    receipt = destination / "release-manifest.json"
    previous = (
        json.loads(receipt.read_text(encoding="utf-8")).get("files", [])
        if receipt.exists()
        else []
    )
    for name in previous:
        relative = safe_relative(name)
        target = (destination / name).resolve()
        if not target.is_relative_to(destination):
            raise ValueError("Old inventory escaped installation.")
        managed = relative.parts[0] in {"_internal", "Licenses"} or name in {
            "ProofQuest.exe",
            "THIRD-PARTY-NOTICES.md",
        }
        if managed and name not in names and target.is_file():
            target.unlink()
    # Keep the receipt last, so a failed copy cannot claim a successful installation.
    for name in sorted(names - {"release-manifest.json"}):
        target = destination / name
        if name == "proofquest.ini" and target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(staging / name, target)
    shutil.copy2(staging / "release-manifest.json", receipt)
    if (
        hashlib.sha256((destination / "ProofQuest.exe").read_bytes()).hexdigest()
        != manifest["executable_sha256"]
    ):
        raise RuntimeError("Installed executable failed verification.")
    return destination


def migrate_state(old_home, new_home):
    """One-time migration of legacy Dist state; retain both copies until verified."""
    old_home, new_home = Path(old_home).resolve(), Path(new_home).resolve()
    if old_home == new_home:
        raise ValueError("Migration folders must be different.")
    require_closed(old_home)
    require_closed(new_home)
    old_ini, new_ini = old_home / "proofquest.ini", new_home / "proofquest.ini"
    old_logs, new_logs = old_home / "Logs", new_home / "Logs"
    # Do not guess how to merge two independently used installations.
    if (
        new_ini.exists()
        and new_ini.read_text(encoding="utf-8").replace("\r\n", "\n") != DEMO_SETTINGS
    ):
        raise ValueError(
            "Local settings already exist; refusing to overwrite them during migration."
        )
    if new_logs.exists() and any(new_logs.rglob("*")):
        raise ValueError(
            "Local history already exists; refusing to merge it automatically."
        )
    new_home.mkdir(parents=True, exist_ok=True)
    if old_ini.exists():
        config = configparser.ConfigParser(interpolation=None)
        config.read(old_ini, encoding="utf-8")
        value = json.loads(config.get("ProofQuest", "dataset", fallback='""'))
        if value:
            selected = Path(value)
            if not selected.is_absolute():
                selected = (old_home / selected).resolve()
            # Bundled demo moves with the application; private selections stay external.
            if selected == (old_home / DEMO_DATASET).resolve():
                selected = new_home / DEMO_DATASET
            try:
                relative = os.path.relpath(selected, new_home)
            except ValueError:
                relative = str(selected)
            config.set(
                "ProofQuest", "dataset", json.dumps(relative, ensure_ascii=False)
            )
        with new_ini.open("w", encoding="utf-8") as f:
            config.write(f)
    if old_logs.exists():
        for source in sorted(old_logs.rglob("*")):
            if not source.is_file():
                continue
            if not source.resolve().is_relative_to(old_logs.resolve()):
                raise ValueError("Log symlink escaped migration folder.")
            relative = source.relative_to(old_logs)
            target = new_logs / relative
            if source.name.endswith(("-wal", "-shm", "-journal")):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == ".sqlite3":
                src = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
                dst = sqlite3.connect(target)
                try:
                    src.backup(dst)
                    if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise RuntimeError("Migrated history failed integrity check.")
                    if list(src.iterdump()) != list(dst.iterdump()):
                        raise RuntimeError("Migrated history differs from original.")
                finally:
                    dst.close()
                    src.close()
            else:
                shutil.copy2(source, target)
                if (
                    hashlib.sha256(source.read_bytes()).digest()
                    != hashlib.sha256(target.read_bytes()).digest()
                ):
                    raise RuntimeError("Migrated log differs from original.")
    # Removal happens only after the copied data has passed verification.
    if old_logs.exists():
        resolved = old_logs.resolve()
        if resolved != old_home / "Logs" or not resolved.is_relative_to(old_home):
            raise ValueError("Unsafe legacy log cleanup path.")
        shutil.rmtree(resolved)
    write_demo_settings(old_home)
