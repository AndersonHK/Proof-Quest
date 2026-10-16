"""Check relative doc links, staged private paths, and release resource boundaries."""

import argparse, json, re, subprocess, sys
from pathlib import Path

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
                x.lower() in {"datasets", "private", "logs", "out", ".venv"}
                for x in parts
            )
            or Path(value).name.lower() == "proofquest.ini"
        ):
            errors.append("Private/generated path staged: " + value)
    release = ROOT / "Dist" / "ProofQuest"
    if release.exists():
        for path in release.rglob("*"):
            relative = path.relative_to(release)
            if any(x.lower() in {"datasets", "private"} for x in relative.parts):
                errors.append("Private release content: " + str(relative))
            if (
                path.name in ["questions.json", "dataset.json"]
                and "Demo" not in relative.parts
            ):
                errors.append("Non-demo dataset bundled: " + str(relative))
            if path.suffix.lower() in {".mp3", ".wav", ".docx", ".pdf"}:
                errors.append("Unexpected source/media in release: " + str(relative))
    if errors:
        print("\n".join(errors))
        return 1
    print("Documentation links, staged paths, and release resource boundaries passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
