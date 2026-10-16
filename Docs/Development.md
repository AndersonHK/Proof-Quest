# Development and release

Proof Quest uses PySide6 widgets and Qt Multimedia. Dataset loading, settings, exam generation/history, playback, and the main window have separate source modules. [Dataset format](Dataset-Format.md) owns external content contracts; [User guide](User-Guide.md) owns visible behavior.

`Src/theme.py` owns the Fable palette. The header XP counter remains an unboxed, content-sized label; button focus changes border color without changing layout geometry. `Src/mascot.py` renders the approved PNG poses from `Assets/Fable/`: neutral, half-lidded in-between, closed blink, and one-eye check-in. The animation renders at 30 fps with timed pose holds and a very small breathing transform; the check-in lasts 1.6 seconds. This is pose-based animation with generated intermediate eye artwork, not thirty unique drawings per second. Timers pause when the mascot is hidden. Built-in image-generation prompts are retained in `Assets/Fable/Prompts.txt`; third-party reference screenshots and rejected drafts are not shipped.

## Environment and checks

Use an isolated environment and the pinned requirements. Setup commands in the root README are explicitly invoked installation steps; builds and tests do not change system packages or settings.

```powershell
.venv\Scripts\python.exe -m pytest Tests -q
.venv\Scripts\python.exe Scripts\validate_dataset.py Examples\Demo\dataset.json
.venv\Scripts\python.exe Scripts\check_repository.py
.venv\Scripts\python.exe Scripts\build.py
.venv\Scripts\python.exe Scripts\install_local.py
```

Tests use synthetic data and temporary histories. They cover pool sampling, grading, log resumption, invalid dataset rejection, many chapters, long Unicode text, supplementary-character highlighting, search, and settings round trips. The release smoke test runs the compiled executable on the original demo in an isolated home directory, produces a grading receipt, and exits. A separate private-dataset smoke test may validate real playback without adding private material to Git.

## Build output

PyInstaller stages a Windows x64 bundle under ignored `Out/Package/ProofQuest/`. The build then produces the single tracked `Dist/ProofQuest-win-x64.zip`. Its top-level `ProofQuest/` folder contains the EXE, shared runtime libraries, original demo, Help, notices, manifest, and a public `proofquest.ini` selecting `_internal/Examples/Demo/dataset.json`. Private dataset roots and personal settings are never build inputs.

The ZIP is the one maintained distribution copy and is not ignored. Personal usage and local testing happen in ignored `Local/ProofQuest/`, deployed by `Scripts/install_local.py`. Build metadata and relative source hashes are inside the ZIP; absolute local paths and raw task logs do not belong in public documentation.

The installer verifies the ZIP before extracting it into temporary ignored staging, then updates managed runtime files. An existing local INI and `Logs/` are preserved. The installer refuses to replace a running EXE. Builds do not modify the personal installation until the install script is invoked.

For migration from the old loose distribution layout, use `python Scripts/install_local.py --migrate-dist-state` once. It rebases the dataset path, copies history using SQLite backup, verifies it, then removes the old Dist history and restores demo defaults there. It refuses to merge independently used local settings/history. After successful migration and verification, retire the old `Dist/ProofQuest/` folder; the ZIP is the distributable.

Run the packaged smoke test from the root:

```powershell
Local\ProofQuest\ProofQuest.exe --home Out\SmokeHome --dataset Local\ProofQuest\_internal\Examples\Demo\dataset.json --smoke-test Out\Smoke\result.json
```

Use an explicit `--dataset` to test another manifest. `--home` isolates INI/logs from everyday use. `--smoke-test` is an explicit developer command that answers and grades a run, captures the app, checks audio-clock progression when audio is present, then exits.

Smoke playback is muted by default. Add `--audible-audio` for an intentional speaker/headset test, and verify the process's Windows audio-session output separately. The Windows player defaults to Qt's native `windows` media backend because the pinned FFmpeg backend can reject some headset channel layouts while its clock continues. `QT_MEDIA_BACKEND` can explicitly override this for diagnosis; the app does not change persistent environment settings.

## Source and publication boundaries

Run `Scripts/check_repository.py` before committing. It checks documentation links, forbidden staged paths, the ZIP inventory, bundled-demo identity, canonical INI, executable hash, and archive integrity. Inspect `git diff --cached --check`, the staged inventory, and `git status` as well. Personal INI/history stay ignored in Local. The only distribution INI is the public demo default inside the tracked ZIP.

Do not add a remote or push without explicit authorization. The original project code has no redistribution license assigned in this initial repository. Upstream runtime components keep their own licenses and notices; see [third-party notices](../THIRD-PARTY-NOTICES.md).

For statistical exports use `Scripts/analyze.py --database path/to/practice.sqlite3 --out Out/Analysis`. It opens the database read-only and writes question-attempt, topic, and question accuracy CSV files. Abandoned runs remain available in JSONL history but are excluded from accuracy summaries.
