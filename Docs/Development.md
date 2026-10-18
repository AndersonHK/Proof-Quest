# Development and release

Proof Quest uses PySide6 widgets and Qt Multimedia. Dataset loading, settings, exam generation/history, playback, and the main window have separate source modules. [Dataset format](Dataset-Format.md) owns external content contracts; [User guide](User-Guide.md) owns visible behavior.

`Src/theme.py` owns the Fable palette and shared explanation colors. Orange review panels and blue successful-explanation panels remain distinct from red/green answer marks; sidebar symbols and accessible status names provide non-color cues. Their text contrast is tested above 7:1. Palette review follows [Adobe Color accessibility guidance](https://adobe.design/ideas/inclusive-palettes-with-adobe-color) and [WCAG text-contrast guidance](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum). The header XP counter remains an unboxed, content-sized label; button focus changes border color without changing layout geometry. `Src/mascot.py` renders approved PNG poses from `Assets/Fable/`; `Src/mascot_scene.py` owns event-driven choreography and a click-through confetti layer. Four base poses plus two 4-by-2 atlases provide wink, walk, mug, sip, and cheer keyframes. Unused atlas cells are not played. Artwork remains unchanged; Qt selects atlas source rectangles and mirrors left-facing walks for rightward travel.

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

PyInstaller stages a Windows x64 bundle under ignored `Out/Package/ProofQuest/`. A native Qt icon packager writes 16–256-pixel fox ICO frames, embedded in the EXE and used by the window. Windows uses an explicit Fable app identity; the local installer refreshes only this app’s shell entries. The build then produces `Dist/ProofQuest-win-x64.zip`, `Dist/ProofQuest-win-x64.msi`, and `Dist/ProofQuest-python.zip`. Its top-level `ProofQuest/` folder contains the EXE, shared runtime libraries, original demo, Help, notices, manifest, and a public `proofquest.ini` selecting `_internal/Examples/Demo/dataset.json`. Private dataset roots and personal settings are never build inputs.

All three packages and `Dist/README.md` are tracked. Personal usage and local testing happen in ignored `Local/ProofQuest/`, deployed by `Scripts/install_local.py`. Build metadata and relative source hashes are inside the ZIP; absolute local paths and raw task logs do not belong in public documentation.

The installer verifies the ZIP before extracting it into temporary ignored staging, then updates managed runtime files. An existing local INI and `Logs/` are preserved. The installer refuses to replace a running EXE. Builds do not modify the personal installation until the install script is invoked.

For migration from the old loose distribution layout, use `python Scripts/install_local.py --migrate-dist-state` once. It rebases the dataset path, copies history using SQLite backup, verifies it, then removes the old Dist history and restores demo defaults there. It refuses to merge independently used local settings/history. After successful migration and verification, retire the old `Dist/ProofQuest/` folder; the ZIP is the distributable.

Run the packaged smoke test from the root:

```powershell
Local\ProofQuest\ProofQuest.exe --home Out\SmokeHome --dataset Local\ProofQuest\_internal\Examples\Demo\dataset.json --smoke-test Out\Smoke\result.json
```

Use an explicit `--dataset` to test another manifest. `--home` isolates INI/logs from everyday use. `--smoke-test` is an explicit developer command that answers and grades a run, captures the app, checks audio-clock progression when audio is present, then exits.

Smoke playback is muted by default. Add `--audible-audio` for an intentional speaker/headset test, and verify the process's Windows audio-session output separately. The Windows player defaults to Qt's native `windows` media backend because the pinned FFmpeg backend can reject some headset channel layouts while its clock continues. `QT_MEDIA_BACKEND` can explicitly override this for diagnosis; the app does not change persistent environment settings.

Speed changes briefly pause an active stream, set the new rate, then resume from its current position. This avoids a reproduced native Windows backend failure where a live rate change silences output while the clock advances. Paused/stopped playback stays paused/stopped; reselecting the current speed does nothing. The sequence is synchronous so a later user pause cannot be overridden by a queued resume. Volume, mute and output-device selection are preserved. When validating rate changes, measure Windows audio-session output as well as position advancement; the packaged smoke test checks transport continuity but is muted by default.

## Installer and Python editions

The full Windows pipeline uses 64-bit Python 3.9–3.12. `Scripts/build_msi.py` uses Windows' cabinet/installer APIs through standard-library `msilib`; Python 3.13 removed that module. No WiX install or dependency download occurs during a build. Run `python Scripts/build_msi.py` to rebuild only the installer from the audited portable ZIP.

The MSI is per-user under LocalAppData/Programs/ProofQuest, with a Start-menu shortcut and normal Installed apps removal. Its stable UpgradeCode identifies this product family; ProductCode changes with the three-part VERSION, and component GUIDs derive from stable paths. Older products are removed inside the upgrade transaction before installing new files, supporting rollback. Newer installed versions block downgrades. Files use HKCU component registration; there are no elevated custom actions. The MSI deliberately omits the portable demo INI: the application creates its own settings and selects the bundled demo on first launch. INI/history are not installer-managed, so repair, upgrade and uninstall preserve them. Close the app before maintenance. A package rebuilt with the same version is a repair, not a new upgrade; increment VERSION for releases.

`Scripts/build_python.py` runs independently on any supported Python platform using the standard library. It packages only the source/resource whitelist, dependencies list, license, Help, original demo and canonical source-layout INI. Its bundled README comes from `Packaging/Python-README.md`. Fixed ZIP metadata and a SHA-256 file inventory make unchanged inputs reproducible. No interpreter, native Qt binaries, private dataset or local environment enters this ZIP. Users install the pinned runtime dependency in a virtual environment. Supported wheel targets and platform testing limits are stated in the distribution README.

Validation covers MSI file-table inventory against the portable ZIP, per-user installation, an older-version upgrade, repair, downgrade rejection, uninstall with user-data preservation, and a demo launch from the installed files. An extracted Python ZIP is launched separately, outside the repository, to verify resources and demo defaults. macOS/Linux execution still needs native platform testing.

Installer design follows [Microsoft's installation-context guidance](https://learn.microsoft.com/en-us/windows/win32/msi/installation-context), [upgrade table](https://learn.microsoft.com/en-us/windows/win32/msi/upgrade-table), and [transaction sequencing](https://learn.microsoft.com/en-us/windows/win32/msi/removeexistingproducts-action).

## Source and publication boundaries

Run `Scripts/check_repository.py` before committing. It checks documentation links, forbidden staged paths, the ZIP inventory, bundled-demo identity, canonical INI, executable hash, and archive integrity. Inspect `git diff --cached --check`, the staged inventory, and `git status` as well. Personal INI/history stay ignored in Local. The only distribution INI is the public demo default inside the tracked ZIP.

Do not add a remote or push without explicit authorization. Original Proof Quest project files are distributed under the [MIT license](../LICENSE). The public ZIP includes that license alongside third-party notices. Upstream runtime components keep their own licenses and notices; see [third-party notices](../THIRD-PARTY-NOTICES.md).

For statistical exports use `Scripts/analyze.py --database path/to/practice.sqlite3 --out Out/Analysis`. It opens the database read-only and writes question-attempt, topic, and question accuracy CSV files. Abandoned runs remain available in JSONL history but are excluded from accuracy summaries.

Scoring uses attempted answers only. `normalize_result` derives scores from saved result rows without modifying stored history. Unanswered rows are excluded from topic/question aggregates and CSV attempts. Empty submissions have no percentage, record, or completion XP bonus.

## Companion dialogue

`Src/companion.py` owns original quips, a last-three-template exclusion queue, authored-hint lookup, and conservative review phrasing. `Src/speech.py` owns free-floating, click-through balloons parented to the central widget; they are not layout children. The header balloon is up to 560 logical pixels wide; its body clears the title while an offset pointer stays beside the mouth. Their tails track the mascot mouth, their words fade without reflow using UTF-16-aware Qt text ranges, and their bounds follow window resizing. A talking cycle spanning the text reveal uses the image-generated `Assets/Fable/talking.png` atlas. `Talking-Prompt.json` retains its built-in imagegen prompt.

Hint priority is question `hint`, bank `topic_hints[topic]`, then an explicitly general fallback. The answer pool and answer explanation are never used to synthesize a hint. Dataset authors must review hint quality and avoid giving the final answer. Clicks record `hint` events with question ID/index. `History.question_performance` reads completed attempts only, through the current run, with hint-assisted milestones distinguished. Speech caches those facts for the current run and invalidates on regeneration. Automatic review comments and quips avoid their last three template IDs; explicitly requesting a hint can show that same authored note again.

Tone research read more than two dozen click reactions across Bandit, Blood Elf Peasant, Draenei, Goblin Sappers, Goblin Zeppelin and other units in the [Warcraft III unit-quote collection](https://gamefaqs.gamespot.com/pc/589475-warcraft-iii-the-frozen-throne/faqs/18136). The useful patterns were brief mock indignation, self-aware asides, and a friendly return to the task. No game quotes or audio are shipped; Fable’s sixteen quips are original.

## Interface copy

Keep the game's personality. Short reactions such as “Right on target,” playful mascot quips, and earned milestone comments are intentional. Remove formulaic explanation headings and rhetorical scaffolding: “Why this is correct,” “Review this step,” “Here is what makes the answer work,” and reflexive “not X, but Y” framing. A brief reaction may lead directly into the actual explanation. Apply this to question review, the full report, saved history, and mascot copy.

Prefer a concrete statement to announcements of what the next sentence will explain. Remove inflated significance, vague progress metaphors, and repeated reassuring conclusions. Preserve useful instructions, actual statistics, scoring status, ordinary encouragement, and accurate mathematical distinctions. Do not blanket-replace negations or comparisons in question data. Review patterns in context; [Wikipedia’s writing-pattern guide](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) is a reference for editing, not an authorship test.

Quips occupy one line, followed by “Click Fable again for a hint.” on its own line. Shorten quips to fit at the normal font size; do not shrink or truncate them. The text layout uses an explicit line separator. Reveal duration, fully-visible reading time, and fade-out each grow with text length. Reading time begins only after the last word appears. `speech_timing` uses the larger of word count and non-space character count divided by six, supporting unspaced text too: reveal = 0.6 + 0.07×units seconds, reading = 3 + 0.4×units seconds, fade-out = 0.5 + 0.012×units seconds. Talking follows the reveal duration. Navigating or regenerating still dismisses obsolete messages immediately.

## Transcript structure

`Src/transcript_layout.py` maps unchanged spoken source spans into display blocks. Optional heading metadata can group spoken title sentences into one block or insert an unspoken topic label. The player styles heading levels at 24, 19, and 16 points over 14-point body text, retaining semantic Qt heading levels. Source-to-display and Unicode-to-UTF-16 mappings keep word highlighting, search, and sentence seeking accurate. Inserted headings have explicit seek targets and no fabricated word boundaries. Metadata validation rejects overlaps and partial-sentence ranges.

## Narration following

Following starts enabled for each listening session. Wheel/trackpad, scrollbar drag/track actions, and transcript navigation keys detach the view; programmatic highlighting and scrolling do not. The checkbox becomes a warm yellow, bold **Sync to Narration** button. Sync reveals the current word immediately, even while paused or before the first timestamp, without seeking or restarting playback. Existing highlighting continues while the user browses. The saved legacy follow preference is ignored on session startup.
