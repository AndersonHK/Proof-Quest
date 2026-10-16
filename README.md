# Proof Quest

Proof Quest is a local Python desktop study app with randomized multiple-choice exams, saved practice history, and an optional audio guide with a searchable word-synchronized transcript. It loads independent datasets for any subject and number of chapters.

Fable, the violet fox, is the study companion. The interface uses violet actions, plum surfaces, and warm cream text, while green/red retain their grading meaning.

## Run

Download [Dist/ProofQuest-win-x64.zip](Dist/ProofQuest-win-x64.zip), extract it completely, and run `ProofQuest/ProofQuest.exe`. The ZIP contains everything needed, including the demo and its default INI. Keep `_internal` beside the EXE. Python is not required to run the packaged app.

For personal use and local testing in this repository, run `python Scripts/install_local.py`, then open `Local/ProofQuest/ProofQuest.exe`. `Local/` is Git-ignored. Updating that installation preserves your settings and practice history. `Dist/` contains only the shareable ZIP and is tracked.

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
| `Assets/Fable/` | Approved fox artwork, animation poses, and generation prompts |
| `Docs/` | Indexed current documentation |
| `Dist/ProofQuest-win-x64.zip` | Single tracked distribution with demo defaults and all runtime files |
| `Local/ProofQuest/` | Ignored personal installation and local testing runtime |
| `Datasets/`, `Private/` | Ignored private educational inputs and derived material |
| `Out/` | Ignored build intermediates, test receipts, screenshots |

See [AGENTS.md](AGENTS.md) for contributor instructions and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for runtime provenance. The executable is an unsigned local build; release evidence is in [Validation](Docs/Validation.md).

## License

Proof Quest is released under the [MIT license](LICENSE), copyright © 2026 Anderson Klein. Bundled third-party components retain their own licenses; see [third-party notices](THIRD-PARTY-NOTICES.md). External datasets retain their authors’ licenses and are not included.
