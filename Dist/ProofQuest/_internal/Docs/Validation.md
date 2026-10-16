# Current release validation

The initial standalone release is version 0.2.0 for Windows x64. The release manifest beside the executable records its source hashes, interpreter/runtime versions, and executable hash. It contains the original demo only; the personal course dataset is external.

## Checks

- Fifteen automated tests cover schema consistency, answer-pool sampling, grading, SQLite restart, dataset isolation, invalid input rejection, settings round trips, dataset switching, Help, long Unicode content, and preservation of private settings/history during release refresh.
- Synthetic coverage includes 32 chapters, question text longer than 5,000 characters, and supplementary Unicode characters in timestamp-to-cursor mapping.
- The packaged executable smoke test opens the bundled demo, answers and grades all questions correctly, saves INI/history in an isolated directory, captures the interface, and exits successfully.
- A separate executable smoke test loads the ignored personal dataset and checks grading plus actual muted media-clock progression. Its content and detailed receipt are not committed.
- Practice and graded-report screenshots are visually inspected. Raw screenshots, test receipts, and build logs stay under ignored `Out/`.
- The staged-file and release-resource audits exclude private datasets, recordings, source generators, logs, and INI settings. The committed runtime resource whitelist is application assets, current documentation, schemas, and the original demo.

These checks establish behavior on the development Windows 10 x64 environment. Other Windows versions and machines have not been separately tested. Service-generated word boundaries provide synchronization; audio-device latency may vary between machines. The release is unsigned and has not been published to a remote.

See [Development](Development.md) for repeatable commands and [Dataset format](Dataset-Format.md) for the contracts validated by the tests. Academic correctness remains the dataset author's responsibility; schema validation cannot determine whether an answer is factually correct.
