#!/usr/bin/env python3
"""Technical MP4 + build input-integrity checks. Human scientific QA remains mandatory."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from build_provenance import verify_build_receipt
from validate import validate

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output/GE1013_Kilauea_2018_DRAFT.mp4"


def run_qa(root=ROOT, output=OUTPUT):
    root, output = Path(root), Path(output)
    errors = validate(strict=True, root=root)
    errors.extend(verify_build_receipt(root, output))
    if not shutil.which("ffprobe"):
        errors.append("ffprobe not installed")
        return errors
    if not output.is_file():
        errors.append("Rendered MP4 not found")
        return errors
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)],
        capture_output=True, text=True,
    )
    if result.returncode:
        errors.append("ffprobe cannot open rendered MP4: " + result.stderr)
        return errors
    data = json.loads(result.stdout)
    duration = float(data["format"].get("duration", 0))
    video = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if not 108 <= duration <= 132:
        errors.append(f"Length outside 108–132 seconds: {duration}")
    if not video or (video[0].get("width"), video[0].get("height")) != (1080, 1920):
        errors.append("Expected 1080x1920 video")
    if not audio:
        errors.append("No audio stream")
    elif int(audio[0].get("sample_rate", 0)) < 16000:
        errors.append("Audio sample rate too low")
    print(f"Media probe: {duration:.2f}s; video={len(video)}; audio={len(audio)}")
    if shutil.which("ffmpeg") and audio:
        loudness = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(output),
             "-vn", "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True,
        )
        peak = re.findall(r"max_volume:\s*(-?(?:inf|\d+(?:\.\d+)?)) dB", loudness.stderr)
        if not peak:
            print("WARNING: audio peak measurement unavailable; human listener required")
        elif peak[-1] == "-inf" or float(peak[-1]) < -48:
            errors.append("Audio too quiet or silent for comfortable listening")
        else:
            print("Audio peak:", peak[-1], "dB")
    return errors


if __name__ == "__main__":
    problems = run_qa()
    for problem in problems:
        print("FAIL:", problem, file=sys.stderr)
    if problems:
        raise SystemExit(1)
    print("TECHNICAL AND BUILD-INTEGRITY QA PASS. HUMAN must still check science, footage context and quality.")
