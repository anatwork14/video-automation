#!/usr/bin/env python3
"""Optional per-scene synthetic voiceover using OpenAI TTS (audio only, not video).
Requires OPENAI_API_KEY, incurs API cost; listen and approve pronunciation.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--voice", default="alloy")
parser.add_argument("--force", action="store_true")
args = parser.parse_args()
if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("Set OPENAI_API_KEY first, or record a real audio narration instead.")
if not shutil.which("ffprobe"):
    raise SystemExit("Install ffprobe")
from openai import OpenAI

timeline = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))["segments"]
narration = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
scripts = {x["index"]: x["text"] for x in narration["segments"]}
out = ROOT / "assets" / "audio"
out.mkdir(parents=True, exist_ok=True)
client = OpenAI()
for index, text in sorted(scripts.items()):
    if not text.strip() or index >= len(timeline):
        raise SystemExit("Invalid narration segment index or text")
    dest = out / f"{index:02d}.mp3"
    if dest.exists() and not args.force:
        print("Keeping existing:", dest.name)
    else:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice=args.voice, input=text, response_format="mp3"
        ) as response:
            response.stream_to_file(dest)
        print("Generated AUDIO ONLY:", dest.name)
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", str(dest)], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("Invalid generated audio for segment " + str(index))
    d = float(result.stdout.strip())
    allocated = float(timeline[index]["duration"])
    if d > allocated - .1:
        print(f"WARNING: scene {index} narration {d:.1f}s > allotted {allocated:.1f}s. REVISE SCRIPT; NEVER AUTO-CUT.")
print("All generated speech must be audited by a group member. AI synthetic audio is not original human speech.")
