# Dataset format

A dataset is a UTF-8 JSON manifest plus a question bank and optional audio assets. The application supports arbitrary string chapter IDs, chapter counts, and text lengths. Practical capacity depends on available memory; the app does not impose a book-specific character or chapter cap.

## Manifest

Choose the manifest through Select new dataset. Paths are relative to its directory and must remain within that directory, including after symlink resolution. Loading data never executes scripts or interprets embedded instructions.

```json
{
  "schema_version": 1,
  "id": "sample-course",
  "title": "Sample course",
  "chapters": [{"id": "unit-a", "title": "Unit A"}],
  "question_bank": "questions.json",
  "audio": {"file": "audio/guide.mp3", "timings": "audio/timings.json"}
}
```

Omit `audio` for a question-only dataset. Each chapter must have at least one question. IDs must be unique and stable. The authoritative structural contracts are [dataset.schema.json](../Schemas/dataset.schema.json), [questions.schema.json](../Schemas/questions.schema.json), and [timings.schema.json](../Schemas/timings.schema.json). The runtime loader additionally verifies references, uniqueness, answer-pool overlap, timestamp order, and offset bounds.

## Question bank

The bank is an object containing a nonempty `version` string and a nonempty `questions` array. Every question has these fields:

| Field | Meaning |
|---|---|
| `id` | Unique, stable question ID |
| `chapter` | A string ID declared in the manifest |
| `topic` | Label used for accuracy statistics |
| `family` | Shared concept/template ID; short runs avoid repeated families |
| `source` | A section, page, or other human-readable reference |
| `prompt` | Question text, including any required assumptions |
| `correct` | At least two distinct valid answer formulations |
| `wrong` | At least eight distinct incorrect alternatives |
| `explanation` | Why the correct answer is correct |
| `answer_format` | Optional uniform display notation: `number`, `set`, `truth_column`, `complexity`, or `property_list` |

Each run selects one member of `correct` and four members of `wrong`. Equivalent correct formulations may appear in the pool but never together in an exam. No answer text may be duplicated or overlap between pools after trimming and case-folding. Source references are displayed as plain text. Questions, answers, and explanations may contain Unicode, line breaks, and long text; answer cards wrap instead of truncating.

Use one presentation style throughout each question's answer pool. Avoid mixing bare numbers or sets with phrases such as “The value is” or “The resulting set is.” With `answer_format`, the loader checks that all answers match the specified notation, that formatted distractors are distinct, and that none collide with a formatted correct answer. Correct formulations such as `7` and `7.0` can share the same canonical display because only one correct alternative is sampled. The engine saves consistent display strings in new snapshots. Older saved runs are formatted for viewing only when every displayed choice matches one narrowly recognized notation; the original log text and answer indexes remain unchanged.

## Audio and word timing

The timing object contains `text`, positive `duration_ms`, nonempty `words`, nonempty `sentences`, and optional `sections`. `voice` and `rate` are optional display metadata. Audio section count is independent of chapter count.

Each word has integer `start`, `end`, `start_ms`, `end_ms`, and `sentence`. Character offsets index the original transcript using Unicode code points; `end` is exclusive. `sentence` is a zero-based index. Each sentence has `start`, `end`, `start_ms`, and `first_word`, a zero-based word index. Sentence start time must equal its first word's start time. Words must lie inside their referenced sentence. Character ranges and start times are ordered, and all times must fit the recording. Spaces and punctuation may occur between timed words.

Sections contain a nonempty `title` and `start_ms`, ordered by time. The player converts code-point positions to Qt's UTF-16 cursor positions, including emoji and other supplementary-plane characters. Search also preserves these offsets.

Supply actual speech-service word boundaries or a verified forced alignment. Do not manufacture timing from a fixed words-per-minute assumption. Playback can use local formats supported by Qt Multimedia, such as MP3 or WAV.

## Generate a dataset from study material

1. Put the private source and all derived files under ignored `Datasets/<Course>/`, or outside the repository. Keep the entire dataset separate from application resources.
2. Give a generator the manifest and question schemas, the desired sections, and the source text. Ask it to cover definitions, conceptual distinctions, calculations, applications, and common mistakes. Preserve required domains and assumptions.
3. Require two independently valid answer formulations and at least eight plausible incorrect alternatives per question, with a concise explanation and source reference. Review distractors for accidental correctness and avoid answer-length or wording clues.
4. Use stable topic and family labels so variants do not crowd out distinct concepts. Validate before opening: `python Scripts/validate_dataset.py path/to/dataset.json`.
5. If audio is wanted, write a separate listening script, synthesize it, and align word/sentence offsets. Validate the timing JSON and inspect playback. Optional audio may be omitted while questions are being prepared.
6. Click Select new dataset. The INI stores the manifest path, not a copy of the source material.

The runtime validators establish format consistency, not academic correctness. Content authors must verify facts and correct/incorrect labels against their chosen source. Do not commit the book, generated material derived from it, private generator inputs, or practice logs. Only original synthetic examples and regression fixtures are tracked.
