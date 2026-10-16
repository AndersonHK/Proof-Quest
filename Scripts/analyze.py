"""Export completed-attempt data to CSV for later statistics, without changing history."""

import argparse, csv, json, sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def analyze(database, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)
    rows = []
    topics = defaultdict(lambda: [0, 0])
    questions = defaultdict(lambda: [0, 0])
    for run_id, created, snapshot, result in conn.execute(
        "SELECT id,created,snapshot,result FROM runs WHERE status='completed'"
    ):
        exam = json.loads(snapshot)
        result = json.loads(result)
        for outcome, q in zip(result["rows"], exam["questions"]):
            pick = outcome["selected"]
            good = outcome["correct_index"]
            right = int(outcome["correct"])
            rows.append(
                [
                    run_id,
                    created,
                    q["id"],
                    q["chapter"],
                    q["source"],
                    q["topic"],
                    q["prompt"],
                    q["options"][pick]["text"] if pick is not None else "",
                    q["options"][good]["text"],
                    right,
                    int(pick is None),
                ]
            )
            topics[q["topic"]][0] += right
            topics[q["topic"]][1] += 1
            questions[q["id"]][0] += right
            questions[q["id"]][1] += 1
    conn.close()
    with (destination / "attempts.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "run_id",
                "created_utc",
                "question_id",
                "chapter",
                "section",
                "topic",
                "question",
                "selected",
                "correct_answer",
                "correct",
                "unanswered",
            ]
        )
        writer.writerows(rows)
    for name, data in [("topics", topics), ("questions", questions)]:
        with (destination / (name + ".csv")).open(
            "w", newline="", encoding="utf-8-sig"
        ) as f:
            writer = csv.writer(f)
            writer.writerow([name[:-1], "correct", "seen", "accuracy"])
            for key, (right, n) in sorted(
                data.items(), key=lambda kv: kv[1][0] / kv[1][1]
            ):
                writer.writerow([key, right, n, right / n])
    return len(rows)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--database", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "Out" / "Analysis")
    args = p.parse_args()
    print(
        "Exported", analyze(args.database, args.out), "completed-run question attempts."
    )
