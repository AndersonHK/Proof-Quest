"""Map spoken source spans to styled display blocks without changing timestamps."""

import bisect


def build_transcript(data):
    sentences = data["sentences"]
    text = data["text"]
    headings = {h["start"]: h for h in data.get("headings", [])}
    pieces = []
    blocks = []
    segments = []
    sentence_offsets = [0] * len(sentences)
    offset = 0

    def append(content, level=0, inserted=False, sentence=0):
        nonlocal offset
        if pieces:
            offset += 1
        start = offset
        pieces.append(content)
        offset += len(content)
        blocks.append(
            {
                "start": start,
                "end": offset,
                "level": level,
                "inserted": inserted,
                "sentence": sentence,
            }
        )
        return start

    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        heading = headings.get(sentence["start"])
        if heading and "title" in heading:
            append(heading["title"], heading["level"], True, i)
        end = heading["end"] if heading and "end" in heading else sentence["end"]
        level = heading["level"] if heading and "end" in heading else 0
        start = sentence["start"]
        base = append(text[start:end], level, False, i)
        segments.append((start, end, base))
        while i < len(sentences) and sentences[i]["start"] < end:
            sentence_offsets[i] = base + sentences[i]["start"] - start
            i += 1
    display = "\n".join(pieces)
    to_qt = [0]
    for char in display:
        to_qt.append(to_qt[-1] + (2 if ord(char) > 0xFFFF else 1))
    starts = [s[0] for s in segments]
    word_ranges = []
    for word in data["words"]:
        start, end, base = segments[bisect.bisect_right(starts, word["start"]) - 1]
        if word["end"] > end:
            raise ValueError("Word crosses a transcript display block.")
        word_ranges.append(
            (to_qt[base + word["start"] - start], to_qt[base + word["end"] - start])
        )
    for block in blocks:
        block["start"] = to_qt[block["start"]]
        block["end"] = to_qt[block["end"]]
    return {
        "display": display,
        "to_qt": to_qt,
        "blocks": blocks,
        "word_ranges": word_ranges,
        "sentence_offsets": [to_qt[p] for p in sentence_offsets],
    }
