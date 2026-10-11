#!/usr/bin/env python3
"""Compose scene-aware captions from edge-tts WordBoundary events.

Timing comes ONLY from the TTS word boundaries (never estimated from text
length). Display text is mapped back onto the approved script's own tokens so
punctuation and casing survive; if that mapping is ambiguous the raw boundary
text is used instead. For recorded voice use manually aligned captions
(Descript etc.) or run --no-subtitles.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

from review_gate import text_sha256

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


def _key(text):
    return " ".join(re.sub(r"[^\w]", "", w) for w in unicodedata.normalize("NFC", str(text)).lower().split()
                    if re.sub(r"[^\w]", "", w))


def align_to_script(boundaries, script):
    """Replace boundary text with the matching script tokens (keeps punctuation). Timing is untouched.

    Edge TTS may merge tokens ("ngày 16 tháng 5" is one boundary). Returns None if
    the boundaries do not consume the script exactly, so callers can fall back.
    """
    tokens = unicodedata.normalize("NFC", str(script)).split()
    aligned, k = [], 0
    for word in boundaries:
        target, taken = _key(word["text"]), []
        if not target:
            return None
        while k < len(tokens) and _key(" ".join(taken)) != target:
            taken.append(tokens[k])
            k += 1
            if len(_key(" ".join(taken))) > len(target):
                return None
        if _key(" ".join(taken)) != target:
            return None
        aligned.append(dict(word, text=" ".join(taken)))
    if any(_key(t) for t in tokens[k:]):
        return None
    if aligned and k < len(tokens):  # trailing punctuation-only tokens belong to the last word
        aligned[-1]["text"] += " " + " ".join(tokens[k:])
    return aligned


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


def scene_cues(root=ROOT):
    """{scene index: [(start, end, text), ...]} with times relative to the scene start."""
    root = Path(root)
    segments = json.loads((root / "timeline.json").read_text(encoding="utf-8"))["segments"]
    narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))["segments"]
    scripts = {item["index"]: item["text"] for item in narration}
    if len(scripts) != len(narration):
        raise ValueError("Duplicate narration scene index")
    cues = {}
    for index, seg in enumerate(segments):
        if index not in scripts:
            continue
        duration = float(seg["duration"])
        data_path = root / "assets" / "audio" / f"{index:02d}.timings.json"
        if not data_path.is_file():
            raise FileNotFoundError(
                f"Missing exact timestamp data assets/audio/{index:02d}.timings.json. Run voiceover.py "
                "or supply accurate SRT with editing tools; no fake timings."
            )
        metadata = json.loads(data_path.read_text(encoding="utf-8"))
        if metadata.get("text_sha256") != text_sha256(scripts[index]):
            raise ValueError(f"Scene {index} script differs from voiceover. Regenerate audio.")
        boundaries = metadata.get("boundaries") or []
        if not boundaries:
            raise ValueError(f"Scene {index} contains no TTS word timestamps")
        if float(metadata.get("duration_seconds", 1e9)) > duration - .25:
            raise ValueError(f"Scene {index} narration overflows video")
        words = align_to_script(boundaries, scripts[index]) or boundaries
        cues[index] = []
        for start, end, text in group_boundaries(words):
            if end > duration + 0.02:
                raise ValueError(f"Scene {index} captions exceed scene duration")
            cues[index].append((start, end, text))
    if not any(cues.values()):
        raise ValueError("No synchronized captions were generated")
    return cues


def generate(root=ROOT):
    """Write output/captions.srt (absolute times) for review and for platform caption upload."""
    root = Path(root)
    segments = json.loads((root / "timeline.json").read_text(encoding="utf-8"))["segments"]
    cues = scene_cues(root)
    lines, at, counter = [], 0.0, 0
    for index, seg in enumerate(segments):
        for start, end, text in cues.get(index, []):
            counter += 1
            lines.append(f"{counter}\n{stamp(at + start)} --> {stamp(at + end)}\n{text}\n")
        at += float(seg["duration"])
    target = root / "output" / "captions.srt"
    target.parent.mkdir(exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print("Synchronized SRT written:", generate().relative_to(ROOT).as_posix())
