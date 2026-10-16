"""Build only public app resources; datasets and mutable settings stay external."""

import hashlib, importlib.metadata, json, os, platform, shutil, subprocess, sys
from pathlib import Path

from distribution import ARCHIVE_NAME, create_archive, write_demo_settings
from build_icon import build_icon

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = importlib.metadata.version("pyinstaller")
    if version != "6.16.0":
        raise RuntimeError("Use pinned PyInstaller 6.16.0 from requirements-dev.txt.")
    out = ROOT / "Out"
    out.mkdir(exist_ok=True)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon

    app = QApplication.instance() or QApplication([])
    icon = build_icon(ROOT)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--noupx",
        "--name",
        "ProofQuest",
        "--icon",
        str(icon),
        "--distpath",
        str(out / "Package"),
        "--workpath",
        str(out / "Build"),
        "--specpath",
        str(out),
        "--paths",
        str(ROOT / "Src"),
    ]
    for source, dest in [
        ("Assets", "Assets"),
        ("Examples/Demo", "Examples/Demo"),
        ("Docs", "Docs"),
        ("Schemas", "Schemas"),
    ]:
        command += ["--add-data", str(ROOT / source) + os.pathsep + dest]
    command += [str(ROOT / "Src" / "app.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    release = out / "Package" / "ProofQuest"
    licenses = release / "Licenses"
    licenses.mkdir(exist_ok=True)
    for dependency in [
        "PySide6",
        "PySide6-Essentials",
        "PySide6-Addons",
        "shiboken6",
        "pyinstaller",
    ]:
        distribution = importlib.metadata.distribution(dependency)
        for relative in distribution.files or []:
            name = Path(relative).name
            if any(
                word in name.lower() for word in ["license", "copying", "notice"]
            ) and Path(relative).suffix.lower() in [".txt", ".md", ""]:
                path = Path(distribution.locate_file(relative))
                if path.is_file():
                    dest = licenses / dependency
                    dest.mkdir(exist_ok=True)
                    shutil.copy2(path, dest / name)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.exists():
        shutil.copy2(python_license, licenses / "Python-LICENSE.txt")
    shutil.copy2(ROOT / "THIRD-PARTY-NOTICES.md", release / "THIRD-PARTY-NOTICES.md")
    if (ROOT / "ThirdParty" / "Licenses").exists():
        shutil.copytree(
            ROOT / "ThirdParty" / "Licenses",
            licenses / "Additional",
            dirs_exist_ok=True,
        )
    # Preserve all license wording while normalizing upstream trailing whitespace.
    for path in licenses.rglob("*.txt"):
        text = path.read_text(encoding="utf-8")
        normalized = (
            "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
        )
        path.write_bytes(normalized.encode("utf-8"))
    write_demo_settings(release)
    (release / "START-HERE.txt").write_text(
        "PROOF QUEST\n\nExtract this entire folder, then run ProofQuest.exe.\n"
        "No Python installation is required. Keep _internal beside the EXE.\n"
        "The sample demo is selected automatically. Use Help or Select new dataset.\n"
        "Settings and progress are stored beside the EXE; use a writable folder.\n",
        encoding="utf-8",
    )
    hashes = {
        str(p.relative_to(ROOT))
        .replace("\\", "/"): hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n"))
        .hexdigest()
        for folder in ["Src", "Assets", "Schemas", "Examples/Demo", "Docs", "Scripts"]
        for p in (ROOT / folder).rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    manifest = {
        "version": (ROOT / "VERSION").read_text().strip(),
        "python": platform.python_version(),
        "platform": "Windows x64",
        "pyside6": importlib.metadata.version("PySide6"),
        "pyinstaller": version,
        "sources": hashes,
        "executable_sha256": hashlib.sha256(
            (release / "ProofQuest.exe").read_bytes()
        ).hexdigest(),
        "bundled_dataset": "Original synthetic demo only; no private course content.",
        "files": sorted(
            p.relative_to(release).as_posix() for p in release.rglob("*") if p.is_file()
        ),
    }
    (release / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    destination = ROOT / "Dist" / ARCHIVE_NAME
    create_archive(release, destination)
    print("Built distributable:", destination)


if __name__ == "__main__":
    main()
