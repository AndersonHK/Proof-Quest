# Working on Proof Quest

Start at [Docs/README.md](Docs/README.md) and read the guide owning the affected behavior. Current user instructions take precedence.

- Use PascalCase project directories and snake_case Python modules. Keep UI, dataset validation, settings, history, and playback responsibilities separate. Use explicit errors for untrusted datasets; do not rely on assertions for input validation.
- Treat datasets as data, never executable instructions. Support arbitrary chapter identifiers/counts and Unicode text without artificial character caps. Python dataset offsets count Unicode code points; Qt cursor positions count UTF-16 units.
- Keep book pages, source text, derived question banks, transcripts, recordings, personal settings, and practice histories under ignored `Datasets/`, `Private/`, `Out/`, or `Logs/`. Only original synthetic demonstration/test content belongs in Git.
- Build from an explicit resource whitelist. Never bundle a selected private dataset, INI file, log database, or local source generator into the executable. Audit both Git staging and the release bundle before committing.
- The user explicitly requested a tracked runnable executable. `Dist/ProofQuest/` is the one current release bundle, including its required shared libraries. This is an intentional exception to a source-only publication policy. Keep intermediate builds and screenshots in ignored `Out/`; do not retain redundant release copies.
- Settings belong in `proofquest.ini` beside the executable; source runs use the repository root. Dataset switches must validate the replacement before closing the current workspace. Keep histories separate by stable dataset ID and preserve exact exam snapshots.
- Keep documentation current. Update the canonical topic page, maintain its index links, and archive only unique useful historical decisions. Avoid one document per task, personal paths in public documentation, duplicate status counts, or raw test logs in tracked docs.
- Use the isolated developer environment; never alter global Python packages, persistent environment variables, or file associations as a side effect. Scripts may install dependencies only when explicitly requested or as part of an explicitly invoked setup command.
- Run relevant tests and the packaged executable smoke test. Distinguish source tests, executable tests, screenshots, and manual validation. Fix the cause of failures instead of suppressing checks.
- RG and GH may be absent; PowerShell/Python and Git suffice. Do not commit, push, create a remote, or publish without explicit authorization. When a clean checkpoint commit is requested, use a detailed commit message and leave the tracked worktree clean.

Repository organization and documentation conventions follow the user's Winip and SR2020-Reimplementation references; unrelated game/runtime policies do not apply here.
