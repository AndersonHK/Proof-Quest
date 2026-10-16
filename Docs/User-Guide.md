# Using Proof Quest

Proof Quest practices recall with randomized exams and helps review material through synchronized audio. It works offline after installation and never uploads your answers.

## Install and update

Extract the complete distribution ZIP to a writable folder and run `ProofQuest.exe` inside its `ProofQuest` folder. The EXE, `_internal` libraries/resources, sample demo, Help content, and demo-configured `proofquest.ini` are all included. Do not run the EXE inside the ZIP or move it away from its runtime folder.

In the development repository, the personal installation is `Local/ProofQuest/`. Run `python Scripts/install_local.py` to install or update it from the tracked ZIP in `Dist/`. Close the local app before updating. The update preserves your INI, course selection, and history. Local files are ignored by Git; the distributable always starts with the public demo.

## Choose material

Click **Select new dataset** near the top right and select a `dataset.json` manifest. Its folder contains a question bank and may contain audio with word timestamps. Any subject and any number of chapters are supported. Chapter filters scroll when needed. Invalid datasets show an explanation and leave the current dataset open.

The selection is remembered in `proofquest.ini` beside the executable. Keep the selected dataset files together. The bundled demo is original sample content; use an external private dataset for your coursework.

## Practice

Choose Sprint, Balanced, Deep dive, Full bank, Weak-topic sprint, or Custom. Choose the chapters, then click **Regenerate test**. If a dataset has fewer questions than requested, the run uses all available questions once.

Full bank displays the total bank size in its label. You can always edit the adjacent question count; doing so selects Custom. Selecting a preset restores its count. The window grows vertically to fit the five choices and review notification when the current monitor has enough usable space, and retains scrolling when it does not.

Every question displays one randomly chosen correct alternative and four randomly chosen incorrect alternatives. The five choices are shuffled. Correctness stays hidden until you finish. Use **Next question**, **Previous**, or the question sidebar to navigate; a filled circle means answered, not necessarily correct. You may change or clear an answer before grading. Keys **1–5** select answers; **Alt+Right** advances.

**Finish exam** grades every question. Unanswered questions count as misses. Correct choices are highlighted green; an incorrect selection is marked separately. The report explains the answer and cites the dataset's source reference. Select a question in the sidebar to inspect its five choices.

Missed-answer explanations use red; successful-answer explanations use green. Feedback introductions rotate through twelve phrases per outcome and remain stable while revisiting the same question. The submitted-exam banner shows the score and items to revisit, without elapsed time. Timing remains available in history and exports.

Regenerating an unfinished run preserves it as abandoned after a prompt. Closing or switching datasets preserves the unfinished run for later resumption. Completed and abandoned snapshots retain the exact questions, five choices, order, answers, timing, and answer-change events.

## Listen

Datasets with audio show it in **Listen + transcript**. Teal marks text already spoken; gold marks the current word. **Follow narration** scrolls with the recording. Uncheck it to browse without automatic scrolling.

Click a word to jump to its sentence's beginning. **Ctrl+F** focuses search; **Enter**, **Next match**, and **Previous match** find and jump through occurrences. Purple marks the found text. **Ctrl+Space** toggles playback. Volume, playback speed, section selection, and ten-second skip controls are available. Leaving the listening tab pauses playback.

Click anywhere on the playback bar to seek to that position; click the volume track to set that level. Both sliders also support dragging and keyboard adjustment. **Audio output** follows the current system default unless you choose a particular speaker or headset. That choice is saved in the INI. If a selected device disconnects, the player falls back to the system default. Playback on Windows uses the native Windows audio backend for headset compatibility.

Audio is optional. A question-only dataset remains fully usable. Word highlights require actual word-timing metadata; the app does not estimate timestamps from reading speed.

## Progress and storage

**Your progress** shows topic accuracy and run history for the active dataset. Double-click a saved run to review it without replacing the active exam. **Export all runs as JSONL** writes exact snapshots for later analysis. Low sample counts are labeled so they are not mistaken for reliable mastery estimates.

Correct answers award ten XP each; finishing a run awards twenty. Each 250 XP adds a level. Abandoned runs do not affect XP or mastery accuracy.

Settings are in `proofquest.ini` beside the executable. Source-code launches keep the INI at the repository root. History databases are under adjacent `Logs/`, separated by dataset ID. A dataset's ID should remain stable across revisions and different books should use different IDs. Elapsed exam time counts the open run, including reading/listening time, but excludes time while the app is closed.

If the selected dataset has moved, choose its new manifest at startup or use `ProofQuest.exe --dataset path\to\dataset.json`. No account, cloud service, or global Python installation is needed for the packaged app.
