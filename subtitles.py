#!/usr/bin/env python3
"""Generate APPROXIMATE subtitles based on scene lengths (not word-level forced alignment).
Human review required: timing and Vietnamese names may be wrong.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def stamp(seconds):
    ms = round(seconds * 1000)
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, msec = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{msec:03d}"


def chunks(text, max_words=10):
    words = text.strip().split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)] or []


def generate(root=ROOT):
    segments = json.loads((root / "timeline.json").read_text(encoding="utf-8"))["segments"]
    narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))["segments"]
    scripts = {r["index"]: r["text"] for r in narration}
    at, lines, counter = 0., [], 0
    for index, scene in enumerate(segments):
        d = float(scene["duration"])
        text = scripts.get(index, "")
        parts = chunks(text)
        if parts:
            total = sum(len(p) for p in parts)
            available = max(0., d - 1.0)
            elapsed = 0.
            for part in parts:
                length = available * len(part) / total
                start, end = at + .5 + elapsed, at + .5 + elapsed + length
                counter += 1
                lines.append(f"{counter}\n{stamp(start)} --> {stamp(end)}\n{part}\n")
                elapsed += length
        at += d
    output = root / "output" / "captions.srt"
    output.parent.mkdir(exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


if __name__ == "__main__":
    print("Wrote approximate, human-review-required subtitle file:", generate())
