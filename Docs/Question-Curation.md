# Question curation

Structural validation is necessary but does not establish learning quality. Review every pool and its possible five-choice displays. A correct answer must win by the concept being tested, not by wording, category counts, typography, or implausible alternatives.

## Anti-pattern register

| ID | Anti-pattern | Required curation response |
|---|---|---|
| AP01 | Bare values or sets mixed with “The value is …” or “The resulting set is …”, especially on the correct answer | Use one notation for the entire pool; declare `answer_format` when supported. |
| AP02 | One “invalid/false/no” choice among four “valid/true/yes” choices, or the reverse | Rewrite as verdict **and justification**, with plausible wrong justifications on both sides. Curate samples with 2:3 or 3:2 splits; make neither majority nor minority reliably correct. |
| AP03 | Several distractors express the same classification or mathematical answer in different words | Remove semantic duplicates, or rewrite into genuinely different complete claims. Do not fill five slots with synonyms. |
| AP04 | Only the correct choice concerns the question's subject; distractors are unrelated definitions or filler | Use nearby concepts and common misconceptions at the same conceptual level. |
| AP05 | Impossible values, signs, units, domains, or types eliminate distractors without using the target concept | For example, cardinalities cannot be negative. Keep plausible domain-valid distractors unless domain membership is itself the target. |
| AP06 | A true statement is labeled wrong without making the question's specific target clear | State whether the target is a contrapositive, a converse, a definition, a tight bound, or another particular form. Explain why a true but nonresponsive choice does not answer that target. |
| AP07 | The right answer alone is much longer, qualified, polished, or explanatory | Match grammar, precision and approximate length across the pool. Do not pad with nonsense merely to equalize length. |
| AP08 | Only correct alternatives use distinctive notation, constant factors, punctuation, or formatting | Canonicalize equivalent representations where safe, including the generated `Θ(2 × expression)` variant. Review both correct formulations. |
| AP09 | Position, magnitude rank, repeated wording, or answer-frequency patterns predict correctness | Shuffle uniformly and inspect many generated runs. Avoid always making the correct value the midpoint of a distractor range. |
| AP10 | A classification plus an incorrect reason is ambiguously treated as partly correct | Explicitly ask for both the classification and justification. Verify the complete conjunction for each alternative. |
| AP11 | A naturally binary or four-way question is padded to five choices with absurd alternatives | Redesign the task around reasoning or a richer application. The pool minimum is not an excuse for filler. |

AP01 and AP08 record the numeric/set formatting examples; AP02 records the verdict imbalance; AP06 records the distinction between a true implication and the requested contrapositive. Keep this register current as new examples are found.

## Review and generation workflow

1. Verify domains, assumptions, the target concept, both correct formulations, and every distractor's actual error. Check the source privately when required.
2. Compare answer shape, topic, syntax, specificity and length. Name the misconception behind each distractor; replace candidates that exist only to reach eight.
3. Check semantic equivalence across all alternatives. A textual uniqueness check cannot do this.
4. If unrestricted random sampling can recreate a clue, add `distractor_sets`: approved groups of four indexes into the wrong-answer pool. Each group must work with **every** correct formulation. The engine randomly chooses a group, then one correct formulation and shuffles all five positions. Repeating groups is allowed for explicit sampling weights; document the reason in the private generator.
5. Run structural validation, then `python Scripts/audit_choices.py path/to/dataset.json --out Out/choice-audit.json`. Inspect its warnings, plus several manual displays across all topics. The audit samples 200 seeded displays per question and only detects selected surface patterns; zero warnings is not proof of content quality.
6. Add synthetic regression examples to tests. Keep source-derived fixes and reports inside the ignored dataset. Retain original historical exam snapshots: curation changes new runs, not what was previously shown or graded.

See [Dataset format](Dataset-Format.md) for schema details and [Development](Development.md) for validation commands.
