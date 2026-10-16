# Current release validation

The current testing release is version 0.3.0 for Windows x64. `Dist/ProofQuest-win-x64.zip` contains the entire runnable bundle and a public INI selecting its original demo. The internal release manifest records source hashes, runtime versions, executable hash, and the file inventory. Personal use and testing take place in ignored `Local/ProofQuest/`.

## Checks

- Thirty-eight automated tests cover schema consistency, answer sampling/formatting, grading, persistence, dataset switching, Help, long Unicode content, ZIP/privacy boundaries, migration, window fitting, editable run counts, rotating feedback, red corrections, direct-click sliders, audio-device selection, Fable artwork/pose timing, and the new palette.
- Synthetic coverage includes 32 chapters, question text longer than 5,000 characters, and supplementary Unicode characters in timestamp-to-cursor mapping.
- The ZIP is extracted to an isolated location and its executable smoke test opens the bundled demo, grades all questions correctly, saves INI/history, captures the interface, and exits successfully without invoking a Python interpreter.
- The installed local executable is also tested with the ignored personal dataset and checks grading plus actual muted media-clock progression. Test history is isolated from personal history. Private content and detailed receipts are not committed.
- An unmuted Windows audio-session probe reproduces the FFmpeg backend's unsupported headset channel-layout failure, then verifies nonzero session output with the native Windows backend. The player also rebinds to the current system default or an explicitly selected device. A moving playback clock alone is not accepted as evidence of sound output.
- Practice and graded-report screenshots are visually inspected. Raw screenshots, test receipts, and build logs stay under ignored `Out/`.
- The staged-file and ZIP audits exclude private datasets, recordings, source generators, logs, and personal settings. The sole distribution INI is the canonical demo default. ZIP integrity, its executable hash, file inventory, and bundled demo identity are checked.

These checks establish behavior on the development Windows 10 x64 environment. Other Windows versions and machines have not been separately tested. Service-generated word boundaries provide synchronization; audio-device latency may vary between machines. The release is unsigned and has not been published to a remote.

See [Development](Development.md) for repeatable commands and [Dataset format](Dataset-Format.md) for the contracts validated by the tests. Academic correctness remains the dataset author's responsibility; schema validation cannot determine whether an answer is factually correct.
