"""Install/update the distributable ZIP into the ignored personal testing folder."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from distribution import ARCHIVE_NAME, deploy, extract_archive, migrate_state

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "Dist" / ARCHIVE_NAME)
    parser.add_argument(
        "--migrate-dist-state",
        action="store_true",
        help="Move settings/history from the legacy Dist/ProofQuest folder once",
    )
    args = parser.parse_args()
    destination = ROOT / "Local" / "ProofQuest"
    try:
        (ROOT / "Out").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="install-", dir=ROOT / "Out"
        ) as temporary:
            staging = extract_archive(args.archive, temporary)
            if args.migrate_dist_state:
                migrate_state(ROOT / "Dist" / "ProofQuest", destination)
            deploy(staging, destination)
        print("Installed:", destination / "ProofQuest.exe")
        print("Settings and history are private and preserved on updates.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
