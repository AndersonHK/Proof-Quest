"""Build the platform-independent source edition using an explicit public whitelist."""

import argparse
import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path

from distribution import safe_relative

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ARCHIVE = "ProofQuest-python.zip"
SOURCE_FOLDERS = {
    "Src": {".py"},
    "Assets": {".png", ".ico", ".txt", ".json", ".ttf", ".otf"},
    "Schemas": {".json"},
    "Examples/Demo": {".json"},
    "Docs": {".md"},
    "ThirdParty/Licenses": {".txt", ".md"},
}
SOURCE_FILES = ("requirements.txt", "LICENSE", "THIRD-PARTY-NOTICES.md", "VERSION")
SOURCE_INI = '[ProofQuest]\ndataset = "Examples/Demo/dataset.json"\n'


def source_payload(root):
    root = Path(root).resolve()
    payload = {}
    for folder, extensions in SOURCE_FOLDERS.items():
        for path in sorted((root / folder).rglob("*")):
            if "__pycache__" in path.parts or not path.is_file():
                continue
            if path.suffix.lower() not in extensions:
                raise ValueError(
                    f"Unexpected source resource: {path.relative_to(root)}"
                )
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError("Source resource escaped the repository.")
            payload[path.relative_to(root).as_posix()] = path.read_bytes()
    for name in SOURCE_FILES:
        payload[name] = (root / name).read_bytes()
    payload["README.md"] = (root / "Packaging/Python-README.md").read_bytes()
    payload["proofquest.ini"] = SOURCE_INI.encode()
    return payload


def inspect_python_archive(path, root=None):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate source ZIP members.")
        for info in archive.infolist():
            relative = safe_relative(info.filename)
            if relative.parts[0] != "ProofQuest" or stat.S_ISLNK(
                info.external_attr >> 16
            ):
                raise ValueError("Invalid source ZIP member.")
            name = relative.relative_to("ProofQuest").as_posix()
            allowed = name in {
                *SOURCE_FILES,
                "README.md",
                "proofquest.ini",
                "source-manifest.json",
            }
            for folder, extensions in SOURCE_FOLDERS.items():
                allowed |= (
                    name.startswith(folder + "/")
                    and relative.suffix.lower() in extensions
                )
            if not allowed or "__pycache__" in relative.parts:
                raise ValueError(f"Unexpected source ZIP content: {name}")
        payload = {n.removeprefix("ProofQuest/"): archive.read(n) for n in names}
        manifest = json.loads(payload.pop("source-manifest.json"))
        if set(payload) != set(manifest["files"]):
            raise ValueError("Source ZIP inventory mismatch.")
        for name, data in payload.items():
            if hashlib.sha256(data).hexdigest() != manifest["files"][name]:
                raise ValueError(f"Source ZIP hash mismatch: {name}")
        for name in ("Src/app.py", "Examples/Demo/dataset.json", *SOURCE_FILES):
            if name not in payload:
                raise ValueError(f"Missing source resource: {name}")
        if payload["proofquest.ini"].decode() != SOURCE_INI:
            raise ValueError("Source edition must select the public demo.")
        if root is not None and payload != source_payload(root):
            raise ValueError("Source ZIP differs from current public sources.")
        if archive.testzip():
            raise ValueError("Source ZIP CRC failure.")
        return manifest


def build_python(root=ROOT, destination=None):
    root = Path(root)
    destination = Path(destination or root / "Dist" / PYTHON_ARCHIVE)
    payload = source_payload(root)
    manifest = {
        "version": payload["VERSION"].decode().strip(),
        "edition": "Python source; install platform-specific dependencies separately",
        "files": {
            name: hashlib.sha256(data).hexdigest() for name, data in payload.items()
        },
    }
    payload["source-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".zip.tmp")
    with zipfile.ZipFile(
        temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for name, data in sorted(payload.items()):
            # Fixed metadata makes identical source inputs produce identical archives.
            info = zipfile.ZipInfo("ProofQuest/" + name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    inspect_python_archive(temporary, root)
    os.replace(temporary, destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    print("Built:", build_python(destination=parser.parse_args().output))
