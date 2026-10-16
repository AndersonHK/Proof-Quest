# Proof Quest

Proof Quest is a local Python desktop study app with randomized multiple-choice exams, saved practice history, and an optional audio guide with a searchable word-synchronized transcript. It loads independent datasets for any subject and number of chapters.

## Run

Open [Dist/ProofQuest/ProofQuest.exe](Dist/ProofQuest/ProofQuest.exe). Keep the entire `Dist/ProofQuest` folder together; Python is not required for the packaged app.

Click **Select new dataset** and choose its `dataset.json`. The **Help** button explains practice, grading, playback, and dataset selection. The initial release includes a small original demo. Private course datasets are external and ignored by Git.

The selected dataset, window dimensions, chapter filters, run mode, volume, playback speed, and playback position are saved in `proofquest.ini` beside the executable. Run the app from a writable folder. Practice history is stored in adjacent `Logs/`, separately for each dataset.

## Develop

Use Windows x64 and Python 3.9 or newer. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe Src\app.py
.venv\Scripts\python.exe -m pytest Tests -q
.venv\Scripts\python.exe Scripts\build.py
```

The build script does not install dependencies. [Build and validation](Docs/Development.md) describes the reproducible packaging and smoke checks. [Dataset format](Docs/Dataset-Format.md) defines the JSON contracts and includes guidance for generating material from another book.

| Directory | Purpose |
|---|---|
| `Src/` | UI, exam engine, dataset loader, settings, audio player |
| `Schemas/` | Versioned JSON schemas |
| `Examples/Demo/` | Original synthetic public dataset |
| `Tests/`, `Scripts/` | Regression tests, build and validation tools |
| `Assets/` | Original application badge |
| `Docs/` | Indexed current documentation |
| `Dist/ProofQuest/` | Current tracked executable and required runtime files |
| `Datasets/`, `Private/` | Ignored private educational inputs and derived material |
| `Out/` | Ignored build intermediates, test receipts, screenshots |

See [AGENTS.md](AGENTS.md) for contributor instructions and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for runtime provenance. This initial repository has no remote configured. The executable is an unsigned local build; release evidence is in [Validation](Docs/Validation.md).
