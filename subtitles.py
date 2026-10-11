#!/usr/bin/env python3
"""Compose scene-aware SRT from edge-tts WordBoundary events.

Never estimate word timing from text length. For recorded voice use manually
reviewed subtitles in output/captions.srt or run --no-subtitles and edit in Descript.
"""
import argparse
import hashlib
import json
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
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def group_boundaries(boundaries, limit_chars=46, max_seconds=3.3):
    """Group timestamped words into two-line-friendly captions."""
    result = []
    current = []
    for word in boundaries:
        text = str(word["text"]).strip()
        if not text:
            continue
        start = float(word["start_seconds"])
        end = start + float(word["duration_seconds"])
        if start < 0 or end <= start:
            raise ValueError("Invalid WordBoundary timing")
        if current and start + .025 < current[-1][1]:
            raise ValueError("WordBoundary timestamps out of order")
        proposed = " ".join([x[2] for x in current] + [text])
        if current and (len(proposed) > limit_chars or
                        end - current[0][0] > max_seconds or
                        start - current[-1][1] > .6):
            result.append((current[0][0], current[-1][1], " ".join(x[2] for x in current)))
            current = []
        current.append((start, end, text))
    if current:
        result.append((current[0][0], current[-1][1], " ".join(x[2] for x in current)))
    return result


def generate(root=ROOT):
    segments = json.loads((root / "timeline.json").read_text(encoding="utf-8"))["segments"]
    narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))["segments"]
    scripts = {item["index"]: item["text"] for item in narration}
    if len(scripts) != len(narration):
        raise ValueError("Duplicate narration scene index")
    at = 0.0
    lines = []
    counter = 0
    for index, seg in enumerate(segments):
        duration = float(seg["duration"])
        if index in scripts:
            data_path = root / "assets" / "audio" / f"{index:02d}.timings.json"
            if not data_path.is_file():
                raise FileNotFoundError(
                    f"Missing exact timestamp data {data_path}. Run voiceover.py "
                    "or supply accurate SRT with editing tools; no fake timings."
                )
            metadata = json.loads(data_path.read_text(encoding="utf-8"))
            if metadata.get("text_sha256") != hashlib.sha256(scripts[index].encode("utf-8")).hexdigest():
                raise ValueError(f"Scene {index} script differs from voiceover. Regenerate audio.")
            boundaries = metadata.get("boundaries") or []
            if not boundaries:
                raise ValueError(f"Scene {index} contains no TTS word timestamps")
            if float(metadata.get("duration_seconds", 1e9)) > duration - .25:
                raise ValueError(f"Scene {index} narration overflows video")
            for start, end, text in group_boundaries(boundaries):
                if end > duration + 0.02:
                    raise ValueError(f"Scene {index} captions exceed scene duration")
                counter += 1
                lines.append(f"{counter}\n{stamp(at + start)} --> {stamp(at + end)}\n{text}\n")
        at += duration
    if not lines:
        raise ValueError("No synchronized captions were generated")
    target = root / "output" / "captions.srt"
    target.parent.mkdir(exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print("Synchronized SRT written:", generate())
