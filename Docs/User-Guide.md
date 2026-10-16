# Using Proof Quest

Proof Quest practices recall with randomized exams and helps review material through synchronized audio. It works offline after installation and never uploads your answers.

Fable is the fox in the header and application icon. The violet/plum/cream palette comes from its artwork. It blinks while you practice and winks when you select an answer, regardless of correctness. On finishing, it walks off the left edge and returns from the right carrying a mug, settling beneath Regenerate test. Changing the reviewed question starts a short sip; switching again lets that sip finish. Clicking the fox with its mug blinks while holding the mug, after any active sip. Regenerating sends it off to the right and back into the header without the mug. Click Fable in the header for a quip, then click again for a hint on the current question. A new personal-best percentage for the active dataset starts with a small paws-up cheer and sparse confetti from both sides, angled about 30 degrees upward. The first nonzero completed result establishes a record; equal scores and abandoned runs do not trigger another celebration. Records compare percentages across all run sizes and chapter filters for that dataset. The motions are intentionally quiet and never block controls. Green still identifies correct answers and red still marks incorrect answer selections. Explanation panels use blue for correct reasoning and orange for a step to review, with scoring status shown separately.

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

**Finish exam** grades every question. Unanswered questions are marked not attempted and excluded from scores, accuracy, weak-topic statistics, streaks, and records. Correct choices are highlighted green; an incorrect selection is marked separately. The report explains the answer and cites the dataset's source reference. Select a question in the sidebar to inspect its five choices.

Missed-answer explanations use muted orange; successful-answer explanations use blue. Answer choices retain green/red grading colors. Short reactions rotate through twelve phrases per outcome and remain stable while revisiting the same question. They lead directly into the explanation, without extra explanatory headings. The submitted-exam banner shows the score and items to revisit, without elapsed time. Timing remains available in history and exports.

Regenerating an unfinished run preserves it as abandoned after a prompt. Closing or switching datasets preserves the unfinished run for later resumption. Previously saved runs use the same attempted-only scoring when viewed or analyzed; their stored snapshots are not rewritten. Completed and abandoned snapshots retain the exact questions, five choices, order, answers, timing, and answer-change events.

## Fable’s study notes

While Fable is in the header, the first click offers an original quip and invites a second click for a hint. The hint explains a topic or approach supplied by the dataset, without selecting or grading an answer. Changing questions resets the invitation. Hint use is recorded with the run; it does not reduce the score.

After grading, Fable comments when it arrives with the mug and when the reviewed question changes. Comments can mark a first correct answer, a consecutive-correct streak, or accuracy on that particular question once at least five attempts exist. Only attempted answers in completed runs count; skipped questions and abandoned runs neither add attempts nor break streaks. Hint-assisted first successes and streaks are identified. Numerical comments describe recorded attempts, not predicted mastery. Quips and review comments avoid their previous three message templates.

The warm yellow balloon floats above the interface, with a tail beside Fable’s mouth. It never takes layout space or intercepts clicks. The quip fits on one line, with the hint invitation on a separate second line. Longer hints reveal more slowly and stay fully visible for longer before fading. Fable talks while the words appear. Active sips finish before review speech begins; rapid question changes replace the pending comment with the current question’s comment. Dataset changes and closing cancel pending speech. A dataset without an authored hint receives a general study prompt rather than an invented explanation.

## Listen

Datasets with audio show it in **Listen + transcript**. Soft plum marks text already spoken; warm gold marks the current word. **Follow narration** scrolls with the recording. Uncheck it to browse without automatic scrolling.

Click a word to jump to its sentence's beginning. **Ctrl+F** focuses search; **Enter**, **Next match**, and **Previous match** find and jump through occurrences. Purple marks the found text. **Ctrl+Space** toggles playback. Volume, playback speed, section selection, and ten-second skip controls are available. Leaving the listening tab pauses playback.

Click anywhere on the playback bar to seek to that position; click the volume track to set that level. Both sliders also support dragging and keyboard adjustment. **Audio output** follows the current system default unless you choose a particular speaker or headset. That choice is saved in the INI. If a selected device disconnects, the player falls back to the system default. Playback on Windows uses the native Windows audio backend for headset compatibility.

Audio is optional. A question-only dataset remains fully usable. Word highlights require actual word-timing metadata; the app does not estimate timestamps from reading speed.

## Progress and storage

**Your progress** shows topic accuracy and run history for the active dataset. Double-click a saved run to review it without replacing the active exam. **Export all runs as JSONL** writes exact snapshots for later analysis. Low sample counts are labeled so they are not mistaken for reliable mastery estimates.

Correct answers award ten XP each; finishing a run with at least one attempted question awards twenty. Each 250 XP adds a level. Abandoned runs do not affect XP or mastery accuracy.

Settings are in `proofquest.ini` beside the executable. Source-code launches keep the INI at the repository root. History databases are under adjacent `Logs/`, separated by dataset ID. A dataset's ID should remain stable across revisions and different books should use different IDs. Elapsed exam time counts the open run, including reading/listening time, but excludes time while the app is closed.

If the selected dataset has moved, choose its new manifest at startup or use `ProofQuest.exe --dataset path\to\dataset.json`. No account, cloud service, or global Python installation is needed for the packaged app.
