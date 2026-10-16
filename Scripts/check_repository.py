"""Check relative doc links, staged private paths, and release resource boundaries."""

import argparse, json, re, subprocess, sys, zipfile
from pathlib import Path
from distribution import ARCHIVE_NAME, inspect_archive

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
    for path in (ROOT / "Dist").iterdir():
        if path.name != ARCHIVE_NAME:
            errors.append("Unexpected loose content in Dist: " + path.name)
    if errors:
        print("\n".join(errors))
        return 1
    print("Documentation links, staged privacy boundaries, and demo ZIP checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
