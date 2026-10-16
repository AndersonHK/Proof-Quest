# Development and release

Proof Quest uses PySide6 widgets and Qt Multimedia. Dataset loading, settings, exam generation/history, playback, and the main window have separate source modules. [Dataset format](Dataset-Format.md) owns external content contracts; [User guide](User-Guide.md) owns visible behavior.

## Environment and checks

Use an isolated environment and the pinned requirements. Setup commands in the root README are explicitly invoked installation steps; builds and tests do not change system packages or settings.

```powershell
.venv\Scripts\python.exe -m pytest Tests -q
.venv\Scripts\python.exe Scripts\validate_dataset.py Examples\Demo\dataset.json
.venv\Scripts\python.exe Scripts\check_repository.py
.venv\Scripts\python.exe Scripts\build.py
```

Tests use synthetic data and temporary histories. They cover pool sampling, grading, log resumption, invalid dataset rejection, many chapters, long Unicode text, supplementary-character highlighting, search, and settings round trips. The release smoke test runs the compiled executable on the original demo in an isolated home directory, produces a grading receipt, and exits. A separate private-dataset smoke test may validate real playback without adding private material to Git.

## Build output

PyInstaller produces a Windows x64 one-folder bundle at `Dist/ProofQuest/`. Keep `ProofQuest.exe` and `_internal/` together. Shared runtime libraries remain separate and replaceable. The script bundles only `Assets`, original `Examples/Demo`, `Schemas`, and current `Docs`; private dataset roots and settings are never build inputs. It does not embed the selected dataset in the executable.

The complete current runtime is intentionally committed because the user requested the compiled executable. This is the only maintained release copy. `Out/` holds ignored compiler/intermediate artifacts and smoke-test screenshots. Avoid redundant backups. Build metadata and relative source hashes belong in the release manifest; absolute local build paths and task logs do not belong in public documentation.

Packaging first builds under `Out/Package`, then updates only managed release files. It preserves adjacent `proofquest.ini`, `Logs/`, and private datasets. Close the app before rebuilding so Windows can replace its loaded executable and libraries.

Run the packaged smoke test from the root:

```powershell
Dist\ProofQuest\ProofQuest.exe --home Out\SmokeHome --smoke-test Out\Smoke\result.json
```

Use an explicit `--dataset` to test another manifest. `--home` isolates INI/logs from everyday use. `--smoke-test` is an explicit developer command that answers and grades a run, captures the app, checks audio-clock progression when audio is present, then exits.

## Source and publication boundaries

Run `Scripts/check_repository.py` before committing. It checks documentation links, forbidden staged paths, and the release resource whitelist. Inspect `git diff --cached --check`, the staged inventory, and `git status` as well. Local private files, INI settings, and history databases must remain ignored, including copies beneath Dist.

Do not add a remote or push without explicit authorization. The original project code has no redistribution license assigned in this initial repository. Upstream runtime components keep their own licenses and notices; see [third-party notices](../THIRD-PARTY-NOTICES.md).

For statistical exports use `Scripts/analyze.py --database path/to/practice.sqlite3 --out Out/Analysis`. It opens the database read-only and writes question-attempt, topic, and question accuracy CSV files. Abandoned runs remain available in JSONL history but are excluded from accuracy summaries.
