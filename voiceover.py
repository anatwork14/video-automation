#!/usr/bin/env python3
"""Generate per-scene Vietnamese/English voice with edge-tts (no paid API key).

Produces authentic-footage-safe AUDIO (synthetic voice is explicitly disclosed).
Stores word timestamps from the SAME TTS session for accurate subtitles.
Internet is required. Service availability/permissions can change.
"""
import argparse
import asyncio
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from review_gate import sha256_file, text_sha256

ROOT = Path(__file__).resolve().parent
RATE = re.compile(r"[+-]\d{1,3}%")


def normalize_rate_args(argv):
    """argparse treats a value like '-5%' as an option flag; turn '--rate -5%' into '--rate=-5%'."""
    out, i = [], 0
    while i < len(argv):
        if argv[i] == "--rate" and i + 1 < len(argv):
            out.append("--rate=" + argv[i + 1])
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def text_digest(text):
    return text_sha256(text)


def select_voice(language, selected):
    if language not in ("vi", "en"):
        raise ValueError(f"Unsupported language: {language}")
    if selected:
        if not selected.startswith(language + "-"):
            raise ValueError(f"Voice {selected!r} does not match narration language {language!r}")
        return selected
    return "vi-VN-NamMinhNeural" if language == "vi" else "en-US-GuyNeural"


def probe_duration(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True, capture_output=True, check=True,
    )
    return float(p.stdout.strip())


async def synthesize_segment(index, text, duration, voice, rate, force=False):
    output_dir = ROOT / "assets" / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)
    media = output_dir / f"{index:02d}.mp3"
    metadata = output_dir / f"{index:02d}.timings.json"
    digest = text_digest(text)
    if media.is_file() and metadata.is_file() and not force:
        saved = json.loads(metadata.read_text(encoding="utf-8"))
        if (saved.get("text_sha256") == digest and saved.get("voice") == voice
                and saved.get("rate") == rate):
            d = probe_duration(media)
            if d > duration - 0.3:
                raise ValueError(f"Scene {index} narration {d:.2f}s > {duration-.3:.2f}s. Edit script.")
            print(f"REUSE approved source text audio scene {index}: {d:.2f}s")
            return
        raise ValueError(
            f"Scene {index} audio is stale: narration/voice/rate changed. "
            "Listen/review new script, then run voiceover.py --force."
        )
    if media.exists() and not force:
        raise ValueError(
            f"Scene {index} existing manual audio has no timing metadata. "
            "Do not overwrite it: move it aside or explicitly use --force."
        )

    import edge_tts  # only after the local reuse/stale checks above (no network needed for those)

    temp_media = media.with_suffix(".partial.mp3")
    temp_media.unlink(missing_ok=True)
    boundaries = []
    try:
        client = edge_tts.Communicate(text=text, voice=voice, rate=rate, boundary="WordBoundary")
        with temp_media.open("wb") as f:
            async for chunk in client.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    boundaries.append({
                        "start_seconds": round(chunk["offset"] / 10_000_000, 4),
                        "duration_seconds": round(chunk["duration"] / 10_000_000, 4),
                        "text": chunk["text"],
                    })
        if temp_media.stat().st_size < 1024:
            raise RuntimeError("TTS produced no usable audio")
        if not boundaries:
            raise RuntimeError("TTS returned no WordBoundary timestamps; cannot create verified subtitle timings")
        actual = probe_duration(temp_media)
        if actual > duration - 0.3:
            raise ValueError(
                f"Scene {index} narration {actual:.2f}s is too long for "
                f"{duration:.2f}s scene. Shorten the text; DO NOT trim speech."
            )
        if any(x["start_seconds"] + x["duration_seconds"] > actual + .8 for x in boundaries):
            raise ValueError(f"Scene {index} timestamps exceed audio duration")
        payload = {
            "provider": "edge-tts",
            "synthetic_voice": True,
            "voice": voice,
            "rate": rate,
            "text_sha256": digest,
            "audio_sha256": sha256_file(temp_media),  # binds this timing file to these exact MP3 bytes
            "duration_seconds": round(actual, 3),
            "boundaries": boundaries,
        }
        temp_metadata = metadata.with_suffix(".partial.json")
        temp_metadata.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp_media.replace(media)
        temp_metadata.replace(metadata)
        print(f"CREATED scene {index}: {actual:.2f}s, {len(boundaries)} synchronized words")
    finally:
        temp_media.unlink(missing_ok=True)


async def run(args):
    timeline = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))["segments"]
    narration = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
    voice = select_voice(narration["language"], args.voice)
    if not shutil.which("ffprobe"):
        raise SystemExit("Install FFmpeg/ffprobe before TTS")
    if not RATE.fullmatch(args.rate):
        raise SystemExit("--rate must be a signed percentage such as +0%, -5% or +10%")
    print("Provider: edge-tts (online, currently no API key; review service terms yourself)")
    print("Voice:", voice, "Rate:", args.rate)
    for item in narration["segments"]:
        index = item["index"]
        if not (1 <= index < len(timeline)):
            raise ValueError(f"Invalid narration index {index}")
        text = item["text"].strip()
        if not text:
            raise ValueError(f"Empty narration {index}")
        await synthesize_segment(
            index, text, float(timeline[index]["duration"]),
            voice, args.rate, args.force,
        )
    print("Voice is SYNTHETIC; inspect pronunciation and science before publishing.")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default=None, help="vi-VN-NamMinhNeural / vi-VN-HoaiMyNeural, or matching English voice")
    parser.add_argument("--rate", default="+0%", help="e.g. +0%, -5%, +8%")
    parser.add_argument("--force", action="store_true", help="Regenerate only after reviewing changed script/voice")
    args = parser.parse_args(normalize_rate_args(sys.argv[1:] if argv is None else argv))
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
