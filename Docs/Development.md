# Development and release

Proof Quest uses PySide6 widgets and Qt Multimedia. Dataset loading, settings, exam generation/history, playback, and the main window have separate source modules. [Dataset format](Dataset-Format.md) owns external content contracts; [User guide](User-Guide.md) owns visible behavior.

`Src/theme.py` owns the Fable palette and shared explanation colors. Orange review panels and blue successful-explanation panels remain distinct from red/green answer marks; headings provide non-color cues. Their text contrast is tested above 7:1. Palette review follows [Adobe Color accessibility guidance](https://adobe.design/ideas/inclusive-palettes-with-adobe-color) and [WCAG text-contrast guidance](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum). The header XP counter remains an unboxed, content-sized label; button focus changes border color without changing layout geometry. `Src/mascot.py` renders approved PNG poses from `Assets/Fable/`; `Src/mascot_scene.py` owns event-driven choreography and a click-through confetti layer. Four base poses plus two 4-by-2 atlases provide wink, walk, mug, sip, and cheer keyframes. Unused atlas cells are not played. Artwork remains unchanged; Qt selects atlas source rectangles and mirrors left-facing walks for rightward travel.

Animation renders at 30 fps with timed pose holds, intermediate eye/mug poses, and subtle breathing, walking and hopping transforms. This is pose-based animation, not thirty unique drawings per second. Finishing transitions through an optional 1.8-second cheer, left exit, right entrance with mug, and review idle. A question change triggers a 1.5-second sip without restarting an active sip. Mug clicks queue a brief mug-holding blink after any active sip. Regeneration cancels the prior sequence and returns the fox home; dataset switching/close stops all timers. Layout anchors reserve room without covering questions. Review animation hides on other tabs. Selection winks never depend on answer correctness.

`History.is_personal_best` compares exact score fractions against completed runs in the dataset-specific database before saving the new result. The first positive score qualifies, ties do not, and abandoned runs are excluded. The comparison includes all run sizes and chapter selections; it is a light gamification rule, not a measure of equal exam difficulty. Built-in image-generation prompts are retained in `Assets/Fable/Prompts.txt` and `Assets/Fable/Animation-Prompts.json`; third-party references and rejected drafts are not shipped.

## Environment and checks

Use an isolated environment and the pinned requirements. Setup commands in the root README are explicitly invoked installation steps; builds and tests do not change system packages or settings.

```powershell
.venv\Scripts\python.exe -m pytest Tests -q
.venv\Scripts\python.exe Scripts\validate_dataset.py Examples\Demo\dataset.json
.venv\Scripts\python.exe Scripts\check_repository.py
.venv\Scripts\python.exe Scripts\build.py
.venv\Scripts\python.exe Scripts\install_local.py
```

Use [Question curation](Question-Curation.md) and `Scripts/audit_choices.py` when maintaining datasets. Heuristic audits flag possible clues; they do not certify academic correctness.

Tests use synthetic data and temporary histories. They cover pool sampling, grading, log resumption, invalid dataset rejection, many chapters, long Unicode text, supplementary-character highlighting, search, and settings round trips. The release smoke test runs the compiled executable on the original demo in an isolated home directory, produces a grading receipt, and exits. A separate private-dataset smoke test may validate real playback without adding private material to Git.

## Build output

PyInstaller stages a Windows x64 bundle under ignored `Out/Package/ProofQuest/`. A native Qt icon packager writes 16–256-pixel fox ICO frames, embedded in the EXE and used by the window. Windows uses an explicit Fable app identity; the local installer refreshes only this app’s shell entries. The build then produces the single tracked `Dist/ProofQuest-win-x64.zip`. Its top-level `ProofQuest/` folder contains the EXE, shared runtime libraries, original demo, Help, notices, manifest, and a public `proofquest.ini` selecting `_internal/Examples/Demo/dataset.json`. Private dataset roots and personal settings are never build inputs.

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

Scoring uses attempted answers only. `normalize_result` derives scores from saved result rows without modifying stored history. Unanswered rows are excluded from topic/question aggregates and CSV attempts. Empty submissions have no percentage, record, or completion XP bonus.
