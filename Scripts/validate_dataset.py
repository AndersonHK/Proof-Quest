import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Src"))
from dataset import Dataset, DatasetError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        dataset = Dataset(args.manifest)
        print(
            f'Valid: {dataset.title}; {len(dataset.chapters)} chapters; {len(dataset.bank["questions"])} questions; audio: {dataset.audio_path is not None}'
        )
        return 0
    except DatasetError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
