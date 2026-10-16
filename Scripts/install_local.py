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
        if sys.platform == "win32":
            import ctypes

            # Invalidate only this app's shell entries, never the global icon cache.
            notify = ctypes.windll.shell32.SHChangeNotify
            notify.argtypes = [
                ctypes.c_long,
                ctypes.c_uint,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ]
            notify.restype = None
            for path in [
                destination / "ProofQuest.exe",
                destination / "_internal/Assets/Fable/application.ico",
            ]:
                value = ctypes.create_unicode_buffer(str(path))
                notify(0x2000, 0x1005, ctypes.addressof(value), None)
            value = ctypes.create_unicode_buffer(str(destination))
            notify(0x1000, 0x1005, ctypes.addressof(value), None)
        print("Installed:", destination / "ProofQuest.exe")
        print("Settings and history are private and preserved on updates.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
