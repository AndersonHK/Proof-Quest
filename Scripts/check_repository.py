"""Check relative doc links, staged private paths, and release resource boundaries."""

import argparse, json, re, subprocess, sys, zipfile
from pathlib import Path
from distribution import ARCHIVE_NAME, inspect_archive
from build_python import PYTHON_ARCHIVE, inspect_python_archive
from build_msi import MSI_NAME, inspect_msi

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--git", default="git")
    args = parser.parse_args()
    errors = []
    for p in [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "THIRD-PARTY-NOTICES.md",
        ROOT / "Dist" / "README.md",
        ROOT / "Packaging" / "Python-README.md",
        *(ROOT / "Docs").rglob("*.md"),
    ]:
        for target in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            destination = (p.parent / target.split("#")[0]).resolve()
            if not destination.exists():
                errors.append(f"{p.relative_to(ROOT)}: missing {target}")
    result = subprocess.run(
        [args.git, "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    for value in result.stdout.split("\0"):
        if not value:
            continue
        parts = Path(value).parts
        if (
            any(
                x.lower() in {"datasets", "private", "local", "logs", "out", ".venv"}
                for x in parts
            )
            or Path(value).name.lower() == "proofquest.ini"
        ):
            errors.append("Private/generated path staged: " + value)
    release = ROOT / "Dist" / ARCHIVE_NAME
    if not release.is_file():
        errors.append("Missing distributable ZIP.")
    else:
        try:
            inspect_archive(release)
            with zipfile.ZipFile(release) as archive:
                sizes = {
                    info.filename.removeprefix("ProofQuest/"): info.file_size
                    for info in archive.infolist()
                    if not info.is_dir()
                    and info.filename != "ProofQuest/proofquest.ini"
                }
                version = (ROOT / "VERSION").read_text().strip()
                receipt = inspect_msi(ROOT / "Dist" / MSI_NAME, sizes, version)
                if (
                    json.loads(archive.read("ProofQuest/release-manifest.json"))[
                        "version"
                    ]
                    != receipt["version"]
                ):
                    errors.append("Windows ZIP and MSI versions differ.")
                for notice in ("LICENSE", "THIRD-PARTY-NOTICES.md"):
                    if archive.read("ProofQuest/" + notice).replace(b"\r\n", b"\n") != (
                        ROOT / notice
                    ).read_bytes().replace(b"\r\n", b"\n"):
                        errors.append(
                            "Bundled license/notice differs from source: " + notice
                        )
                for name in ("dataset.json", "questions.json"):
                    bundled = json.loads(
                        archive.read("ProofQuest/_internal/Examples/Demo/" + name)
                    )
                    original = json.loads(
                        (ROOT / "Examples" / "Demo" / name).read_text(encoding="utf-8")
                    )
                    if bundled != original:
                        errors.append("Bundled demo differs from the original: " + name)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
            errors.append(str(error))
    try:
        inspect_python_archive(ROOT / "Dist" / PYTHON_ARCHIVE, ROOT)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        errors.append(str(error))
    for path in (ROOT / "Dist").iterdir():
        if path.name not in {ARCHIVE_NAME, MSI_NAME, PYTHON_ARCHIVE, "README.md"}:
            errors.append("Unexpected loose content in Dist: " + path.name)
    if errors:
        print("\n".join(errors))
        return 1
    print(
        "Documentation, staged privacy, Windows ZIP/MSI and Python ZIP checks passed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
