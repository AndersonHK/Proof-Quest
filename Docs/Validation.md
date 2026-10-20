# Current release validation

Version 0.4.10 provides the Windows portable ZIP, per-user Windows MSI, and Python-source ZIP listed in [Distribution editions](../Dist/README.md). All contain the original demo and public resources only. Personal settings, history, source pages, course datasets, transcripts and recordings remain external. Detailed receipts, screenshots and build logs stay in ignored `Out/`.

## Automated checks

The 90-test suite covers dataset/schema validation, answer sampling and formatting, attempted-only grading, persistence, dataset switching, Help, Unicode content, packaging boundaries, narration controls, transcript headings and word mapping, Fable's animation/dialogue, and UI layout.

Active-time tests use an injected monotonic clock to verify activity-triggered startup, focus suspension/resumption, explicit pause across tabs and question activity, restored runs, saved pause intent, finished totals and regeneration. UI checks verify fixed timer/button geometry, reserved mascot space through the full animation round trip, compact card height, timer clearance and a review pointer that moves with its bubble.

Synthetic fixtures include 32 chapters, question text longer than 5,000 characters, and supplementary Unicode characters. Choice-surface audits sample 200 displays per question; academic correctness and semantic distractor quality still require editorial review.

## Runtime and visual checks

- Packaged demo and private-dataset smoke tests exercise answer selection, grading, hint logging, settings/history, and the mascot's review/sip/return sequence. Audio-enabled tests also verify muted clock progression through a playback-speed change. Test homes are isolated from personal history.
- A native Windows two-window probe verifies that focus loss excludes time, focus return resumes it, running transcript time counts, and explicit pause remains effective on the transcript tab.
- The approved card and speech layout was visually inspected at native 200% scaling. The single-line card measured 54 logical pixels tall. Fable's space is reserved before grading; the review bubble retains its normal width/padding and lowers its body and short pointer together to clear the timer controls. Speech remains a floating overlay and can cover underlying review text while visible.
- Earlier unmuted Windows audio-session probes reproduced silent output with the FFmpeg backend and with direct native playback-rate changes. The native backend plus pause/change-rate/resume sequence produced nonzero output at each tested speed transition. A moving media clock alone is not evidence of audible output.

## Distribution checks

Release audits verify documentation links, staged private-path exclusions, ZIP integrity, public-demo identity, canonical settings, source/executable hashes, and MSI inventory/version agreement with the portable ZIP. The Python ZIP is checked against its exact public source/resource whitelist and SHA-256 inventory, and launched from a separate extracted folder.

The installer lifecycle was validated when the MSI pipeline was introduced: per-user install, older-version upgrade, repair at the remembered install path, downgrade rejection, and uninstall all behaved as expected. User-created INI/history survived maintenance, and installed payload bytes matched the portable ZIP. The installer implementation is unchanged in this release; current MSI inventory and version checks are repeated for the rebuilt package.

## Limits

Runtime validation is on Windows 10 x64. Native macOS/Linux behavior and other Windows machines have not been separately tested. Word boundaries come from the dataset's timing metadata; device latency may vary. Windows packages are unsigned. Existing historical elapsed totals are preserved because earlier unfocused intervals cannot be reconstructed retroactively.

See [Development](Development.md) for repeatable commands and [Dataset format](Dataset-Format.md) for validated content contracts. Proof Quest is MIT licensed; external datasets retain their authors' rights and are not distributed with the app.
